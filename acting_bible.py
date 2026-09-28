from __future__ import annotations
import json, re, unicodedata
from pathlib import Path
from typing import Any

BASE=Path(__file__).resolve().parent
BIBLE_PATH=BASE/"character_acting_bibles.json"
GRAPH_PATH=BASE/"character_relationship_graph.json"

def _load()->dict[str,Any]:
    with BIBLE_PATH.open("r",encoding="utf-8") as f:
        return json.load(f)

def _graph()->dict[str,Any]:
    with GRAPH_PATH.open("r",encoding="utf-8") as f:
        return json.load(f)

def _norm(value:str)->str:
    s=unicodedata.normalize("NFKD",str(value or "").casefold())
    return "".join(c for c in s if not unicodedata.combining(c))

def resolve_name(name:str)->str|None:
    q=_norm(name)
    if not q:return None
    names=list(_load().get("characters",{}))
    exact=[n for n in names if _norm(n)==q]
    if len(exact)==1:return exact[0]
    first=[n for n in names if _norm(n.split()[0])==q]
    if len(first)==1:return first[0]
    partial=[n for n in names if q in _norm(n)]
    return partial[0] if len(partial)==1 else None

def character_bible(name:str)->dict[str,Any]:
    resolved=resolve_name(name)
    if not resolved:return {"status":"not_found","query":name}
    entry=_load()["characters"][resolved]
    return {"status":"ok","version":_load()["meta"]["version"],"name":resolved,"bible":entry}

def relationship_bible(name:str,interlocutor:str)->dict[str,Any]:
    actor=resolve_name(name);target=resolve_name(interlocutor)
    if not actor:return {"status":"actor_not_found","query":name}
    if interlocutor and not target:return {"status":"interlocutor_not_found","query":interlocutor}
    entry=_load()["characters"][actor]
    overrides=entry.get("relationship_overrides",{})
    explicit=overrides.get(target or interlocutor,{})
    graph_rel=_graph().get("edges",{}).get(actor,{}).get(target or interlocutor,{})
    rel=explicit or graph_rel
    source="explicit_override" if explicit else "relationship_graph" if graph_rel else "fallback_summary"
    return {
        "status":"ok","version":_load()["meta"]["version"],"actor":actor,
        "interlocutor":target or interlocutor or None,
        "specific":bool(explicit),"graph_known":bool(graph_rel),"relationship_source":source,
        "relationship":rel,
        "fallback_relation_summary":entry.get("voice",{}).get("relation_summary",""),
        "rule":"explicit relationship override > established relationship graph > dossier summary > generic personality/reference"
    }

def _trigger_level(actor:str,target:str|None,text:str)->tuple[int,list[str]]:
    n=_norm(text)
    reasons=[]
    level=0
    if any(x in n for x in ["idiota","patetic","fracass","vergonha","perdeu","humilh"]):
        level=max(level,2);reasons.append("direct_personal_provocation")
    if actor=="Shin Uchiha" and target=="Amatsu Uchiha":
        if any(x in n for x in ["vergonha do cla","vergonha do clã","cla aqui","clã aqui"]):
            level=max(level,3);reasons.append("academy_clan_shame_trigger")
        if any(x in n for x in ["daigo","meu pai","seu pai","pai dele","filhinho","prodigio","prodígio","grande ninja do cla","grande ninja do clã"]):
            level=max(level,4);reasons.append("family_daigo_status_trigger")
        if any(x in n for x in ["perdeu","patetic","patética","patetica","passou vergonha"]):
            level=max(level,3);reasons.append("public_loss_pride_trigger")
    if actor=="Kaede Uchiha" and target=="Amatsu Uchiha":
        if any(x in n for x in ["vergonha","cla","clã","uchiha"]):
            level=max(level,2);reasons.append("clan_reputation_trigger")
        if any(x in n for x in ["melhor","prodig","competencia","competência","fraca","fracass"]):
            level=max(level,3);reasons.append("competence_status_trigger")
    if actor=="Yoshiro Sabaku":
        blood_or_pain = bool(
            re.search(r"\b(sangue|sangra|sangrou|sangrando|ferimento|ferido|ferida|dor|blood|bleeding|wound|wounded|pain)\b", n)
            or any(x in n for x in ["sangue visivel","sangue visível","dor real","own blood","real pain"])
        )
        breach = any(x in n for x in ["defesa atravess","defesa romp","areia atravess","defense breached","sand defense breached","humilh","invulner"])
        shukaku_break = any(x in n for x in ["shukaku","instabil","perde a compostura","perdeu a compostura"," rage "," fury "])
        if blood_or_pain:
            level=max(level,3);reasons.append("gaara_chunin_blood_or_pain_trigger")
        if breach:
            level=max(level,3);reasons.append("gaara_chunin_defense_breach_or_humiliation_trigger")
        if shukaku_break:
            level=max(level,4);reasons.append("shukaku_instability_trigger")
    if actor in {"Sayo Sabaku","Kuroto Sabaku"}:
        if any(x in n for x in ["yoshiro perde","yoshiro com sangue","yoshiro sangra","shukaku","instabilidade de yoshiro","yoshiro instavel","yoshiro instável"]):
            level=max(level,3);reasons.append("dangerous_sibling_instability_trigger")
    return level,reasons

def escalation_packet(name:str,interlocutor:str="",stimulus:str="",prior_exchange:str="",situation:str="",pressure:str="normal")->dict[str,Any]:
    actor=resolve_name(name)
    target=resolve_name(interlocutor) if interlocutor else None
    if not actor:return {"status":"actor_not_found","query":name}
    entry=_load()["characters"][actor]
    level,reasons=_trigger_level(actor,target,f"{prior_exchange}\n{stimulus}\n{situation}")
    p=_norm(pressure)
    if p in {"alta","high","extrema","extreme"}:
        level=max(level,1);reasons.append("scene_pressure")
    levels=entry.get("escalation",{}).get("levels",[])
    matched=next((x for x in levels if x.get("level")==level),{"level":level,"name":"custom","surface":""})
    actor_rule=entry.get("escalation",{}).get("actor_rule","")
    relation=entry.get("relationship_overrides",{}).get(target or interlocutor,{})
    trigger_rules=relation.get("trigger_rules",[])
    return {
        "status":"ok","version":_load()["meta"]["version"],"actor":actor,"interlocutor":target or interlocutor or None,
        "level":level,"level_name":matched.get("name"),"surface":matched.get("surface"),"reasons":reasons,
        "actor_rule":actor_rule,"relationship_trigger_rules":trigger_rules,
        "continuity_rule":entry.get("acting",{}).get("continuity_rule"),
        "must_not":relation.get("must_not","")
    }

def compile_acting_packet(name:str,interlocutor:str="",stimulus:str="",situation:str="",prior_exchange:str="",pressure:str="normal",audience:str="",body_state:str="")->dict[str,Any]:
    base=character_bible(name)
    if base.get("status")!="ok":return base
    rel=relationship_bible(name,interlocutor) if interlocutor else {"status":"ok","specific":False,"relationship":{}}
    esc=escalation_packet(name,interlocutor,stimulus,prior_exchange,situation,pressure)
    b=base["bible"]
    return {
        "status":"ok","version":base["version"],"actor":base["name"],"interlocutor":rel.get("interlocutor"),
        "identity":b.get("identity",{}),"canon_memory":b.get("canon_memory",{}),"voice":b.get("voice",{}),
        "acting":b.get("acting",{}),"reference_essence_v34":b.get("acting",{}).get("reference_essence_override_v34") or b.get("acting",{}).get("reference_essence_v34",{}),
        "actor_essence_v34":b.get("acting",{}).get("actor_essence_v34",{}),
        "reference_relationship_matrix":b.get("reference_relationship_matrix",{}),"relationship":rel.get("relationship",{}),"relationship_specific":rel.get("specific",False),"relationship_graph_known":rel.get("graph_known",False),"relationship_source":rel.get("relationship_source"),
        "escalation":esc,"stimulus":stimulus,"situation":situation,"prior_exchange":prior_exchange,
        "pressure":pressure,"audience":audience,"body_state":body_state,
        "generation_directive":[
            "Carry prior exchange forward; do not reset emotional temperature.",
            "Resolve relation history before generic reference-character behavior.",
            "Apply Reference Essence v34 at the exact mapped phase: dominant core + social surface + combat pressure + break trigger + body/voice + anti-regression.",
            "For mixed references, use the source anchor/explicit transfer axes; never average every reference trait.",
            "Apply trigger escalation before wording; canonical break behavior outranks artificial calm when the trigger is actually present.",
            "Choose speak/body/silence from objective + body + audience, then bend the line into actor rhythm.",
            "Reject a line that could be swapped unchanged onto multiple cast members."
        ]
    }

def audit_line(name:str,interlocutor:str="",candidate_dialogue:str="",candidate_action:str="",stimulus:str="",prior_exchange:str="",situation:str="",pressure:str="normal")->dict[str,Any]:
    packet=compile_acting_packet(name,interlocutor,stimulus,situation,prior_exchange,pressure)
    if packet.get("status")!="ok":return {"pass":False,"violations":["actor_not_found"],"packet":packet}
    text=_norm(f"{candidate_dialogue} {candidate_action}")
    violations=[];warnings=[]
    esc=packet.get("escalation",{})
    actor=packet.get("actor");target=packet.get("interlocutor")
    if actor=="Shin Uchiha" and target=="Amatsu Uchiha" and esc.get("level",0)>=3:
        if len(candidate_dialogue.split())>28:
            warnings.append("shin_triggered_reply_too_long")
        if any(x in text for x in ["fala o que quiser","quando te chamarem","mostra mesmo","so nao usa meu pai","só não usa meu pai"]):
            violations.append("shin_triggered_reply_too_composed_or_reflective")
        if not any(x in text for x in ["cala","repete","fala de novo","amatsu","idiota","quem","vem","tenta","pai","cla","clã","vergonha","perdeu","eu"]):
            warnings.append("shin_triggered_reply_lacks_direct_personal_contact")
    if actor=="Kaede Uchiha" and target=="Amatsu Uchiha":
        if len(candidate_dialogue.split())>35:
            warnings.append("kaede_amatsu_reply_may_be_too_explanatory")
        if any(x in text for x in ["relaxa","fica tranquilo","eu entendo"]):
            violations.append("kaede_amatsu_unearned_warmth")
    if candidate_dialogue and len(candidate_dialogue.split())>45 and esc.get("level",0)>=2:
        warnings.append("provoked_dialogue_may_be_overlong")
    return {"pass":not violations,"violations":violations,"warnings":warnings,"packet":packet}

def health()->dict[str,Any]:
    d=_load();chars=d.get("characters",{});g=_graph()
    missing=[n for n,v in chars.items() if not v.get("acting") or not v.get("voice")]
    relation_overrides=sum(len(v.get("relationship_overrides",{})) for v in chars.values())
    directional_edges=sum(len(v) for v in g.get("edges",{}).values())
    return {
        "ok":not missing,"version":d.get("meta",{}).get("version"),"reference_essence_protocol":"v34","characters":len(chars),
        "relation_overrides":relation_overrides,"directional_relation_edges":directional_edges,
        "missing":missing,"supports_relationship_graph":True,
        "supports_prior_exchange":True,"supports_trigger_escalation":True,"supports_reference_essence_v34":True,"supports_actor_essence_v34":True,"supports_genericity_audit":True
    }

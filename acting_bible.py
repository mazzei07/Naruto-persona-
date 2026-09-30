from __future__ import annotations
import json, re, unicodedata
from pathlib import Path
from typing import Any
from fidelity_core import source_proximate_match_v41

BASE=Path(__file__).resolve().parent
BIBLE_PATH=BASE/"character_acting_bibles.json"
GRAPH_PATH=BASE/"character_relationship_graph.json"

def _apply_continuity_firewall_v36(data:dict[str,Any])->dict[str,Any]:
    data.setdefault("meta",{})["continuity_firewall_v36"]={
        "active_continuity_id":"classico_floresta_da_morte",
        "rule":"Only Classic-continuity biography/status/relations/powers/knowledge may be used. Revalidated entity existence never imports legacy chronology."
    }
    amatsu=(data.get("characters") or {}).get("Amatsu Uchiha")
    if isinstance(amatsu,dict):
        amatsu["continuity_firewall_v36"]={
            "parents":"mortos; nenhum pai ou mãe vivo",
            "living_direct_relative":"Takeru Uchiha",
            "takeru_status":"nukenin de Konoha; membro da Tenkai",
            "natural_base_reserve":"literalmente equivalente à reserva natural/base de Naruto no Naruto Clássico desta fase",
            "kurama":"separada, selada e não cooperativa",
            "kage_bunshin":"sem teto operacional fixo de 24; feito live confirmado de 200; máximo absoluto não estabelecido",
            "narration":"Não expositar ausências familiares já estabelecidas sem relevância concreta."
        }
        def repl(v):
            if isinstance(v,str):
                v=v.replace("Em reserva natural está na mesma categoria excepcional de Naruto","A reserva natural/base de Amatsu é literalmente equivalente à de Naruto no Naruto Clássico desta fase; Kurama permanece separada e não cooperativa")
                v=v.replace("Kage Bunshin: 1–4 confortável; 5–8 operacional; 9–15 pesado; 16–24 extremo.","Kage Bunshin não possui teto operacional fixo de 24 clones. Feito live confirmado: 200 Kage Bunshin; cerca de 100 em tarefas simples também é compatível; máximo absoluto não estabelecido.")
                v=v.replace("Kage Bunshin: 1-4 confortável; 5-8 operacional; 9-15 pesado; 16-24 extremo.","Kage Bunshin não possui teto operacional fixo de 24 clones. Feito live confirmado: 200 Kage Bunshin; cerca de 100 em tarefas simples também é compatível; máximo absoluto não estabelecido.")
                return v
            if isinstance(v,list): return [repl(x) for x in v]
            if isinstance(v,dict):
                for k in list(v): v[k]=repl(v[k])
            return v
        repl(amatsu)
    kaede=(data.get("characters") or {}).get("Kaede Uchiha")
    if isinstance(kaede,dict):
        # v47: the Academy hostility remains historical dossier context, but it
        # must not survive inside the CURRENT acting core after the dating state.
        acting=kaede.get("acting") or {}
        traits=acting.get("core_traits")
        if isinstance(traits,list):
            acting["core_traits"]=[
                ("reservada com afeto contido; namoro live com Amatsu, hostilidade da Academia é histórica"
                 if isinstance(x,str) and "não gosta de Amatsu" in x else x)
                for x in traits
            ]
        kaede["acting"]=acting
    return data

def _load()->dict[str,Any]:
    with BIBLE_PATH.open("r",encoding="utf-8") as f:
        return _apply_continuity_firewall_v36(json.load(f))

def _graph()->dict[str,Any]:
    with GRAPH_PATH.open("r",encoding="utf-8") as f:
        return json.load(f)

def _norm(value:str)->str:
    s=unicodedata.normalize("NFKD",str(value or "").casefold())
    return "".join(c for c in s if not unicodedata.combining(c))

def _classic_voice_fidelity_v39(actor:str,bible:dict[str,Any])->dict[str,Any]:
    voice=(bible or {}).get("voice",{}) or {}
    acting=(bible or {}).get("acting",{}) or {}
    refs=[str(x) for x in (voice.get("reference_characters") or [])]
    anchor=str(voice.get("reference_anchor") or "")
    ref_text=_norm(" ".join([anchor,*refs]))
    shared=[
        "Write the semantic intent plainly first; then bend syntax, rhythm, interruption, omission and address into the exact reference-phase fingerprint.",
        "Do not maximize sentence completeness. A performable fragment, grunt, interruption, self-correction, abrupt topic shift or unfinished thought is preferable when the reference behaves that way.",
        "Do not manufacture symmetrical banter, setup/punchline pairs, polished aphorisms, trailer threats or tidy three-beat exchanges.",
        "Dialogue must answer the immediately previous beat, not summarize the scene, explain the character, or verbalize the narrator's analysis.",
        "Use body, timing and silence to carry information that the character would not naturally say aloud.",
        "Final prose/dialogue surface is Brazilian Portuguese only; internal English labels or evidence language must never leak into RP output.",
        "When source evidence is missing, keep the own-dossier voice and request research rather than filling the gap with generic anime dialogue."
    ]
    profile={"reference_anchor":anchor,"shared_rules":shared,"source_mechanics":[],"anti_patterns":[]}
    if "jiraiya" in ref_text:
        profile["source_mechanics"]=[
            "Jiraiya alternates boisterous/energetic bursts with lazy grunts, brush-offs, complaints, teasing and sudden competence; do not make every line witty or wise.",
            "With a student, he often gives the minimum useful instruction, lets the student struggle, notices results, and only then comments; he does not narrate every technical inference.",
            "His humor can be vulgar or shameless, but the joke may simply land and end; avoid neat callback chains and modern stand-up timing.",
            "When serious, the shift should be sharp and functional rather than solemnly eloquent."
        ]
        profile["anti_patterns"]=[
            "over-complete teacher speech",
            "constant mentor wisdom",
            "every reply as punchline",
            "explaining obvious observations to the student",
            "polished symmetrical banter"
        ]
    if "tsunade" in ref_text:
        profile["source_mechanics"]=[
            "Tsunade is blunt, impatient and technically authoritative; she can inspect with silence, a short correction, a challenge or a contemptuous remark instead of a lecture.",
            "Respect is earned reluctantly. Strong performance may interrupt her mockery, but does not instantly make her warm or complimentary.",
            "Her temper changes body and timing first; anger compresses language instead of producing long moral speeches.",
            "When conflicted in the Search for Tsunade phase, she hides the conflict in delay, evasion and action; do not make her confess her whole internal debate to Jiraiya-like peers.",
            "With Orochimaru-like old peers, hostility is familiar and terse; she does not need to restate their shared history."
        ]
        profile["anti_patterns"]=[
            "maternal reassurance by default",
            "clinical lecture after every observation",
            "generic calm authority",
            "instant praise for talent",
            "expository confession of internal conflict"
        ]
    if "orochimaru" in ref_text:
        profile["source_mechanics"]=[
            "Orochimaru speaks softly, completely and with invasive calm; menace comes from certainty and implication more than volume.",
            "In negotiation he presents the tempting or coercive piece, then watches. Do not over-explain the bargain after the target understands it.",
            "He personalizes observations and probes reactions, but does not sound like a modern scientist or therapist.",
            "When a rare specimen or unexpected technique appears, curiosity sharpens rather than becoming loud excitement.",
            "With Jiraiya/Tsunade peers, shared history permits intimate barbs and compressed references; no villain monologue is needed."
        ]
        profile["anti_patterns"]=[
            "loud ranting villain",
            "scientific jargon dump",
            "explaining his own manipulation",
            "constant sinister one-liners",
            "overstating threats already implied"
        ]
    profile["dialogue_flow"]=acting.get("dialogue_flow_v27",{})
    return profile

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
    graph_sources=[str(x) for x in graph_rel.get("sources",[]) if x]
    graph_roles=[str(x) for x in graph_rel.get("roles",[]) if x]
    graph_is_live=bool(graph_rel) and (
        any(x.startswith("live") or "current_live" in x for x in graph_sources)
        or any(x in {"girlfriend","boyfriend","partner","spouse","current_romantic_partner"} for x in graph_roles)
        or str(graph_rel.get("current_status","")).lower() in {"dating","relationship","romantic"}
        or str(graph_rel.get("familiarity","")).lower().startswith("deep_shared_history")
    )
    if graph_is_live:
        # v47: a current live relationship is authoritative state, not an additive
        # overlay on top of stale Academy-era surface rules. Keep the live graph
        # clean and carry only non-conflicting trigger/history metadata.
        rel=dict(graph_rel)
        # v47 schema guard: hard current-state fields must survive even if an
        # older graph producer omitted them. These are copied only when absent.
        for key in ("current_status","baseline","address","must_not"):
            if explicit.get(key) and not rel.get(key):
                rel[key]=explicit.get(key)
        if explicit.get("trigger_rules") and not rel.get("trigger_rules"):
            rel["trigger_rules"]=explicit.get("trigger_rules",[])
        if explicit.get("history") or graph_rel.get("history"):
            rel["history"]=list(dict.fromkeys([
                *(explicit.get("history",[]) if isinstance(explicit.get("history"),list) else []),
                *(graph_rel.get("history",[]) if isinstance(graph_rel.get("history"),list) else [])
            ]))
        if explicit:
            rel["historical_overlay_present"]=True
        source="relationship_graph_live_override"
    else:
        rel=explicit or graph_rel
        source="explicit_override" if explicit else "relationship_graph" if graph_rel else "fallback_summary"
    return {
        "status":"ok","version":_load()["meta"]["version"],"actor":actor,
        "interlocutor":target or interlocutor or None,
        "specific":bool(explicit or graph_rel),"graph_known":bool(graph_rel),"relationship_source":source,
        "relationship":rel,
        "fallback_relation_summary":entry.get("voice",{}).get("relation_summary",""),
        "rule":"current live relationship graph > accumulated live explicit override > dossier historical baseline > generic personality/reference"
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
        # v47: surnames/locations like "Uchiha" or "distrito Uchiha" are context,
        # not provocation. Reputation escalation requires an actual evaluative hit.
        clan_reputation = any(x in n for x in [
            "vergonha do cla","vergonha do clã","vergonha dos uchiha",
            "vergonha para o cla","vergonha para o clã","envergonha o cla","envergonha o clã",
            "nome uchiha","reputacao do cla","reputação do clã","honra do cla","honra do clã"
        ])
        if clan_reputation:
            level=max(level,2);reasons.append("clan_reputation_trigger")
        competence_provocation = any(x in n for x in [
            "voce e fraca","você é fraca","mais fraca","fracassada","fracasso",
            "sou melhor que voce","sou melhor que você","melhor que voce","melhor que você",
            "prodigio de verdade","prodígio de verdade","competencia uchiha","competência uchiha"
        ])
        if competence_provocation:
            level=max(level,3);reasons.append("competence_status_trigger")
    if actor=="Yoshiro Sabaku":
        trigger_n = re.sub(
            r"\b(?:sem|nenhum[ao]?|nao)\s+(?:qualquer\s+)?(?:sangue(?:\s+visivel)?|dor(?:\s+real)?|ferimento|ferida?|blood|pain|wound)\b",
            " ",
            n,
        )
        trigger_n = re.sub(
            r"\bnao\s+(?:sangra|sangrou|sangrando|esta\s+ferid[oa]|tem\s+sangue|sente\s+dor)\b",
            " ",
            trigger_n,
        )
        blood_or_pain = bool(
            re.search(r"\b(sangue|sangra|sangrou|sangrando|ferimento|ferido|ferida|dor|blood|bleeding|wound|wounded|pain)\b", trigger_n)
            or any(x in trigger_n for x in ["sangue visivel","dor real","own blood","real pain"])
        )
        breach = any(x in trigger_n for x in ["defesa atravess","defesa romp","areia atravess","defense breached","sand defense breached","humilh","invulner"])
        shukaku_break = any(x in trigger_n for x in ["shukaku","instabil","perde a compostura","perdeu a compostura"," rage "," fury "])
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
    relation_packet=relationship_bible(actor,target or interlocutor or "") if (target or interlocutor) else {"relationship":{}}
    relation=relation_packet.get("relationship",{}) or {}
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
        "source_proximate_v41":source_proximate_match_v41(base["name"],interlocutor,situation,stimulus),
        "classic_voice_fidelity_v39":_classic_voice_fidelity_v39(base["name"],b),
        "generation_directive":[
            "Carry prior exchange forward; do not reset emotional temperature.",
            "Resolve relation history before generic reference-character behavior.",
            "Apply Reference Essence v34 at the exact mapped phase: dominant core + social surface + combat pressure + break trigger + body/voice + anti-regression.",
            "For mixed references, use the source anchor/explicit transfer axes; never average every reference trait.",
            "Apply trigger escalation before wording; canonical break behavior outranks artificial calm when the trigger is actually present.",
            "Choose speak/body/silence from objective + body + audience, then bend the line into actor rhythm.",
            "Apply classic_voice_fidelity_v39: exact-phase oral rhythm outranks polished sentence completeness.",
            "Use source_proximate_v41 closest card only for documented mechanics; request evidence when source is synopsis-only, and preserve live dossier/relation.",
            "Reject symmetrical banter, narrator-like technical explanation, and tidy setup/punchline exchanges unless source evidence supports them.",
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
        "supports_prior_exchange":True,"supports_trigger_escalation":True,"supports_reference_essence_v34":True,"supports_actor_essence_v34":True,"supports_genericity_audit":True,"supports_classic_voice_fidelity_v39":True,"supports_source_proximate_dialogue_v41":True
    }


# v41 — Source-proximate dialogue fidelity
SOURCE_PROXIMATE_DIALOGUE_V41 = {
  "rule": "For every material NPC turn, retrieve the closest manga/anime reference by exact character, phase, interlocutor relation and situation. Transfer pragmatic function, cadence, interruption, latency, body timing and social pressure; never copy copyrighted dialogue verbatim beyond a very short fragment.",
  "pipeline": [
    "find_exact_or_nearest_reference_scene",
    "extract_pragmatic_function_and_turn_shape",
    "map_directional_relation_and_live_knowledge",
    "rewrite_into_reboot_character_and_PTBR_orality",
    "compare_read_aloud_against_source_mechanics",
    "reject_if_generic_or_over-explained"
  ],
  "priority": "live continuity and own dossier/relation > exact-phase documented source mechanics > phase analogue; never import source biography",
  "anti_patterns": [
    "generic anime comeback",
    "invented modern phrasing",
    "long explanatory speech where source used action/silence",
    "symmetrical banter not present in source mechanics",
    "verbatim reproduction of copyrighted dialogue"
  ]
}

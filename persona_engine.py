from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parent
CHARACTERS_PATH = ROOT / "character_registry_seed.json"
WORLD_PATH = ROOT / "world_registry_seed.json"
RULES_PATH = ROOT / "persona_rules.json"


def _norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", (value or "").casefold())
    return "".join(c for c in value if not unicodedata.combining(c))


def _clean_bullet(line: str) -> str:
    line = line.strip()
    line = re.sub(r"^[-*]\s*", "", line)
    return line.strip()


def _uniq(items: Iterable[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for item in items:
        item = (item or "").strip()
        if not item:
            continue
        key = _norm(item)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


@lru_cache(maxsize=1)
def _characters() -> Dict[str, Any]:
    with CHARACTERS_PATH.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _world() -> Dict[str, Any]:
    with WORLD_PATH.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _rules() -> Dict[str, Any]:
    with RULES_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def resolve_name(name: str) -> Optional[str]:
    if not isinstance(name, str) or not name.strip():
        return None
    chars = _characters().get("characters", {})
    if name in chars:
        return name
    q = _norm(name.strip())
    exact = []
    prefix = []
    contains = []
    for key, profile in chars.items():
        candidates = [key, profile.get("canonical_name", "")]
        ncands = [_norm(x) for x in candidates if x]
        if q in ncands:
            exact.append(key)
        elif any(x.startswith(q) or q.startswith(x) for x in ncands):
            prefix.append(key)
        elif any(q in x for x in ncands):
            contains.append(key)
    if len(exact) == 1:
        return exact[0]
    if len(prefix) == 1:
        return prefix[0]
    if len(contains) == 1:
        return contains[0]
    return None


def _profile(name: str) -> Dict[str, Any]:
    resolved = resolve_name(name)
    if not resolved:
        return {}
    return _characters()["characters"][resolved]


def _first_name(name: str) -> str:
    return (name or "").split()[0] if name else ""


def _extract_field(profile: Dict[str, Any], *keys: str) -> str:
    fields = profile.get("dossier_fields", {}) or {}
    for key in keys:
        if key in fields:
            return str(fields.get(key) or "")
    nfields = {_norm(k): v for k, v in fields.items()}
    for key in keys:
        nk = _norm(key)
        if nk in nfields:
            return str(nfields[nk] or "")
    return ""


def _baseline_voice_lines(voice_raw: str) -> List[str]:
    out = []
    for raw in (voice_raw or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("###"):
            break
        if line.startswith("-"):
            out.append(_clean_bullet(line))
    return _uniq(out)


def _relation_lines(voice_raw: str, interlocutor: str) -> List[str]:
    if not voice_raw or not interlocutor:
        return []
    first = _first_name(interlocutor)
    nf = _norm(first)
    lines = voice_raw.splitlines()
    collected: List[str] = []
    in_section = False
    for raw in lines:
        stripped = raw.strip()
        if stripped.startswith("###"):
            heading = _norm(stripped.lstrip("# "))
            if heading.startswith("com "):
                in_section = nf and nf in heading
            else:
                in_section = False
            continue
        if in_section and stripped:
            collected.append(_clean_bullet(stripped))
        # Also capture one-line relationship bullets such as **Com Amatsu:** ...
        if stripped.startswith("-") and nf and (f"com {nf}" in _norm(stripped) or f"{nf}:" in _norm(stripped)):
            collected.append(_clean_bullet(stripped))
    return _uniq(collected)


def _extract_labels(lines: Iterable[str], labels: Iterable[str]) -> List[str]:
    wanted = [_norm(x) for x in labels]
    out = []
    for line in lines:
        n = _norm(line)
        if any(lbl in n for lbl in wanted):
            out.append(line)
    return _uniq(out)


def _infer_reference(profile: Dict[str, Any]) -> Dict[str, Any]:
    voice = profile.get("voice_raw", "") or ""
    inspiration = _extract_field(profile, "Inspiração e comparação — Naruto Clássico", "Inspiração e comparação")
    anchor = ""
    m = re.search(r"Âncora de referência:\*?\*?\s*([^\n.]+)", voice, flags=re.I)
    if not m:
        m = re.search(r"referência(?: primária| estrutural| funcional)?:\*?\*?\s*([^\n.]+)", voice, flags=re.I)
    if m:
        anchor = m.group(1).strip(" *-:")
    source = anchor or inspiration or "Referência não estruturada"
    ns = _norm(source)
    if any(k in ns for k in ["inicial", "jovem", "academ", "classica", "classico"]):
        phase = "Naruto Clássico / fase juvenil correspondente"
    else:
        phase = "fase indicada pela ficha; confirmar em interação importante"
    return {
        "primary_reference": source,
        "reference_phase": phase,
        "source_summary": inspiration,
    }


def _relation_anchor(lines: List[str]) -> str:
    joined = "\n".join(lines)
    patterns = [
        r"eixo\s+([^\n.;]+?)\s*[→>-]+\s*([^\n.;]+)",
        r"equivalente\s+([^\n.;]+?)\s*[→>-]+\s*([^\n.;]+)",
    ]
    for pat in patterns:
        m = re.search(pat, joined, flags=re.I)
        if m:
            return f"{m.group(1).strip()} → {m.group(2).strip()}"
    return ""


def _classify_situation(stimulus: str, situation: str) -> List[str]:
    text = _norm(f"{stimulus} {situation}")
    tags = []
    for tag, words in _rules().get("situation_keywords", {}).items():
        if any(_norm(w) in text for w in words):
            tags.append(tag)
    if not tags:
        tags.append("neutral")
    return tags


def _pressure_level(pressure: str) -> str:
    p = _norm(pressure)
    if any(x in p for x in ["alta", "high", "extrema", "letal", "urgente"]):
        return "high"
    if any(x in p for x in ["media", "medium", "moderada"]):
        return "medium"
    if any(x in p for x in ["baixa", "low", "segura", "normal"]):
        return "low"
    return "normal"


def _filter_level(relation_lines: List[str]) -> str:
    # Prefer explicit "filtro social" statements, which are relation-specific
    # in the source matrix, over incidental comparisons elsewhere in the block.
    for line in relation_lines:
        n = _norm(line)
        if "filtro social baixo" in n:
            return "low"
        if "filtro social alto" in n:
            return "high"
    text = _norm(" ".join(relation_lines))
    if any(x in text for x in ["baixo filtro", "filtro baixo", "nao autocorrige"]):
        return "low"
    if any(x in text for x in ["filtro alto", "maior autocontrole", "preservar imagem"]):
        return "high"
    return "medium"


def _speech_tendency(name: str, relation_lines: List[str], baseline: List[str], tags: List[str], pressure: str) -> Dict[str, Any]:
    if name == "Amatsu Uchiha":
        return {"status": "blocked_player_control", "reason": "Amatsu é controlado 100% pelo usuário."}
    text = _norm(" ".join(relation_lines + baseline))
    high = pressure == "high" or "danger" in tags
    if high:
        if any(x in text for x in ["pouca fala", "silencio", "economico", "baixa frequencia"]):
            return {"status": "speak_only_if_functional", "reason": "Pressão alta + voz econômica; comando/alerta tem prioridade."}
        return {"status": "likely_speaks_if_directly_affected", "reason": "Pressão alta comprime a fala e prioriza alerta/comando."}
    if any(x in text for x in ["pode ignorar", "silencio e frequentemente mais fiel", "silencio e padrao", "pouca fala", "baixa frequencia"]):
        return {"status": "silence_or_short_functional_reply", "reason": "Evidência negativa e economia verbal no perfil."}
    if "comedy" in tags and any(x in text for x in ["explos", "grito", "comedia fisica", "irritacao rapida"]):
        return {"status": "likely_speaks_and_may_act_physically", "reason": "Contexto cômico compatível com expressão aberta do perfil."}
    return {"status": "context_dependent", "reason": "Resolver pelo objetivo, relação e necessidade real de fala."}


def _physical_comedy(name: str, relation_lines: List[str], tags: List[str], pressure: str) -> Dict[str, Any]:
    text = _norm(" ".join(relation_lines))
    if pressure == "high" or "danger" in tags:
        return {"allowed": False, "reason": "Perigo real bloqueia slapstick que comprometa a cena."}
    if "comedy" in tags and any(x in text for x in ["comedia fisica", "bater", "perseguir", "puxar", "agarrar", "acao fisica"]):
        return {"allowed": True, "reason": "Relação e contexto permitem fisicalidade cômica legítima."}
    return {"allowed": False, "reason": "Sem evidência relacional suficiente para fisicalidade cômica."}


def _research_packet(profile: Dict[str, Any], interlocutor_profile: Dict[str, Any], relation_lines: List[str], situation: str, stimulus: str) -> Dict[str, Any]:
    ref_a = _infer_reference(profile)["primary_reference"]
    ref_b = _infer_reference(interlocutor_profile)["primary_reference"] if interlocutor_profile else "interlocutor equivalente"
    anchor = _relation_anchor(relation_lines)
    need = not bool(anchor) or len(relation_lines) < 2
    query = f"Naruto Clássico {ref_a} com {ref_b}; relação equivalente; situação: {situation or stimulus}; fase juvenil correspondente; diálogo, silêncio, corpo, timing e registro"
    return {
        "research_required": need,
        "reason": "Relação sem âncora clássica suficientemente explícita no cache." if need else "Âncora relacional já presente no registro; pesquisa externa só se a cena for excepcional/ambígua.",
        "suggested_query": query,
        "existing_relation_anchor": anchor,
    }


def healthcheck() -> Dict[str, Any]:
    data = _characters()
    rules = _rules()
    chars = data.get("characters", {})
    missing_voice = sorted(k for k, v in chars.items() if not (v.get("voice_raw") or "").strip())
    missing_dossier = sorted(k for k, v in chars.items() if not (v.get("dossier_raw") or "").strip())
    return {
        "ok": not missing_voice and not missing_dossier,
        "module": "Naruto Persona Engine",
        "version": rules.get("version"),
        "continuity_id": rules.get("continuity_id"),
        "characters": len(chars),
        "missing_voice": missing_voice,
        "missing_dossier": missing_dossier,
        "llm_required_for_core": False,
        "external_research_policy": "only_when_reference_cache_is_insufficient_or_scene_is_exceptional",
    }


def persona_get(name: str) -> Dict[str, Any]:
    resolved = resolve_name(name)
    if not resolved:
        return {"status": "not_found", "query": name}
    p = _profile(resolved)
    ref = _infer_reference(p)
    return {
        "status": "ok",
        "name": resolved,
        "source_status": p.get("source_status"),
        "source_files": p.get("source_files", []),
        "identity": _extract_field(p, "Identificação"),
        "personality_voice": _extract_field(p, "Personalidade / voz"),
        "relations_knowledge": _extract_field(p, "Relações e conhecimento"),
        "combat_identity": _extract_field(p, "Identidade de combate"),
        "reference": ref,
        "voice_baseline": _baseline_voice_lines(p.get("voice_raw", "")),
        "raw_voice_rules": p.get("voice_raw", ""),
        "arc_specific": bool(p.get("arc_specific")),
    }


def persona_search(query: str, limit: int = 12) -> Dict[str, Any]:
    if not isinstance(query, str) or not query.strip():
        return {"status": "invalid_input", "reason": "query must be nonempty"}
    limit = max(1, min(int(limit), 30))
    terms = [x for x in re.findall(r"[\wÀ-ÿ]+", _norm(query)) if len(x) > 1]
    rows = []
    for name, p in _characters().get("characters", {}).items():
        hay = _norm(" ".join([
            name,
            p.get("canonical_name", ""),
            p.get("dossier_raw", ""),
            p.get("voice_raw", ""),
        ]))
        hits = sum(1 for t in terms if t in hay)
        if hits:
            rows.append((hits / max(1, len(terms)), hits, name))
    rows.sort(key=lambda x: (-x[0], -x[1], x[2]))
    return {
        "status": "ok",
        "query": query,
        "matches": [{"name": n, "score": round(s, 3)} for s, _, n in rows[:limit]],
    }


def relation_get(speaker: str, interlocutor: str, situation: str = "", pressure: str = "normal", audience: str = "") -> Dict[str, Any]:
    a = resolve_name(speaker)
    b = resolve_name(interlocutor)
    if not a:
        return {"status": "speaker_not_found", "speaker": speaker}
    if not b:
        return {"status": "interlocutor_not_found", "interlocutor": interlocutor}
    pa, pb = _profile(a), _profile(b)
    rel_lines = _relation_lines(pa.get("voice_raw", ""), b)
    baseline = _baseline_voice_lines(pa.get("voice_raw", ""))
    ref = _infer_reference(pa)
    tags = _classify_situation("", situation)
    plev = _pressure_level(pressure)
    return {
        "status": "ok",
        "speaker": a,
        "interlocutor": b,
        "directional": True,
        "situation": situation,
        "pressure": plev,
        "audience": audience or "unspecified",
        "reference": ref,
        "equivalent_relation_anchor": _relation_anchor(rel_lines),
        "social_filter": _filter_level(rel_lines),
        "baseline_voice": baseline,
        "relationship_rules": rel_lines,
        "latency_notes": _extract_labels(rel_lines + baseline, ["latência", "reação rápida", "deliberada", "instantânea"]),
        "vocative_notes": _extract_labels(rel_lines + baseline, ["vocativo", "nome", "abertura", "fechamento", "sensei", "hokage"]),
        "morphosyntax_notes": _extract_labels(rel_lines + baseline, ["oralidade", "imperativo", "corretividade", "forma", "para", "pare", "suba", "sobe"]),
        "body_notes": _extract_labels(rel_lines + baseline, ["corpo", "punho", "olhar", "postura", "avanço", "passo", "fisic"]),
        "silence_notes": _extract_labels(rel_lines + baseline, ["silêncio", "calar", "ignorar", "não precisa", "pouca fala"]),
        "forbidden_or_avoid": _extract_labels(rel_lines + baseline, ["evitar", "proibido", "bloqueio", "não transformar", "não fazer"]),
        "research": _research_packet(pa, pb, rel_lines, situation, ""),
    }


def character_turn_packet(
    name: str,
    interlocutor: str = "",
    stimulus: str = "",
    situation: str = "",
    pressure: str = "normal",
    audience: str = "",
    body_state: str = "",
    objective: str = "",
    perception_constraint: str = "",
    knowledge_constraint: str = "",
) -> Dict[str, Any]:
    actor = resolve_name(name)
    if not actor:
        return {"status": "not_found", "name": name}
    if actor == "Amatsu Uchiha":
        return {
            "status": "blocked_player_control",
            "name": actor,
            "rule": "Amatsu é controlado 100% pelo usuário.",
            "allowed_output": "Somente perfil de referência passivo; nenhuma reação voluntária deve ser gerada.",
        }
    p = _profile(actor)
    interlocutor_resolved = resolve_name(interlocutor) if interlocutor else None
    ip = _profile(interlocutor_resolved) if interlocutor_resolved else {}
    baseline = _baseline_voice_lines(p.get("voice_raw", ""))
    rel_lines = _relation_lines(p.get("voice_raw", ""), interlocutor_resolved or "")
    tags = _classify_situation(stimulus, situation)
    plev = _pressure_level(pressure)
    ref = _infer_reference(p)
    filter_level = _filter_level(rel_lines)
    relation_anchor = _relation_anchor(rel_lines)
    combined = rel_lines + baseline
    latency = _extract_labels(combined, ["latência", "instantânea", "deliberada", "reação rápida"])
    body = _extract_labels(combined, ["corpo", "punho", "olhar", "postura", "avanço", "passo", "fisic", "gesto"])
    vocative = _extract_labels(combined, ["vocativo", "nome", "abertura", "fechamento", "sensei", "hokage"])
    morph = _extract_labels(combined, ["oralidade", "imperativo", "corretividade", "coloquial", "formalidade", "para", "pare", "suba", "sobe"])
    silence = _extract_labels(combined, ["silêncio", "ignorar", "não precisa", "pouca fala", "baixa frequência"])
    forb = _extract_labels(combined, ["evitar", "proibido", "bloqueio", "não transformar", "não fazer", "não importar"])
    speech = _speech_tendency(actor, rel_lines, baseline, tags, plev)
    comedy = _physical_comedy(actor, rel_lines, tags, plev)
    research = _research_packet(p, ip, rel_lines, situation, stimulus)

    private_public = {
        "private_impulse": "derive_from_stimulus_and_character; do not invent facts outside scene",
        "public_filter": filter_level,
        "leakage_rule": "lower filter allows more direct voice/body leakage; high filter favors mitigation, repair, silence or body-only leakage",
    }
    if filter_level == "low":
        private_public["likely_surface"] = "private emotion can reach voice/body quickly if context permits"
    elif filter_level == "high":
        private_public["likely_surface"] = "emotion is more likely to be softened, delayed, reformulated or shown through body before voice"
    else:
        private_public["likely_surface"] = "moderate translation from impulse to public behavior"

    return {
        "status": "ok",
        "engine": "Naruto Persona Engine",
        "version": _rules().get("version"),
        "actor": actor,
        "interlocutor": interlocutor_resolved or interlocutor or None,
        "stimulus": stimulus,
        "situation": situation,
        "situation_tags": tags,
        "pressure": plev,
        "audience": audience or "unspecified",
        "body_state_input": body_state or "not_provided",
        "objective_input": objective or "not_provided",
        "epistemic_constraints": {
            "perception": perception_constraint or "must be supplied by chat/Canoney if material",
            "knowledge": knowledge_constraint or "must be supplied by chat/Canoney if material",
            "rule": "Persona Engine never upgrades perception into recognition/knowledge on its own."
        },
        "reference": ref,
        "directional_relationship": {
            "anchor": relation_anchor,
            "rules": rel_lines,
            "social_filter": filter_level,
        },
        "private_public": private_public,
        "decision_surface": {
            "speech": speech,
            "physical_comedy": comedy,
            "silence_evidence": silence,
        },
        "voice_realization": {
            "baseline": baseline,
            "latency": latency,
            "vocative": vocative,
            "morphosyntax": morph,
            "pressure_rule": "high pressure compresses language and prioritizes functional speech; it does not grant adult command vocabulary",
        },
        "body_realization": {
            "tendencies": body,
            "rule": "body and voice must arise from the same impulse; do not add random microgestures for decoration"
        },
        "forbidden_or_avoid": forb,
        "research": research,
        "generation_order": _rules().get("pipeline", []),
        "final_gate": [
            "Would this reaction still fit if the interlocutor changed? If yes, it may be generic.",
            "Would this line fit three other NPCs unchanged? If yes, add specific cadence/filter/body or use silence.",
            "Is silence more faithful than speaking?",
            "Does age/reference phase match current stage?",
            "Does the output preserve reboot identity instead of copying canon?"
        ],
    }


def persona_audit(
    name: str,
    interlocutor: str = "",
    candidate_dialogue: str = "",
    candidate_action: str = "",
    situation: str = "",
    pressure: str = "normal",
) -> Dict[str, Any]:
    packet = character_turn_packet(name, interlocutor, candidate_action or candidate_dialogue, situation, pressure)
    if packet.get("status") != "ok":
        return {"pass": False, "packet_status": packet.get("status"), "violations": [packet.get("rule", "invalid actor")], "packet": packet}
    violations = []
    warnings = []
    text = f"{candidate_dialogue} {candidate_action}".strip()
    ntext = _norm(text)
    for word in _rules().get("forbidden_modernisms", []):
        if _norm(word) in ntext:
            violations.append(f"modernism_or_meta_language:{word}")
    if candidate_dialogue and packet["decision_surface"]["speech"]["status"] == "silence_or_short_functional_reply" and len(candidate_dialogue.split()) > 35:
        warnings.append("dialogue_may_be_too_long_for_current_silence/economy_profile")
    if packet["pressure"] == "high" and len(candidate_dialogue.split()) > 45:
        warnings.append("high_pressure_dialogue_may_be_overlong")
    if name == "Saya Haruno" and resolve_name(interlocutor) == "Kazuma Uzumaki":
        aggressive = any(x in ntext for x in ["idiota", "burro", "cala a boca", "imbecil"])
        if aggressive and "danger" not in packet["situation_tags"]:
            warnings.append("Saya→Kazuma aggressive casual register requires a strong filter-breaking cause")
    return {
        "pass": not violations,
        "actor": packet["actor"],
        "interlocutor": packet["interlocutor"],
        "violations": violations,
        "warnings": warnings,
        "audit_dimensions": [
            "reference_phase",
            "directional_relationship",
            "social_filter",
            "speech_vs_silence",
            "vocative_function",
            "morphosyntax",
            "body_voice_consistency",
            "modernism",
            "player_control"
        ],
        "packet": packet,
    }

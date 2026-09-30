from __future__ import annotations

from epistemic_gate import fact_supported

import json
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from fidelity_core import evidence_packet as evidence_v24, lint as lint_v24, classify as classify_v24, health as fidelity_health, catalog as fidelity_catalog, resolve as resolve_fidelity_name
from actor_state_compiler import compile_actor_state
from acting_bible import (
    character_bible as acting_character_bible,
    relationship_bible as acting_relationship_bible,
    compile_acting_packet as acting_compile_packet,
    audit_line as acting_audit_line,
    health as acting_health,
)

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

def _continuity_firewall_v36() -> Dict[str, Any]:
    return _rules().get("continuity_firewall_v36", {
        "version": "v36",
        "active_continuity_id": "classico_floresta_da_morte",
        "legacy_chronology_import": "forbidden",
        "character_carryover": "entity existence only if revalidated",
    })


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
    known = {"Gakuji Aramori": "Zabuza Clássico", "Nagi Sazanami": "Haku Clássico"}
    if profile.get("name") in known:
        voice = "Âncora de referência: " + known[profile["name"]] + "\n" + voice
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
    return classify_v24(stimulus, situation)


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


def _research_packet(profile, interlocutor_profile, relation_lines, situation, stimulus):
    name = profile.get("name") or profile.get("canonical_name", "")
    target = interlocutor_profile.get("name") or interlocutor_profile.get("canonical_name", "")
    return evidence_v24(name, target, situation, stimulus)


def _reference_voice_family_v23(profile: Dict[str, Any], baseline: List[str]) -> Dict[str, Any]:
    """Infer a Naruto speech-family from the explicit reference/profile, with a profile-driven fallback."""
    ref = _infer_reference(profile)
    name = resolve_fidelity_name(profile.get("name") or profile.get("canonical_name", ""))
    mapping = fidelity_catalog()['characters'].get(name, {})
    if mapping.get('transfer_scope') in ('original', 'technical_or_function_only'):
        return {
            "family": "profile_driven", "matched_reference_cues": [],
            "reference": ref.get("primary_reference"),
            "rule": "Derive voice from the actor's own dossier; a technical/functional reference is not a personality model.",
        }
    primary = _norm(ref.get("primary_reference", ""))
    fallback = _norm(" ".join([
        ref.get("source_summary", ""),
        " ".join(baseline),
    ]))
    ordered = [
        ("relaxed_adult", ["kakashi"]),
        ("expressive_teacher", ["iruka"]),
        ("warm_authority", ["hiruzen"]),
        ("low_energy_plain", ["shikamaru"]),
        ("sparse_unsettling", ["gaara"]),
        ("direct_confident", ["temari"]),
        ("reactive_irritable", ["kankuro"]),
        ("polite_reserved_youthful", ["hinata"]),
        ("rough_youthful", ["naruto", "kiba"]),
        ("clipped_plain", ["sasuke", "neji"]),
        ("socially_adaptive_youthful", ["sakura", "ino"]),
    ]
    family = "profile_driven"
    matched = []
    # Primary reference always wins over incidental names in comparison text.
    for search_space in (primary, fallback):
        for fam, keys in ordered:
            hits = [k for k in keys if k in search_space]
            if hits:
                family = fam
                matched = hits
                break
        if matched:
            break
    return {
        "family": family,
        "matched_reference_cues": matched,
        "reference": ref.get("primary_reference"),
        "rule": "reference family shapes delivery mechanisms, never imports biography, knowledge or powers",
    }


def _formality_profile_v23(
    actor: str,
    interlocutor: str,
    profile: Dict[str, Any],
    interlocutor_profile: Dict[str, Any],
    relation_lines: List[str],
    baseline: List[str],
    tags: List[str],
    pressure: str,
    filter_level: str,
) -> Dict[str, Any]:
    """Resolve situational formality before dialogue wording."""
    family_packet = _reference_voice_family_v23(profile, baseline)
    family = family_packet["family"]
    base_by_family = {
        "rough_youthful": 1.0,
        "clipped_plain": 1.7,
        "socially_adaptive_youthful": 2.0,
        "polite_reserved_youthful": 2.5,
        "earnest_deferential_youthful": 2.6,
        "relaxed_adult": 2.1,
        "expressive_teacher": 2.2,
        "warm_authority": 3.1,
        "low_energy_plain": 1.3,
        "sparse_unsettling": 1.5,
        "direct_confident": 1.8,
        "reactive_irritable": 1.4,
        "profile_driven": 2.0,
    }
    score = base_by_family.get(family, 2.0)
    cues: List[str] = [f"reference_family:{family}"]

    def _is_directional_voice_line(line: str) -> bool:
        n = _norm(line).strip(" *-:")
        return n.startswith("com ") or n.startswith("eixo ") or "→" in line

    baseline_style = [line for line in baseline if not _is_directional_voice_line(line)]
    baseline_text = _norm(" ".join(baseline_style))
    relation_text = _norm(" ".join(relation_lines))
    text = _norm(" ".join(baseline_style + relation_lines))

    if any(x in baseline_text for x in ["correto-formal", "formalidade alta", "cerimonial", "muito formal"]):
        score += 1.2; cues.append("explicit_formal_baseline")
    elif any(x in baseline_text for x in ["fala formal", "registro formal", "polido", "corretividade alta"]):
        score += 0.6; cues.append("formal_or_polite_baseline")
    if any(x in baseline_text for x in ["coloquial", "oralidade", "rude", "provoc", "explos"]):
        score -= 0.35; cues.append("oral_baseline")
    if any(x in baseline_text for x in ["economico", "pouca fala", "silencio"]):
        cues.append("economical_voice_not_equivalent_to_informal")

    if filter_level != "low" and any(x in relation_text for x in ["mais formal", "mais polid", "mais correta", "mais organizado", "respeitoso", "o senhor", "a senhora"]):
        score += 0.45; cues.append("directional_respect_shift")
    if any(x in relation_text for x in ["mais casual", "intimidade", "familiar", "proximidade", "reduz formalidade", "velho", "velhote"]):
        score -= 0.55; cues.append("directional_intimacy_shift")

    actor_identity = _norm(_extract_field(profile, "Identificação", "Identificacao")) if profile else ""
    target_identity = _norm(_extract_field(interlocutor_profile, "Identificação", "Identificacao")) if interlocutor_profile else ""

    def _rank_level(identity: str) -> int:
        if "hokage" in identity or re.search(r"\bkage\b", identity):
            return 6
        if "jonin" in identity or "jounin" in identity:
            return 4
        if "chunin" in identity:
            return 3
        if "genin" in identity:
            return 2
        if "academ" in identity and ("aluno" in identity or "estudante" in identity):
            return 1
        return 0

    actor_rank = _rank_level(actor_identity)
    target_rank = _rank_level(target_identity)
    target_self_role = any(x in target_identity for x in [
        "professor da academia", "instrutor", "hokage", "chefe do cla", "chefe de cla", "comandante"
    ])
    relation_marks_superior = any(x in relation_text for x in [
        "superior", "autoridade", "o senhor", "a senhora", "sensei", "hokage-sama"
    ])
    authority_target = (
        target_rank > actor_rank
        or target_self_role
        or relation_marks_superior
        or any(x in _norm(interlocutor) for x in ["daizen", "kagetsu", "iruka"])
    )
    if authority_target:
        hierarchy_sensitivity = 1.0
        if family in {"rough_youthful", "clipped_plain", "sparse_unsettling"}:
            hierarchy_sensitivity = 0.25
        elif family == "socially_adaptive_youthful":
            hierarchy_sensitivity = 1.25
        elif family == "polite_reserved_youthful":
            hierarchy_sensitivity = 1.35
        elif family == "earnest_deferential_youthful":
            hierarchy_sensitivity = 1.5
        elif family in {"warm_authority", "expressive_teacher"}:
            hierarchy_sensitivity = 0.8
        if filter_level == "high":
            hierarchy_sensitivity += 0.4
        elif filter_level == "low":
            hierarchy_sensitivity -= 0.2
        score += hierarchy_sensitivity
        cues.append(f"authority_target_shift:{round(hierarchy_sensitivity,2)}")

    if filter_level == "high":
        score += 0.45; cues.append("high_social_filter")
    elif filter_level == "low":
        score -= 0.35; cues.append("low_social_filter")

    if pressure == "high":
        score -= 0.45; cues.append("pressure_compresses_surface")
    elif pressure == "medium":
        score -= 0.15

    score = max(0.0, min(4.0, score))
    if score < 0.75:
        level = 0
    elif score < 1.5:
        level = 1
    elif score < 2.6:
        level = 2
    elif score < 3.5:
        level = 3
    else:
        level = 4
    labels = {
        0: "rough_plain",
        1: "casual_plain",
        2: "colloquial_correct",
        3: "polite",
        4: "formal_institutional",
    }
    contraction = {
        0: "high_if_character_supports",
        1: "moderate_to_high",
        2: "contextual",
        3: "low_to_contextual",
        4: "low",
    }[level]
    completeness = {
        0: "fragment_or_direct_sentence",
        1: "short_natural",
        2: "natural_complete_with_ellipsis_when_characteristic",
        3: "more_complete_and_self_monitored",
        4: "complete_institutional_without_grandiloquence",
    }[level]
    lexical = "age_and_experience_bounded"
    if family in {"rough_youthful", "socially_adaptive_youthful", "polite_reserved_youthful", "earnest_deferential_youthful", "clipped_plain", "low_energy_plain"}:
        lexical = "juvenile_concrete_unless_subject_is_studied_or_technical"
    elif family in {"relaxed_adult", "expressive_teacher", "warm_authority"}:
        lexical = "adult_natural_no_bureaucratic_padding"

    return {
        "score": round(score, 2),
        "level": level,
        "register": labels[level],
        "reference_family": family_packet,
        "authority_target": authority_target,
        "social_filter": filter_level,
        "pressure": pressure,
        "contraction_policy": contraction,
        "sentence_completeness": completeness,
        "lexical_complexity": lexical,
        "grammar_rule": "correctness and formality are independent; preserve character-specific grammar/orality",
        "honorific_rule": "resolve from directional relation and addressing plan; never add merely to sound like anime",
        "cues": cues,
    }


def _universal_language_contract_v23(
    profile: Dict[str, Any],
    relation_lines: List[str],
    baseline: List[str],
    filter_level: str,
    pressure: str,
    formality: Dict[str, Any],
) -> Dict[str, Any]:
    combined = relation_lines + baseline
    return {
        "version": "v23",
        "universal_naruto_register": {
            "language": "PT-BR Naruto Clássico",
            "invariants": [
                "natural shonen dialogue; performable aloud",
                "no internet slang/memes/therapy-speak/system language",
                "no modern corporate/bureaucratic register",
                "no generic medieval fantasy register",
                "shinobi institutional vocabulary is natural when context calls for it",
                "honorifics/titles carry relationship, not decoration",
                "plain speech may still be grammatically correct",
                "polite speech must not become artificial ceremonial Portuguese",
            ],
            "translation_rule": "translate pragmatic function from Japanese role-language into Brazilian Portuguese rather than copying Japanese grammar mechanically",
        },
        "individual_transform": {
            "baseline": baseline,
            "relationship_shift": relation_lines,
            "social_filter": filter_level,
            "pressure": pressure,
            "formality_profile": formality,
            "correction_orality": _extract_labels(combined, ["formalidade", "corretividade", "coloquial", "oralidade", "imperativo"]),
            "vocative_position": _extract_labels(combined, ["vocativo", "nome", "abertura", "fechamento", "sensei", "kun", "san", "sama"]),
            "latency_cadence": _extract_labels(combined, ["latência", "cadência", "interrup", "silêncio", "pouca fala", "rápida"]),
            "body_prosody": _extract_labels(combined, ["corpo", "olhar", "postura", "volume", "tom", "punho", "passo", "gesto"]),
        },
        "kishimoto_bend_line": [
            "draft semantic intent plainly",
            "bend grammar and rhythm into the actor",
            "remove vocabulary/complexity the actor would not own",
            "resolve bare-name/title/honorific/omission",
            "reshape sentence length, interruption, ellipsis and breath",
            "delete dialogue if body/silence is truer",
            "verify it still sounds born inside Naruto",
        ],
        "performance_wash": [
            "reference_exact_phase", "reboot_divergence", "directional_relation",
            "private_impulse", "social_filter", "body_state", "formality_gate",
            "speech_or_silence", "micro_signature", "subtext",
        ],
        "dialogue_refinement": [
            "write_semantic_line_then_bend_into_character",
            "formality_must_be_resolved_before_wording",
            "remove_explanation_the_character_would_not_say",
            "place_name_or_honorific_where_this_relation_naturally_uses_it",
            "prefer_body_or_silence_when_more_faithful",
            "scene_level_decision_and_relationship_test; functional_shared_phrases_are_valid",
            "mental_read_aloud_test",
        ],
        "anti_ai": [
            "no scene summary in dialogue", "no self-psychology explanation",
            "no narrator thesis in NPC mouth", "no obligatory reaction line",
            "no decorative microgesture", "no trailer aphorism",
        ],
    }


def _v21_voice_contract(profile: Dict[str, Any], relation_lines: List[str], baseline: List[str], filter_level: str, pressure: str) -> Dict[str, Any]:
    """Legacy wrapper retained for compatibility; v24 evidence and scope take precedence."""
    combined = relation_lines + baseline
    return {
        "version": "v21",
        "universe_register": "PT-BR Naruto Clássico: natural, shōnen, sem internetês, sem terapia-speak, sem fala burocrática de IA.",
        "individual_register": {
            "baseline": baseline,
            "relationship_shift": relation_lines,
            "social_filter": filter_level,
            "pressure": pressure,
            "correction_orality": _extract_labels(combined, ["formalidade", "corretividade", "coloquial", "oralidade", "imperativo"]),
            "vocative_position": _extract_labels(combined, ["vocativo", "nome", "abertura", "fechamento", "sensei", "kun", "san"]),
            "latency_cadence": _extract_labels(combined, ["latência", "cadência", "interrup", "silêncio", "pouca fala", "rápida"]),
            "body_prosody": _extract_labels(combined, ["corpo", "olhar", "postura", "volume", "tom", "punho", "passo", "gesto"]),
        },
        "performance_wash": [
            "reference_exact_phase",
            "reboot_divergence",
            "directional_relation",
            "private_impulse",
            "social_filter",
            "body_state",
            "speech_or_silence",
            "micro_signature",
            "subtext",
        ],
        "dialogue_refinement": [
            "write_semantic_line_then_bend_into_character",
            "remove_explanation_the_character_would_not_say",
            "place_name_or_honorific_where_this_relation_naturally_uses_it",
            "prefer_body_or_silence_when_more_faithful",
            "scene_level_decision_and_relationship_test; functional_shared_phrases_are_valid",
            "mental_read_aloud_test",
        ],
        "anti_ai": [
            "no scene summary in dialogue",
            "no self-psychology explanation",
            "no narrator thesis in NPC mouth",
            "no obligatory reaction line",
            "no decorative microgesture",
            "no trailer aphorism",
        ],
    }



def _sayability_gate_v22(
    actor: str,
    stimulus: str,
    situation: str,
    objective: str,
    relation_lines: List[str],
    baseline: List[str],
    pressure: str,
    audience: str,
    knowledge_constraint: str,
) -> Dict[str, Any]:
    """Decide whether this actor should speak before any wording is generated."""
    if actor == "Amatsu Uchiha":
        return {"verdict": "must_not_speak", "reason": "player_control"}
    mapping = fidelity_catalog().get("characters", {}).get(actor, {})
    entity_type = mapping.get("entity_type", "individual")
    if entity_type == "ninken":
        return {"verdict": "must_not_speak", "reason": "ninken_nonverbal_human_dialogue_blocked", "reasons": ["use_body_sound_scent_action"]}
    if entity_type == "historical":
        situation_n = _norm(situation)
        flashback_cue = any(x in situation_n for x in ["flashback", "memoria", "lembranca", "registro historico", "historia narrada"])
        negated_flashback = bool(re.search(r"\b(?:sem|nao ha|nao existe)\s+(?:um\s+|uma\s+)?(?:flashback|memoria|lembranca|registro historico|historia narrada)\b", situation_n))
        if not flashback_cue or negated_flashback:
            return {"verdict": "must_not_speak", "reason": "historical_actor_requires_legitimate_flashback_source", "reasons": []}
    text = _norm(" ".join(relation_lines + baseline))
    event = _norm(f"{stimulus} {situation}")
    objective_n = _norm(objective)
    reasons: List[str] = []

    direct = bool(stimulus.strip()) and any(x in event for x in [
        _norm(_first_name(actor)), "responde", "pergunta", "chama", "diz", "fala",
        "ataca", "atinge", "provoca", "olha", "ordem", "alerta"
    ])
    if direct:
        reasons.append("directly_affected_or_addressed")

    functional_objective = bool(objective_n and objective_n not in {"not_provided", "nao fornecido"})
    if functional_objective:
        reasons.append("explicit_scene_objective")

    economy = any(x in text for x in [
        "pouca fala", "baixa frequencia", "silencio", "pode ignorar",
        "economico", "raramente explica"
    ])
    expressive = any(x in text for x in [
        "explos", "reacao rapida", "interromp", "fala rapida", "grito",
        "assertiv", "provoc"
    ])

    high = pressure == "high"
    if economy and not direct and not functional_objective:
        return {
            "verdict": "prefer_body_or_silence",
            "reason": "economical_profile_without_verbal_need",
            "reasons": reasons,
        }
    if high and direct:
        return {
            "verdict": "may_speak",
            "reason": "pressure_allows_only_functional_compressed_speech",
            "reasons": reasons,
        }
    if direct and expressive:
        return {
            "verdict": "may_speak",
            "reason": "direct_stimulus_matches_expressive_profile",
            "reasons": reasons,
        }
    if direct or functional_objective:
        return {
            "verdict": "may_speak",
            "reason": "scene_has_legitimate_verbal_motive",
            "reasons": reasons,
        }
    return {
        "verdict": "prefer_body_or_silence",
        "reason": "no_clear_verbal_motive",
        "reasons": reasons,
    }


def _addressing_plan_v22(
    actor: str,
    interlocutor: str,
    profile: Dict[str, Any],
    interlocutor_profile: Dict[str, Any],
    relation_lines: List[str],
    baseline: List[str],
    tags: List[str],
    pressure: str,
    formality: Dict[str, Any],
) -> Dict[str, Any]:
    """Resolve vocative/title/honorific as relational state (v33), retaining the v22 key for compatibility."""
    combined = relation_lines + baseline
    notes = _extract_labels(combined, [
        "vocativo", "nome", "sensei", "kun", "san", "sama", "senhor",
        "senhora", "titulo", "honorifico", "abertura", "fechamento"
    ])
    resolved_actor = resolve_fidelity_name(actor)
    mapping = fidelity_catalog().get("characters", {}).get(resolved_actor, {})
    refs = [str(x) for x in mapping.get("reference_characters", [])]
    refs_n = {_norm(x) for x in refs}
    family = (formality.get("reference_family") or {}).get("family", "profile_driven")

    actor_sensei = str(profile.get("sensei") or "")
    if not actor_sensei:
        actor_sensei = str(_extract_field(profile, "Sensei") or "")
    if not actor_sensei:
        actor_bible = acting_character_bible(actor)
        actor_sensei = str(
            ((actor_bible.get("bible") or {}).get("identity") or {}).get("sensei") or ""
        )
    is_own_teacher = bool(actor_sensei and _norm(actor_sensei) == _norm(interlocutor))

    target_identity = _norm(_extract_field(interlocutor_profile, "Identificação", "Identificacao")) if interlocutor_profile else ""
    target_name = _norm(interlocutor)
    is_kage = bool(
        "hokage" in target_identity
        or re.search(r"\bkage\b", target_identity)
        or "hokage" in target_name
        or any(x in target_name for x in ["daizen sarutobi"])
    )
    relation_text = _norm(" ".join(relation_lines))
    is_teacher = bool(
        is_own_teacher
        or "sensei" in relation_text
        or "professor" in target_identity
        or "instrutor" in target_identity
    )
    urgent = pressure == "high" or "danger" in tags
    respect_family = family in {
        "socially_adaptive_youthful", "polite_reserved_youthful",
        "earnest_deferential_youthful", "warm_authority", "expressive_teacher"
    }
    teacher_title_strength = "strong_default" if respect_family else "contextual_default"

    plan = {
        "version": "v33-relational-addressing",
        "actor": actor,
        "interlocutor": interlocutor or None,
        "notes": notes,
        "rule": "address form is relational state, not decoration; resolve reference + phase + hierarchy + intimacy + urgency before wording",
        "placement": "omit_if_conversation_already_clear",
        "honorific_policy": "profile_reference_relation_specific",
        "reference_characters": refs,
        "reference_family": family,
        "authority_target": bool(formality.get("authority_target")),
        "urgency_compression": urgent,
    }

    # Explicit reboot relation always outranks family defaults.
    if actor == "Saya Haruno" and interlocutor == "Kazuma Uzumaki":
        plan.update({
            "preferred_forms": ["Kazuma-kun", "Kazuma"],
            "default_form": "Kazuma-kun",
            "honorific_strength": "strong_relational_default",
            "honorific_policy": "early Sakura→Sasuke-like investment preserves -kun in ordinary direct address; bare Kazuma is licensed by urgency, sharp irritation, or later live relationship change",
            "placement": "ending for appeal/checking; beginning for alert; may be omitted when turn is already obvious"
        })
        return plan
    if actor == "Saya Haruno" and interlocutor == "Amatsu Uchiha":
        plan.update({
            "preferred_forms": ["Amatsu"],
            "default_form": "Amatsu",
            "honorific_strength": "none_by_default",
            "honorific_policy": "bare name/omission is the established peer-conflict surface",
            "placement": "beginning for reprimand/alert; often omitted during continuous argument"
        })
        return plan

    # Teacher/superior titles survive casual personality when the reference does.
    if is_teacher:
        first = _first_name(interlocutor)
        plan.update({
            "preferred_forms": [f"{first}-sensei", "sensei"],
            "default_form": "sensei" if urgent else f"{first}-sensei",
            "honorific_strength": teacher_title_strength,
            "honorific_policy": "teacher title is relational; urgency may compress Name-sensei to sensei! but should not erase respect automatically",
            "placement": "name+title in ordinary direct address; title alone when turn is established or urgent"
        })
        # Rough/clipped youths may have explicit nickname/bare-name exceptions in relation rules.
        if family in {"rough_youthful", "clipped_plain", "sparse_unsettling"} and not any(
            x in relation_text for x in ["sensei", "respeit", "formal", "autoridade"]
        ):
            plan["honorific_strength"] = "contextual_default"
        return plan

    if is_kage:
        if respect_family or "sakura" in refs_n or "ino" in refs_n or "hinata" in refs_n or "lee" in refs_n:
            plan.update({
                "preferred_forms": ["Hokage-sama", "Senhor(a) Hokage", "Grande Hokage"],
                "default_form": "Hokage-sama",
                "honorific_strength": "strong_authority_default",
                "honorific_policy": "use a deferential Kage title; choose Japanese or established PT-BR equivalent by scene register, not at random",
                "placement": "title in direct address; omission only when grammar does not require vocative"
            })
        else:
            plan.update({
                "preferred_forms": ["Hokage", "Hokage-sama", "Senhor(a) Hokage"],
                "honorific_strength": "profile_dependent",
                "honorific_policy": "rank alone does not erase actor-specific rudeness/intimacy; explicit relation may override"
            })
        return plan

    # Canonical-reference social suffix tendencies. They never license blanket suffix insertion.
    if "hinata" in refs_n and any(x in relation_text for x in ["admira", "romanc", "interesse", "afei", "proxim"]):
        first = _first_name(interlocutor)
        plan.update({
            "preferred_forms": [f"{first}-kun", first],
            "default_form": f"{first}-kun",
            "honorific_strength": "relationship_stable_when_supported",
            "honorific_policy": "Hinata-like -kun is preserved only for the mapped emotionally invested relation, never for every male peer"
        })
    elif "lee" in refs_n and any(x in relation_text for x in ["respeit", "admira", "colega", "par"]):
        first = _first_name(interlocutor)
        plan.update({
            "preferred_forms": [f"{first}-san", first],
            "honorific_strength": "contextual_respect",
            "honorific_policy": "Lee-like -san requires the corresponding respectful peer relation; do not universalize"
        })
    elif actor == "Kazuma Uzumaki":
        plan.update({
            "honorific_policy": "do not insert honorifics mechanically; Sasuke-initial axis favors bare names or omission unless an explicit teacher/authority/relation rule applies",
            "honorific_strength": "low_by_default",
            "placement": "name rare; beginning only for real alert/challenge/call"
        })
    elif actor == "Iruka Umino":
        plan.update({
            "honorific_policy": "students usually addressed by first name",
            "honorific_strength": "teacher_to_student_no_suffix_default",
            "placement": "student name first in reprimand/urgent correction"
        })

    return plan

def _actor_beat_v22(
    actor: str,
    interlocutor: str,
    stimulus: str,
    situation: str,
    objective: str,
    body_state: str,
    filter_level: str,
    pressure: str,
    relation_lines: List[str],
    baseline: List[str],
) -> Dict[str, Any]:
    combined = relation_lines + baseline
    return {
        "given_circumstances": situation or "current scene",
        "target_person": interlocutor or "scene/world",
        "immediate_objective": objective or "derive from established role/relation; do not invent plot motive",
        "obstacle": "derive only from current stimulus, body, hierarchy and legitimate knowledge",
        "private_impulse": "derive from stimulus + established persona",
        "social_mask": filter_level,
        "action_verb": "choose a playable verb such as warn, dismiss, impress, challenge, soothe, conceal, test, command, deflect; never an abstract thesis",
        "subtext": "what the actor wants the other person to feel/do without explaining it aloud",
        "physical_score": _extract_labels(combined, ["corpo", "olhar", "postura", "punho", "passo", "gesto", "distancia"]),
        "vocal_score": _extract_labels(combined, ["volume", "tom", "cadencia", "latencia", "oralidade", "formalidade"]),
        "breath_phrase_shape": "pressure compresses phrasing; calm allows fuller breath groups; do not punctuate as AI cadence",
        "exit_beat": "leave a causal opening for the next actor/player response",
    }


def _microexpression_plan_v22(
    actor: str,
    interlocutor: str,
    relation_lines: List[str],
    baseline: List[str],
    pressure: str,
) -> Dict[str, Any]:
    combined = relation_lines + baseline
    established = _extract_labels(combined, [
        "olhar", "sobrancelha", "boca", "sorriso", "punho", "postura",
        "passo", "corpo", "rubor", "vergonha", "gesto"
    ])
    plan: Dict[str, Any] = {
        "established_cues": established,
        "rule": "use at most the cues caused by the same impulse; no decorative gesture quota",
    }
    if actor == "Saya Haruno":
        if interlocutor == "Amatsu Uchiha":
            plan["relation_bias"] = "faster visible leakage: eyes/brows/posture can react before verbal self-control"
        elif interlocutor == "Kazuma Uzumaki":
            plan["relation_bias"] = "self-monitoring rises: posture/voice may correct, hesitation or repair can precede/interrupt line"
        else:
            plan["relation_bias"] = "with teachers/superiors, respect can surface as quick posture/voice correction and title use"
    return plan


def healthcheck() -> Dict[str, Any]:
    data = _characters()
    rules = _rules()
    chars = data.get("characters", {})
    missing_voice = sorted(k for k, v in chars.items() if not (v.get("voice_raw") or "").strip())
    missing_dossier = sorted(k for k, v in chars.items() if not (v.get("dossier_raw") or "").strip())
    return {
        "ok": not missing_voice and not missing_dossier,
        "module": "Naruto Persona Engine",
        "quality_protocol": "v49-evidence-agency-tactical-performance",
        "version": rules.get("version"),
        "continuity_id": rules.get("continuity_id"),
        "characters": len(chars),
        "persona_profiles": len(chars),
        "evidence_entities": len(fidelity_catalog().get("characters", {})),
        "missing_voice": missing_voice,
        "missing_dossier": missing_dossier,
        "llm_required_for_core": False,
        "external_research_policy": "verify_reference_every_turn_and_research_missing_evidence",
        "fidelity_v24": fidelity_health(),
        "fidelity_protocol": "v25.0.0",
        "acting_bible_v25": acting_health(),
        "universal_language_protocol": "v23",
        "formality_protocol": "v23",
        "addressing_protocol": "v33",
        "relational_hierarchy_protocol": "v43",
        "supports_third_person_hierarchy_v43": True,
        "supports_pairwise_reference_v43": True,
        "pairwise_match_requires_explicit_interaction_pairs": True,
        "supports_epistemic_fact_gate_v46": True,
        "supports_non_destructive_live_history_v46": True,
        "supports_emotional_density_v46": True,
        "reference_essence_protocol": "v34",
        "formality_calibration": "v33-relational-honorifics",
        "continuity_firewall_v36": _continuity_firewall_v36(),
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
        "acting_bible_v25": acting_character_bible(resolved).get("bible"),
        "voice_baseline": _baseline_voice_lines(p.get("voice_raw", "")),
        "raw_voice_rules": p.get("voice_raw", ""),
        "arc_specific": bool(p.get("arc_specific")),
        "evidence_v24": evidence_v24(resolved),
        "continuity_firewall_v36": _continuity_firewall_v36(),
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
    relationship_bible_v36 = acting_relationship_bible(a, b)
    graph_relation_v36 = relationship_bible_v36.get("relationship", {}) if relationship_bible_v36.get("status") == "ok" else {}
    if graph_relation_v36:
        if relationship_bible_v36.get("relationship_source") == "relationship_graph_live_override":
            rel_lines = []
        rel_lines = _uniq(rel_lines + [
            *(graph_relation_v36.get("facts", []) if isinstance(graph_relation_v36.get("facts"), list) else []),
            *(graph_relation_v36.get("history", []) if isinstance(graph_relation_v36.get("history"), list) else []),
            str(graph_relation_v36.get("rule") or ""),
            str(graph_relation_v36.get("baseline") or ""),
            str(graph_relation_v36.get("address") or ""),
            str(graph_relation_v36.get("must_not") or ""),
            str(graph_relation_v36.get("reference_relation_axis_v28") or ""),
            str(graph_relation_v36.get("reference_relation_transfer_v28") or ""),
            str(graph_relation_v36.get("reference_relation_must_not_v28") or "")
        ])
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
        "relationship_bible_v36": relationship_bible_v36,
        "latency_notes": _extract_labels(rel_lines + baseline, ["latência", "reação rápida", "deliberada", "instantânea"]),
        "vocative_notes": _extract_labels(rel_lines + baseline, ["vocativo", "nome", "abertura", "fechamento", "sensei", "hokage"]),
        "morphosyntax_notes": _extract_labels(rel_lines + baseline, ["oralidade", "imperativo", "corretividade", "forma", "para", "pare", "suba", "sobe"]),
        "body_notes": _extract_labels(rel_lines + baseline, ["corpo", "punho", "olhar", "postura", "avanço", "passo", "fisic"]),
        "silence_notes": _extract_labels(rel_lines + baseline, ["silêncio", "calar", "ignorar", "não precisa", "pouca fala"]),
        "forbidden_or_avoid": _extract_labels(rel_lines + baseline, ["evitar", "proibido", "bloqueio", "não transformar", "não fazer"]),
        "formality_profile_v23": _formality_profile_v23(
            a, b, pa, pb, rel_lines, baseline, tags, plev, _filter_level(rel_lines)
        ),
        "research": _research_packet(pa, pb, rel_lines, situation, ""),
        "continuity_firewall_v36": _continuity_firewall_v36(),
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
    prior_exchange: str = "",
    relationship_state: str = "",
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
    acting_v25 = acting_compile_packet(
        actor, interlocutor_resolved or interlocutor or "", stimulus, situation,
        prior_exchange, pressure, audience, body_state
    )
    baseline = _baseline_voice_lines(p.get("voice_raw", ""))
    rel_lines = _relation_lines(p.get("voice_raw", ""), interlocutor_resolved or "")
    rel_v25 = acting_v25.get("relationship", {}) if acting_v25.get("status") == "ok" else {}
    if rel_v25:
        if acting_v25.get("relationship_source") == "relationship_graph_live_override":
            rel_lines = []
        rel_lines = _uniq(rel_lines + [
            *(rel_v25.get("facts", []) if isinstance(rel_v25.get("facts"), list) else []),
            *(rel_v25.get("history", []) if isinstance(rel_v25.get("history"), list) else []),
            rel_v25.get("rule", ""),
            rel_v25.get("baseline", ""),
            rel_v25.get("address", ""),
            rel_v25.get("must_not", ""),
            rel_v25.get("reference_relation_axis_v28", ""),
            rel_v25.get("reference_relation_transfer_v28", ""),
            rel_v25.get("reference_relation_must_not_v28", ""),
            *[str(x.get("response", "")) for x in rel_v25.get("trigger_rules", []) if isinstance(x, dict)]
        ])
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
    evidence = evidence_v24(actor, interlocutor_resolved or interlocutor or "", situation, stimulus)
    formality_v23 = _formality_profile_v23(
        actor, interlocutor_resolved or interlocutor or "", p, ip, rel_lines, baseline,
        tags, plev, filter_level
    )
    universal_voice_v23 = _universal_language_contract_v23(
        p, rel_lines, baseline, filter_level, plev, formality_v23
    )
    sayability_v22 = _sayability_gate_v22(
        actor, stimulus, situation, objective, rel_lines, baseline, plev, audience, knowledge_constraint
    )
    actor_beat_v22 = _actor_beat_v22(
        actor, interlocutor_resolved or interlocutor or "", stimulus, situation, objective,
        body_state, filter_level, plev, rel_lines, baseline
    )
    actor_state_v29 = compile_actor_state(
        actor=actor,
        interlocutor=interlocutor_resolved or interlocutor or "",
        stimulus=stimulus,
        situation=situation,
        pressure=plev,
        audience=audience or "unspecified",
        body_state=body_state or "not_provided",
        objective=objective or "",
        perception_constraint=perception_constraint or "",
        knowledge_constraint=knowledge_constraint or "",
        prior_exchange=prior_exchange or "",
        relationship_state=relationship_state or "",
        acting_packet=acting_v25,
        sayability=sayability_v22,
        actor_beat=actor_beat_v22,
        formality=formality_v23,
    )

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
        "prior_exchange": prior_exchange or "",
        "relationship_state_input": relationship_state or "",
        "acting_bible_v25": acting_v25,
        "escalation_v25": acting_v25.get("escalation", {}) if acting_v25.get("status") == "ok" else {},
        "dialogue_continuity_v25": {
            "rule": "Prior exchange is state. Do not reset hostility/intimacy/embarrassment at each reply.",
            "prior_exchange_supplied": bool(prior_exchange),
            "relationship_state": relationship_state or "derive from live history + acting bible"
        },
        "epistemic_constraints": {
            "perception": perception_constraint or "must be supplied by chat/Canoney if material",
            "knowledge": knowledge_constraint or "must be supplied by chat/Canoney if material",
            "rule": "Persona Engine never upgrades perception into recognition/knowledge on its own."
        },
        "continuity_firewall_v36": _rules().get("continuity_firewall_v36", {}),
        "character_continuity_v36": p.get("continuity_firewall_v36", {}),
        "reference": ref,
        "directional_relationship": {
            "anchor": relation_anchor,
            "rules": rel_lines,
            "social_filter": filter_level,
        },
        "reference_voice_family_v23": formality_v23.get("reference_family"),
        "formality_profile_v23": formality_v23,
        "universal_language_v23": universal_voice_v23,
        "sayability_gate_v22": sayability_v22,
        "actor_beat_v22": actor_beat_v22,
        "actor_state_v29": actor_state_v29,
        "addressing_plan_v22": _addressing_plan_v22(
            actor, interlocutor_resolved or interlocutor or "", p, ip, rel_lines, baseline, tags, plev, formality_v23
        ),
        "addressing_plan_v33": _addressing_plan_v22(
            actor, interlocutor_resolved or interlocutor or "", p, ip, rel_lines, baseline, tags, plev, formality_v23
        ),
        "microexpression_plan_v22": _microexpression_plan_v22(
            actor, interlocutor_resolved or interlocutor or "", rel_lines, baseline, plev
        ),
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
        "voice_contract_v23": universal_voice_v23,
        "voice_contract_v21_legacy": _v21_voice_contract(p, rel_lines, baseline, filter_level, plev),
        "body_realization": {
            "tendencies": body,
            "rule": "body and voice must arise from the same impulse; do not add random microgestures for decoration"
        },
        "forbidden_or_avoid": forb,
        "continuity_firewall_v36": _continuity_firewall_v36(),
        "research": research,
        "generation_order": _rules().get("pipeline", []),
        "final_gate": [
            "Continuity firewall v36: use only classico_floresta_da_morte; never import chronology/relations/powers from another continuity.",
            "Amatsu family state: parents dead; Takeru is the only living direct relative and is nukenin/Tenkai; do not exposit absence without scene relevance.",
            "ActorState v29 must be compiled before wording.",
            "Verificar referência v25 por fase, relação e situação; pesquisar lacunas materiais.",
            "Aplicar a Bíblia de Atuação v25: histórico relacional e gatilho pessoal vencem personalidade genérica.",
            "V47: relação live atual SUBSTITUI baseline histórico conflitante; história antiga não volta a operar como estado atual.",
            "V47: mapear world truth / percepção individual / compreensão antes da fala; fato sem canal legítimo bloqueia o candidato antes de sair.",
            "Carregar o prior_exchange; não reiniciar temperatura emocional a cada fala.",
            "Economia verbal não é baixa intensidade: beat relacional material precisa carregar peso em corpo, latência, subtexto, ação ou fala.",
            "Se a fala puder ser trocada entre três NPCs sem alteração, reescrever.",
            "Uma ordem funcional como Abaixa! pode servir a várias pessoas sem ser um erro.",
            "Avaliar identidade no conjunto de decisões e falas; não forçar bordão, gesto ou insulto.",
            "Ficha própria precede analogia; inspiração técnica não autoriza copiar personalidade.",
            "Amatsu permanece inteiramente do jogador; tentativa de NPC não decide reação dele.",
            "Rever conhecimento, corpo, pressão e continuidade; somente então apresentar a cena."
        ],
    }


def _epistemic_fact_gate_v46(
    candidate_text: str,
    knowledge_constraint: str = "",
    known_facts: List[str] | None = None,
    forbidden_facts: List[str] | None = None,
    candidate_facts: List[str] | None = None,
    prior_exchange: str = "",
) -> List[str]:
    """Deterministic hard gate for material facts, not only proper names."""
    issues: List[str] = []
    ntext = _norm(candidate_text)
    nk = _norm(knowledge_constraint)
    nprior = _norm(prior_exchange)
    known = [_norm(x) for x in (known_facts or []) if str(x).strip()]
    forbidden = [_norm(x) for x in (forbidden_facts or []) if str(x).strip()]

    # Explicitly forbidden facts are always a hard issue when asserted.
    for fact in forbidden:
        if fact and (fact in ntext or any(tok in ntext for tok in fact.split() if len(tok) >= 6)):
            issues.append(f"v46_knowledge_without_channel:{fact}")

    # Backward-compatible parsing for callers that only have knowledge_constraint.
    # We only mine the negative portion, never infer new positive knowledge.
    negative_markers = [
        "nao sabe", "nao conhece", "sem canal", "sem conhecimento",
        "does not know", "has no channel", "unknown to"
    ]
    for marker in negative_markers:
        pos = nk.find(marker)
        if pos < 0:
            continue
        tail = nk[pos + len(marker):]
        tail = re.split(r"[.;\n]", tail, maxsplit=1)[0]
        pieces = re.split(r"[,/]|\bou\b|\be\b|\band\b", tail)
        for piece in pieces:
            p = piece.strip(" :-")
            if not p:
                continue
            keywords = [x for x in p.split() if len(x) >= 5 and x not in {"detalhes","qualquer","sobre","facts","details"}]
            if keywords and any(x in ntext for x in keywords):
                issues.append(f"v46_knowledge_constraint_violation:{p}")

    # Structured candidate claims can be checked positively.
    if candidate_facts:
        for fact in candidate_facts:
            if not fact_supported(fact, known_facts or []):
                issues.append(f"v46_unverified_material_fact:{_norm(str(fact))}")

    return _uniq(issues)


def persona_audit(
    name: str,
    interlocutor: str = "",
    candidate_dialogue: str = "",
    candidate_action: str = "",
    situation: str = "",
    pressure: str = "normal",
    stimulus: str = "",
    prior_exchange: str = "",
    perception_constraint: str = "",
    knowledge_constraint: str = "",
    known_facts: List[str] | None = None,
    forbidden_facts: List[str] | None = None,
    candidate_facts: List[str] | None = None,
) -> Dict[str, Any]:
    if isinstance(situation, str) and situation.lstrip().startswith('{'):
        try:
            envelope = json.loads(situation)
        except (ValueError, TypeError):
            envelope = None
        if isinstance(envelope, dict) and "persona_audit_v49" in envelope:
            evidence = envelope["persona_audit_v49"]
            if not isinstance(evidence, dict) or not isinstance(evidence.get("situation", ""), str):
                return {"pass": False, "violations": ["Malformed persona_audit_v49 envelope"]}
            for field in ("known_facts", "forbidden_facts", "candidate_facts"):
                if field in evidence and (not isinstance(evidence[field], list) or
                        not all(isinstance(x, str) and x.strip() for x in evidence[field])):
                    return {"pass": False, "violations": [f"Invalid persona_audit_v49.{field}"]}
            situation = evidence.get("situation", "")
            known_facts = known_facts if known_facts is not None else evidence.get("known_facts")
            forbidden_facts = forbidden_facts if forbidden_facts is not None else evidence.get("forbidden_facts")
            candidate_facts = candidate_facts if candidate_facts is not None else evidence.get("candidate_facts")
    packet = character_turn_packet(
        name=name,
        interlocutor=interlocutor,
        stimulus=stimulus or candidate_action or candidate_dialogue,
        situation=situation,
        pressure=pressure,
        perception_constraint=perception_constraint,
        knowledge_constraint=knowledge_constraint,
        prior_exchange=prior_exchange,
    )
    if packet.get("status") != "ok":
        return {"pass": False, "packet_status": packet.get("status"), "violations": [packet.get("rule", "invalid actor")], "packet": packet}
    violations = []
    warnings = []
    acting_review = acting_audit_line(
        name, interlocutor, candidate_dialogue, candidate_action,
        stimulus or candidate_action or candidate_dialogue, prior_exchange, situation, pressure
    )
    violations.extend(acting_review.get("violations", []))
    warnings.extend(acting_review.get("warnings", []))
    text = f"{candidate_dialogue} {candidate_action}".strip()
    ntext = _norm(text)

    # v46: ordinary factual claims need a knowledge channel, not only proper names.
    violations.extend(_epistemic_fact_gate_v46(
        text,
        knowledge_constraint="\n".join(x for x in [knowledge_constraint, situation] if x),
        known_facts=known_facts,
        forbidden_facts=forbidden_facts,
        candidate_facts=candidate_facts,
        prior_exchange=prior_exchange,
    ))

    # v46 non-destructive relationship regression gate.
    acting_relation = ((packet.get("acting_bible_v25") or {}).get("relationship") or {})
    current_status = _norm(acting_relation.get("current_status", ""))
    if current_status in {"dating", "romantic", "relationship"} and candidate_dialogue:
        denial_patterns = [
            r"\bnao\s+(?:sou|somos)\b.{0,24}\b(?:amor|namorad[oa]|casal)\b",
            r"\bnao\s+estamos\s+namorando\b",
            r"\bvoce\s+nao\s+e\s+meu\s+(?:amor|namorad[oa])\b",
        ]
        if any(re.search(p, ntext) for p in denial_patterns):
            violations.append("v46_live_relationship_regression:established_dating_denied")
    for word in _rules().get("forbidden_modernisms", []):
        if re.search(r"(?<!\w)" + re.escape(_norm(word)) + r"(?!\w)", ntext):
            violations.append(f"modernism_or_meta_language:{word}")
    ai_patterns = [
        "isso significa", "a diferença é que", "você precisa entender",
        "na verdade o que acontece", "o ponto é que", "não é x, é y",
        "em outras palavras", "basicamente", "de certa forma"
    ]
    for pattern in ai_patterns:
        if _norm(pattern) in ntext:
            warnings.append(f"possible_ai_exposition:{pattern}")
    if candidate_dialogue and len(candidate_dialogue.split()) > 20:
        explanatory = sum(1 for x in ["porque", "significa", "diferença", "objetivo", "situação", "estado"] if x in ntext)
        if explanatory >= 3:
            warnings.append("dialogue_may_be_explaining_scene_instead_of_living_it")
    if candidate_dialogue and packet["decision_surface"]["speech"]["status"] == "silence_or_short_functional_reply" and len(candidate_dialogue.split()) > 35:
        warnings.append("dialogue_may_be_too_long_for_current_silence/economy_profile")
    if packet["pressure"] == "high" and len(candidate_dialogue.split()) > 45:
        warnings.append("high_pressure_dialogue_may_be_overlong")
    formality_profile = packet.get("formality_profile_v23", {})
    formality_level = int(formality_profile.get("level", 2))
    contractions = [" ta ", " to ", " pra ", " ce ", " pro "]
    padded = f" {ntext} "
    if candidate_dialogue and formality_level >= 3 and any(x in padded for x in contractions) and packet.get("pressure") != "high":
        warnings.append("dialogue_may_be_too_contracted_for_resolved_formality")
    if candidate_dialogue and formality_level <= 2 and any(x in padded for x in [" por gentileza ", " gostaria de ", " o senhor poderia ", " a senhora poderia "]):
        warnings.append("dialogue_may_be_too_formal_for_resolved_register")
    sayability = packet.get("sayability_gate_v22", {})
    if candidate_dialogue and sayability.get("verdict") in {"prefer_body_or_silence", "must_not_speak"}:
        warnings.append("sayability_gate_prefers_no_dialogue")
    if candidate_dialogue and packet.get("actor") == "Kazuma Uzumaki":
        if any(x in ntext for x in ["sensei", "-kun", "-san"]) and not packet.get("addressing_plan_v22", {}).get("notes"):
            warnings.append("kazuma_honorific_requires_specific_live_evidence")
    if candidate_dialogue and packet.get("actor") == "Saya Haruno":
        target = packet.get("interlocutor")
        if target and any(x in _norm(target) for x in ["iruka", "kagetsu", "kakashi"]):
            target_first = _norm(_first_name(target))
            if target_first in ntext and "sensei" not in ntext:
                warnings.append("Saya_to_teacher_bare_name_is_unusual_without_contextual_reason")
            elif "sensei" not in ntext and len(candidate_dialogue.split()) > 5:
                warnings.append("Saya_to_teacher_may_need_title_or_more_respectful_register")
    # v43: hierarchy must survive third-person reference, not only direct vocative.
    # Conservative deterministic gate: only fires when the scene explicitly identifies
    # the actor's own sensei/superior as the person being discussed.
    if candidate_dialogue:
        bible = acting_character_bible(name)
        raw_bible = bible.get("bible", {}) if isinstance(bible, dict) else {}
        actor_sensei = str((raw_bible.get("identity", {}) or {}).get("sensei") or "")
        nsit = _norm(situation)
        sensei_first = _norm(_first_name(actor_sensei)) if actor_sensei else ""
        discusses_own_sensei = bool(actor_sensei and (
            _norm(actor_sensei) in nsit or
            (sensei_first and sensei_first in nsit and "sensei" in nsit) or
            ("seu sensei" in nsit or "sensei dela" in nsit or "sensei dele" in nsit)
        ))
        pronoun_only = bool(re.search(r"(?<!\w)(ele|ela)(?!\w)", ntext))
        preserves_teacher_form = bool(
            "sensei" in ntext or
            (sensei_first and re.search(r"(?<!\w)" + re.escape(sensei_first) + r"(?!\w)", ntext))
        )
        if discusses_own_sensei and pronoun_only and not preserves_teacher_form:
            warnings.append("v43_third_person_hierarchy_erased:own_sensei_referenced_as_bare_pronoun")
            grounded_revision = "third_person_hierarchy: preserve sensei/title when the superior is materially identified; pronoun-only reference needs contextual justification"
        else:
            grounded_revision = ""
        # General v43 authority reference gate. Fires only when the scene itself
        # explicitly identifies a named authority/teacher as the person being discussed.
        hierarchy_targets = []
        for candidate_name, candidate_profile in _characters().get("characters", {}).items():
            cname = _norm(candidate_name)
            cfirst = _norm(_first_name(candidate_name))
            mentioned = cname in nsit or (cfirst and len(cfirst) > 3 and re.search(r"(?<!\\w)" + re.escape(cfirst) + r"(?!\\w)", nsit))
            if not mentioned:
                continue
            ident = _norm(_extract_field(candidate_profile, "Identificação"))
            dossier = _norm(candidate_profile.get("dossier_raw", ""))
            explicit_role = ""
            for role in ["hokage", "kazekage", "mizukage", "raikage", "tsuchikage", "sannin"]:
                if role in ident or role in dossier or role in nsit:
                    explicit_role = role
                    break
            # Teacher/master status needs an explicit scene cue unless this is the actor's own sensei.
            if not explicit_role and ("sensei" in nsit or "mestre" in nsit):
                if candidate_name == actor_sensei or cname in nsit or cfirst in nsit:
                    explicit_role = "sensei" if "sensei" in nsit else "mestre"
            if explicit_role:
                hierarchy_targets.append((candidate_name, explicit_role))

        if hierarchy_targets:
            target_names_in_line = any(
                _norm(_first_name(tname)) in ntext or _norm(tname) in ntext
                for tname, _ in hierarchy_targets
            )
            target_titles_in_line = any(
                title in ntext for title in [
                    "sensei", "hokage", "kazekage", "mizukage", "raikage",
                    "tsuchikage", "sannin", "mestre", "sama"
                ]
            )
            if pronoun_only and not target_names_in_line and not target_titles_in_line:
                warnings.append("v43_third_person_authority_erased:named_superior_referenced_as_bare_pronoun")
                grounded_revision = "third_person_hierarchy: preserve the materially identified superior's title/name form; bare pronoun needs contextual justification"
    # v44 source-grounded speech-act gate: negative voice evidence can veto a line.
    v44_revision = ""
    if candidate_dialogue:
        evidence_pack = packet.get("evidence_v24", {}) or packet.get("research", {}) or {}
        cards = evidence_pack.get("scene_cards", []) or []
        supported_acts = set()
        negative_rules = []
        for card in cards:
            mechanics = card.get("voice_mechanics", {}) if isinstance(card, dict) else {}
            for act in mechanics.get("speech_acts", []) or []:
                supported_acts.add(_norm(str(act)))
            for neg in mechanics.get("negative", []) or []:
                negative_rules.append(_norm(str(neg)))
        words = candidate_dialogue.split()
        punchline_markers = [
            "viu?", "dessa vez", "nem fui eu", "nao fui eu",
            "pelo menos", "ate que", "quem diria", "olha so"
        ]
        looks_like_punchline = len(words) <= 18 and any(m in ntext for m in punchline_markers)
        forbids_punchline = any(
            ("punchline" in neg or "one-liner" in neg or "piada" in neg or "joke" in neg)
            for neg in negative_rules
        )
        supports_banter = any(
            any(k in act for k in ["banter","joke","humor","comedy","quip"])
            for act in supported_acts
        )
        if looks_like_punchline and forbids_punchline and not supports_banter:
            warnings.append("v44_unsupported_punchline:line_shape_not_supported_by_reference_voice_evidence")
            v44_revision = "source_grounded_voice_v44: remove the invented punchline; use a source-supported speech act, or silence/body if the beat is already complete"

    grounded = lint_v24(name, interlocutor, candidate_dialogue, candidate_action, situation, pressure)
    violations = _uniq(violations + grounded["violations"])
    revisions = grounded["revision_requests"]
    if 'grounded_revision' in locals() and grounded_revision:
        revisions = _uniq(revisions + [grounded_revision])
    if 'v44_revision' in locals() and v44_revision:
        revisions = _uniq(revisions + [v44_revision])
    status = "blocked" if violations else "revision_required" if revisions else grounded["status"]
    return {
        "pass": status == "reviewable",
        "status": status,
        "revision_requests": revisions,
        "semantic_review_required": True,
        "certifies_character_fidelity": False,
        "evidence_v24": grounded["evidence"],
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
            "universal_naruto_register",
            "formality_gate",
            "reference_voice_family",
            "body_voice_consistency",
            "modernism",
            "third_person_hierarchy_v43",
            "pairwise_reference_v43",
            "source_grounded_voice_v44",
            "source_speech_act_gate_v44",
            "epistemic_fact_gate_v46",
            "non_destructive_live_history_v46",
            "emotional_density_v46",
            "player_control"
        ],
        "packet": packet,
    }


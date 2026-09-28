from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from fidelity_core import evidence_packet as evidence_v24, lint as lint_v24, classify as classify_v24, health as fidelity_health, catalog as fidelity_catalog, resolve as resolve_fidelity_name

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
            hierarchy_sensitivity = 1.0
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
    if family in {"rough_youthful", "socially_adaptive_youthful", "clipped_plain", "low_energy_plain"}:
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
    if entity_type == "historical" and not any(x in _norm(situation) for x in ["flashback", "memoria", "lembranca", "registro historico", "historia narrada"]):
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
    relation_lines: List[str],
    baseline: List[str],
    tags: List[str],
    pressure: str,
) -> Dict[str, Any]:
    combined = relation_lines + baseline
    notes = _extract_labels(combined, [
        "vocativo", "nome", "sensei", "kun", "san", "sama", "senhor",
        "senhora", "titulo", "honorifico", "abertura", "fechamento"
    ])
    plan = {
        "actor": actor,
        "interlocutor": interlocutor or None,
        "notes": notes,
        "rule": "address form is functional, not decorative",
        "placement": "omit_if_conversation_already_clear",
        "honorific_policy": "profile_and_relation_specific",
    }
    if actor == "Saya Haruno":
        if interlocutor == "Kazuma Uzumaki":
            plan.update({
                "preferred_forms": ["Kazuma", "Kazuma-kun"],
                "honorific_policy": "Kazuma-kun only when admiration/appeal/self-conscious investment is active",
                "placement": "ending for appeal/checking; beginning for alert"
            })
        elif interlocutor == "Amatsu Uchiha":
            plan.update({
                "preferred_forms": ["Amatsu"],
                "honorific_policy": "normally none",
                "placement": "beginning for reprimand/alert; often omitted during continuous argument"
            })
        elif interlocutor:
            # Saya is comparatively overt about teacher/superior titles.
            if any(x in _norm(interlocutor) for x in ["iruka", "kagetsu", "kakashi"]):
                plan.update({
                    "preferred_forms": [f"{_first_name(interlocutor)}-sensei", "sensei"],
                    "honorific_policy": "highly natural with teacher/superior; can become just 'sensei!' under urgency",
                    "placement": "name+title in direct address; title alone when turn is already established"
                })
    elif actor == "Kazuma Uzumaki":
        plan.update({
            "honorific_policy": "do not insert honorifics mechanically; Sasuke-initial axis favors bare names or omission",
            "placement": "name rare; beginning only for real alert/challenge/call"
        })
    elif actor == "Iruka Umino":
        plan.update({
            "honorific_policy": "students usually addressed by first name",
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
        "fidelity_protocol": "v24.1",
        "universal_language_protocol": "v23",
        "formality_protocol": "v23",
        "formality_calibration": "v23.3-audit-and-low-filter",
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
        "evidence_v24": evidence,
        "voice_baseline": _baseline_voice_lines(p.get("voice_raw", "")),
        "raw_voice_rules": p.get("voice_raw", ""),
        "arc_specific": bool(p.get("arc_specific")),
        "evidence_v24": evidence_v24(resolved),
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
        "formality_profile_v23": _formality_profile_v23(
            a, b, pa, pb, rel_lines, baseline, tags, plev, _filter_level(rel_lines)
        ),
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
    evidence = evidence_v24(actor, interlocutor_resolved or interlocutor or "", situation, stimulus)
    formality_v23 = _formality_profile_v23(
        actor, interlocutor_resolved or interlocutor or "", p, ip, rel_lines, baseline,
        tags, plev, filter_level
    )
    universal_voice_v23 = _universal_language_contract_v23(
        p, rel_lines, baseline, filter_level, plev, formality_v23
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
        "reference_voice_family_v23": formality_v23.get("reference_family"),
        "formality_profile_v23": formality_v23,
        "universal_language_v23": universal_voice_v23,
        "sayability_gate_v22": _sayability_gate_v22(
            actor, stimulus, situation, objective, rel_lines, baseline, plev, audience, knowledge_constraint
        ),
        "actor_beat_v22": _actor_beat_v22(
            actor, interlocutor_resolved or interlocutor or "", stimulus, situation, objective,
            body_state, filter_level, plev, rel_lines, baseline
        ),
        "addressing_plan_v22": _addressing_plan_v22(
            actor, interlocutor_resolved or interlocutor or "", rel_lines, baseline, tags, plev
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
        "research": research,
        "generation_order": _rules().get("pipeline", []),
        "final_gate": [
            "Verificar referência v24 por fase, relação e situação; pesquisar lacunas materiais.",
            "Uma ordem funcional como Abaixa! pode servir a várias pessoas sem ser um erro.",
            "Avaliar identidade no conjunto de decisões e falas; não forçar bordão, gesto ou insulto.",
            "Ficha própria precede analogia; inspiração técnica não autoriza copiar personalidade.",
            "Amatsu permanece inteiramente do jogador; tentativa de NPC não decide reação dele.",
            "Rever conhecimento, corpo, pressão e continuidade; somente então apresentar a cena."
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
    grounded = lint_v24(name, interlocutor, candidate_dialogue, candidate_action, situation, pressure)
    violations = _uniq(violations + grounded["violations"])
    revisions = grounded["revision_requests"]
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
            "player_control"
        ],
        "packet": packet,
    }

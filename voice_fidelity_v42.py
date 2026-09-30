"""Voice Fidelity Runtime v42 — shared hard gate for Classic Naruto RP."""
from __future__ import annotations
import re
from typing import Any

VERSION = "v43-relational-hierarchy-pair-research"

MODERNITY_FLAGS = (
    "operacionalmente", "otimizar", "protocolo de resposta", "janela operacional",
    "alinhamento", "gestão", "stakeholder", "feedback", "processar isso",
    "validar seu sentimento", "o ponto é que", "em outras palavras"
)

def _norm(v: Any) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", str(v or "").casefold())
    return "".join(c for c in s if not unicodedata.combining(c))

def compile_voice_fingerprint(actor: str, bible: dict[str, Any] | None, interlocutor: str = "", pressure: str = "", audience: str = "") -> dict[str, Any]:
    bible = bible or {}
    voice = bible.get("voice", {}) or {}
    acting = bible.get("acting", {}) or {}
    raw = voice.get("raw_voice_rules", "")
    contract = acting.get("voice_contract_v23", {}) or {}
    individual = contract.get("individual_register", {}) or {}
    formality = individual.get("formality_profile", {}) or {}
    return {
        "version": VERSION,
        "actor": actor,
        "interlocutor": interlocutor or None,
        "age_phase": (bible.get("identity", {}) or {}).get("identification", ""),
        "reference_anchor": voice.get("reference_anchor", ""),
        "reference_characters": voice.get("reference_characters", []),
        "register": voice.get("register", ""),
        "cadence": voice.get("cadence", ""),
        "addressing": voice.get("addressing", ""),
        "avoid": voice.get("avoid", ""),
        "raw_voice_rules": raw,
        "formality_profile": formality,
        "pressure": pressure,
        "audience": audience,
        "hard_rules": [
            "reserved_is_not_robotic",
            "correct_is_not_bureaucratic",
            "age_limits_lexicon_and_syntax",
            "relation_changes_surface",
            "pressure_compresses_without_uniformity",
            "body_or_silence_may_replace_speech",
            "no_generic_one_liner_personality",
            "no_modern_internet_therapy_corporate_register",
            "no_future_phase_leak",
            "epistemic_name_gate",
            "ptbr_performability_gate",
            "speech_act_resolution_required",
            "morphology_variant_gate",
            "breath_time_gate",
            "third_person_hierarchy_gate",
            "pairwise_reference_interaction_gate",
        ],
        "qes_v42": {
            "speech_act": "resolve before wording",
            "pressure": pressure,
            "hierarchy": "resolve from directional relation + scene",
            "affective_valence": "resolve from live relation",
            "approval_drive": "resolve from actor/interlocutor",
            "image_protection": "resolve from actor/interlocutor/audience",
            "rivalry": "resolve from live relation",
            "modality": "command/request/question/etc before syntax",
            "morphology": "test plausible directive variants before choosing",
            "breath_time": "combat speech requires real physical window",
            "third_person_hierarchy": "resolve whether a superior must retain sensei/Kage/Sannin/master title when referred to, not only when addressed",
            "pairwise_reference": "when actor and interlocutor both map to official references, exact-phase pair interaction evidence outranks individual personality fallback"
        },
        "line_review": [
            "immediate_beat_response","speaker_swap","interlocutor_swap","sentence_length_fit",
            "lexical_age_fit","vocative_fit","fragment_or_completeness_fit","body_first_fit",
            "source_phase_fit","knowledge_channel_fit","speech_act_fit","morphology_fit","breath_time_fit",
            "third_person_hierarchy_fit","pairwise_reference_fit"
        ],
    }

def audit_surface_line(text: str, *, allow_short: bool = False) -> list[str]:
    raw = str(text or "").strip()
    low = _norm(raw)
    issues: list[str] = []
    if not raw:
        return issues
    words = re.findall(r"\b[\wÀ-ÿ'-]+\b", raw, flags=re.UNICODE)
    if len(words) <= 3 and not allow_short and not raw.endswith(("!", "?")):
        issues.append("dry_line_review_required")
    if any(_norm(flag) in low for flag in MODERNITY_FLAGS):
        issues.append("modernity_register_review_required")
    if re.search(r"\b(?:isso significa|a diferença é que|você precisa entender|em outras palavras)\b", low):
        issues.append("ai_exposition_review_required")
    return issues

def epistemic_name_gate(name_or_claim: str, known: list[str] | None, observed: list[str] | None = None) -> bool:
    claim = _norm(name_or_claim)
    pool = " ".join(_norm(x) for x in ((known or []) + (observed or [])))
    return bool(claim and (claim in pool or any(tok and tok in pool for tok in claim.split() if len(tok) > 3)))

from __future__ import annotations

from typing import Any, Dict, List
import json
from pathlib import Path

QUALITY_V48 = json.loads((Path(__file__).parent / "RP_QUALITY_V48.json").read_text())
from voice_fidelity_v42 import VERSION as VOICE_V42_VERSION, compile_voice_fingerprint


VERSION = "v29.0-relational-actor-compiler"


def _list(value: Any) -> List[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if str(x).strip()]
    return [str(value)]


def _reference_relation(acting_bible: Dict[str, Any], interlocutor: str) -> Dict[str, Any]:
    if not isinstance(acting_bible, dict):
        return {}
    matrix = acting_bible.get("reference_relationship_matrix", {}) or {}
    if interlocutor and interlocutor in matrix:
        return matrix[interlocutor] or {}
    rel = acting_bible.get("relationship", {}) or {}
    if isinstance(rel, dict):
        axis = rel.get("reference_relation_axis_v28")
        transfer = rel.get("transfer_v28")
        must_not = rel.get("must_not_v28")
        if axis or transfer or must_not:
            return {"reference_axis": axis, "transfer": transfer, "must_not": must_not}
    return {}


def _silence_prior(voice: Dict[str, Any], sayability: Dict[str, Any]) -> str:
    cadence = str((voice or {}).get("cadence", "")).casefold()
    baseline = str((voice or {}).get("baseline", "")).casefold()
    verdict = str((sayability or {}).get("verdict", "")).casefold()
    if verdict in {"must_not_speak", "prefer_body_or_silence"}:
        return "high"
    if any(x in cadence + " " + baseline for x in ["silêncio", "baixa frequência", "pouca fala", "econôm"]):
        return "medium_high"
    if verdict == "may_speak":
        return "medium"
    return "contextual"


def compile_actor_state(
    *,
    actor: str,
    interlocutor: str,
    stimulus: str,
    situation: str,
    pressure: str,
    audience: str,
    body_state: str,
    objective: str,
    perception_constraint: str,
    knowledge_constraint: str,
    prior_exchange: str,
    relationship_state: str,
    acting_packet: Dict[str, Any],
    sayability: Dict[str, Any],
    actor_beat: Dict[str, Any],
    formality: Dict[str, Any],
) -> Dict[str, Any]:
    bible = (acting_packet or {}).get("acting_bible_v25") or (acting_packet or {})
    if "voice" not in bible and isinstance((acting_packet or {}).get("voice"), dict):
        bible = acting_packet

    voice = bible.get("voice", {}) if isinstance(bible, dict) else {}
    acting = bible.get("acting", {}) if isinstance(bible, dict) else {}
    escalation = (acting_packet or {}).get("escalation", {}) or {}
    relation = _reference_relation(bible, interlocutor)

    memory = {
        "anchor": [
            x for x in [
                f"actor={actor}",
                f"interlocutor={interlocutor}" if interlocutor else "",
                f"situation={situation}" if situation else "",
                f"objective={objective}" if objective else "",
            ] if x
        ],
        "select": [
            x for x in [
                prior_exchange,
                relationship_state,
                perception_constraint,
                knowledge_constraint,
            ] if x
        ],
        "bound": {
            "perception_limit": perception_constraint or "do not upgrade observation into recognition",
            "knowledge_limit": knowledge_constraint or "use only established knowledge channels",
            "player_control": "Amatsu voluntary action remains user-only",
        },
        "enact": "Use retrieved memory only when it changes decision, threshold, relation, body, silence, or wording; do not dump memories into dialogue.",
    }

    threshold = {
        "current_level": escalation.get("level", 0),
        "current_name": escalation.get("level_name", "baseline"),
        "reasons": _list(escalation.get("reasons")),
        "rule": "A possible behavior is not a constant behavior. Escalate only when stimulus crosses an actor-specific threshold supported by history/body/pressure.",
    }

    behavior_frequency_ledger = {
        "typical": [
            voice.get("cadence", ""),
            relation.get("transfer", "") or relation.get("transfer_v28", ""),
        ],
        "possible": [
            "speech/action patterns licensed by current objective and relationship but not required every turn",
            escalation.get("surface", ""),
        ],
        "rare": [
            "breaking-point, unusually warm, unusually cruel, or highly exposed behavior requires a strong live trigger and repetition check"
        ],
        "forbidden": [
            voice.get("avoid", ""),
            relation.get("must_not", "") or relation.get("must_not_v28", ""),
        ],
        "repetition_context": prior_exchange or "no prior exchange supplied",
        "rule": "Frequency is part of characterization. A behavior that is merely possible must not become a default catchphrase or reaction.",
    }

    candidate_surfaces = [
        {
            "mode": "silence_or_body",
            "when": "no legitimate verbal objective, reserved reference, or body carries the beat better",
        },
        {
            "mode": "short_functional_speech",
            "when": "direct task, warning, challenge, refusal, correction, request, or concrete social move",
        },
        {
            "mode": "fuller_relational_speech",
            "when": "relationship stakes or emotion genuinely require it; do not choose this merely because complete prose sounds polished",
        },
    ]

    relation_axis = {
        "reference_axis": relation.get("reference_axis") or relation.get("reference_relation_axis_v28") or "",
        "transfer": relation.get("transfer") or relation.get("transfer_v28") or "",
        "must_not": relation.get("must_not") or relation.get("must_not_v28") or "",
        "directional_rule": "A→B is compiled independently from B→A.",
    }

    decision = {
        "given_circumstances": actor_beat.get("given_circumstances", situation),
        "target": actor_beat.get("target_person", interlocutor),
        "objective": objective or actor_beat.get("immediate_objective", ""),
        "obstacle": actor_beat.get("obstacle", ""),
        "playable_action": actor_beat.get("action_verb", ""),
        "subtext": actor_beat.get("subtext", ""),
        "silence_prior": _silence_prior(voice, sayability),
        "candidate_surfaces": candidate_surfaces,
        "rule": "Choose decision category before wording. Style may not override the chosen action.",
    }

    realization = {
        "reference_anchor": voice.get("reference_anchor", ""),
        "reference_characters": voice.get("reference_characters", []),
        "register": voice.get("register", ""),
        "cadence": voice.get("cadence", ""),
        "addressing": voice.get("addressing", ""),
        "avoid": voice.get("avoid", ""),
        "formality": formality,
        "adaptive_voice_v51": QUALITY_V48.get("adaptive_voice_v51", {}),
        "body_voice_rule": acting.get("body_voice_link", "body and voice must share one impulse"),
        "dialogue_flow": acting.get("dialogue_flow_v27", {}),
        "classic_voice_fidelity_v39": (acting_packet or {}).get("classic_voice_fidelity_v39", {}),
        "source_proximate_v41": (acting_packet or {}).get("source_proximate_v41", {}),
        "voice_fidelity_v42": compile_voice_fingerprint(actor, bible, interlocutor, pressure, audience),
    }

    verifier = {
        "interlocutor_swap": "Would this exact response still work if the interlocutor changed? If yes, revise relation-specific behavior.",
        "speaker_transplant": "Could three other active NPCs say/do this unchanged? If yes, revise identity-specific decision or realization.",
        "threshold_check": "Is this reaction activated at the right frequency/intensity, or merely possible for the character?",
        "silence_check": "Was speech chosen because the actor needs it, or because the generator wanted every present NPC to talk?",
        "memory_check": "Did retrieved history change behavior rather than become exposition?",
        "camera_check": "Can body/action demonstrate the point more faithfully than narrator explanation?",
        "anti_caricature": "Reference character is a decision model, not a bag of catchphrases.",
        "oral_fingerprint_v39": "Read aloud in PT-BR. If syntax feels translated, over-complete, too polished, symmetrical, or narrator-like, bend or cut it before output.",
        "source_mechanics_v39": "Check whether the exact-phase reference would speak this much, this neatly, and this explicitly. If not, reduce, interrupt, redirect, or move meaning into body/silence.",
        "source_proximity_v41": "Check the selected card, provenance, phase and relation. Never call a synopsis a verified transcript; request evidence for unsupported cadence or turn shape.",
        "voice_surface_v42": "Resolve age/phase, grammar, formality, orality, sentence completeness, lexical age, vocative, latency and silence independently; reserved is not robotic.",
        "epistemic_name_gate_v42": "No NPC may use an unlearned proper name, technique label, organization, diagnosis or secret. Rephrase perceptually or block.",
        "epistemic_fact_gate_v46": "Extend the knowledge gate to every material proposition: events, medical status, injuries, mission results, private conversations, plans, locations, identities, relations and causes all require a legitimate channel. Narrator dossier knowledge is not actor knowledge.",
        "emotional_density_v46": "Economical speech must not flatten a high-stakes relationship beat. Preserve pressure through body, latency, action, subtext, interruption, lexical choice or dialogue; silence must perform a specific action.",
    }

    return {
        "version": VERSION,
        "quality_contract_v48": QUALITY_V48,
        "actor": actor,
        "interlocutor": interlocutor or None,
        "stimulus": stimulus,
        "pressure": pressure,
        "audience": audience,
        "body_state": body_state,
        "memory_pipeline": memory,
        "reference_relation": relation_axis,
        "reaction_threshold": threshold,
        "behavior_frequency_ledger": behavior_frequency_ledger,
        "decision_workspace": decision,
        "realization_envelope": realization,
        "verification": verifier,
        "generation_contract": [
            "ANCHOR memory",
            "SELECT only relevant memories",
            "BOUND by perception/knowledge/player control",
            "ENACT memory as behavior",
            "COMPILE directional relation and threshold",
            "CHOOSE decision/body/silence before words",
            "REALIZE language/body in exact-phase reference fingerprint",
            "APPLY classic_voice_fidelity_v39 before sentence-completeness/formality smoothing",
            "VERIFY oral PT-BR cadence, asymmetry, source mechanics, interlocutor-swap, threshold, silence, memory, and camera tests",
            "VERIFY source_proximate_v41 card and evidence quality; request source review when mechanics are unverified",
            "APPLY VOICE FIDELITY v42: age/register/orality/completeness/vocative/latency/silence as independent gates",
            "APPLY EPISTEMIC NAME GATE v42 before every proper-name or technical-label use",
            "APPLY EPISTEMIC FACT GATE v46 before every material factual proposition; no channel means no certainty",
            "APPLY EMOTIONAL DENSITY v46: economy is not blandness; high-stakes relation must remain felt in body/timing/subtext/action/voice",
        ],
    }


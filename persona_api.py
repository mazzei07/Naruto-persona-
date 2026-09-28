"""Thin tool-facing API for Naruto Persona Engine.

Each function returns JSON-serializable dictionaries and can be exposed by an MCP/plugin wrapper.
No LLM call is performed in the core path.
"""
from fidelity_core import evidence_packet as fidelity_evidence_packet, validate_turn_packet, health as fidelity_health
from acting_bible import (
    character_bible as acting_character_bible,
    relationship_bible as acting_relationship_bible,
    compile_acting_packet as acting_compile_packet,
    audit_line as acting_audit_line,
    health as acting_health,
)
from persona_engine import (
    healthcheck,
    persona_get,
    persona_search,
    relation_get,
    character_turn_packet,
    persona_audit,
)


def persona_healthcheck():
    return healthcheck()


def persona_profile(name: str):
    return persona_get(name)


def persona_find(query: str, limit: int = 12):
    return persona_search(query, limit)


def persona_relation(speaker: str, interlocutor: str, situation: str = "", pressure: str = "normal", audience: str = ""):
    return relation_get(speaker, interlocutor, situation, pressure, audience)


def persona_turn(
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
):
    packet = character_turn_packet(
        name=name,
        interlocutor=interlocutor,
        stimulus=stimulus,
        situation=situation,
        pressure=pressure,
        audience=audience,
        body_state=body_state,
        objective=objective,
        perception_constraint=perception_constraint,
        knowledge_constraint=knowledge_constraint,
        prior_exchange=prior_exchange,
        relationship_state=relationship_state,
    )
    if packet.get("status") == "ok":
        packet.setdefault("evidence_v24", fidelity_evidence_packet(name, interlocutor, situation, stimulus))
        packet.setdefault("semantic_review_required", True)
    return packet


def persona_check(
    name: str,
    interlocutor: str = "",
    candidate_dialogue: str = "",
    candidate_action: str = "",
    situation: str = "",
    pressure: str = "normal",
    stimulus: str = "",
    prior_exchange: str = "",
):
    return persona_audit(name, interlocutor, candidate_dialogue, candidate_action, situation, pressure, stimulus, prior_exchange)


def persona_sayability(
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
):
    packet = character_turn_packet(
        name=name,
        interlocutor=interlocutor,
        stimulus=stimulus,
        situation=situation,
        pressure=pressure,
        audience=audience,
        body_state=body_state,
        objective=objective,
        perception_constraint=perception_constraint,
        knowledge_constraint=knowledge_constraint,
        prior_exchange=prior_exchange,
        relationship_state=relationship_state,
    )
    return {
        "status": packet.get("status"),
        "actor": packet.get("actor"),
        "interlocutor": packet.get("interlocutor"),
        "sayability_gate_v22": packet.get("sayability_gate_v22"),
        "addressing_plan_v22": packet.get("addressing_plan_v22"),
        "actor_beat_v22": packet.get("actor_beat_v22"),
        "microexpression_plan_v22": packet.get("microexpression_plan_v22"),
        "reference_voice_family_v23": packet.get("reference_voice_family_v23"),
        "formality_profile_v23": packet.get("formality_profile_v23"),
        "universal_language_v23": packet.get("universal_language_v23"),
        "acting_bible_v25": packet.get("acting_bible_v25"),
        "escalation_v25": packet.get("escalation_v25"),
        "dialogue_continuity_v25": packet.get("dialogue_continuity_v25"),
        "evidence_v24": packet.get("evidence_v24") or fidelity_evidence_packet(name, interlocutor, situation, stimulus),
        "semantic_review_required": packet.get("semantic_review_required", True),
    }


def persona_evidence(name: str, interlocutor: str = "", situation: str = "", stimulus: str = ""):
    """Return v25 phase-scoped evidence cards without generating prose."""
    return fidelity_evidence_packet(name, interlocutor, situation, stimulus)


def persona_validate_turn_packet(packet: dict):
    """Validate the shared v25 turn packet used by Persona/Canoney/Gemini."""
    return validate_turn_packet(packet)


def persona_fidelity_health():
    """Report the evidence catalog separately from the persona registry."""
    return fidelity_health()


def persona_bible(name: str):
    return acting_character_bible(name)

def persona_relationship_bible(name: str, interlocutor: str):
    return acting_relationship_bible(name, interlocutor)

def persona_acting_packet(
    name: str,
    interlocutor: str = "",
    stimulus: str = "",
    situation: str = "",
    prior_exchange: str = "",
    pressure: str = "normal",
    audience: str = "",
    body_state: str = "",
):
    return acting_compile_packet(name, interlocutor, stimulus, situation, prior_exchange, pressure, audience, body_state)

def persona_dialogue_audit_v25(
    name: str,
    interlocutor: str = "",
    candidate_dialogue: str = "",
    candidate_action: str = "",
    stimulus: str = "",
    prior_exchange: str = "",
    situation: str = "",
    pressure: str = "normal",
):
    return acting_audit_line(name, interlocutor, candidate_dialogue, candidate_action, stimulus, prior_exchange, situation, pressure)

def persona_acting_health():
    return acting_health()

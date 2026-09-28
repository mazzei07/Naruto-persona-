"""Thin tool-facing API for Naruto Persona Engine.

Each function returns JSON-serializable dictionaries and can be exposed by an MCP/plugin wrapper.
No LLM call is performed in the core path.
"""
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
):
    return character_turn_packet(
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
    )


def persona_check(
    name: str,
    interlocutor: str = "",
    candidate_dialogue: str = "",
    candidate_action: str = "",
    situation: str = "",
    pressure: str = "normal",
):
    return persona_audit(name, interlocutor, candidate_dialogue, candidate_action, situation, pressure)


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
    )
    return {
        "status": packet.get("status"),
        "actor": packet.get("actor"),
        "interlocutor": packet.get("interlocutor"),
        "sayability_gate_v22": packet.get("sayability_gate_v22"),
        "addressing_plan_v22": packet.get("addressing_plan_v22"),
        "actor_beat_v22": packet.get("actor_beat_v22"),
        "microexpression_plan_v22": packet.get("microexpression_plan_v22"),
    }

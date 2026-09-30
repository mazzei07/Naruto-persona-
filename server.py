"""Naruto Persona Engine — remote MCP server v0.2.

Read-only behavioral specialist for Naruto Reboot — Continuidade Clássica.
Production deployment target: Render (public HTTPS) using MCP Streamable HTTP.
"""
from __future__ import annotations

import os
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse
from scene_agenda_scheduler import compile_scene_agendas

from persona_api import (
    persona_healthcheck as _healthcheck,
    persona_profile as _profile,
    persona_find as _find,
    persona_relation as _relation,
    persona_turn as _turn,
    persona_check as _check,
    persona_sayability as _sayability,
    persona_evidence as _evidence,
    persona_validate_turn_packet as _validate_turn_packet,
    persona_fidelity_health as _fidelity_health,
    persona_bible as _bible,
    persona_relationship_bible as _relationship_bible,
    persona_acting_packet as _acting_packet,
    persona_dialogue_audit_v25 as _dialogue_audit_v25,
    persona_acting_health as _acting_health,
    persona_voice_fingerprint_v42 as _voice_fingerprint_v42,
    persona_voice_audit_v42 as _voice_audit_v42,
)

PORT = int(os.getenv("PORT", "8000"))

mcp = MCPServer(
    "Naruto Persona Engine",
    version="0.13.0-v47-strict-preflight",
    instructions=(
        "Especialista read-only v47: Bíblia de Atuação por personagem, histórico relacional, prior_exchange, gatilhos de escalada, impressão linguística por idade/fase e Epistemic Name Gate antes da voz. Evidência por turno continua obrigatória; inspiração técnica não importa personalidade. "
        "Resolve referência, fase, relação direcional, filtro social, latência, corpo, voz, "
        "vocativo, morfossintaxe, silêncio e reação. Aplica o contrato v25 antes das heurísticas de registro, formalidade e relação; não força microgestos nem bordões. Família de voz só vale para inspiração de personalidade documentada. Canoney/estado live continuam sendo "
        "autoridade factual. Nunca gere decisão voluntária de Amatsu Uchiha."
    ),
)


@mcp.custom_route("/", methods=["GET"])
async def root(_: Request) -> JSONResponse:
    """Human-readable liveness page; not an MCP operation."""
    return JSONResponse(
        {
            "service": "Naruto Persona Engine",
            "version": "0.13.0-v47-strict-preflight",
            "status": "ok",
            "mcp_endpoint": "/mcp",
            "health_endpoint": "/health",
        }
    )


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    """Unauthenticated liveness/readiness endpoint for Render."""
    result = _healthcheck()
    return JSONResponse(
        {
            "status": "ok" if result.get("ok") else "degraded",
            "service": "Naruto Persona Engine",
            "version": "0.13.0-v47-strict-preflight",
            "persona_engine": result,
        },
        status_code=200 if result.get("ok") else 503,
    )


@mcp.tool()
def persona_healthcheck() -> dict[str, Any]:
    """Check local persona registry/rules health. Read-only and no web/LLM call."""
    return _healthcheck()


@mcp.tool()
def persona_profile(name: str) -> dict[str, Any]:
    """Get the operational persona profile for one Naruto Reboot character."""
    return _profile(name)


@mcp.tool()
def persona_find(query: str, limit: int = 12) -> dict[str, Any]:
    """Search the bounded local Persona Engine registry. No public-web access."""
    return _find(query, limit)


@mcp.tool()
def persona_relation(
    speaker: str,
    interlocutor: str,
    situation: str = "",
    pressure: str = "normal",
    audience: str = "",
) -> dict[str, Any]:
    """Resolve an asymmetric speaker -> interlocutor relationship packet."""
    return _relation(speaker, interlocutor, situation, pressure, audience)


@mcp.tool()
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
) -> dict[str, Any]:
    """Build the behavioral packet for one actor in the current scene beat.

    Main persona tool. It resolves stimulus -> relation -> private/public filter ->
    body/voice/silence tendencies. It does not write final RP prose or control Amatsu.
    """
    return _turn(
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


@mcp.tool()
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
) -> dict[str, Any]:
    """Resolve fala/silêncio com Bíblia v25, histórico relacional, endereçamento e formalidade contextual."""
    return _sayability(
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


@mcp.tool()
def persona_check(
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
    known_facts: list[str] | None = None,
    forbidden_facts: list[str] | None = None,
    candidate_facts: list[str] | None = None,
) -> dict[str, Any]:
    """Audit a proposed line/action against persona, relation, stage, source evidence and v46 epistemic fact gate."""
    return _check(
        name=name,
        interlocutor=interlocutor,
        candidate_dialogue=candidate_dialogue,
        candidate_action=candidate_action,
        situation=situation,
        pressure=pressure,
        stimulus=stimulus,
        prior_exchange=prior_exchange,
        perception_constraint=perception_constraint,
        knowledge_constraint=knowledge_constraint,
        known_facts=known_facts,
        forbidden_facts=forbidden_facts,
        candidate_facts=candidate_facts,
    )


@mcp.tool()
def persona_evidence(
    name: str,
    interlocutor: str = "",
    situation: str = "",
    stimulus: str = "",
) -> dict[str, Any]:
    """Retrieve v25 phase/reference evidence for one actor/beat without generating prose."""
    return _evidence(name, interlocutor, situation, stimulus)


@mcp.tool()
def persona_validate_turn_packet(packet: dict[str, Any]) -> dict[str, Any]:
    """Validate the shared v25 evidence/acting envelope before Gemini drafting."""
    return _validate_turn_packet(packet)


@mcp.tool()
def persona_fidelity_health() -> dict[str, Any]:
    """Check the v25 evidence catalog and actor-scope contract."""
    return _fidelity_health()


@mcp.tool()
def persona_bible(name: str) -> dict[str, Any]:
    """Return the full v25 acting bible for one character."""
    return _bible(name)

@mcp.tool()
def persona_relationship_bible(name: str, interlocutor: str) -> dict[str, Any]:
    """Return directional history/voice rules for actor -> interlocutor."""
    return _relationship_bible(name, interlocutor)

@mcp.tool()
def persona_acting_packet(
    name: str,
    interlocutor: str = "",
    stimulus: str = "",
    situation: str = "",
    prior_exchange: str = "",
    pressure: str = "normal",
    audience: str = "",
    body_state: str = "",
) -> dict[str, Any]:
    """Compile v25 acting state with relationship memory, trigger escalation and dialogue momentum."""
    return _acting_packet(name, interlocutor, stimulus, situation, prior_exchange, pressure, audience, body_state)

@mcp.tool()
def persona_dialogue_audit_v25(
    name: str,
    interlocutor: str = "",
    candidate_dialogue: str = "",
    candidate_action: str = "",
    stimulus: str = "",
    prior_exchange: str = "",
    situation: str = "",
    pressure: str = "normal",
) -> dict[str, Any]:
    """Audit genericity, relation drift and missed trigger escalation."""
    return _dialogue_audit_v25(name, interlocutor, candidate_dialogue, candidate_action, stimulus, prior_exchange, situation, pressure)

@mcp.tool()
def persona_generation_preflight(
    scene: dict[str, Any],
    actors: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compile all active NPC ActorStates plus parallel scene agendas before any RP prose."""
    packets = []
    issues = []
    for item in actors:
        if not isinstance(item, dict):
            issues.append("invalid_actor_item")
            continue
        name = str(item.get("name") or item.get("actor") or "")
        if not name:
            issues.append("actor_name_missing")
            continue
        if name == "Amatsu Uchiha":
            packets.append({
                "actor": name,
                "status": "player_controlled",
                "rule": "No voluntary action/reaction may be generated."
            })
            continue
        packet = _turn(
            name=name,
            interlocutor=str(item.get("interlocutor") or ""),
            stimulus=str(item.get("stimulus") or scene.get("stimulus") or ""),
            situation=str(item.get("situation") or scene.get("situation") or scene.get("location") or ""),
            pressure=str(item.get("pressure") or scene.get("pressure") or "normal"),
            audience=str(item.get("audience") or scene.get("audience") or ""),
            body_state=str(item.get("body_state") or ""),
            objective=str(item.get("objective") or ""),
            perception_constraint=str(item.get("perception_constraint") or ""),
            knowledge_constraint=str(item.get("knowledge_constraint") or ""),
            prior_exchange=str(item.get("prior_exchange") or scene.get("prior_exchange") or ""),
            relationship_state=str(item.get("relationship_state") or ""),
        )
        packets.append(packet)
        if packet.get("status") != "ok":
            issues.append(f"{name}:{packet.get('status')}")
        elif not packet.get("actor_state_v29"):
            issues.append(f"{name}:actor_state_v29_missing")
    agenda_input = []
    for item in actors:
        if isinstance(item, dict):
            agenda_input.append({
                "actor": item.get("name") or item.get("actor"),
                "player_controlled": (item.get("name") or item.get("actor")) == "Amatsu Uchiha",
                "position": item.get("position"),
                "body_state": item.get("body_state"),
                "perception": item.get("perception_constraint"),
                "knowledge": item.get("knowledge_constraint"),
                "objective": item.get("objective"),
                "current_action": item.get("current_action"),
                "attention_target": item.get("interlocutor"),
                "urgency": item.get("urgency", "normal"),
            })
    scheduler = compile_scene_agendas(scene, agenda_input)
    return {
        "status": "needs_evidence" if issues else "reviewable",
        "version": "v31-preflight",
        "issues": issues,
        "actor_packets": packets,
        "scene_scheduler_v30": scheduler,
        "rule": "No prose before ActorState + scene agenda compilation."
    }


@mcp.tool()
def persona_acting_health() -> dict[str, Any]:
    """Check v25 acting-bible coverage for the full cast."""
    return _acting_health()


@mcp.tool()
def persona_voice_fingerprint_v42(
    name: str,
    interlocutor: str = "",
    pressure: str = "normal",
    audience: str = "",
) -> dict[str, Any]:
    """Compile age/phase/register/orality/cadence/vocative/silence fingerprint before dialogue."""
    return _voice_fingerprint_v42(name, interlocutor, pressure, audience)


@mcp.tool()
def persona_voice_audit_v42(
    name: str,
    candidate_dialogue: str,
    interlocutor: str = "",
    pressure: str = "normal",
    audience: str = "",
) -> dict[str, Any]:
    """Audit a proposed line for dry/generic/modern surface risks under Voice Fidelity v42."""
    return _voice_audit_v42(name, candidate_dialogue, interlocutor, pressure, audience)


if __name__ == "__main__":
    # Render already sits behind a controlled public reverse proxy. The SDK docs
    # explicitly allow disabling DNS-rebinding Host/Origin checks in this topology.
    transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    )

    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=PORT,
        streamable_http_path="/mcp",
        stateless_http=True,
        json_response=True,
        transport_security=transport_security,
    )

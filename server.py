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
)

PORT = int(os.getenv("PORT", "8000"))

mcp = MCPServer(
    "Naruto Persona Engine",
    version="0.6.1",
    instructions=(
        "Especialista read-only v24: recuperar evidências por turno, pesquisar lacunas e nunca tratar pass como certificação semântica. Inspiração técnica não importa personalidade. "
        "Resolve referência, fase, relação direcional, filtro social, latência, corpo, voz, "
        "vocativo, morfossintaxe, silêncio e reação. Aplica o contrato v24 antes das heurísticas de registro, formalidade e relação; não força microgestos nem bordões. Família de voz só vale para inspiração de personalidade documentada. Canoney/estado live continuam sendo "
        "autoridade factual. Nunca gere decisão voluntária de Amatsu Uchiha."
    ),
)


@mcp.custom_route("/", methods=["GET"])
async def root(_: Request) -> JSONResponse:
    """Human-readable liveness page; not an MCP operation."""
    return JSONResponse(
        {
            "service": "Naruto Persona Engine",
            "version": "0.6.1",
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
            "version": "0.6.0",
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
) -> dict[str, Any]:
    """Resolve fala/silêncio com evidência v24.1, endereçamento e formalidade contextual."""
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
    )


@mcp.tool()
def persona_check(
    name: str,
    interlocutor: str = "",
    candidate_dialogue: str = "",
    candidate_action: str = "",
    situation: str = "",
    pressure: str = "normal",
) -> dict[str, Any]:
    """Audit a proposed line/action against persona, relation, and stage rules."""
    return _check(
        name=name,
        interlocutor=interlocutor,
        candidate_dialogue=candidate_dialogue,
        candidate_action=candidate_action,
        situation=situation,
        pressure=pressure,
    )


@mcp.tool()
def persona_evidence(
    name: str,
    interlocutor: str = "",
    situation: str = "",
    stimulus: str = "",
) -> dict[str, Any]:
    """Retrieve v24.1 reference evidence for one actor/beat without generating prose."""
    return _evidence(name, interlocutor, situation, stimulus)


@mcp.tool()
def persona_validate_turn_packet(packet: dict[str, Any]) -> dict[str, Any]:
    """Validate the shared v24.1 evidence envelope before Gemini drafting."""
    return _validate_turn_packet(packet)


@mcp.tool()
def persona_fidelity_health() -> dict[str, Any]:
    """Check only the v24.1 evidence catalog and actor-scope contract."""
    return _fidelity_health()


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

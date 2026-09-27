"""Remote MCP server for Naruto Persona Engine.

Read-only specialist for behavioral interpretation in
Naruto Reboot — Continuidade Clássica.
"""
from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from persona_api import (
    persona_healthcheck as _healthcheck,
    persona_profile as _profile,
    persona_find as _find,
    persona_relation as _relation,
    persona_turn as _turn,
    persona_check as _check,
)

PORT = int(os.getenv("PORT", "8000"))

mcp = FastMCP(
    "Naruto Persona Engine",
    host="0.0.0.0",
    port=PORT,
    stateless_http=True,
    instructions=(
        "Especialista read-only de interpretação do Naruto Reboot — Continuidade Clássica. "
        "Use para resolver referência, fase, relação direcional, filtro social, latência, "
        "corpo, voz, vocativo, morfossintaxe, silêncio e reação. O Canoney/estado live "
        "continua sendo autoridade factual. Nunca gere decisão voluntária de Amatsu Uchiha."
    ),
)


@mcp.tool()
def persona_healthcheck() -> dict[str, Any]:
    """Check registry/rules health for the Naruto Persona Engine."""
    return _healthcheck()


@mcp.tool()
def persona_profile(name: str) -> dict[str, Any]:
    """Get the operational persona profile for one reboot character.

    Use this for stable identity, reference anchor, baseline voice, stage locks,
    behavioral tendencies and known relation notes. It is not live scene state.
    """
    return _profile(name)


@mcp.tool()
def persona_find(query: str, limit: int = 12) -> dict[str, Any]:
    """Search the local Persona Engine registry for matching characters/rules.

    This is a bounded local lookup and does not access the public web.
    """
    return _find(query, limit)


@mcp.tool()
def persona_relation(
    speaker: str,
    interlocutor: str,
    situation: str = "",
    pressure: str = "normal",
    audience: str = "",
) -> dict[str, Any]:
    """Resolve an asymmetric speaker->interlocutor relationship packet.

    Returns relation anchor, social filter, stage/reference constraints, voice/body
    shifts and whether additional canonical research is needed for this situation.
    """
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
    """Build the behavioral packet for one character in the current beat.

    This is the main tool. Supply live perception/knowledge constraints from Canoney
    or the chat when relevant. It resolves stimulus -> private impulse -> relational
    filter -> body/voice/silence tendencies without writing final RP prose.
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
def persona_check(
    name: str,
    interlocutor: str = "",
    candidate_dialogue: str = "",
    candidate_action: str = "",
    situation: str = "",
    pressure: str = "normal",
) -> dict[str, Any]:
    """Audit a proposed line/action against persona, relationship and stage rules.

    Use after drafting or when a character reaction feels wrong. This does not make
    the candidate canonical; it only reports likely fidelity problems.
    """
    return _check(
        name=name,
        interlocutor=interlocutor,
        candidate_dialogue=candidate_dialogue,
        candidate_action=candidate_action,
        situation=situation,
        pressure=pressure,
    )


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "streamable-http")
    mcp.run(transport=transport)

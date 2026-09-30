import asyncio
import json
from unittest.mock import patch

import server
from actor_state_compiler import QUALITY_V48
from persona_api import persona_turn, persona_healthcheck


def assert_actor_state(packet):
    state = packet["actor_state_v29"]
    assert state["realization_envelope"]["adaptive_voice_v51"] == QUALITY_V48["adaptive_voice_v51"]
    assert state["memory_pipeline"]["bound"]["knowledge_limit"] == "sabe apenas do retorno"
    assert state["memory_pipeline"]["bound"]["perception_limit"] == "viu chegar; não viu hospital"
    assert "conversa anterior" in state["memory_pipeline"]["select"]


def test_api_and_mcp_turn_preserve_v51_and_knowledge_limits():
    args = dict(name="Kaede Uchiha", interlocutor="Amatsu Uchiha", stimulus="retorno",
                situation="Casa de Kaede", prior_exchange="conversa anterior",
                knowledge_constraint="sabe apenas do retorno", perception_constraint="viu chegar; não viu hospital")
    assert_actor_state(persona_turn(**args))
    assert_actor_state(server.persona_turn(**args))
    result = server.persona_generation_preflight({"location":"Casa de Kaede"}, [args, {"name":"Amatsu Uchiha"}])
    assert result["status"] == "reviewable"
    assert_actor_state(result["actor_packets"][0])
    assert result["actor_packets"][1]["status"] == "player_controlled"


def test_mcp_and_http_health_use_loaded_contract():
    assert persona_healthcheck()["quality_protocol"] == QUALITY_V48["version"]
    result = server.persona_healthcheck()
    assert result["supports_adaptive_voice_v51"] is True
    assert result["preserves_structured_actor_memory_v51"] is True
    response = asyncio.run(server.health(None))
    assert response.status_code == 200
    assert json.loads(response.body)["persona_engine"]["quality_protocol"] == QUALITY_V48["version"]
    with patch.dict(QUALITY_V48, {"adaptive_voice_v51":{}}, clear=False):
        response = asyncio.run(server.health(None))
        assert response.status_code == 503
        assert json.loads(response.body)["persona_engine"]["supports_adaptive_voice_v51"] is False

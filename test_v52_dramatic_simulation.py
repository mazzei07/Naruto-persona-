from actor_state_compiler import QUALITY_V48, compile_actor_state, quality_health_v51


def _state(**overrides):
    args = dict(
        actor="Kaede Uchiha", interlocutor="Amatsu Uchiha", stimulus="provocacao",
        situation="sala", pressure="social", audience="familia", body_state="em pe",
        objective="responder", perception_constraint="ouve a fala de Amatsu",
        knowledge_constraint="nao sabe fatos privados de Suna", prior_exchange="",
        relationship_state="namoro", acting_packet={}, sayability={}, actor_beat={}, formality={},
    )
    args.update(overrides)
    return compile_actor_state(**args)


def test_v52_contract_is_loaded_and_health_checked():
    health = quality_health_v51()
    assert QUALITY_V48["version"] == "v52-dramatic-simulation-gates"
    assert health["quality_contract_valid"] is True
    assert health["supports_adaptive_voice_v51"] is True
    assert health["preserves_structured_actor_memory_v51"] is True
    assert health["supports_dramatic_simulation_v52"] is True
    assert health["enforces_player_window_v52"] is True
    assert health["enforces_sensory_gate_v52"] is True


def test_v52_actor_state_carries_private_simulation_gates_without_forcing_gesture():
    state = _state()
    sim = state["simulation_workspace"]
    assert sim["contract"]["version"] == "v52"
    assert sim["sensory_gate"]["available_cues"] == "ouve a fala de Amatsu"
    assert sim["physical_commitment"]["first_move"] == ""
    assert "chain-of-thought" in sim["psychological_pressure"]["rule"]
    assert "meaningful voluntary" in sim["player_boundary"]["rule"]


def test_v52_surface_contract_contains_persistence_and_anti_cliche_rules():
    v52 = QUALITY_V48["dramatic_simulation_v52"]
    assert "Persist" in v52["physical_consequence"]
    assert "testamento" in v52["anti_cliche"]["avoid_terms"]
    assert "hidden JSON" in v52["final_surface"]

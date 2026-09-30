from persona_api import persona_check, persona_relation, persona_turn


def test_v46_kaede_live_relationship_wins():
    rel = persona_relation(
        "Kaede Uchiha",
        "Amatsu Uchiha",
        situation="Noite na casa de Kaede após o retorno de Suna; namoro vigente.",
        pressure="low",
        audience="privado",
    )
    r = rel["relationship_bible_v36"]["relationship"]
    assert r.get("current_status") == "dating", rel
    assert "Academia" in " ".join(r.get("history", [])), rel
    assert "não negar o namoro" in r.get("must_not", "").lower(), rel
    assert rel["relationship_bible_v36"]["relationship_source"] in {
        "relationship_graph_live_override", "explicit_override"
    }, rel


def test_v46_dating_denial_blocked():
    bad = persona_check(
        "Kaede Uchiha",
        "Amatsu Uchiha",
        candidate_dialogue="Eu não sou seu amor.",
        situation="Noite na casa de Kaede; namoro com Amatsu já está estabelecido.",
        pressure="low",
    )
    assert bad["status"] == "blocked", bad
    assert any("live_relationship_regression" in x for x in bad["violations"]), bad


def test_v46_hospital_knowledge_leak_blocked():
    bad = persona_check(
        "Kaede Uchiha",
        "Amatsu Uchiha",
        candidate_dialogue="Você foi parar no hospital em Suna.",
        situation="Kaede só sabe que Amatsu esteve em missão em Suna, perdeu o jantar e voltou alguns dias depois.",
        pressure="low",
        knowledge_constraint="Kaede não sabe que Amatsu foi ao hospital; não sabe detalhes médicos nem ferimentos.",
        forbidden_facts=["hospital"],
        candidate_facts=["Amatsu foi ao hospital em Suna"],
    )
    assert bad["status"] == "blocked", bad
    assert any("knowledge" in x or "unverified_material_fact" in x for x in bad["violations"]), bad


def test_v46_kaede_voice_evidence_is_now_grounded():
    pkt = persona_turn(
        "Kaede Uchiha",
        "Amatsu Uchiha",
        stimulus="Amatsu voltou de Suna e entra na casa dela.",
        situation="Reencontro privado após alguns dias; namoro vigente.",
        pressure="low",
        knowledge_constraint="Kaede sabe apenas que ele foi a Suna, perdeu o jantar e voltou.",
        relationship_state="dating; shared childhood; reconciled",
    )
    prox = pkt["research"]["source_proximate_v41"]
    assert prox["voice_exemplar_research_required"] is False, prox
    assert prox["dialogue_mechanics_verified"] is True, prox
    assert prox["voice_exemplar_count"] >= 2, prox


if __name__ == "__main__":
    test_v46_kaede_live_relationship_wins()
    test_v46_dating_denial_blocked()
    test_v46_hospital_knowledge_leak_blocked()
    test_v46_kaede_voice_evidence_is_now_grounded()
    print("v46 live-history/epistemic regression: ok")

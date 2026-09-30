from persona_api import persona_check, persona_turn

def test_third_person_hierarchy_v43():
    bad = persona_check(
        "Saya Haruno", "Amatsu Uchiha",
        candidate_dialogue="Você acha que ele ia deixar você sair daqui assim?",
        situation="Saya fala de Kagetsu Shiranui para Amatsu; Kagetsu é o sensei dela; contexto seguro.",
        pressure="low",
    )
    assert bad["status"] == "revision_required", bad
    assert any("third_person_hierarchy" in x for x in bad["revision_requests"]), bad

    good = persona_check(
        "Saya Haruno", "Amatsu Uchiha",
        candidate_dialogue="Você acha que o Kagetsu-sensei ia deixar você sair daqui assim?",
        situation="Saya fala de Kagetsu Shiranui para Amatsu; Kagetsu é o sensei dela; contexto seguro.",
        pressure="low",
    )
    assert good["status"] in {"reviewable", "needs_evidence"}, good

def test_pairwise_reference_v43():
    pkt = persona_turn(
        "Saya Haruno", "Kagetsu Shiranui",
        stimulus="Saya pergunta algo ao sensei.",
        situation="conversa segura entre aluna e sensei",
        pressure="low",
    )
    prox = pkt["research"]["source_proximate_v41"]
    assert prox["pair_reference_required"] is True, prox
    assert prox["pair_reference_match_found"] is True, prox
    assert prox["closest"]["pair_reference_match"] is True, prox

if __name__ == "__main__":
    test_third_person_hierarchy_v43()
    test_pairwise_reference_v43()
    print("v43 hierarchy/pairwise regression: ok")

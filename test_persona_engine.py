import json
from persona_api import persona_healthcheck, persona_relation, persona_turn, persona_check, persona_sayability, persona_bible, persona_acting_packet, persona_dialogue_audit_v25


def main():
    h = persona_healthcheck()
    assert h["characters"] == 92, h
    assert h["evidence_entities"] == 99, h
    assert h["fidelity_protocol"] == "v25.0.0", h
    assert h["acting_bible_v25"]["characters"] == 99, h
    assert h["continuity_id"] == "classico_floresta_da_morte"
    assert h["universal_language_protocol"] == "v23"
    assert h["formality_protocol"] == "v23"
    assert h["addressing_protocol"] == "v33"

    sa = persona_turn(
        "Saya Haruno", "Amatsu Uchiha",
        stimulus="Amatsu provoca Saya durante uma pausa segura",
        situation="cotidiano social cômico entre colegas",
        pressure="baixa",
        audience="Time 7"
    )
    sk = persona_turn(
        "Saya Haruno", "Kazuma Uzumaki",
        stimulus="Saya precisa corrigir Kazuma sobre algo banal",
        situation="conversa segura entre colegas",
        pressure="baixa",
        audience="Time 7"
    )
    assert sa["directional_relationship"]["social_filter"] == "low", sa["directional_relationship"]
    assert sk["directional_relationship"]["social_filter"] == "high", sk["directional_relationship"]
    assert sa["decision_surface"]["physical_comedy"]["allowed"] is True, sa["decision_surface"]
    assert sk["decision_surface"]["physical_comedy"]["allowed"] is False, sk["decision_surface"]

    ka = persona_turn(
        "Kazuma Uzumaki", "Amatsu Uchiha",
        stimulus="Amatsu faz uma provocação banal",
        situation="cotidiano sem perigo",
        pressure="baixa"
    )
    assert ka["status"] == "ok"

    kag = persona_relation("Kagetsu Shiranui", "Saya Haruno", "treino seguro", "baixa")
    assert kag["status"] == "ok"

    blocked = persona_turn("Amatsu Uchiha", "Saya Haruno", "Saya fala com ele")
    assert blocked["status"] == "blocked_player_control"

    audit = persona_check("Saya Haruno", "Kazuma Uzumaki", "Cala a boca, idiota.", situation="conversa banal", pressure="baixa")
    assert audit["pass"] is False
    assert audit["status"] == "revision_required", audit
    assert audit["revision_requests"], audit

    v22_sayability = persona_sayability(
        "Kazuma Uzumaki", "Amatsu Uchiha",
        stimulus="Amatsu faz uma careta banal que não exige resposta",
        situation="pausa segura",
        pressure="baixa",
        objective=""
    )
    assert v22_sayability["status"] == "ok"
    assert v22_sayability["sayability_gate_v22"]["verdict"] in {"prefer_body_or_silence", "may_speak"}

    saya_authority = persona_turn(
        "Saya Haruno", "Iruka Umino",
        stimulus="Iruka dá uma instrução direta à equipe",
        situation="ambiente institucional seguro",
        pressure="baixa",
        audience="Time 7"
    )
    addressing = saya_authority["addressing_plan_v22"]
    assert "sensei" in " ".join(addressing.get("preferred_forms", [])).casefold(), addressing
    assert saya_authority["addressing_plan_v33"]["version"] == "v33-relational-addressing"

    saya_kagetsu = persona_turn(
        "Saya Haruno", "Kagetsu Shiranui",
        stimulus="Kagetsu corrige Saya durante treino seguro",
        situation="treino de equipe, sem urgência",
        pressure="baixa",
        audience="Time 7"
    )
    kag_address = saya_kagetsu["addressing_plan_v33"]
    assert kag_address["default_form"] == "Kagetsu-sensei", kag_address
    assert kag_address["honorific_strength"] == "strong_default", kag_address

    kazuma_address = sk["addressing_plan_v33"]
    assert kazuma_address["default_form"] == "Kazuma-kun", kazuma_address
    assert kazuma_address["honorific_strength"] == "strong_relational_default", kazuma_address

    kaz_address = ka["addressing_plan_v22"]
    assert "mechanically" in kaz_address["honorific_policy"] or "default" in kaz_address["honorific_policy"]

    for actor, teacher, expected_strength in [
        ("Hana Yamanaka", "Akihiko Sarutobi", "strong_default"),
        ("Natsuki Hyūga", "Shōma Sarutobi", "strong_default"),
        ("Kaede Uchiha", "Sayuri Hyūga", "contextual_default"),
        ("Shin Uchiha", "Shigure Namikado", "contextual_default"),
    ]:
        pkt = persona_turn(actor, teacher, stimulus="instrução do sensei", situation="treino seguro", pressure="baixa")
        plan = pkt["addressing_plan_v33"]
        assert "sensei" in " ".join(plan.get("preferred_forms", [])).casefold(), (actor, plan)
        assert plan.get("honorific_strength") == expected_strength, (actor, plan)

    hana_peer = persona_turn("Hana Yamanaka", "Daichi Akimichi", stimulus="conversa de equipe", situation="pausa segura", pressure="baixa")
    assert not any("-kun" in x or "-san" in x for x in hana_peer["addressing_plan_v33"].get("preferred_forms", [])), hana_peer["addressing_plan_v33"]

    saya_to_iruka_formality = saya_authority["formality_profile_v23"]
    saya_to_amatsu_formality = sa["formality_profile_v23"]
    assert saya_to_iruka_formality["level"] >= saya_to_amatsu_formality["level"], (
        saya_to_iruka_formality, saya_to_amatsu_formality
    )
    assert saya_authority["universal_language_v23"]["version"] == "v23"
    assert saya_authority["reference_voice_family_v23"]["family"] == "socially_adaptive_youthful"

    iruka_turn = persona_turn(
        "Iruka Umino", "Amatsu Uchiha",
        stimulus="Amatsu responde casualmente ao professor",
        situation="conversa segura após o exame",
        pressure="baixa"
    )
    assert iruka_turn["reference_voice_family_v23"]["family"] == "expressive_teacher"
    assert iruka_turn["voice_contract_v23"]["universal_naruto_register"]["language"] == "PT-BR Naruto Clássico"

    yoshiro_turn = persona_turn(
        "Yoshiro Sabaku", "Amatsu Uchiha",
        stimulus="Yoshiro reencontra Amatsu após o confronto",
        situation="torre do Exame Chūnin; tensão controlada",
        pressure="média"
    )
    assert yoshiro_turn["status"] == "ok", yoshiro_turn
    assert yoshiro_turn["reference_voice_family_v23"]["family"] == "sparse_unsettling"

    yoru_turn = persona_turn(
        "Yoru", "Mio Inuzuka",
        stimulus="Mio para e Yoru percebe um cheiro",
        situation="corredor seguro",
        pressure="baixa"
    )
    assert yoru_turn["sayability_gate_v22"]["verdict"] == "must_not_speak", yoru_turn

    shin_trigger = persona_acting_packet(
        "Shin Uchiha", "Amatsu Uchiha",
        stimulus="a vergonha do clã vai mostrar pro filhinho prodígio como se faz",
        prior_exchange="Shin perdeu para Ayame e Amatsu chamou a derrota de patética.",
        situation="galeria das preliminares",
        pressure="média"
    )
    assert shin_trigger["escalation"]["level"] == 4, shin_trigger
    assert shin_trigger["relationship_specific"] is True, shin_trigger

    bad_shin = persona_dialogue_audit_v25(
        "Shin Uchiha", "Amatsu Uchiha",
        candidate_dialogue="Fala o que quiser. Só não usa meu pai pra tentar parecer maior do que você é.",
        stimulus="filhinho prodígio de um dos grandes ninjas do clã",
        prior_exchange="Amatsu devolve a acusação de vergonha do clã.",
        situation="galeria das preliminares",
        pressure="média"
    )
    assert bad_shin["pass"] is False, bad_shin

    kaede_bible = persona_bible("Kaede Uchiha")
    assert kaede_bible["bible"]["relationship_overrides"]["Amatsu Uchiha"]["baseline"], kaede_bible

    historical_turn = persona_turn(
        "Arashi Senju — Primeiro Hokage (histórico)", "Shūsei Uchiha — cofundador (histórico)",
        stimulus="nome citado numa conversa atual",
        situation="presente, sem flashback",
        pressure="baixa"
    )
    assert historical_turn["sayability_gate_v22"]["verdict"] == "must_not_speak", historical_turn

    print(json.dumps({
        "healthcheck": h,
        "saya_to_amatsu": sa,
        "saya_to_kazuma": sk,
        "kazuma_to_amatsu": ka,
        "kagetsu_to_saya": kag,
        "amatsu_block": blocked,
        "audit_example": audit,
        "v22_sayability": v22_sayability,
        "saya_authority": saya_authority,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

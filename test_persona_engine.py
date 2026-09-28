import json
from persona_api import persona_healthcheck, persona_relation, persona_turn, persona_check, persona_sayability


def main():
    h = persona_healthcheck()
    assert h["characters"] == 80, h
    assert h["continuity_id"] == "classico_floresta_da_morte"

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
    assert audit["pass"] is True
    assert audit["warnings"], audit

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

    kaz_address = ka["addressing_plan_v22"]
    assert "mechanically" in kaz_address["honorific_policy"] or "default" in kaz_address["honorific_policy"]

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

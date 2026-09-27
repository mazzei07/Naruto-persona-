import json
from persona_api import persona_healthcheck, persona_relation, persona_turn, persona_check


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

    print(json.dumps({
        "healthcheck": h,
        "saya_to_amatsu": sa,
        "saya_to_kazuma": sk,
        "kazuma_to_amatsu": ka,
        "kagetsu_to_saya": kag,
        "amatsu_block": blocked,
        "audit_example": audit,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

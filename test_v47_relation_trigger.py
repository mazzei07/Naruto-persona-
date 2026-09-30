from acting_bible import escalation_packet, relationship_bible

def test_kaede_uchiha_context_is_not_a_provocation():
    out = escalation_packet(
        "Kaede Uchiha",
        "Amatsu Uchiha",
        stimulus="Amatsu voltou inteiro e entrou.",
        prior_exchange="Kaede pediu que ele voltasse direito.",
        situation="Casa de Kaede Uchiha, distrito Uchiha, Konoha; namoro vigente.",
        pressure="low",
    )
    assert "clan_reputation_trigger" not in out.get("reasons", []), out
    assert "competence_status_trigger" not in out.get("reasons", []), out

def test_actual_clan_shame_can_trigger():
    out = escalation_packet(
        "Kaede Uchiha",
        "Amatsu Uchiha",
        stimulus="Você é uma vergonha para o clã.",
        situation="Confronto pessoal.",
        pressure="low",
    )
    assert "clan_reputation_trigger" in out.get("reasons", []), out

def test_live_dating_relation_is_authoritative():
    rel = relationship_bible("Kaede Uchiha", "Amatsu Uchiha")
    assert rel.get("relationship_source") == "relationship_graph_live_override", rel
    current = rel.get("relationship", {})
    assert current.get("current_status") == "dating", rel
    assert "não negar o namoro" in str(current.get("must_not", "")).lower(), rel

if __name__ == "__main__":
    test_kaede_uchiha_context_is_not_a_provocation()
    test_actual_clan_shame_can_trigger()
    test_live_dating_relation_is_authoritative()
    print("v47 relation trigger regression: ok")

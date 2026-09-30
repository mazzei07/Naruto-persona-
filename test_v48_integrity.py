import unittest
from persona_engine import _epistemic_fact_gate_v46
from acting_bible import relationship_bible


class PersonaIntegrityTests(unittest.TestCase):
    def test_negative_constraint_and_prior_exchange_are_not_positive_ledger(self):
        issues = _epistemic_fact_gate_v46('Você foi hospitalizado em Suna.',
            knowledge_constraint='Kaede não sabe: Amatsu foi hospitalizado em Suna',
            prior_exchange='Narrador: Amatsu foi hospitalizado em Suna',
            known_facts=[], candidate_facts=['Amatsu foi hospitalizado em Suna'])
        self.assertTrue(any('unverified_material_fact' in x for x in issues))

    def test_known_fact_is_accepted_and_dating_survives(self):
        self.assertEqual(_epistemic_fact_gate_v46('Você voltou.',
            known_facts=['Amatsu voltou a Konoha'],candidate_facts=['Amatsu voltou a Konoha']), [])
        self.assertEqual(relationship_bible('Kaede Uchiha','Amatsu Uchiha')['relationship']['current_status'], 'dating')


if __name__ == '__main__':
    unittest.main()

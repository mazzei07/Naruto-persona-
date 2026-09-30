import unittest,json
from persona_engine import persona_audit, character_turn_packet
from pathlib import Path

class EnvelopeTests(unittest.TestCase):
    def test_old_tool_schema_can_audit_material_claims(self):
        fact='Amatsu foi hospitalizado em Suna'
        result=persona_audit(name='Kaede Uchiha',interlocutor='Amatsu Uchiha',candidate_dialogue='Você foi hospitalizado em Suna.',situation=json.dumps({'persona_audit_v49':{'situation':'Casa de Kaede, à noite','known_facts':['Amatsu voltou de Suna'],'candidate_facts':[fact]}}))
        self.assertFalse(result['pass'])
        self.assertTrue(any('knowledge' in x.lower() or 'fato' in x.lower() or 'epistem' in x.lower() or 'unverified_material_fact' in x for x in result['violations']),result)
    def test_malformed_ledger_rejected(self):
        result=persona_audit(name='Kaede Uchiha',situation=json.dumps({'persona_audit_v49':{'known_facts':'secret'}}))
        self.assertFalse(result['pass'])
        self.assertIn('Invalid persona_audit_v49.known_facts',result['violations'])

class CastTests(unittest.TestCase):
    def test_whole_cast_compiles_without_stealing_player_or_group_identity(self):
        cast=json.loads((Path(__file__).parent/'fidelity_catalog.json').read_text())['characters']
        self.assertEqual(len(cast),101)
        for name, mapping in cast.items():
            with self.subTest(actor=name):
                result=character_turn_packet(name=name,interlocutor='Amatsu Uchiha',stimulus='Teste isolado',situation='Cena de teste sem atualização do cânone')
                expected='blocked_player_control' if name=='Amatsu Uchiha' else 'not_found' if mapping.get('entity_type') in ('group','unresolved_identity') else 'ok'
                self.assertEqual(result['status'],expected)

import unittest
from fidelity_core import catalog, classify, evidence_packet, lint, validate_turn_packet, health
from persona_api import persona_turn, persona_check, persona_profile

def example():
    return {'continuity_id':'classico_floresta_da_morte','user_action':'Como funciona o exame?',
            'scene':{'location':'torre','present':['Amatsu Uchiha','Iruka Umino'],'positions':{},'physical_state':{},'knowledge':{'Iruka Umino':['regras da prova']}},
            'actors':[{'name':'Iruka Umino','interlocutor':'Amatsu Uchiha','objective':'explicar a próxima etapa','known_facts':['regras da prova'],'reference_card_ids':['iruka_tower'],'dossier_source':'ficha vigente'}]}

class FidelityTests(unittest.TestCase):
    def test_regression_saya_crush_not_aggressive_without_event(self):
        for name in ['Saya','saya haruno','Saya Haruno']:
            with self.subTest(name=name):
                r=persona_check(name,'Kazuma','Cala a boca, idiota.',situation='conversa banal sem perigo ou provocação')
                self.assertFalse(r['pass']);self.assertEqual(r['status'],'revision_required')
    def test_high_pressure_does_not_create_filter_breaking_event(self):
        self.assertFalse(lint('Saya','Kazuma','Idiota.',situation='conversa banal',pressure='alta')['pass'])
    def test_safe_place_is_not_danger(self):
        self.assertNotIn('danger',classify('','Pausa segura na Floresta da Morte; sem perigo ou ameaça.'))
    def test_real_threat_is_still_detected(self):
        self.assertIn('danger',classify('','Sem perigo no abrigo; inimigo prepara ataque do lado de fora.'))
    def test_word_boundaries(self):
        r=lint('Iruka','Amatsu','O metal da kunai está gasto.',situation='torre, explicação do exame')
        self.assertNotIn('registro_meta_ou_moderno:meta',r['revision_requests'])
    def test_didactic_language_not_blanket_banned(self):
        r=lint('Iruka','Amatsu','Isso significa que vocês passaram porque trouxeram os dois pergaminhos.',situation='explicação na torre')
        self.assertEqual(r['violations'],[])
        self.assertNotIn('explicacao_didatica_proibida',r.get('revision_requests',[]))
        self.assertTrue(r['semantic_review_required'])
    def test_agency(self):
        self.assertEqual(persona_turn('Amatsu','Saya')['status'],'blocked_player_control')
    def test_scene_not_biography(self):
        p=evidence_packet('Kazuma','Amatsu','perigo de combate')
        self.assertTrue(p['scene_cards']);self.assertTrue(all(c['not_rp_event'] for c in p['scene_cards']))
    def test_phase_filter(self):
        p=evidence_packet('Renji','Hana','equipe em combate')
        self.assertTrue(all(c['episode_ceiling']<=catalog()['contract']['reference_episode_ceiling'] and c.get('phase')!='later_reference_only' for c in p['scene_cards']))
        self.assertIn('shikamaru_tactics',p['later_scene_ids_excluded'])
    def test_technical_reference_is_not_voice(self):
        self.assertTrue(evidence_packet('Kaito','Kaede','conversa')['voice_from_own_dossier'])
        self.assertEqual(catalog()['characters']['Kaito Shimura']['transfer_scope'],'technical_or_function_only')
    def test_original_not_overwritten_by_clan(self):
        self.assertEqual(catalog()['characters']['Emi Nara']['reference_characters'],[])
    def test_technical_inspiration_does_not_set_speech_family(self):
        for name in ['Kaito', 'Riku', 'Emi']:
            with self.subTest(name=name):
                p=persona_turn(name,'Amatsu',situation='conversa durante uma pausa')
                self.assertEqual(p['reference_voice_family_v23']['family'],'profile_driven')
    def test_later_only_not_invented_classic(self):
        p=evidence_packet('Kōmei Bakuhara','Gazan','combate')
        self.assertTrue(p['research_required']);self.assertFalse(p['scene_cards'])
    def test_arc_profile_resolves_actual_reference(self):
        self.assertIn('Zabuza',persona_profile('Gakuji')['reference']['primary_reference'])
        self.assertIn('Haku',persona_profile('Nagi')['reference']['primary_reference'])
    def test_tower_evidence_first(self):
        self.assertEqual(evidence_packet('Iruka','Amatsu','torre exame explicação')['scene_cards'][0]['id'],'iruka_tower')
    def test_no_automatic_perfect_rating(self):
        r=persona_check('Iruka','Amatsu','Vocês passaram.',situation='torre, exame')
        self.assertTrue(r['semantic_review_required']);self.assertFalse(r['certifies_character_fidelity'])
    def test_sufficient_envelope(self):
        self.assertEqual(validate_turn_packet(example())['status'],'reviewable')
    def test_unknown_source_id(self):
        p=example();p['actors'][0]['reference_card_ids']=['invented']
        self.assertEqual(validate_turn_packet(p)['status'],'needs_evidence')
    def test_wrong_actor_evidence(self):
        p=example();p['actors'][0]['reference_card_ids']=['sakura_choice']
        self.assertIn('Iruka Umino:reference_actor_mismatch:sakura_choice',validate_turn_packet(p)['issues'])
    def test_unknown_knowledge(self):
        p=example();p['actors'][0]['known_facts'].append('segredo não revelado')
        self.assertIn('Iruka Umino:knowledge_without_channel',validate_turn_packet(p)['issues'])
    def test_missing_scene_actor(self):
        p=example();p['scene']['present'].append('Saya Haruno')
        self.assertIn('missing_actor_card:Saya Haruno',validate_turn_packet(p)['issues'])
    def test_empty_scene_never_passes(self):
        self.assertEqual(validate_turn_packet({})['status'],'needs_evidence')
    def test_health_is_coverage_not_quality(self):
        r=health();self.assertTrue(r['ok']);self.assertFalse(r['full_manga_read']);self.assertFalse(r['br_dub_verified']);self.assertEqual(r['version'],'v25.0.0');self.assertTrue(r['supports_active_npcs'])
    def test_active_npcs_allow_background_presence(self):
        p=example();p['scene']['present'] += ['Saya Haruno','Kazuma Uzumaki'];p['scene']['active_npcs']=['Iruka Umino']
        self.assertEqual(validate_turn_packet(p)['status'],'reviewable')
    def test_active_npc_still_needs_card(self):
        p=example();p['scene']['present'].append('Saya Haruno');p['scene']['active_npcs']=['Iruka Umino','Saya Haruno']
        self.assertIn('missing_actor_card:Saya Haruno',validate_turn_packet(p)['issues'])
    def test_group_cannot_be_active_persona(self):
        p=example();p['scene']['present'].append('Equipe de Amegakure');p['scene']['active_npcs']=['Iruka Umino','Equipe de Amegakure']
        self.assertIn('non_persona_entity_cannot_be_active:Equipe de Amegakure',validate_turn_packet(p)['issues'])
    def test_preliminary_phase_reference_ceiling(self):
        r=health();self.assertEqual(r['reference_episode_ceiling'],catalog()['contract']['reference_episode_ceiling']);self.assertEqual(r['acting_bible_version'],'v25.0.0')
        p=evidence_packet('Shin','Amatsu','preliminares rivalidade provocação')
        self.assertTrue(any(x['id']=='kiba_naruto_public_rivalry' for x in p['scene_cards']),p)
    def test_newly_researched_scene_is_accepted(self):
        p=example()
        p['external_reference_cards']=[{'id':'external:iruka-check','references':['Iruka'],'episode_ceiling':37,'source_url':'https://naruto-official.com/en/news/01_1788','locator':'capítulo 64','observed_summary':'Iruka orienta os candidatos na torre.','acting_inference':'Explicar com objetivo concreto.','checked_at':'2026-09-28','dialogue_evidence':'official_editorial_or_synopsis'}]
        p['actors'][0]['reference_card_ids']=['external:iruka-check']
        self.assertEqual(validate_turn_packet(p)['status'],'reviewable')
        p['external_reference_cards'][0]['episode_ceiling']=100
        self.assertEqual(validate_turn_packet(p)['status'],'needs_evidence')
    def test_unapproved_external_source_is_not_certified(self):
        p=example();p['external_reference_cards']=[{'id':'external:fake','source_url':'https://example.com/fanfic'}]
        self.assertIn('external:fake:primary_source_required',validate_turn_packet(p)['issues'])
    def test_malformed_state_is_reported_not_crashed(self):
        for value in [None,[],42,'segredo']:
            p=example();p['scene']['knowledge']['Iruka Umino']=value
            self.assertEqual(validate_turn_packet(p)['status'],'needs_evidence')
    def test_empty_dossier_is_not_evidence(self):
        p=example();p['actors'][0]['dossier_source']=''
        self.assertEqual(validate_turn_packet(p)['status'],'needs_evidence')


    def test_v41_proximity_is_provenance_limited(self):
        from fidelity_core import source_proximate_match_v41
        from acting_bible import compile_acting_packet, health as acting_health
        p=source_proximate_match_v41('Kaede Uchiha','Amatsu Uchiha','ataque e perigo','proteger companheiro')
        self.assertEqual(p['status'],'reference_available')
        self.assertTrue(p['closest']['card_id'])
        self.assertEqual(p['match_quality'],'source_excerpt')
        self.assertTrue(p['dialogue_mechanics_verified'])
        acting=compile_acting_packet('Kaede Uchiha','Amatsu Uchiha','proteger companheiro','ataque e perigo')
        self.assertEqual(acting['source_proximate_v41']['closest']['card_id'],p['closest']['card_id'])
        self.assertTrue(acting_health()['supports_source_proximate_dialogue_v41'])


    def test_v41_external_excerpt_is_not_preverified(self):
        from fidelity_core import source_proximate_match_v41
        card={'id':'external:kaede','references':['Sasuke'],'episode_ceiling':37,
              'tags':['danger','protect'],'locator':'capítulo 50',
              'dialogue_evidence':'official_excerpt','source_url':'https://naruto-official.com/en/news/example',
              'checked_at':'2026-09-29','provenance':'caller_supplied_research_requires_semantic_review'}
        p=source_proximate_match_v41('Kaede Uchiha','Amatsu Uchiha','ataque e perigo','proteger companheiro',[card])
        self.assertEqual(p['closest']['card_id'],'external:kaede')
        self.assertEqual(p['closest']['source_url'],card['source_url'])
        self.assertFalse(p['dialogue_mechanics_verified'])
        weak=source_proximate_match_v41('Kaede Uchiha','Amatsu Uchiha','conversa sem assunto específico','',[card])
        self.assertEqual(weak['match_quality'],'weak_phase_analogue')
        self.assertEqual(weak['status'],'needs_evidence')


    def test_v41_turn_validation_reads_external_card(self):
        p=example()
        p['external_reference_cards']=[{'id':'external:iruka-v41','references':['Iruka'],
            'episode_ceiling':37,'source_url':'https://naruto-official.com/en/news/01_1788',
            'locator':'capítulo 64','observed_summary':'Iruka orienta candidatos.',
            'acting_inference':'Instrução funcional.','checked_at':'2026-09-29',
            'dialogue_evidence':'official_excerpt','tags':['exam','tower','instruction']}]
        p['actors'][0]['reference_card_ids']=['external:iruka-v41']
        result=validate_turn_packet(p)
        self.assertEqual(result['status'],'reviewable')
        match=result['source_proximate_v41']['Iruka Umino']
        self.assertEqual(match['closest']['card_id'],'external:iruka-v41')
        self.assertFalse(match['dialogue_mechanics_verified'])

if __name__=='__main__':unittest.main()


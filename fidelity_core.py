"""Small, inspectable evidence layer. No network, LLM or canonical state writes.

This is a retrieval/linting gate, not a claim to understand all prose or prove
acting quality. Source summaries and editorial inferences remain separate.
"""
from __future__ import annotations
import copy
import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

VERSION = 'v24.1.0'
CONTINUITY = 'classico_floresta_da_morte'
ROOT = Path(__file__).resolve().parent

def norm(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(value or '').casefold()) if not unicodedata.combining(c))

@lru_cache(maxsize=1)
def catalog():
    return json.loads((ROOT/'fidelity_catalog.json').read_text(encoding='utf8'))

def resolve(name):
    query=norm(name).strip()
    if not query:return None
    names=catalog()['characters']
    exact=[n for n in names if norm(n)==query]
    if len(exact)==1:return exact[0]
    first=[n for n in names if norm(n.split()[0])==query]
    return first[0] if len(first)==1 else None

def context_text(text):
    """Avoid negation/place-name false positives. Not a semantic parser."""
    text=norm(text)
    text=re.sub(r'\bfloresta da morte\b','floresta',text)
    terms=r'(?:perigo|ameaca|ataque|combate|emboscada|provocacao|piada|risco|ferimento|urgencia|inimigo|humilhacao)'
    neg=r'\b(?:sem|nenhum[ao]?|ausencia de|nao ha|nao existe)\s+(?:qualquer\s+)?'+terms+r'(?:\s+(?:real|imediat[ao]|atual|algum[ao]?))?(?:\s+(?:ou|nem|e)\s+'+terms+r')*'
    return re.sub(neg,' ',text)

TAG_WORDS={
 'danger':['perigo','ameaca','ataque','emboscada','inimigo','explosao','armadilha','letal','urgente','combate'],
 'comedy':['piada','provocacao','provoca','brinca','comico','pegadinha'],
 'authority':['hokage','sensei','superior','comandante','instrutor','professor','examinador','examinadora'],
 'romance':['admira','elogio','aproximacao','ciume','vergonha','romance'],
 'instruction':['treino','ensina','instrucao','corrige','exercicio','explica','regras'],
 'social':['conversa','cotidiano','descanso','refeicao','fome','comida','social','pausa'],
 'tower':['torre'], 'exam':['exame','prova','pergaminho'],
 'fatigue':['exausto','cansado','cansada','exausta','esgotado'],
 'injury':['ferido','ferida','sangra','incapacitado'],
 'protect':['protege','proteger','protecao','defender','guarda'],
 'fear':['medo','pavor','assustado','assustada'],
 'team':['equipe','time','companheiro'],
 'deception':['disfarce','impostor','ilusao','engano'],
 'care':['preocupacao','cuida','cuidar','afeto'],
 'reprimand':['travessura','repreende','bronca'],
 'disagreement':['discorda','discute','contesta'],
 'tracking':['faro','cheiro','rastreio'], 'observe':['observa','espreita'],
 'weapons':['arma','armas','kunai','shuriken'],
}
def classify(stimulus='',situation=''):
    text=context_text(f'{stimulus}. {situation}')
    tags=[tag for tag,words in TAG_WORDS.items() if any(re.search(r'(?<!\w)'+re.escape(w)+r'(?!\w)',text) for w in words)]
    return tags or ['neutral']

def evidence_packet(name,interlocutor='',situation='',stimulus=''):
    actor=resolve(name)
    if not actor:return {'version':VERSION,'status':'needs_evidence','reason':'Personagem ausente ou ambíguo. Consultar Canoney; não fabricar equivalente.','research_required':True}
    mapping=copy.deepcopy(catalog()['characters'][actor])
    tags=set(classify(stimulus,situation))
    candidates=[];out_of_phase=[]
    for card in catalog()['scene_cards']:
        if not set(mapping['reference_characters'])&set(card['references']):continue
        if card['episode_ceiling']>catalog()['contract']['reference_episode_ceiling']:
            out_of_phase.append(card['id']);continue
        score=len(tags&set(card['tags']))
        if score:candidates.append((score,card))
    candidates.sort(key=lambda p:(-p[0],p[1]['id']))
    selected=[copy.deepcopy(p[1]) for p in candidates[:3]]
    own_voice=mapping['transfer_scope'] in ('technical_or_function_only','original')
    missing=[]
    if mapping['mapping_status']=='unresolved_or_original' and not mapping.get('baseline'):missing.append('matriz de voz própria não fechada')
    if mapping['reference_characters'] and not selected:missing.append('cena equivalente da fase atual não encontrada no catálogo')
    if not situation and not stimulus:missing.append('situação/estímulo não fornecidos')
    if mapping['later_reference_characters']:missing.append('referência posterior exige recorte explícito; não existe versão juvenil presumida')
    query=f"Naruto clássico {', '.join(mapping['reference_characters']) or 'referência original não documentada'} interlocutor {interlocutor or 'a definir'} situação {situation or stimulus or 'a definir'} Exame Chunin Floresta da Morte diálogo ação relação capítulo episódio fonte oficial"
    return {
        'version':VERSION,'status':'needs_evidence' if missing else 'reference_available',
        'actor':actor,'mapping':mapping,'scene_cards':selected,
        'source_links':{sid:catalog()['sources'][sid] for sid in sorted({s for c in selected for s in c['source_ids']})},
        'later_scene_ids_excluded':out_of_phase,'missing_evidence':missing,
        'research_required':bool(missing),'suggested_query':query,
        'voice_from_own_dossier':own_voice,
        'entity_type':mapping.get('entity_type','individual'),
        'reference_check_required_every_turn':True,
        'semantic_review_required':True,'br_dub_verified':False,
        'rule':'Consultar estas evidências antes de cada geração. Cena de referência não é acontecimento do RP; sinopse não prova redação, prosódia nem dublagem. Se faltar referência material, pesquisar antes de fechar a atuação.',
    }

def lint(name,interlocutor='',dialogue='',action='',situation='',pressure='normal'):
    actor=resolve(name);listener=resolve(interlocutor) or interlocutor
    violations=[];revisions=[];notes=[]
    text=norm(f'{dialogue} {action}')
    if actor=='Amatsu Uchiha':violations.append('player_agency: Amatsu não é ator gerável pela IA')
    for term in ['cringe','skill issue','red flag','gaslighting','npc','buff','nerf','build','meta','gatilho emocional']:
        if re.search(r'(?<!\w)'+re.escape(term)+r'(?!\w)',text):revisions.append('registro_meta_ou_moderno:'+term)
    if not actor:violations.append('personagem_ausente_ou_ambiguo')
    tags=classify('',situation)
    aggressive=bool(re.search(r'\b(?:idiota|burro|imbecil)\b|cala a boca',norm(dialogue)))
    if actor=='Saya Haruno' and listener=='Kazuma Uzumaki' and aggressive:
        if re.search(r'kazuma\s+(?:humilha|ameaca|ataca|agride)',context_text(situation)):
            notes.append('Quebra de filtro exige revisão semântica do evento e alvo, não somente pressão alta.')
        else:revisions.append('saya_kazuma: agressividade casual contradiz a relação documentada; falta causa concreta de ruptura')
    if actor=='Saya Haruno' and 'danger' in tags and re.search(r'\b(?:soco|tapa|bate|bater|persegue)\b',norm(action)) and 'comedy' in tags:
        revisions.append('comedia_fisica_em_emergencia: não comprometer a tarefa séria')
    if actor in ('Kaito Shimura','Riku Fūma') and 'igual a temari' in text:
        revisions.append('inspiracao_tecnica_nao_autoriza_copia_de_personalidade')
    if re.search(r'\b(?:destino|escuridao|verdadeira forca|preco do poder)\b',norm(dialogue)):
        notes.append('Verificar se abstração atende ao objetivo real; palavra isolada não é prova de clichê.')
    if len(dialogue.split())>65 and ('danger' in tags or norm(pressure) in ('alta','high','letal')):
        revisions.append('fala_longa_sob_pressao: verificar tempo, respiração e utilidade')
    packet=evidence_packet(name,interlocutor,situation)
    status='blocked' if violations else 'revision_required' if revisions else 'needs_evidence' if packet['research_required'] else 'reviewable'
    return {'status':status,'pass':status=='reviewable','violations':violations,'revision_requests':revisions,'notes':notes,'semantic_review_required':True,'certifies_character_fidelity':False,'evidence':packet}

def reference_index(packet):
    """Accept newly researched scene cards without pretending to fetch/verify their contents."""
    cards={c['id']:c for c in catalog()['scene_cards']}
    issues=[]
    extra=packet.get('external_reference_cards',[])
    if not isinstance(extra,list):return cards,['invalid_external_reference_cards']
    for c in extra:
        if not isinstance(c,dict):issues.append('invalid_external_reference_card');continue
        cid=c.get('id')
        if not isinstance(cid,str) or not cid.startswith('external:') or cid in cards:
            issues.append('invalid_or_duplicate_external_id');continue
        errors=[]
        for key in ('locator','observed_summary','acting_inference','checked_at','source_url'):
            if not isinstance(c.get(key),str) or not c[key].strip():errors.append('missing_'+key)
        try:
            url=urlparse(c.get('source_url',''))
            if url.scheme!='https' or url.hostname not in ('naruto-official.com','www.viz.com','viz.com','books.shueisha.co.jp','www.shueisha.co.jp','shueisha.co.jp'):
                errors.append('primary_source_required')
        except (ValueError,TypeError):errors.append('invalid_source_url')
        if not isinstance(c.get('references'),list) or not c['references'] or not all(isinstance(r,str) and r for r in c['references']):errors.append('invalid_references')
        ceiling=c.get('episode_ceiling')
        if type(ceiling) is not int or not 1<=ceiling<=catalog()['contract']['reference_episode_ceiling']:errors.append('wrong_reference_phase')
        if c.get('dialogue_evidence') not in ('official_editorial_or_synopsis','official_excerpt','licensed_text_or_audio'):errors.append('missing_access_kind')
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',str(c.get('checked_at',''))):errors.append('invalid_checked_at')
        if errors:issues.extend(cid+':'+e for e in errors)
        else:cards[cid]={**c,'provenance':'caller_supplied_research_requires_semantic_review','not_rp_event':True}
    return cards,issues

def validate_turn_packet(packet):
    """Validate a compact, caller-supplied fact/evidence envelope, not hidden reasoning."""
    if not isinstance(packet,dict):return {'status':'needs_evidence','issues':['turn_packet must be an object']}
    cards,issues=reference_index(packet)
    if packet.get('continuity_id')!=CONTINUITY:issues.append('wrong_or_missing_continuity')
    if not isinstance(packet.get('user_action'),str) or not packet['user_action'].strip():issues.append('missing_exact_user_action')
    scene=packet.get('scene')
    if not isinstance(scene,dict):scene={};issues.append('missing_scene')
    for key in ['location','present','positions','physical_state','knowledge']:
        if key not in scene:issues.append('missing_scene:'+key)
    for key in ['positions','physical_state','knowledge']:
        if not isinstance(scene.get(key),dict):issues.append('invalid_scene:'+key)
    if not isinstance(scene.get('location'),str) or not scene['location'].strip():issues.append('invalid_scene:location')
    if not isinstance(scene.get('present'),list) or not scene.get('present'):issues.append('missing_present_actors')
    actor_cards=packet.get('actors',[])
    if not isinstance(actor_cards,list):actor_cards=[];issues.append('invalid_actors')
    covered=set()
    for a in actor_cards:
        if not isinstance(a,dict):issues.append('invalid_actor');continue
        name=resolve(a.get('name'));covered.add(name)
        if not name:issues.append('unknown_actor:'+str(a.get('name')));continue
        if name=='Amatsu Uchiha':continue
        for key in ['interlocutor','objective','known_facts','reference_card_ids','dossier_source']:
            if key not in a:issues.append(name+':missing_'+key)
        for key in ['interlocutor','objective','dossier_source']:
            if not isinstance(a.get(key),str) or not a[key].strip():issues.append(name+':empty_'+key)
        ids=a.get('reference_card_ids',[])
        if not isinstance(ids,list):issues.append(name+':invalid_reference_ids');continue
        m=catalog()['characters'][name]
        own=m['transfer_scope'] in ('original','technical_or_function_only')
        if not ids and not (own and a.get('dossier_source')):issues.append(name+':missing_reference_evidence')
        for cid in ids:
            card=cards.get(cid) if isinstance(cid,str) else None
            if not card:issues.append(name+':unknown_reference:'+str(cid));continue
            if card['episode_ceiling']>37:issues.append(name+':future_reference:'+cid)
            if not set(card['references'])&set(m['reference_characters']):issues.append(name+':reference_actor_mismatch:'+cid)
        declared=scene.get('knowledge',{}).get(name,[]) if isinstance(scene.get('knowledge'),dict) else []
        if not isinstance(declared,list):issues.append(name+':invalid_scene_knowledge')
        elif not isinstance(a.get('known_facts',[]),list):issues.append(name+':invalid_known_facts')
        elif any(f not in declared for f in a.get('known_facts',[])):issues.append(name+':knowledge_without_channel')
    present = scene.get('present',[]) if isinstance(scene.get('present'),list) else []
    active_supplied = 'active_npcs' in scene
    active = scene.get('active_npcs',[]) if active_supplied else None
    if active_supplied and not isinstance(active,list):
        issues.append('invalid_scene:active_npcs'); active=[]
    for name in present:
        resolved=resolve(name)
        if not resolved:
            issues.append('unknown_present_actor:'+str(name))
    if active_supplied:
        required=[]
        for name in active:
            resolved=resolve(name)
            if not resolved:
                issues.append('unknown_active_actor:'+str(name)); continue
            if resolved not in [resolve(x) for x in present]:
                issues.append('active_actor_not_present:'+resolved); continue
            kind=catalog()['characters'][resolved].get('entity_type','individual')
            if kind in ('group','unresolved_identity'):
                issues.append('non_persona_entity_cannot_be_active:'+resolved); continue
            if resolved!='Amatsu Uchiha':
                required.append(resolved)
        for resolved in required:
            if resolved not in covered:issues.append('missing_actor_card:'+resolved)
    else:
        for name in present:
            resolved=resolve(name)
            if not resolved or resolved=='Amatsu Uchiha':continue
            kind=catalog()['characters'][resolved].get('entity_type','individual')
            if kind in ('group','unresolved_identity'):continue
            if resolved not in covered:issues.append('missing_actor_card:'+resolved)
    return {'status':'needs_evidence' if issues else 'reviewable','issues':issues,'semantic_review_required':True,'active_actor_policy':'active_npcs' if active_supplied else 'legacy_all_present'}

def health():
    d=catalog();ids={c['id'] for c in d['scene_cards']}
    bad=[s for c in d['scene_cards'] for s in c['source_ids'] if s not in d['sources']]
    kinds={}
    for m in d['characters'].values():
        kind=m.get('entity_type','individual');kinds[kind]=kinds.get(kind,0)+1
    return {'version':VERSION,'ok':not bad and len(ids)==len(d['scene_cards']),'characters_mapped':len(d['characters']),'entity_types':kinds,'scene_cards':len(ids),'source_records':len(d['sources']),'coverage':'selected_evidence_not_complete_corpus','br_dub_verified':False,'full_manga_read':False,'network_access':False,'semantic_review_required':True,'supports_active_npcs':True}

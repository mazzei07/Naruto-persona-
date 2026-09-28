# Integração v25 — Atuação relacional e diálogo com continuidade

## Objetivo

A v25 acrescenta uma Bíblia de Atuação por personagem ao pipeline anterior de evidência. O sistema não deve mais gerar uma fala a partir de "personalidade geral + referência Naruto". A unidade mínima é:

```
estado live
→ prior_exchange
→ ator + interlocutor
→ histórico direcional
→ gatilho pessoal
→ conhecimento/percepção
→ corpo/pressão/público
→ referência oficial da fase
→ objetivo
→ fala/ação/silêncio
→ bend de voz
→ auditoria anti-genérica
→ revisão semântica final
```

## Arquivos compartilhados

- `character_acting_bibles.json` — 97 entidades com dossier, voz, identidade, limites, referências, escalada e overrides relacionais.
- `character_relationship_graph.json` — grafo direcional de equipe, professor/aluno, clã e relações documentadas, sem inferir intimidade.
- `fidelity_catalog.json` — evidência oficial e scene cards; teto atual de referência: episódio 51, fim das preliminares.
- `CHARACTER_ACTING_BIBLES_V25.md` — leitura humana do contrato.

## Precedência de atuação

1. correção explícita mais recente do usuário;
2. ação/fala exata do jogador;
3. estado live + prior_exchange;
4. override relacional da Bíblia v25;
5. gatilho/escalada específica;
6. conhecimento, corpo, hierarquia e público;
7. dossier vigente;
8. referência oficial da fase correta;
9. família de voz genérica.

## Regra de continuidade conversacional

Uma discussão não reinicia a cada turno. O `prior_exchange` carrega:
- temperatura emocional;
- tópico ainda aberto;
- última provocação;
- vergonha pública;
- ameaça;
- aproximação/afeto;
- mudança de posição;
- qualquer quebra de filtro que ainda não teve tempo de esfriar.

Se `prior_exchange` não for enviado por um cliente antigo, o runtime ainda usa histórico relacional e o estímulo atual, mas clientes v25 devem enviá-lo em conflito contínuo.

## Escalada

Níveis comuns:
- 0 baseline;
- 1 irritado;
- 2 provocado pessoalmente;
- 3 gatilho de identidade;
- 4 breaking point.

O nível não dita a mesma reação para todos. Cada personagem tem `actor_rule` e, quando necessário, `trigger_rules` específicos.

Exemplo vigente:
- Shin → Amatsu + "vergonha do clã" = pelo menos L3;
- Shin → Amatsu + Daigo/pai/"filhinho prodígio" = L4;
- Kaede → Amatsu sob provocação clânica = escalada fria: menos calor, menos palavras, mais precisão; não copiar explosividade de Shin.

## Anti-genérico

Antes da saída:
- verificar se a decisão nasceu da relação atual;
- verificar se o corpo e a fala vêm do mesmo impulso;
- impedir comentário de plateia sem objetivo;
- impedir fala adulta/terapêutica em criança;
- impedir explicação do próprio estado psicológico;
- executar swap test: se três NPCs poderiam dizer/fazer a mesma coisa sem alteração, reescrever quando houver material específico.

## Interface Canoney / Reboot Engine

Ferramentas v25:
- `character_acting_bible(name)`
- `character_relationship_bible(name, interlocutor)`
- `character_acting_packet(... prior_exchange ...)`
- `character_dialogue_audit(...)`
- `acting_bible_healthcheck()`

`character_get` inclui a Bíblia.
`character_scene_packet` inclui `acting_v25`.

## Interface Persona

Ferramentas v25:
- `persona_bible`
- `persona_relationship_bible`
- `persona_acting_packet`
- `persona_dialogue_audit_v25`
- `persona_acting_health`

`persona_turn` e `persona_sayability` aceitam:
- `prior_exchange`
- `relationship_state`

`persona_check` aceita:
- `stimulus`
- `prior_exchange`

## Interface Gemini

Ferramentas v25:
- `gemini_character_bible`
- `gemini_acting_packet`
- `gemini_acting_health`
- `gemini_preflight`
- `gemini_rp_draft`

O preflight anexa `acting_v25` automaticamente a cada actor card. O reviewer deve reprovar:
- gatilho pessoal ignorado;
- relação reiniciada;
- linha genérica/intercambiável;
- maturidade futura;
- biografia/poder importado da referência;
- agência de Amatsu violada.

## Packet recomendado

```json
{
  "continuity_id": "classico_floresta_da_morte",
  "user_action": "<ação exata>",
  "scene": {
    "location": "<local>",
    "present": ["<nomes>"],
    "active_npcs": ["<NPCs que terão decisão gerada>"],
    "prior_exchange": "<troca anterior relevante>",
    "positions": {},
    "physical_state": {},
    "knowledge": {}
  },
  "actors": [
    {
      "name": "<NPC>",
      "interlocutor": "<alvo>",
      "objective": "<objetivo concreto>",
      "known_facts": [],
      "prior_exchange": "<opcional por ator>",
      "dossier_source": "<fonte vigente>",
      "reference_card_ids": ["<cards v25>"]
    }
  ]
}
```

## Amatsu

Amatsu continua integralmente controlado pelo usuário. Nenhuma Bíblia, referência ou reviewer pode autorizar:
- fala;
- pensamento;
- emoção;
- intenção;
- olhar voluntário;
- gesto;
- movimento;
- ataque/defesa;
- técnica/tática
não declarados pelo usuário.

## Quota Gemini

`rate_limited` e `provider_error` são estados operacionais, não aprovação semântica. O ChatGPT pode continuar com Canoney + Reboot Engine + Persona + documentos/referências e fazer a arbitragem final sem fingir que o Gemini respondeu.

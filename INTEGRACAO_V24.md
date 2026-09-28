# Integração v24.1 — evidência antes da atuação

A fase ativa continua `classico_floresta_da_morte`. Esta atualização trata da interpretação; não avança a história, não altera fichas de combate e não canoniza exemplos.

## Fluxo de cada turno

1. Obter o estado live validado e as fichas/relações vigentes no Canoney. Não substituir o estado atual por um trecho antigo de memória.
2. Consultar `persona_turn` / `character_scene_packet` para cada NPC relevante, com interlocutor, estímulo e situação concretos. Ler `evidence_v24` / `research_packet`: referência, escopo, cenas e lacunas.
3. Conferir a fase e o objetivo da cena. A inspiração de arma, técnica ou função não fornece automaticamente personalidade. Ficha própria e correções do usuário prevalecem.
4. Se faltar evidência material, pesquisar e abrir fonte primária antes de fechar a atuação. Registrar o que a página realmente mostrou. Sinopse não comprova diálogo exato, prosódia ou dublagem brasileira. Não afirmar que foi lida uma obra inteira a partir do catálogo editorial.
5. Montar `turn_packet` com a ação exata do jogador, estado, conhecimento por personagem e referências selecionadas. Enviar ao Gemini; schemas antigos aceitam o pacote como JSON em `character_references`.
6. Gemini gera e faz uma chamada separada de revisão. Havendo erro, reescreve uma vez e revisa novamente: duas chamadas normalmente, no máximo quatro. `GEMINI_REVIEW_MODEL` permite configurar outro modelo compatível; por padrão o mesmo modelo revisa em chamada separada. Isso não garante independência nem perfeição.
7. Canoney revisa o beat e compara o pacote ao estado. O narrador final ainda verifica agência, repertório, tempo, alvo, relação, voz e consequências antes de exibir. Rascunho não grava cânone.

## Pacote mínimo

Exemplo de formato, **não é evento ou estado atual do RP**. Substituir todos os dados pela cena vigente.

```json
{
  "continuity_id": "classico_floresta_da_morte",
  "user_action": "Como funciona o exame?",
  "scene": {
    "location": "torre",
    "present": ["Amatsu Uchiha", "Iruka Umino", "Saya Haruno", "Kazuma Uzumaki"],
    "active_npcs": ["Iruka Umino"],
    "positions": {},
    "physical_state": {},
    "knowledge": {"Iruka Umino": ["regras da prova"]}
  },
  "actors": [{
    "name": "Iruka Umino",
    "interlocutor": "Amatsu Uchiha",
    "objective": "explicar a próxima etapa",
    "known_facts": ["regras da prova"],
    "dossier_source": "ficha vigente obtida em character_get",
    "reference_card_ids": ["iruka_tower"]
  }]
}
```

`user_action` precisa coincidir exatamente com `action` no Gemini. Em v24.1, `present` guarda quem está fisicamente na cena e `active_npcs` guarda apenas quem terá decisão/fala/ação/reação material gerada neste beat. Só `active_npcs` exige actor card. Se `active_npcs` for omitido, permanece o comportamento legado de exigir card de todo indivíduo presente. Não escrever ficha de atuação para Amatsu. `known_facts` é um subconjunto do conhecimento documentado no estado. Campos vazios de posição/corpo só servem se o estado vigente também estiver vazio: nunca apagar dados para passar no gate.

No Canoney, `proposed.turn_packet` recebe o mesmo pacote; `proposed.dialogue` usa objetos `{actor, interlocutor, text}`. O estado separado mantém os demais campos mecânicos exigidos, como `scrolls`.

## Novas referências sem editar o catálogo

`turn_packet.external_reference_cards` aceita cartões adicionais pesquisados pelo narrador principal. Cada cartão tem:

- `id` iniciado por `external:` e citado em `reference_card_ids`;
- `references`: nomes oficiais já documentados no mapeamento do ator;
- `source_url`: URL HTTPS oficial Naruto, VIZ ou Shueisha;
- `locator`: capítulo/episódio/página identificados;
- `episode_ceiling`: inteiro de 1 a 37 para este recorte;
- `observed_summary`: descrição breve do que foi efetivamente consultado;
- `acting_inference`: aplicação proposta, separada do fato;
- `checked_at`: data ISO da consulta;
- `dialogue_evidence`: `official_editorial_or_synopsis`, `official_excerpt` ou `licensed_text_or_audio`, conforme o acesso real.

O código valida formato, fonte declarada, ator e fase. **Não acessa a URL nem prova que a fonte foi lida**: essa conferência pertence ao narrador que pesquisou. Sem referência adequada, retornar a lacuna e pesquisar; não inventar cartão. Referências posteriores ficam documentadas, mas excluídas da calibração automática desta fase. Para usar uma obra posterior como eixo específico de um OC adulto, primeiro documentar o recorte aprovado, sem importar maturidade futura dos genins.

## Estados de saída

| Estado | Significado |
|---|---|
| `reference_available` / `reviewable` | Evidência estrutural disponível; ainda exige avaliação semântica. |
| `reviewable_draft` | Rascunho passou pelo revisor de modelo; ainda não é cânone. |
| `needs_evidence` | Faltam estado, ficha, canal de conhecimento ou fonte da fase. Pesquisar/recuperar e reenviar. |
| `revision_required` | Há problemas de voz/atuação; corrigir antes de mostrar. |
| `review_failed` | Revisor retornou saída inválida; rascunho retido. |
| `blocked` | Contradição de agência, estado ou outra regra objetiva. |
| `rate_limited` | Gemini foi limitado pelo provedor; pacote continua válido e o ChatGPT pode prosseguir com Canoney + Persona sem inventar evidência. |
| `provider_error` | Falha operacional do provedor; não é aprovação nem reprovação semântica. |

## Cobertura e limites

O catálogo é uma seleção auditável, não a obra completa. `REFERENCIAS_V24.md` registra mapas, fontes e limitações; `fidelity_catalog.json` separa observação de inferência. Databooks/novels encontrados só em catálogo são referências bibliográficas, não evidência de falas lidas. Nenhum teste automatizado certifica atuação perfeita nem o timbre da dublagem.

## Testes

Python: `python3 -m unittest -v test_fidelity_v24.py`.
Gemini: `npm test` (modelos simulados, sem cobrança de API).
Os casos cobrem relação Saya→Kazuma, negação de perigo, limites de palavras, fase, agência, fontes incompatíveis, conhecimento, reparo e retenção de saída reprovada. Os testes não medem qualidade estética universal.


## Entidades e atores

O catálogo v24.1 distingue `individual`, `ninken`, `historical`, `group` e `unresolved_identity`.
- `ninken`: pode agir/reagir, mas não recebe fala humana.
- `historical`: não atua no presente sem flashback/fonte legítima.
- `group`: é agregado e nunca vira uma única personalidade falante.
- `unresolved_identity`: não recebe voz inventada.

No Persona, os atores individuais/ninken/históricos com ficha própria são separados de agregados de equipe. No Gemini e Canoney, o catálogo completo continua útil para validação de presença e escopo.

## Ferramentas sem gasto de modelo

- Persona: `persona_evidence`, `persona_validate_turn_packet`, `persona_fidelity_health`.
- Canoney: `character_evidence`, `turn_packet_validate`, `fidelity_healthcheck`.
- Gemini: `gemini_preflight`, `gemini_packet_example`, `gemini_healthcheck`.

Use preflight/health antes de gastar uma chamada Gemini quando houver dúvida de pacote ou deploy.

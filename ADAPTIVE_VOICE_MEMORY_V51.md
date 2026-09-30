# v51 — voz contextual e memória estruturada

30/09/2026. Continuidade Clássica. Complementa v49.1 e v50; nenhuma cena é canonizada.

## Comparação com as sugestões recebidas

| Proposta | Estado verificado | Decisão |
|---|---|---|
| Fichas por personagem | Bíblias, perfis, ActorState e relações direcionais já existem | Preservar; não duplicar como cards de outro frontend |
| Sintaxe e ritmo próprios | Fingerprint v42 e coesão v50 já existem | Acrescentar modulação contextual explícita, sem quotas |
| Exemplos few-shot | Catálogo selecionado de evidências, mínimo vigente de dois exemplares diretos | Reutilizar evidência válida e variada; nunca declarar mimetismo perfeito |
| Pensamento obrigatório antes da fala | ActorState já contém objetivo/subtexto | Não imprimir cadeia de pensamento ou linha obrigatória de pensamento; Inner Saya é recurso ficcional contextual |
| JSON de chakra em cada resposta | Engine já possui contabilidade e snapshots | Preservar cálculos e ausência de HUD; JSON gerado não comprova gasto correto |
| Lorebook por palavra-chave | Bundles e seleção de referência já existem | Relevância ajuda; regras centrais não podem depender de aparecer a palavra-chave |
| RAG vetorial e memória durável | Catálogo recuperável existe; state_store exige snapshot conservado pelo chamador | Não confundir catálogo de referência com memória episódica permanente. Banco persistente não foi instalado nesta revisão |
| SillyTavern/local LLM | Não são parte destes serviços | Não migrar infraestrutura ou trocar provedores sem comparação real; frontend/modelo local não garantem fidelidade |
| Voz/TTS | Não faz parte do fluxo textual inspecionado | Nenhum serviço pago, clonagem ou dependência de áudio adicionado |
| Penalização matemática de palavras | Não há mecanismo de logit bias por persona comprovado | Corrigir a descrição: instrução textual não instala penalizações numéricas |
| IC-80 = 80% de psicologia | Interpretação recebida não demonstrada pelas regras vigentes | Não alterar o significado existente de IC-80 |

## Alterações

O contrato compartilhado RP_QUALITY_V48.json contém adaptive_voice_v51. Trata ritmo, sintaxe, hesitação, silêncio e vocabulário como tendências dependentes de identidade, fase, objetivo, destinatário, pressão e estado residual. Não impõe teto de dez palavras, !!, Hm ou elipses obrigatórios; não produz falas ou pensamentos de Amatsu.

Os compiladores Python incluem esse contrato em realization_envelope. O Narrator o recebe pela instrução de sistema compartilhada, pelo ActorState e pela revisão semântica.

A compactação do Narrator usava conversão para string no objeto anchor e uma função destinada a arrays em select/bound/enact. Assim, um objeto virava [object Object] e os demais podiam virar arrays vazios. compactActorMemoryV51 preserva os tipos JSON e clona os valores, incluindo limites de conhecimento e percepção. O authoritative_turn_packet já preservava a fonte principal; a correção evita degradação da cópia de atuação.

Não foi criado índice vetorial, armazenamento episódico durável, cache remoto de pesquisa ou frontend novo. A memória continua dependendo de contexto/snapshot efetivamente reapresentado. A revisão deve separar documento recuperado, fato validado e canal de conhecimento do personagem.

## Validação

Quatro verificações isoladas do helper foram executadas em V8: objetos preservados, arrays legados preservados, entrada intacta e ausência não inventada. Testes Node permanentes verificam os mesmos cenários pelo módulo integrado. Workflows executam a suíte Node e as suítes Python/compilação quando publicados; consultar o resultado real do CI, sem inferir aprovação pela existência de testes.

Estes testes comprovam transporte e integração, não fidelidade perfeita de todas as cenas. Um teste de atuação deve avaliar sequência de estímulos, mudança de interlocutor, pressão e recuperação, além de frases isoladas.

## Fontes primárias conferidas

- https://ai.google.dev/gemini-api/docs/prompting-strategies — exemplos específicos e variados; engenharia iterativa, sem garantia de perfeição.
- https://ai.google.dev/api/generate-content — parâmetros explícitos de geração não equivalem a descrições de personalidade.
- https://docs.sillytavern.app/usage/core-concepts/worldinfo/ — ativação de contexto/lore depende de configuração e orçamento.
- https://docs.sillytavern.app/extensions/chat-vectorization/ — recuperação por similaridade; não substitui autoridade/canais de conhecimento.
- https://huggingface.co/coqui/XTTS-v2 — card oficial anuncia clonagem com seis segundos; não sustenta promessa universal de três segundos ou superioridade absoluta de TTS.

# Tool spec — Naruto Persona Engine v0.1

## persona_healthcheck
Sem argumentos.

## persona_profile
- `name: string`

## persona_find
- `query: string`
- `limit: integer = 12`

## persona_relation
- `speaker: string`
- `interlocutor: string`
- `situation: string = ""`
- `pressure: string = "normal"`
- `audience: string = ""`

## persona_turn
- `name: string`
- `interlocutor: string = ""`
- `stimulus: string = ""`
- `situation: string = ""`
- `pressure: string = "normal"`
- `audience: string = ""`
- `body_state: string = ""`
- `objective: string = ""`
- `perception_constraint: string = ""`
- `knowledge_constraint: string = ""`

### Contract
`perception_constraint` e `knowledge_constraint` devem vir do Canoney/chat quando forem materialmente relevantes. O Persona Engine não deve transformar percepção em conhecimento automaticamente.

## persona_check
- `name: string`
- `interlocutor: string = ""`
- `candidate_dialogue: string = ""`
- `candidate_action: string = ""`
- `situation: string = ""`
- `pressure: string = "normal"`

## Hard constraints
1. `Amatsu Uchiha` → geração voluntária bloqueada.
2. Relação é assimétrica.
3. Fase juvenil da referência é obrigatória.
4. Pesquisa externa nunca substitui fonte do reboot.
5. Sem fala canônica copiada.
6. Silêncio é saída válida.
7. Comédia física depende de situação + pressão + relação.
8. Morfossintaxe e vocativo fazem parte da persona.

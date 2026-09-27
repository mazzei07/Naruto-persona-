# Naruto Persona Engine v0.1 — MCP remoto

Especialista read-only de interpretação para **Naruto Reboot — Continuidade Clássica**.

Ele NÃO substitui o Canoney nem o motor mecânico. A divisão é:

- **Naruto canoney**: verdade canônica, continuidade, conhecimento e estado.
- **Naruto Reboot Engine**: causalidade física, combate, chakra e técnicas.
- **Naruto Persona Engine**: personalidade, referência, fase, relação, filtro, corpo, voz e reação.
- **ChatGPT principal**: orquestra, cruza documentos e escreve a prosa final.

## Ferramentas MCP

- `persona_healthcheck()`
- `persona_profile(name)`
- `persona_find(query, limit=12)`
- `persona_relation(speaker, interlocutor, situation="", pressure="normal", audience="")`
- `persona_turn(name, interlocutor="", stimulus="", situation="", pressure="normal", audience="", body_state="", objective="", perception_constraint="", knowledge_constraint="")`
- `persona_check(name, interlocutor="", candidate_dialogue="", candidate_action="", situation="", pressure="normal")`

## Princípios duros

1. Amatsu Uchiha é 100% do usuário; geração voluntária é bloqueada.
2. Relações são direcionais: A→B não é B→A.
3. Fase exata da referência é obrigatória.
4. Relação específica vence personalidade genérica.
5. Percepção não vira reconhecimento/conhecimento automaticamente.
6. Silêncio é saída válida.
7. Vocativo, latência, completude e morfossintaxe fazem parte da persona.
8. Referência canônica calibra atuação; não importa trauma, técnica, história ou destino.
9. Pesquisa externa só é indicada quando o cache/repertório local é insuficiente.
10. O Persona Engine devolve pacote comportamental; o chat principal escreve a cena.

## Estrutura

- `server.py` — servidor MCP remoto via Streamable HTTP.
- `persona_api.py` — API fina usada pelas ferramentas MCP.
- `persona_engine.py` — solver determinístico/local.
- `persona_rules.json` — regras operacionais.
- `character_registry_seed.json` — registro de 80 personagens/entidades da Continuidade Clássica.
- `world_registry_seed.json` — times e clãs.
- `test_persona_engine.py` — regressões locais.
- `Dockerfile` — implantação em serviço compatível com Docker.
- `requirements.txt` — SDK MCP oficial para Python.

## Teste local do núcleo (sem MCP)

```bash
python test_persona_engine.py
```

## Rodar servidor MCP

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python server.py
```

Por padrão o servidor usa `PORT=8000` e transporte `streamable-http`.
O endpoint MCP será servido pelo SDK em `/mcp`.

## Testar com MCP Inspector

```bash
npx @modelcontextprotocol/inspector@latest
```

Selecione **Streamable HTTP** e conecte:

```text
http://localhost:8000/mcp
```

Teste primeiro:

1. `persona_healthcheck`
2. `persona_turn` Saya Haruno → Amatsu Uchiha
3. `persona_turn` Saya Haruno → Kazuma Uzumaki
4. `persona_turn` Amatsu Uchiha → Saya Haruno (deve bloquear)
5. `persona_check` com uma fala deliberadamente errada.

## Implantação

O repositório já inclui `Dockerfile`. Em Render, Railway ou serviço equivalente:

1. crie um novo serviço a partir do repositório;
2. use Dockerfile;
3. deixe o serviço fornecer a variável `PORT`;
4. após o deploy, a URL a conectar no ChatGPT é:

```text
https://SEU-DOMINIO/mcp
```

Não é necessária chave de API para a v0.1 porque o núcleo não chama LLM nem web.

## Conectar ao ChatGPT

No modo de desenvolvedor/plugins do ChatGPT, crie uma conexão MCP e informe a URL HTTPS terminada em `/mcp`.
Nome sugerido:

```text
Naruto Persona Engine
```

Descrição sugerida:

```text
Especialista read-only de personalidade, referência canônica, fase, relação direcional, verbalização, linguagem corporal e reação do Naruto Reboot — Continuidade Clássica. Não substitui Canoney nem motor mecânico.
```

Depois de conectado, rode `persona_healthcheck` antes dos testes de regressão.

## Política de economia de usos

A v0.1 não chama LLM. `persona_turn` tenta resolver tudo a partir do registro local.
Quando uma interação não possui âncora suficiente, o retorno contém `research_required=true` e uma `suggested_query`. O chat principal pode então pesquisar apenas aquele caso excepcional, em vez de gastar uma chamada externa em toda fala.

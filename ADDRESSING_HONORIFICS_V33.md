# ADDRESSING / HONORIFICS V33 — Naruto Reboot Clássico

Status: obrigatório para geração de fala e revisão de voz.
Continuidade: classico_floresta_da_morte.

## Princípio
Tratamento, título e honorífico são estado relacional. Eles não são decoração "anime" e não são distribuídos por sexo, idade ou cargo de forma automática.

Antes de redigir uma fala, resolver nesta ordem:
1. relação direcional A→B;
2. personagem de referência e fase exata;
3. cargo/hierarquia de B;
4. educação social e registro basal de A;
5. intimidade, hostilidade, admiração ou investimento romântico;
6. público/privado;
7. urgência/perigo;
8. superfície PT-BR já estabelecida naquela relação.

Urgência pode comprimir um tratamento ("Kagetsu-sensei" → "sensei!"), mas não apaga respeito automaticamente.

## Famílias de referência
- Sakura/Ino-like: alta adaptação social. Podem ser coloquiais/explosivas com pares e subir claramente o registro com sensei/Kage/superior.
- Hinata-like: deferência alta; -kun pode ser estável quando a relação investida correspondente está mapeada.
- Lee-like: deferência explícita a mestre; -sensei forte; -san entre pares apenas quando a relação concreta sustenta.
- Naruto/Kiba-like: mais rudes e variáveis; sensei continua natural para professor, salvo apelido/intimidade explicitamente estabelecidos.
- Sasuke/Neji-like: tratamento seletivo e econômico; nome nu/omissão é comum entre pares, mas não autoriza apagar título preservado pela relação.
- Shikamaru-like: baixa energia muda cadência, não elimina automaticamente "sensei".

## Calibrações canônicas do Reboot
- Saya Haruno → Kazuma Uzumaki: "Kazuma-kun" é o default de endereçamento direto nesta fase de interesse inicial equivalente a Sakura→Sasuke. "Kazuma" nu surge por urgência, irritação forte ou mudança relacional live.
- Saya Haruno → Amatsu Uchiha: "Amatsu"/omissão, sem honorífico por default.
- Saya Haruno → Kagetsu Shiranui: "Kagetsu-sensei" em fala segura/normal; "sensei!" em urgência é compressão válida.
- Saya Haruno → Hokage: título deferente por default ("Hokage-sama", "Senhor(a) Hokage" ou "Grande Hokage" conforme a superfície PT-BR estabelecida na cena); não nome nu por reflexo.
- Relações Hinata-like: não espalhar "-kun" para todos os meninos; aplicar somente ao vínculo equivalente documentado.
- Relações Lee-like: não espalhar "-san"; aplicar quando respeito entre pares estiver realmente estabelecido.

## Gate de verificação
Reprovar/revisar quando:
- professor/Kage recebe nome nu contra o padrão do falante sem gatilho;
- um sufixo relacional estável desaparece sem urgência, irritação ou mudança live;
- -kun/-san/-chan é usado por estética ou em massa;
- todos os superiores recebem a mesma fala;
- personagem respeitoso vira casual apenas porque a cena tem pressão;
- honorífico é repetido em toda frase apesar de o interlocutor já estar claro.

## Relação com outros protocolos
Este gate ocorre depois de relação/referência/hierarquia serem recuperadas e antes da redação final da frase.
Ele complementa, sem substituir:
- ActorState relacional;
- Bíblia de Atuação v25/v32;
- gate de formalidade v23;
- diálogo v27;
- RP Generation Kernel v31.1-addressing-v33.

A ficha própria e a relação live sempre vencem analogia genérica com personagem oficial.


---

# ADENDO V43 — HIERARQUIA EM TERCEIRA PESSOA + PESQUISA RELACIONAL PAR-A-PAR

Status: obrigatório. Este adendo prevalece sobre qualquer regra anterior mais permissiva.

## 1. Título/honorífico não existe só no vocativo

A forma de tratamento deve ser resolvida tanto no endereçamento direto quanto ao REFERIR-SE ao superior em terceira pessoa.

Exemplos funcionais:
- aluno Sakura-like falando de seu professor Kakashi-like em situação normal: preferir "Kakashi-sensei", "o Kakashi-sensei" ou a superfície PT-BR equivalente já estabelecida; não degradar automaticamente para "ele" quando a identidade/relação é material à frase;
- Genin falando de Hokage: título deferente permanece ("Hokage-sama", "o Hokage", "Senhor Hokage" conforme a superfície escolhida);
- subordinado falando de Sannin/mestre reconhecido: preservar o tratamento/documentado pela referência e relação quando o nome/título é parte natural da fala;
- urgência pode comprimir "Kagetsu-sensei" para "sensei!", mas não autoriza transformar referência respeitosa em nome nu ou pronome casual por padrão.

Pronomes continuam permitidos quando o referente já está claro e a referência oficial daquela relação realmente os usa naturalmente. O gate não exige repetir o título em toda oração. Ele proíbe APAGAR sistematicamente a hierarquia.

## 2. Regra de preservação hierárquica

Antes de escolher nome, título, honorífico ou pronome:
1. recuperar A→B;
2. identificar referência oficial de A e de B;
3. travar a fase exata de ambos;
4. verificar como A trata B diretamente;
5. verificar como A SE REFERE A B diante de terceiros;
6. separar situação normal, irritação, urgência, intimidade e ruptura;
7. escolher a superfície PT-BR/Japonês-híbrida já estabelecida.

Se a referência oficial mantém "-sensei", "-sama", cargo ou título com alta frequência nessa relação, omiti-lo exige uma razão de cena; a omissão não pode ser o default do gerador.

## 3. Pesquisa relacional par-a-par obrigatória

Quando ator e interlocutor possuem personagens oficiais de referência, a pesquisa deve procurar primeiro evidência em que AS DUAS referências interajam na mesma fase.

Ordem:
1. mesma dupla oficial + mesma fase + situação equivalente;
2. mesma dupla oficial + mesma fase + situação funcionalmente próxima;
3. mesma relação funcional na mesma fase (ex.: sensei→aluno, rival→rival);
4. perfil individual apenas como fallback conservador.

A busca deve extrair:
- forma de tratamento direta;
- forma de referência em terceira pessoa;
- vocativo e posição do nome/título;
- comprimento/cadência da resposta;
- quem inicia/interrompe/cede;
- diferença público×privado;
- mudança sob perigo/raiva/vergonha;
- corpo/silêncio que substitui fala;
- frequência: típico, possível, raro;
- o que NÃO deve ser transferido (biografia, poderes, eventos futuros).

## 4. Gate de evidência

Se ambos possuem referência oficial e não existe evidência par-a-par suficiente:
- marcar pair_reference_research_required=true;
- gerar uma query de pesquisa com referência A + referência B + fase + situação;
- NÃO certificar cadência, honorífico, intimidade ou padrão de interrupção como "verificado";
- usar voz própria + relação direcional conservadora até a pesquisa externa ser concluída.

Sinopse prova evento/comportamento geral; não prova redação, prosódia ou dublagem.

## 5. Testes destrutivos obrigatórios

Reprovar/revisar quando:
- Sakura-like fala de Kakashi-like como mero "ele" em contexto onde a referência normal preservaria "Kakashi-sensei";
- Genin chama ou referencia Kage/Sannin/sensei por nome nu sem suporte relacional/fase/gatilho;
- trocar o interlocutor não muda tratamento;
- uma cena individual é usada para ignorar evidência direta da dupla;
- o gerador sabe que existe hierarquia, mas ela só aparece no metadata e some da frase;
- título/honorífico é repetido mecanicamente em toda frase apesar de o referente já estar claro.

## 6. Regra operacional

Hierarquia não é sinônimo de formalidade permanente. Naruto-like pode ser rude, impulsivo ou reclamar e ainda assim usar "Kakashi-sensei"; Sakura-like pode explodir com um par e subir registro imediatamente diante de autoridade. A personalidade controla COMO o respeito aparece; não apaga o vínculo institucional por conveniência do gerador.

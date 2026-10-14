# resume-score-agent

Projeto de estudo: um agente de LLM minimalista que lê um currículo, consulta
o perfil de uma vaga num banco DuckDB e devolve um score de compatibilidade —
a mesma ideia do Talent Finder, só que reduzida ao essencial pra deixar o
*mecanismo do agente* visível.

Roda **sem gastar nenhum token**: por padrão usa um "cérebro" falso
(`FunctionModel` do Pydantic AI) que decide as ações em Python puro, no lugar
de uma LLM de verdade. A estrutura do agente — tools, schemas, loop de
execução — é idêntica à que você usaria com um modelo real; só quem decide
a próxima ação muda.

## Por que isso é um "agente" e não só uma chamada de API

Uma chamada comum de LLM é: manda um prompt, recebe um texto, acabou. Um
**agente** é um loop: o modelo recebe o histórico, decide se quer *chamar uma
ferramenta* ou *responder em texto*, o programa executa a ferramenta, devolve
o resultado pro modelo, e ele decide de novo. Isso se repete até ele decidir
responder.

Aqui o loop tem 3 passos fixos:

```
1. decide chamar ler_curriculo(caminho_arquivo)
2. observa o resultado -> decide chamar calcular_score(nome, cargo, exp, skills)
3. observa o resultado -> responde em texto com o score final
```

Esse "decide, observa, decide de novo" é o padrão ReAct, e é o que separa um
agente de uma function chain comum (uma chain executa uma sequência fixa; um
agente decide a sequência em tempo de execução, inclusive podendo pular
passos, repetir uma tool com argumentos diferentes, ou nunca usar uma tool
que está disponível).

## Estrutura

```
src/
  models.py    # os schemas Pydantic (CandidateData, JobProfile, ScoreResult)
  db.py        # DuckDB: tabela de vagas + lookup
  tools.py     # as duas tools: ler_curriculo, calcular_score
  fake_llm.py  # o "cérebro" sem API key — leia este arquivo primeiro
  agent.py     # monta o Agent e registra as tools
  main.py      # CLI
data/
  curriculo_ana.txt    # candidata forte pra vaga de eng. de dados
  curriculo_bruno.txt  # candidato fraco pra vaga de analista de dados
  vagas.duckdb          # gerado automaticamente na primeira execução
tests/
  test_tools.py   # testa as tools isoladas, sem agente
  test_agent.py   # testa o loop completo do agente
```

**Ordem de leitura recomendada:** `models.py` → `tools.py` → `fake_llm.py` →
`agent.py` → `main.py`. O `fake_llm.py` é o arquivo mais importante pra
entender o conceito — é ele que simula a decisão que, numa LLM real, seria
tomada por tool calling.

## Rodando

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m src.main data/curriculo_ana.txt
python -m src.main data/curriculo_bruno.txt

python -m pytest tests/ -v
```

## Trocando pro modelo de verdade

Não precisa mudar nenhuma tool nem o schema. Só setar uma env var:

```bash
export OPENAI_API_KEY=sk-...
export AGENT_MODEL="openai:gpt-4o-mini"
python -m src.main data/curriculo_ana.txt

# ou, com Anthropic:
export ANTHROPIC_API_KEY=sk-ant-...
export AGENT_MODEL="anthropic:claude-sonnet-4-5"
python -m src.main data/curriculo_ana.txt
```

Com um modelo real, o agente deixa de seguir sempre a mesma sequência rígida
de 2 passos — ele decide com base no prompt, pode chamar as tools em outra
ordem, re-tentar, ou pedir mais contexto. É o mesmo código de `agent.py` e
`tools.py`; só a fonte da decisão muda (`fake_llm.py` → a API).

## Pydantic AI vs LangChain (anotações de estudo)

Não são a mesma coisa, embora resolvam o mesmo problema:

- **Pydantic AI**: mais magro, construído em cima do Pydantic que você já usa
  no stack. Tools são funções Python comuns com type hints — o schema sai
  sozinho da assinatura da função. Menos abstração "escondida", mais fácil
  de debugar linha a linha (foi por isso que foi escolhido aqui).
- **LangChain**: mais antigo, mais adotado no mercado (então aparece mais em
  vaga/currículo), mas com camadas de abstração próprias (`Chain`, `Runnable`,
  `LCEL`) que têm uma curva de aprendizado separada do Python puro. Vale
  conhecer o vocabulário (`chain`, `tool calling`, `agent executor`) mesmo
  sem ter implementado nele.

Pra conversar sobre o assunto numa entrevista, os conceitos que importam são
os mesmos nos dois frameworks:
- **tool / function calling**: o modelo recebe uma lista de funções
  disponíveis (nome, descrição, schema de argumentos) e decide se e qual
  chamar.
- **agent loop**: a repetição de decidir → agir → observar até terminar.
- **structured output**: forçar a resposta do modelo a bater com um schema
  (aqui, toda tool retorna um modelo Pydantic validado).

Documentação oficial pra aprofundar:
- Pydantic AI: https://ai.pydantic.dev
- LangChain (seção "Get started"): https://python.langchain.com

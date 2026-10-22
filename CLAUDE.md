# job-search-agent

Agente de procura de emprego: lê um anúncio de vaga, analisa o portfólio GitHub do utilizador
(RubenSilva13), pesquisa a empresa e entrega um relatório estruturado (Pydantic, em modelos.py).

## Estrutura
- config.py — chaves (ANTHROPIC_API_KEY, GITHUB_TOKEN), modelo (claude-haiku-5-5), MAX_PASSOS e MAX_TOKENS
- ferramentas.py — ferramentas do GitHub (listar_repositorios, ler_readme, ler_varios_readmes, ler_portfolio)
- ferramentas_web.py — ler_pagina_web e pesquisar_web
- modelos.py — Relatorio e Requisito (Pydantic, com validadores)
- agente.py — ciclo do agente escrito à mão (sem LangChain), formato da API da Anthropic
  (tool_use / tool_result), com cache e validação do relatório
- requirements.txt — dependências (anthropic, pydantic, requests, beautifulsoup4, ddgs, python-dotenv)
- As descrições das ferramentas usam o formato da Anthropic: name, description, input_schema

## Regras para trabalhar comigo
- Estou a aprender: antes de alterares um ficheiro, explica em poucas frases o que vais mudar e porquê.
- Código escrito por extenso: um passo por linha, nomes de variáveis claros, sem compactar.
- Nomes de variáveis e mensagens em português de Portugal.
- Não uses LangChain nem frameworks de agentes: o ciclo do agente é escrito à mão de propósito.
- Testa cada ferramenta sozinha antes de a usares no agente.
- Nunca mostres nem faças commit do .env. Confirma com `git status` antes de qualquer commit.
- O ambiente virtual está em venv/ e tem de estar ativo para correr o código.
- O plano do projeto está em ROADMAP.md. Lê-o antes de propores próximos passos.
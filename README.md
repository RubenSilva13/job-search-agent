# job-search-agent

Agente de procura de emprego. Recebe o link de uma vaga, lê o anúncio, analisa o portfólio GitHub
e o perfil do utilizador, pesquisa a empresa e entrega um relatório estruturado: que requisitos
da vaga o utilizador cumpre, com a prova de cada um, um score de compatibilidade e sugestões.

O agente nunca se candidata sozinho: prepara a análise e quem decide é o utilizador.

## Como funciona

O ciclo do agente está escrito à mão, sem LangChain nem outros frameworks de agentes, para se
perceber cada passo. Usa o formato de ferramentas da API da Anthropic (`tool_use` / `tool_result`).

1. O modelo recebe a tarefa e decide que ferramenta usar.
2. O código executa a ferramenta e devolve o resultado ao modelo.
3. O ciclo repete-se até o modelo entregar o relatório, ou até acabarem os passos.

O modelo decide o que fazer; o código garante o que tem de acontecer sempre:

- **Validação do relatório:** o relatório é um modelo Pydantic. Se o modelo entregar algo inválido
  (por exemplo, um requisito como "cumpre" sem evidência), o erro volta ao modelo para ele se corrigir.
- **Limite de passos:** no último passo, o modelo é obrigado a entregar o relatório.
- **Cache:** uma ferramenta chamada duas vezes com os mesmos argumentos não é executada outra vez.
- **Sem exagerar:** só conta o que está escrito nos READMEs e no perfil. Cada requisito cumprido
  indica a origem da prova e respeita o nível indicado no perfil.

## Ferramentas

| Ferramenta | O que faz |
|---|---|
| `ler_pagina_web` | Lê o texto de uma página (anúncio da vaga, site da empresa) |
| `pesquisar_web` | Pesquisa na web (DuckDuckGo) |
| `ler_portfolio` | Lê todos os repositórios públicos do GitHub, com o README de cada um |
| `listar_repositorios`, `ler_readme`, `ler_varios_readmes` | Versões mais finas do GitHub |
| `ler_perfil` | Lê `perfil.json`: formação, línguas, experiência e competências com o nível |
| `entregar_relatorio` | Entrega o relatório final (validado com Pydantic) |

## Relatório

Cada requisito do anúncio recebe um estado:

- ✅ `cumpre`: há prova clara num repositório ou no perfil
- 🟡 `parcial`: há prova de algo próximo, ou o perfil indica um nível inferior ao pedido
- ❌ `falta`: competência técnica que não aparece em lado nenhum
- ❔ `nao_confirmado`: algo que nem o GitHub nem o perfil mostram, como soft skills

O relatório inclui ainda o score (0 a 100), um resumo da empresa e sugestões. Fica guardado em
JSON na pasta `relatorios/`.

## Estrutura

```
agente.py           ciclo do agente, validação e apresentação do relatório
config.py           chaves, modelo e limites
ferramentas.py      ferramentas do GitHub e do perfil
ferramentas_web.py  ler páginas e pesquisar na web
modelos.py          Relatorio e Requisito (Pydantic, com validadores)
perfil.json         perfil do utilizador
ROADMAP.md          plano do projeto
```

## Como correr

Precisa de Python 3 e de uma chave da API da Anthropic.

```bash
python -m venv venv
venv\Scripts\activate          # Windows; em Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
```

Cria um ficheiro `.env` na raiz:

```
ANTHROPIC_API_KEY=a-tua-chave
GITHUB_TOKEN=opcional
```

O `GITHUB_TOKEN` é opcional e só aumenta o limite de pedidos à API do GitHub.

Edita o `perfil.json` com os teus dados. O nome de utilizador do GitHub indica-se na tarefa, como
no exemplo abaixo. Depois:

```bash
python agente.py
```

Escreve a tarefa quando o programa pedir, por exemplo:

```
Analisa esta vaga para o utilizador do GitHub RubenSilva13: https://exemplo.com/vaga
```

## Limitações conhecidas

- Páginas que exigem login (como o LinkedIn) ou que carregam o conteúdo com JavaScript não são
  lidas. Funciona melhor com anúncios em sites de empresas e plataformas abertas.
- O agente só conhece o que está no GitHub e no `perfil.json`. Não lê o CV.

## Estado e próximos passos

Concluído: ciclo do agente com ferramentas do GitHub, ferramentas web, relatório estruturado com
Pydantic, migração para a API do Claude e leitura do perfil.

Planeado (ver [ROADMAP.md](ROADMAP.md)): base de dados PostgreSQL, recolha diária de vagas,
registo dos passos e custos, avaliação com vagas classificadas à mão, frontend em React/Next.js,
testes, CI e Docker.

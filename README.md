# job-search-agent

Agente de procura de emprego. Recebe o link de uma vaga, lê o anúncio, analisa o portfólio GitHub
e o perfil do utilizador, pesquisa a empresa e entrega um relatório estruturado: que requisitos
da vaga o utilizador cumpre, com a prova de cada um, um score de compatibilidade e sugestões.

O agente nunca se candidata sozinho: prepara a análise e quem decide é o utilizador.

Também faz uma varredura de vagas: com `python diario.py` recolhe as vagas mais recentes do ITJobs
(API oficial), filtra-as pelas preferências do perfil (cidade, regime, nível júnior, área) e analisa
as que passam, guardando tudo numa base de dados PostgreSQL.

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
- **Cache:** uma ferramenta chamada duas vezes com os mesmos argumentos não é executada outra vez
  na mesma análise. O portfólio do GitHub fica ainda guardado em memória durante 30 minutos, para
  ser lido uma só vez por execução e não uma vez por vaga.
- **Registo:** cada análise guarda na base de dados a duração, os tokens, o custo estimado e cada
  passo (chamada ao modelo ou ferramenta), mesmo quando falha a meio.
- **Sem exagerar:** só conta o que está escrito nos READMEs e no perfil. Cada requisito cumprido
  indica a origem da prova e respeita o nível indicado no perfil.

## Ferramentas

| Ferramenta | O que faz |
|---|---|
| `ler_pagina_web` | Lê o texto de uma página (anúncio da vaga, site da empresa) |
| `pesquisar_web` | Pesquisa na web (DuckDuckGo) |
| `ler_portfolio` | Lê todos os repositórios públicos do GitHub, com o README de cada um |
| `listar_repositorios`, `ler_readme`, `ler_varios_readmes` | Versões mais finas do GitHub |
| `ler_perfil` | Lê o perfil da base de dados: formação, línguas, experiência e competências com o nível |
| `entregar_relatorio` | Entrega o relatório final (validado com Pydantic) |

## Relatório

Cada requisito do anúncio recebe um estado:

- ✅ `cumpre`: há prova clara num repositório ou no perfil
- 🟡 `parcial`: há prova de algo próximo, ou o perfil indica um nível inferior ao pedido
- ❌ `falta`: competência técnica que não aparece em lado nenhum
- ❔ `nao_confirmado`: algo que nem o GitHub nem o perfil mostram, como soft skills

O relatório inclui ainda o score (0 a 100), um resumo da empresa e sugestões. Fica guardado em
JSON na pasta `relatorios/`, com o link da vaga.

## Custos e tempos

No fim de cada análise aparece uma linha, por exemplo:

```
📊 2 chamadas ao modelo, 22,500 tokens, ~$0.0042, 28 s (ok)
```

`python custos.py` junta tudo o que ficou registado: total e média por análise, custo por dia, as
ferramentas mais lentas, onde vai o tempo e as análises mais caras. Com o `claude-haiku-5-5`, uma
análise custa cerca de 0,4 cêntimos.

As medições serviram para otimizar o agente (valores médios, em 3 a 6 análises por fase, por isso
são indicativos e não uma experiência controlada):

| | Ponto de partida | Cache do portfólio | Cache + uma pesquisa por análise |
|---|---|---|---|
| Leitura do portfólio | 10,7 s | 2,9 s | 2,9 s |
| Chamadas ao modelo por análise | 2,0 | 3,3 | 2,0 |
| Tempo total por análise | 37,3 s | 35,0 s | 27,9 s |
| Custo médio por análise | 0,42 ¢ | 0,59 ¢ | 0,42 ¢ |

A cache sozinha encurtou a leitura do portfólio mas não o tempo total: nessa fase o agente passou a
fazer pesquisas a mais, e cada chamada extra ao modelo reenvia todo o histórico. O limite de uma
pesquisa, escrito nas instruções do agente, corrigiu-o.

## Estrutura

```
agente.py           ciclo do agente, validação e apresentação do relatório
config.py           chaves, modelo e limites
ferramentas.py      ferramentas do GitHub e do perfil
ferramentas_web.py  ler páginas e pesquisar na web
modelos.py          Relatorio e Requisito (Pydantic, com validadores)
base_de_dados.py    ligação ao PostgreSQL: perfil, vagas e análises
schema.sql          tabelas da base de dados
recolha.py          recolhe vagas do ITJobs, filtra-as e guarda-as
filtro.py           decide se uma vaga serve (senioridade, anos pedidos, área, local e regime)
analise_diaria.py   analisa com o agente as vagas aceites que ainda não têm análise
diario.py           comando único: recolher, filtrar e analisar
custos.py           relatório de custos e tempos das análises (lê a base de dados)
docker-compose.yml  PostgreSQL num contentor Docker
perfil.json         perfil do utilizador, carregado para a base de dados
ROADMAP.md          plano do projeto
```

## Como correr

Precisa de Python 3, do Docker e de uma chave da API da Anthropic.

```bash
python -m venv venv
venv\Scripts\activate          # Windows; em Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
```

Cria um ficheiro `.env` na raiz:

```
ANTHROPIC_API_KEY=a-tua-chave
GITHUB_TOKEN=opcional
POSTGRES_PASSWORD=uma-palavra-passe-tua
ITJOBS_API_KEY=a-tua-chave
```

O `GITHUB_TOKEN` é opcional e só aumenta o limite de pedidos à API do GitHub. A chave do ITJobs
pede-se em [itjobs.pt/api](https://itjobs.pt/api).

Edita o `perfil.json` com os teus dados. Depois arranca a base de dados e carrega o perfil
(só é preciso repetir o segundo comando quando alteras o `perfil.json`):

```bash
docker compose up -d
python base_de_dados.py
```

Para fazer a varredura de vagas (precisa do Docker aberto):

```bash
python diario.py
```

Para ver quanto custaram e quanto demoraram as análises:

```bash
python custos.py
```

Para analisar uma vaga em concreto, o nome de utilizador do GitHub indica-se na tarefa:

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
- O agente só conhece o que está no GitHub e no perfil guardado na base de dados. Não lê o CV.
- O score varia entre execuções da mesma vaga, porque o modelo decide quais são os requisitos
  principais. Os estados de cada requisito são mais fiáveis do que o número.
- Se a base de dados estiver desligada, o `diario.py` avisa e termina com código de erro.
- A recolha só usa o ITJobs. O filtro é uma heurística (palavras no título e anos de experiência
  pedidos no texto), por isso pode deixar passar vagas sénior ou recusar vagas boas.
- O campo `workModel` do ITJobs (0, 1, 2) foi interpretado como presencial, remoto e híbrido, mas
  isso não está confirmado pela fonte.
- O limite de uma pesquisa web por análise é uma instrução ao modelo, não uma garantia do código.
- O custo é uma estimativa: tokens devolvidos pela API vezes a tabela de preços do `config.py`
  (verificada em 2026-11-03), que convém rever de vez em quando.

## Estado e próximos passos

Concluído: ciclo do agente com ferramentas do GitHub, ferramentas web, relatório estruturado com
Pydantic, migração para a API do Claude, base de dados PostgreSQL (em Docker) com o perfil, as
vagas e as análises, a recolha, filtro e análise de vagas do ITJobs com um só comando, e o registo de
duração, tokens e custo de cada análise.

Planeado (ver [ROADMAP.md](ROADMAP.md)): avaliação com vagas classificadas à mão, frontend em
React/Next.js, testes, CI e deploy.

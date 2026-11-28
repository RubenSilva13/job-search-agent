# Roadmap

Objetivo: um agente que me ajuda na procura de emprego. Encontra vagas, avalia-as contra o meu
perfil e o meu GitHub, investiga a empresa e prepara a candidatura. Nunca se candidata sozinho:
prepara tudo e eu decido.

## Fases
1. ✅ Ciclo do agente escrito à mão, com ferramentas do GitHub
2. ✅ Ferramentas web (ler páginas, pesquisar), relatório estruturado com Pydantic, migração para a API do Claude
3. ✅ Base de dados (PostgreSQL) com o meu perfil (CV, formação, línguas), vagas e candidaturas
4. ✅ Recolha de vagas a partir de fontes com acesso oficial (ITJobs), filtro pelas preferências e análise automática, com um só comando (python diario.py). Corre a pedido, não agendada
5. ✅ Registo de cada execução do agente (duração, tokens, custo e passos) na base de dados, e relatório de custos (python custos.py)
6. ✅ Avaliação: vagas classificadas por mim (24 de desenvolvimento e 15 de teste, nunca vistas), com o score comparado com as minhas notas e a estabilidade medida em 3 repetições (ver avaliacao/)
7. ✅ Frontend em Next.js com uma API em FastAPI: lista de vagas por score, relatório de cada uma, acompanhamento das candidaturas, análise de uma vaga a partir do link e página de custos
8. ✅ Testes (111, com pytest, incluindo SQL contra um PostgreSQL a sério), CI com GitHub Actions e Docker (imagens da API e do painel, compose com profile app). O deploy não foi feito, por decisão (ver abaixo)

## Decisões já tomadas
- O ciclo do agente é escrito à mão (sem LangChain) até à fase 2, para perceber como funciona.
  Migrar para o LangGraph só se surgir um passo com aprovação humana ou estado persistente. Depois da
  fase 6, refazer o mesmo agente em LangGraph e comparar as duas versões com as vagas classificadas.
- O projeto corre a pedido (python diario.py). Não há agendamento: é um projeto de portfólio.
- O modelo decide o que fazer; o código garante o que tem de acontecer sempre
  (por exemplo, ler o portfólio completo com ler_portfolio).
- Otimizar só depois de medir. A cache do portfólio e o limite de pesquisas por análise vieram do
  custos.py, e a segunda só foi descoberta porque a primeira não encurtou o tempo total.
- O score é calculado em código a partir dos estados dos requisitos, e não escrito pelo modelo. A
  avaliação mostrou que o modelo nem sempre seguia a sua própria regra, e a oscilação desceu de 12,9
  para 8,1 pontos.
- Classifico as vagas sem ver o score do agente. O conjunto de teste usa-se uma só vez, com vagas
  que o agente nunca analisou, e fica "queimado" depois de ver o resultado: uma melhoria nova
  confirma-se com vagas novas.
- O agente nunca exagera a minha experiência: só afirma o que está escrito nos READMEs e no perfil.
- O painel é uma ferramenta pessoal, sem contas: o perfil é uma só linha da base de dados e o GitHub
  vem do config.py. Torná-lo multiutilizador mudaria a base de dados e só se faz se o objetivo mudar.
- Não há deploy. Uma demo pública pedia uma base de dados alojada, proteger a API (cada análise
  gasta a chave da Anthropic) e mantê-la a funcionar, e um link morto prejudica mais do que ajuda.
  O projeto mostra-se com o repositório (README, testes e CI) e com um vídeo do painel. Se um dia
  se fizer, o caminho é uma demo só de leitura, com a escrita desligada.
- Os testes usam uma base de dados à parte (job_search_teste), forçada pelo conftest.py, para nunca
  tocarem na base real. Os endereços da API do painel vêm de variáveis de ambiente (API_URL no
  servidor do Next.js e NEXT_PUBLIC_API_URL no browser), com o 127.0.0.1:8000 como valor por defeito.
- No frontend, a lista e o detalhe lêem a API no servidor do Next.js; só o que reage ao clique
  (candidatura, análise por link) corre no browser.

## Problemas conhecidos
- O score ainda oscila entre execuções da mesma vaga (8,1 pontos em média no teste, 33 no pior caso).
  O que varia é a classificação dos requisitos (falta contra nao_confirmado), e com poucos
  requisitos contáveis um só que mude move o score 17 a 33 pontos.
- O agente não distingue talvez de nao (score médio 36 contra 33 no teste). Encontra as vagas boas,
  não as intermédias.
- O score mede a cobertura comprovada, e não o meu interesse: marco serve em vagas em que aprenderia
  o que falta, e o agente vê isso como falta. As minhas duas notas correlacionam-se 0,70 no teste,
  por isso a avaliação não separa bem as duas coisas.
- A avaliação tem um só avaliador e poucas vagas: os intervalos de confiança são largos e os das
  correlações tocam o zero. Indica uma direção, não é uma prova.
- Ideias por confirmar em vagas novas: afinar a regra falta contra nao_confirmado, mostrar o número
  de requisitos contáveis ao lado do score, e devolver dois números (cobertura e ajuste ao que
  procuro).
- O perfil existe em dois sítios (perfil.json e base de dados). Edita-se o ficheiro e recarrega-se
  com python base_de_dados.py. O painel não edita o perfil, por isso continua assim.
- O url da vaga é guardado como veio, com parâmetros de rastreio. A mesma vaga com outro link
  pode entrar duas vezes. Fica por tratar.
- As preferências do perfil só são usadas pelo filtro, não pelo agente na análise.
- A API não tem autenticação, e cada análise pedida no painel (POST /analises) gasta a chave da
  Anthropic. Serve para correr em local. O estado das análises pedidas fica em memória: se a API
  reiniciar a meio (o --reload reinicia ao gravar um ficheiro), perde-se o seguimento.
- A imagem Docker do painel pesa 1,1 GB, por levar todo o node_modules. O modo standalone do
  Next.js reduzi-la-ia, mas só importa se houver deploy.
- O Docker lê as chaves do ficheiro .env (env_file). Quem clonar o repositório tem de criar o seu.
- As consultas SQL dos custos existem em dois sítios (custos.py e api.py). Podiam passar para uma
  função em base_de_dados.py.
- Uma análise pedida no painel fica em execucoes sem vaga_id (o id só se conhece depois do
  relatório), por isso na página de custos aparece como "(sem vaga)". O python agente.py faz o mesmo.
- A lista do painel filtra no Next.js, depois de a API devolver todas as vagas. Com milhares de
  vagas, o filtro passaria para a API.
- O significado do campo workModel do ITJobs (0, 1, 2) é uma hipótese por confirmar. Condiciona o
  filtro de regime (presencial, remoto, híbrido).
- O filtro de vagas é por palavras no título e por anos de experiência no texto. É uma heurística:
  deixa passar vagas sénior que não o dizem, e pode recusar vagas boas.
- A pesquisa web repete até 3 vezes se falhar. Se falhar sempre, a análise sai sem informação da
  empresa, e o relatório diz que não foi possível confirmar.
- O limite de uma pesquisa por análise é uma instrução no SYSTEM, não uma garantia do código. O
  agente pode voltar a pesquisar mais vezes, e o custos.py mostra-o (cada chamada extra ao modelo
  reenvia todo o histórico).
- O filtro deixa passar vagas da área com pouca compatibilidade (scores de 13 a 25 são comuns).
- O custo é uma estimativa: tokens devolvidos pela API vezes a tabela PRECOS do config.py, verificada
  em 2026-11-03. Rever a tabela de vez em quando e conferir o total com a Console.
- A extração de páginas web falha em sites que exigem login (LinkedIn) ou que usam JavaScript.
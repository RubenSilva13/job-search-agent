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
6. Avaliação: um conjunto de vagas classificadas por mim, para medir as decisões do agente
7. Frontend em React/Next.js: painel de vagas e candidaturas
8. Testes, CI com GitHub Actions, Docker e deploy

## Decisões já tomadas
- O ciclo do agente é escrito à mão (sem LangChain) até à fase 2, para perceber como funciona.
  Migrar para o LangGraph só se surgir um passo com aprovação humana ou estado persistente. Depois da
  fase 6, refazer o mesmo agente em LangGraph e comparar as duas versões com as vagas classificadas.
- O projeto corre a pedido (python diario.py). Não há agendamento: é um projeto de portfólio.
- O modelo decide o que fazer; o código garante o que tem de acontecer sempre
  (por exemplo, ler o portfólio completo com ler_portfolio).
- Otimizar só depois de medir. A cache do portfólio e o limite de pesquisas por análise vieram do
  custos.py, e a segunda só foi descoberta porque a primeira não encurtou o tempo total.
- O agente nunca exagera a minha experiência: só afirma o que está escrito nos READMEs e no perfil.

## Problemas conhecidos
- O score varia entre execuções da mesma vaga. Mede-se na fase 6.
- O perfil existe em dois sítios (perfil.json e base de dados). Edita-se o ficheiro e recarrega-se
  com python base_de_dados.py. Fica só a base de dados quando existir o frontend (fase 7).
- O url da vaga é guardado como veio, com parâmetros de rastreio. A mesma vaga com outro link
  pode entrar duas vezes. Fica por tratar.
- A tabela candidaturas ainda não é usada. As preferências do perfil só são usadas pelo filtro,
  não pelo agente na análise.
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
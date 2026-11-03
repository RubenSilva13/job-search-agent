# Roadmap

Objetivo: um agente que me ajuda na procura de emprego. Encontra vagas, avalia-as contra o meu
perfil e o meu GitHub, investiga a empresa e prepara a candidatura. Nunca se candidata sozinho:
prepara tudo e eu decido.

## Fases
1. ✅ Ciclo do agente escrito à mão, com ferramentas do GitHub
2. ✅ Ferramentas web (ler páginas, pesquisar), relatório estruturado com Pydantic, migração para a API do Claude
3. ✅ Base de dados (PostgreSQL) com o meu perfil (CV, formação, línguas), vagas e candidaturas
4. Recolha diária de vagas, agendada, a partir de fontes com acesso oficial (APIs ou RSS)
5. Registo de cada passo do agente (traces) e dos custos
6. Avaliação: um conjunto de vagas classificadas por mim, para medir as decisões do agente
7. Frontend em React/Next.js: painel de vagas e candidaturas
8. Testes, CI com GitHub Actions, Docker e deploy

## Decisões já tomadas
- O ciclo do agente é escrito à mão (sem LangChain) até à fase 2, para perceber como funciona.
  Na fase 3 ou 4, migrar para o LangGraph, quando forem precisos estado persistente e aprovação humana.
- O modelo decide o que fazer; o código garante o que tem de acontecer sempre
  (por exemplo, ler o portfólio completo com ler_portfolio).
- O agente nunca exagera a minha experiência: só afirma o que está escrito nos READMEs e no perfil.

## Problemas conhecidos
- O score varia entre execuções da mesma vaga. Mede-se na fase 6.
- O perfil existe em dois sítios (perfil.json e base de dados). Edita-se o ficheiro e recarrega-se
  com python base_de_dados.py. Fica só a base de dados quando existir o frontend (fase 7).
- O url da vaga é guardado como veio, com parâmetros de rastreio. A mesma vaga com outro link
  pode entrar duas vezes. Limpar o url por fonte, na fase 4.
- A tabela candidaturas e as preferências do perfil ainda não são usadas pelo agente.
- A extração de páginas web falha em sites que exigem login (LinkedIn) ou que usam JavaScript.
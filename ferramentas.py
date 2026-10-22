import requests
from config import GITHUB_TOKEN
from ferramentas_web import FERRAMENTAS_WEB, DESCRICOES_WEB



URL_API ="https://api.github.com"

def cabecalhos_github():
    """Cabeçalho para os pedidos à API do github, com o token se existir."""
    cabecalhos = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        cabecalhos["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return cabecalhos



def listar_repositorios(utilizador):
    url = f"{URL_API}/users/{utilizador}/repos"
    parametros = {"per_page": 100, "sort": "updated"}
    resposta = requests.get(url, headers=cabecalhos_github(), params= parametros, timeout=15)

    if resposta.status_code == 404:
        return f"O utilizador '{utilizador}' nao existe no Github"
    resposta.raise_for_status()

    linhas = []
    for repo in resposta.json():
        if repo["fork"]:
            continue

        nome = repo["name"]
        linguagem = repo["language"] or "sem linguagem"
        descricao = repo["description"] or "sem descriçao"
        linhas.append(f"- {nome} ({linguagem}): {descricao}")

    if not linhas:
        return "Este utilizador nao tem repositorios publicos"
    return "\n".join(linhas)



def ler_readme(utilizador, repositorio, limite=6000):
    url = f"{URL_API}/repos/{utilizador}/{repositorio}/readme"

    cabecalhos = cabecalhos_github()
    cabecalhos["Accept"] = "application/vnd.github.raw"
    resposta = requests.get(url, headers=cabecalhos, timeout=15)

    if resposta.status_code ==  404:
        return f"O repositorio: '{repositorio}' nao tem readme ou nao existe."
    resposta.raise_for_status()

    texto = resposta.text
    if len(texto) > limite:
        texto = texto[:limite] + "\n[... readme cortado por ser demasiado longo]"
    return texto

def ler_varios_readmes(utilizador, repositorios):
    blocos = []
    for repositorio in repositorios:
        texto = ler_readme(utilizador, repositorio)
        blocos.append(f"----README de {repositorio} ----\n{texto}")
    return "\n\n".join(blocos)

def ler_portfolio(utilizador):
    url =f"{URL_API}/users/{utilizador}/repos"
    parametros = {"per_page": 100, "sort": "updated"}

    resposta = requests.get(url, headers=cabecalhos_github(), params=parametros, timeout=15)

    if resposta.status_code==404:
        return f"O utilizador '{utilizador}' nao existe no github"
    resposta.raise_for_status()

    blocos = []
    for repo in resposta.json():
        if repo["fork"]:
            continue

        nome = repo["name"]
        linguagem = repo ["language"] or "sem linguagem"
        descricao = repo ["description"] or "sem descriçao"

        readme = ler_readme(utilizador, nome, limite=3000)

        bloco = (
            f"----{nome} ({linguagem}) ----\n"
            f"Descriçao: {descricao}\n\n"
            f"{readme}"

        )
        blocos.append(bloco)
    if not blocos:
        return "Este utilizador nao tem repositorios publicos."
    return "\n\n".join(blocos)



FERRAMENTAS = {
    "listar_repositorios": listar_repositorios,
    "ler_readme": ler_readme,
    "ler_varios_readmes": ler_varios_readmes,
    "ler_portfolio": ler_portfolio,
}


DESCRICOES = [
    {
    "type":"function",
    "function":{
        "name":"listar_repositorios",
        "description":"Lista os repositorios publicos de um utilizador do github, com a linguagem principal e a descriçao de cada um.",

        "parameters": {
            "type": "object",
            "properties": {
                "utilizador": {"type": "string", "description": "Nome do utilizador do github"},
            },
            "required":["utilizador"],
         },
       },
     },


     {
         "type":"function",
         "function": {
             "name": "ler_readme",
             "description": "Le o readme de um repositorio do github. usa para saber em detalhe o que um projeto faz e que tecnologias usa.",

             "parameters": {
                 "type":"object",
                 "properties": {
                     "utilizador":{"type":"string", "description": "Dono do repositorio"},
                     "repositorio": {"type":"string", "description":" Nome exato do repositorio"},

                 },
                 "required":["utilizador", "repositorio"],

             },
         },
     },
     {
         "type":"function",
         "function": {
             "name":"ler_varios_readmes",
             "description": "Le os readmes de varios repositorios de uma so vez. Prefere esta ferramente a ler_readme sempre que precisares de mais do que um readme.",
             "parameters": {
                 "type":"object",
                 "properties": {
                     "utilizador":{"type":"string", "description": "Dono dos repositorios"},
                     "repositorios": {
                         "type":"array",
                         "items":{"type":"string"},
                         "description":"lista com os nomes exatos dos repositorios",
                     },
                 },
                 "required": ["utilizador", "repositorios"],
             },
         },
     },

     {
        "type": "function",
        "function": {
            "name": "ler_portfolio",
            "description": "Lê o portfólio completo de um utilizador do GitHub: todos os repositórios, "
                           "com a linguagem, a descrição e o README de cada um. "
                           "Usa esta ferramenta, uma só vez, para avaliar o utilizador para uma vaga.",
            "parameters": {
                "type": "object",
                "properties": {
                    "utilizador": {"type": "string", "description": "Nome de utilizador no GitHub"},
                },
                "required": ["utilizador"],
            },
        },
    },
]

FERRAMENTAS.update(FERRAMENTAS_WEB)
DESCRICOES.extend(DESCRICOES_WEB)
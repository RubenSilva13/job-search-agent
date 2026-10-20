import requests
from config import GITHUB_TOKEN

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
    resposta = requests.get(url, headers=cabecalhos_github(), params= parametros, timeput=15)

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



def ler_readme(utilizador, repositorio):
    url = f"{URL_API}/repo/{utilizador}/{repositorio}/readme"

    cabecalhos = cabecalhos_github()
    cabecalhos["Accept"] = "application/vnd.github.raw"
    resposta = requests.get(url, headers=cabecalhos, timeout=15)

    if resposta.status_code ==  404:
        return f"O repositorio: '{repositorio}' nao tem readme ou nao existe."
    resposta.raise_for_status()

    texto = resposta.text
    limite = 6000
    if len(texto) > limite:
        texto = texto[:limite] + "\n[... readme cortado por ser demasiado longo]"
    return texto



FERRAMENTAS = {
    "listar_repositorios": listar_repositorios,
    "ler_readme": ler_readme,
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
         "type":"function5",
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
],
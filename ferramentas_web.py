import requests
from bs4 import BeautifulSoup
from ddgs import DDGS

def ler_pagina_web(url):
    if not url.startswith("http://") and not url.startswith ("https://"):
        return "Erro: o URL tem de começar por http: // ou https://."

    cabecalhos = {"User-Agent": "Mozilla/5.0 (job-search-agent)"}

    try:
        resposta = requests.get(url, headers=cabecalhos, timeout=15)
    except requests.RequestException as erro:
        return f"Erro: nao foi possivel abrir a pagina ({erro})"

    if resposta.status_code !=200:
        return (
            f"Erro: a pagina respondeu com o codigo {resposta.status_code}."
            "Pode existir login ou ja nao existir."
        )

    tipo_de_conteudo = resposta.headers.get("Content-Type", "")
    if "html" not in tipo_de_conteudo:
        return f"Erro: o link nao é uma pagina web (tipo: {tipo_de_conteudo})"

    sopa = BeautifulSoup(resposta.text, "html.parser")
    for etiqueta in sopa(["script", "style", "nav", "footer", "header"]):
        etiqueta.decompose()

       
    tags_de_bloco = ["h1", "h2", "h3", "h4", "p", "li", "td"]

    blocos = []
    for elemento in sopa.find_all(tags_de_bloco):
        if elemento.find_parent(tags_de_bloco):
            continue

        texto_do_bloco = elemento.get_text(separator=" ", strip=True)
        if texto_do_bloco:
            blocos.append(texto_do_bloco)

    texto_limpo = "\n".join(blocos)

    
    if len(texto_limpo) < 200:
        linhas_limpas = []
        for linha in sopa.get_text(separator="\n").splitlines():
            linha = linha.strip()
            if linha:
                linhas_limpas.append(linha)
        texto_limpo = "\n".join(linhas_limpas)


    if len(texto_limpo) < 200:
        return (
            "Aviso: a página tem muito pouco texto. Pode ser carregada com JavaScript "
            "ou exigir login, e por isso não foi possível ler o conteúdo."
        )

    limite = 8000
    if len(texto_limpo) > limite:
        texto_limpo = texto_limpo[:limite] + "\n[... página cortada por ser demasiado longa]"

    return texto_limpo


def pesquisar_web(consulta):
    try:
        resultados = DDGS().text(consulta, max_results=5)
    except Exception as erro:
        return f"Erro na pesquisa {erro}."
    if not resultados:
        return f"A pesquisa por '{consulta}' nao devolveu resultados."

    blocos = []
    for resultado in resultados:
        titulo = resultado["title"]
        resumo = resultado["body"]
        link = resultado["href"]
        blocos.append(f"{titulo}\n{resumo}\n{link}")

    return "\n\n".join(blocos)



FERRAMENTAS_WEB ={
    "ler_pagina_web": ler_pagina_web,
    "pesquisar_web": pesquisar_web,
}

DESCRICOES_WEB = [
    {
        "type": "function",
        "function": {
            "name":"ler_pagina_web",
            "description": "Abre um link e devolve o texto da pagina. usa pra ler anuncios de vagas ou o site de uma empresa. Nao funciona com paginas que exigem login.",
            "parameters" : {
                "type": "object",
                "properties": {
                    "url":{"type": "string", "description": "Endereço completo, a começar com https://"},
                },
                "required": ["url"],
            },

        },
    },
    {
        "type":"function",
        "function": {
            "name":"pesquisar_web",
            "description":"Pesquisa na web e devolve os 5 primeiros resultados (titulo, resumo e link). Usa para saber o que uma empresa faz, que tecnologias usa ou noticias recentes",
            "parameters": {
                "type":"object",
                "properties": {
                    "consulta":{"type": "string", "description":"Termos de pesquisa"},
                },
                "required": ["consulta"],
            },
                    
        },

    },
]

import requests
from bs4 import BeautifulSoup
from config import ITJOBS_API_KEY

URL_ITJOBS = "https://api.itjobs.pt/job/list.json"

# Identificação honesta do programa. Com o identificador genérico do requests,
# o Cloudflare do ITJobs responde 403.
CABECALHOS = {"User-Agent": "job-search-agent/0.1 (projeto pessoal de procura de emprego)"}

# workModel (por confirmar com o ITJobs): 0 = presencial ou não indicado, 1 = remoto, 2 = híbrido
REGIMES = {0: "presencial", 1: "remoto", 2: "hibrido"}


def html_para_texto(html):
    """Converte HTML em texto simples, removendo tags e entidades HTML."""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n", strip=True)


def recolher_itjobs(limite=100):
    """Pede ao ITJobs as vagas mais recentes e devolve-as numa lista de dicionários simples."""
    parametros = {
        "api_key": ITJOBS_API_KEY,
        "limit": limite,
    }

    try:
        resposta = requests.get(URL_ITJOBS, params=parametros, headers=CABECALHOS, timeout=15)
    except requests.RequestException as erro:
        # não imprimir o erro: pode conter o endereço com a chave
        print(f"ITJobs: não foi possível ligar ({type(erro).__name__}).")
        return []

    if resposta.status_code != 200:
        print(f"ITJobs: a API respondeu com o código {resposta.status_code}.")
        return []

    vagas = []
    for item in resposta.json()["results"]:
        locais = [local["name"] for local in item.get("locations", [])]

        vagas.append({
            "titulo": item["title"],
            "empresa": item["company"]["name"],
            "url": f"https://www.itjobs.pt/oferta/{item['id']}/{item.get('slug', '')}",
            "localizacoes": locais,
            "regime": REGIMES.get(item.get("workModel")),
            "descricao": html_para_texto(item.get("body", "")),
            "publicada_em": item["publishedAt"],
            "fonte": "itjobs",
        })

    return vagas


if __name__ == "__main__":
    vagas = recolher_itjobs(5)
    for vaga in vagas:
        print(f"{vaga['titulo']} — {vaga['empresa']}")
        print(f"  {vaga['url']}")
        print(f"  locais: {vaga['localizacoes']} | regime: {vaga['regime']} | "
              f"publicada: {vaga['publicada_em']} | descrição: {len(vaga['descricao'])} caracteres")

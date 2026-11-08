import requests
from bs4 import BeautifulSoup
from psycopg.rows import dict_row
from base_de_dados import abrir_ligacao, guardar_vaga, ler_perfil_da_base
from config import ITJOBS_API_KEY
from filtro import filtrar_vaga

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


def recolher_e_guardar(limite=100):
    """Recolhe as vagas, filtra-as pelas preferências e guarda todas na base de dados.

    Guarda também as recusadas, com o motivo, para não as voltar a tratar e para se poder rever o filtro.
    """
    perfil = ler_perfil_da_base()
    if perfil is None:
        print("O perfil ainda não foi carregado. Corre 'python base_de_dados.py'.")
        return

    preferencias = perfil["preferencias"]
    vagas = recolher_itjobs(limite)
    if not vagas:
        print("Nenhuma vaga recolhida, nada foi guardado.")
        return

    aceites = 0
    for vaga in vagas:
        decisao = filtrar_vaga(vaga, preferencias)

        guardar_vaga(
            vaga["titulo"],
            vaga["empresa"],
            vaga["url"],
            localizacao=", ".join(vaga["localizacoes"]) or None,
            descricao=vaga["descricao"],
            fonte=vaga["fonte"],
            publicada_em=vaga["publicada_em"],
            regime=vaga["regime"],
            aceite=decisao["aceite"],
            motivo_filtro=decisao["motivo"],
        )

        if decisao["aceite"]:
            aceites += 1

    print(f"ITJobs: {len(vagas)} vagas recolhidas, {aceites} aceites, todas guardadas na base de dados.")


def refiltrar_vagas():
    """Volta a aplicar o filtro a todas as vagas guardadas. Usa-se quando as regras do filtro mudam."""
    perfil = ler_perfil_da_base()
    if perfil is None:
        print("O perfil ainda não foi carregado. Corre 'python base_de_dados.py'.")
        return

    preferencias = perfil["preferencias"]
    aceites_antes = 0
    aceites_depois = 0

    with abrir_ligacao() as ligacao:
        with ligacao.cursor(row_factory=dict_row) as cursor:
            cursor.execute("SELECT id, titulo, localizacao, regime, descricao, aceite FROM vagas")
            guardadas = cursor.fetchall()

            for guardada in guardadas:
                # reconstrói a vaga no formato que o filtro espera
                vaga = {
                    "titulo": guardada["titulo"],
                    "localizacoes": guardada["localizacao"].split(", ") if guardada["localizacao"] else [],
                    "regime": guardada["regime"],
                    "descricao": guardada["descricao"],
                }
                decisao = filtrar_vaga(vaga, preferencias)

                cursor.execute(
                    "UPDATE vagas SET aceite = %s, motivo_filtro = %s WHERE id = %s",
                    (decisao["aceite"], decisao["motivo"], guardada["id"]),
                )

                aceites_antes += bool(guardada["aceite"])
                aceites_depois += decisao["aceite"]

    print(f"Filtro reaplicado a {len(guardadas)} vagas: aceites {aceites_antes} -> {aceites_depois}.")


if __name__ == "__main__":
    vagas = recolher_itjobs(5)
    for vaga in vagas:
        print(f"{vaga['titulo']} — {vaga['empresa']}")
        print(f"  {vaga['url']}")
        print(f"  locais: {vaga['localizacoes']} | regime: {vaga['regime']} | "
              f"publicada: {vaga['publicada_em']} | descrição: {len(vaga['descricao'])} caracteres")

from base_de_dados import guardar_analise, guardar_vaga
from modelos import Relatorio, Requisito


def relatorio_valido(estados=("cumpre",), vaga="Programador Python", empresa="Empresa X"):
    """Um relatório válido, com um requisito por estado. O score vem dos estados:
    ("cumpre",) dá 100, ("cumpre", "falta") dá 50 e ("falta",) dá 0."""
    requisitos = []
    for posicao, estado in enumerate(estados):
        # cumpre e parcial exigem evidência; os outros estados não
        evidencia = "repositório X: README" if estado in ("cumpre", "parcial") else None
        requisitos.append(Requisito(requisito=f"requisito {posicao}", estado=estado, evidencia=evidencia))

    return Relatorio(
        vaga=vaga,
        empresa=empresa,
        localizacao="Braga",
        requisitos=requisitos,
        resumo_empresa="Uma empresa.",
        sugestoes=["Uma sugestão."],
    )


def criar_vaga(titulo="Vaga", url=None, **campos):
    """Guarda uma vaga na base de dados de teste e devolve o id."""
    url = url or f"https://exemplo.com/{titulo.replace(' ', '-')}"
    return guardar_vaga(titulo, "Empresa X", url, **campos)


def criar_vaga_analisada(titulo, estados=("cumpre",)):
    """Guarda uma vaga e uma análise dela. Devolve o id da vaga."""
    vaga_id = criar_vaga(titulo)
    guardar_analise(vaga_id, relatorio_valido(estados, vaga=titulo))
    return vaga_id

import pytest
from pydantic import ValidationError

from modelos import Relatorio, Requisito


def requisito(estado, texto="Python"):
    """Um requisito válido com o estado pedido (com evidência quando o estado a exige)."""
    evidencia = "repositório X: README" if estado in ("cumpre", "parcial") else None
    return Requisito(requisito=texto, estado=estado, evidencia=evidencia)


def relatorio(*estados):
    """Um relatório válido com um requisito por estado, todos com textos diferentes."""
    requisitos = [requisito(estado, f"requisito {posicao}") for posicao, estado in enumerate(estados)]
    return Relatorio(
        vaga="Programador",
        empresa="Empresa",
        requisitos=requisitos,
        resumo_empresa="Uma empresa.",
        sugestoes=["Uma sugestão."],
    )


# ---------- score ----------

def test_score_tudo_cumprido_e_100():
    assert relatorio("cumpre", "cumpre", "cumpre").score == 100


def test_score_nada_cumprido_e_0():
    assert relatorio("falta", "falta").score == 0


def test_score_metade_cumprida_e_50():
    assert relatorio("cumpre", "falta").score == 50


def test_score_parcial_vale_metade():
    # um parcial e uma falta: (0.5 * 1) / 2 = 25
    assert relatorio("parcial", "falta").score == 25


def test_score_nao_confirmado_nao_conta():
    # os nao_confirmado saem da conta: 1 cumpre em 1 requisito contável = 100
    assert relatorio("cumpre", "nao_confirmado", "nao_confirmado").score == 100


def test_score_sem_requisitos_contaveis_e_0():
    assert relatorio("nao_confirmado", "nao_confirmado").score == 0


def test_score_sem_requisitos_e_0():
    assert relatorio().score == 0


def test_score_aparece_no_dicionario_do_relatorio():
    # o score é guardado na base de dados a partir do model_dump, por isso tem de lá estar
    dados = relatorio("cumpre", "falta").model_dump()
    assert dados["score"] == 50


def test_o_modelo_nao_consegue_impor_um_score():
    # se o modelo entregar um score no relatório, é ignorado: vale o calculado a partir dos estados
    dados = relatorio("falta", "falta").model_dump()
    dados["score"] = 99
    assert Relatorio.model_validate(dados).score == 0


# ---------- validadores do requisito ----------

@pytest.mark.parametrize("estado", ["cumpre", "parcial"])
def test_cumpre_e_parcial_exigem_evidencia(estado):
    with pytest.raises(ValidationError):
        Requisito(requisito="Python", estado=estado)


@pytest.mark.parametrize("estado", ["cumpre", "parcial"])
def test_evidencia_vazia_nao_conta(estado):
    with pytest.raises(ValidationError):
        Requisito(requisito="Python", estado=estado, evidencia="")


@pytest.mark.parametrize("estado", ["falta", "nao_confirmado"])
def test_falta_e_nao_confirmado_aceitam_ficar_sem_evidencia(estado):
    assert Requisito(requisito="Docker", estado=estado).evidencia is None


def test_estado_desconhecido_e_recusado():
    with pytest.raises(ValidationError):
        Requisito(requisito="Python", estado="talvez")


# ---------- requisitos repetidos ----------

def test_requisito_repetido_e_recusado():
    with pytest.raises(ValidationError):
        Relatorio(
            vaga="Programador",
            empresa="Empresa",
            requisitos=[requisito("falta", "Python"), requisito("falta", "Python")],
            resumo_empresa="x",
            sugestoes=[],
        )


def test_requisito_repetido_ignora_maiusculas_e_espacos():
    with pytest.raises(ValidationError):
        Relatorio(
            vaga="Programador",
            empresa="Empresa",
            requisitos=[requisito("falta", "Python"), requisito("falta", "  python ")],
            resumo_empresa="x",
            sugestoes=[],
        )

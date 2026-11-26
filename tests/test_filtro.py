import pytest

from filtro import (
    anos_exigidos,
    avaliar_localizacao,
    classificar_senioridade,
    filtrar_vaga,
    normalizar,
    palavra_excluida,
)

# As preferências do perfil: Braga com qualquer regime, Porto só híbrido, e remoto em qualquer sítio.
PREFERENCIAS = {
    "localizacoes": [
        {"local": "Braga", "regimes": ["presencial", "hibrido", "remoto"], "prioridade": 1},
        {"local": "Porto", "regimes": ["hibrido"], "prioridade": 2},
        {"local": "qualquer local", "regimes": ["remoto"], "prioridade": 3},
    ]
}


def vaga(titulo="Software Engineer", descricao="", localizacoes=("Braga",), regime="hibrido"):
    """Uma vaga no formato que o recolher_itjobs devolve."""
    return {
        "titulo": titulo,
        "descricao": descricao,
        "localizacoes": list(localizacoes),
        "regime": regime,
    }


# ---------- normalizar ----------

def test_normalizar_tira_acentos_e_maiusculas():
    assert normalizar("Júnior") == "junior"
    assert normalizar("ESTÁGIO") == "estagio"


# ---------- anos de experiência ----------

@pytest.mark.parametrize(
    "descricao, esperado",
    [
        ("", 0),
        (None, 0),
        ("Procuramos alguém motivado.", 0),
        ("3 years of experience", 3),
        ("5+ years of experience", 5),
        ("2 anos de experiência", 2),
        # intervalos: conta o mínimo (foi um bug: lia o máximo)
        ("3-7 years of experience", 3),
        ("3–7 years of experience", 3),
        ("2–5+ years of experience", 2),
        ("3 e 5 anos de experiência", 3),
        # vários números: fica o maior pedido
        ("1 year with Python and 4 years with Java", 4),
        # "mais de 10 anos" é sobre a empresa, não sobre o candidato
        ("A empresa tem mais de 10 anos de mercado", 0),
        ("Over 15 years in the market", 0),
    ],
)
def test_anos_exigidos(descricao, esperado):
    assert anos_exigidos(vaga(descricao=descricao)) == esperado


# ---------- senioridade ----------

@pytest.mark.parametrize(
    "titulo, esperado",
    [
        ("Senior Python Developer", "senior"),
        ("Sénior Backend Engineer", "senior"),
        ("Sr. Developer", "senior"),
        ("Tech Lead", "senior"),
        ("Software Architect", "senior"),
        ("Programador Pleno", "senior"),
        ("Junior Developer", "junior"),
        ("Programador Júnior", "junior"),
        ("Estágio em Engenharia Informática", "junior"),
        ("Trainee Software", "junior"),
        ("Software Engineer", "indefinida"),
        # palavras inteiras: "Midnight" não é "mid", "Leadership" não é "lead"
        ("Midnight Developer", "indefinida"),
        ("Developer for Leadership Tools", "indefinida"),
    ],
)
def test_classificar_senioridade(titulo, esperado):
    assert classificar_senioridade(vaga(titulo=titulo)) == esperado


# ---------- palavras excluídas ----------

def test_palavra_excluida_encontra_funcoes_fora_da_area():
    assert palavra_excluida(vaga(titulo="Sales Executive")) == "sales"
    assert palavra_excluida(vaga(titulo="Técnico de Apoio ao Cliente")) == "apoio ao cliente"


def test_palavra_excluida_nao_apanha_titulos_tecnicos():
    assert palavra_excluida(vaga(titulo="Python Developer")) is None


# ---------- local e regime ----------

def test_braga_aceita_qualquer_regime():
    for regime in ("presencial", "hibrido", "remoto"):
        aceite, _, prioridade = avaliar_localizacao(vaga(localizacoes=["Braga"], regime=regime), PREFERENCIAS)
        assert aceite is True
        assert prioridade == 1


def test_porto_so_aceita_hibrido():
    aceite, _, prioridade = avaliar_localizacao(vaga(localizacoes=["Porto"], regime="hibrido"), PREFERENCIAS)
    assert (aceite, prioridade) == (True, 2)

    aceite, _, _ = avaliar_localizacao(vaga(localizacoes=["Porto"], regime="presencial"), PREFERENCIAS)
    assert aceite is False


def test_remoto_aceita_se_em_qualquer_local():
    aceite, _, prioridade = avaliar_localizacao(vaga(localizacoes=["Lisboa"], regime="remoto"), PREFERENCIAS)
    assert (aceite, prioridade) == (True, 3)


def test_lisboa_presencial_e_recusada():
    aceite, motivo, prioridade = avaliar_localizacao(vaga(localizacoes=["Lisboa"], regime="presencial"), PREFERENCIAS)
    assert aceite is False
    assert prioridade is None
    assert "fora das preferências" in motivo


def test_local_ignora_acentos_e_maiusculas():
    aceite, _, _ = avaliar_localizacao(vaga(localizacoes=["BRAGA"], regime="presencial"), PREFERENCIAS)
    assert aceite is True


def test_vaga_com_varios_locais_aceita_se_um_servir():
    aceite, _, _ = avaliar_localizacao(vaga(localizacoes=["Lisboa", "Braga"], regime="presencial"), PREFERENCIAS)
    assert aceite is True


def test_braganca_nao_e_braga():
    # "braga" está dentro de "braganca" como texto, mas são cidades diferentes
    aceite, _, _ = avaliar_localizacao(vaga(localizacoes=["Bragança"], regime="presencial"), PREFERENCIAS)
    assert aceite is False


# ---------- a decisão completa ----------

def test_vaga_senior_e_recusada():
    decisao = filtrar_vaga(vaga(titulo="Senior Python Developer"), PREFERENCIAS)
    assert decisao["aceite"] is False
    assert "sénior" in decisao["motivo"]


def test_funcao_fora_da_area_e_recusada():
    decisao = filtrar_vaga(vaga(titulo="Sales Engineer"), PREFERENCIAS)
    assert decisao["aceite"] is False
    assert "fora da área" in decisao["motivo"]


def test_pedir_muitos_anos_recusa_quando_o_titulo_nao_diz_o_nivel():
    decisao = filtrar_vaga(vaga(descricao="Requires 5 years of experience"), PREFERENCIAS)
    assert decisao["aceite"] is False
    assert "5 anos" in decisao["motivo"]


def test_titulo_junior_ganha_aos_anos_pedidos():
    # um título que diz júnior é de confiança, mesmo que o texto fale em anos
    decisao = filtrar_vaga(vaga(titulo="Junior Developer", descricao="3 years of experience"), PREFERENCIAS)
    assert decisao["aceite"] is True


def test_ate_dois_anos_passa():
    decisao = filtrar_vaga(vaga(descricao="2 years of experience"), PREFERENCIAS)
    assert decisao["aceite"] is True


def test_vaga_boa_e_aceite_com_a_prioridade_do_local():
    decisao = filtrar_vaga(vaga(titulo="Junior Python Developer", localizacoes=["Braga"], regime="hibrido"), PREFERENCIAS)
    assert decisao["aceite"] is True
    assert decisao["prioridade"] == 1


def test_local_fora_das_preferencias_e_recusada():
    decisao = filtrar_vaga(vaga(localizacoes=["Faro"], regime="presencial"), PREFERENCIAS)
    assert decisao["aceite"] is False

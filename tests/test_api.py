import anthropic
import httpx
import pytest
from fastapi.testclient import TestClient

import api
from ajudas import relatorio_valido


@pytest.fixture(autouse=True)
def analises_vazias(monkeypatch):
    """Cada teste começa sem análises pedidas, e não mexe nas dos outros."""
    monkeypatch.setattr(api, "ANALISES", {})


@pytest.fixture
def cliente():
    return TestClient(api.app)


# ---------- GET /saude ----------

def test_saude_responde_ok_sem_precisar_da_base_de_dados(cliente):
    resposta = cliente.get("/saude")
    assert resposta.status_code == 200
    assert resposta.json() == {"ok": True}


# ---------- POST /analises: validações ----------

@pytest.mark.parametrize("url", ["isto-nao-e-um-link", "ftp://servidor/vaga", "", "   "])
def test_pedir_analise_recusa_links_invalidos(cliente, url):
    resposta = cliente.post("/analises", json={"url": url})
    assert resposta.status_code == 400


def test_pedir_analise_sem_corpo_da_422(cliente):
    assert cliente.post("/analises").status_code == 422


def test_so_uma_analise_de_cada_vez(cliente):
    api.ANALISES["outra"] = {"estado": "a_analisar", "vaga_id": None, "mensagem": None}
    resposta = cliente.post("/analises", json={"url": "https://exemplo.com/vaga"})
    assert resposta.status_code == 409


def test_pode_pedir_outra_quando_a_anterior_ja_acabou(cliente, monkeypatch):
    monkeypatch.setattr(api, "analisar_em_segundo_plano", lambda analise_id, url: None)
    api.ANALISES["antiga"] = {"estado": "pronta", "vaga_id": 1, "mensagem": None}
    resposta = cliente.post("/analises", json={"url": "https://exemplo.com/vaga"})
    assert resposta.status_code == 200


# ---------- POST /analises e GET /analises/{id}: o ciclo completo, com o agente falso ----------

def test_pedir_analise_devolve_id_e_o_estado_fica_consultavel(cliente, monkeypatch):
    chamadas = []
    # o agente falso não faz nada: só regista que foi chamado
    monkeypatch.setattr(api, "analisar_em_segundo_plano", lambda analise_id, url: chamadas.append(url))

    resposta = cliente.post("/analises", json={"url": "  https://exemplo.com/vaga  "})
    analise_id = resposta.json()["id"]

    assert chamadas == ["https://exemplo.com/vaga"]  # o link chega sem espaços
    estado = cliente.get(f"/analises/{analise_id}").json()
    assert estado["estado"] == "a_analisar"


def test_analise_desconhecida_da_404(cliente):
    assert cliente.get("/analises/nao-existe").status_code == 404


# ---------- a função que corre em segundo plano ----------

def preparar(monkeypatch, correr):
    """Põe uma análise 'a_analisar' e substitui o agente e a base de dados por falsos."""
    gravacoes = {}

    def guardar_vaga_falso(*argumentos, **palavras):
        gravacoes["vaga"] = (argumentos, palavras)
        return 42  # o id que a base de dados devolveria

    def guardar_analise_falso(vaga_id, relatorio):
        gravacoes["analise"] = (vaga_id, relatorio.score)

    monkeypatch.setattr(api, "correr_agente", correr)
    monkeypatch.setattr(api, "guardar_vaga", guardar_vaga_falso)
    monkeypatch.setattr(api, "guardar_analise", guardar_analise_falso)
    api.ANALISES["a1"] = {"estado": "a_analisar", "vaga_id": None, "mensagem": None}
    return gravacoes


def test_analise_com_sucesso_fica_pronta_com_o_id_da_vaga(monkeypatch):
    gravacoes = preparar(monkeypatch, lambda tarefa: relatorio_valido())

    api.analisar_em_segundo_plano("a1", "https://exemplo.com/vaga")

    assert api.ANALISES["a1"]["estado"] == "pronta"
    assert api.ANALISES["a1"]["vaga_id"] == 42
    # a vaga é guardada como "manual", com o link pedido
    argumentos, palavras = gravacoes["vaga"]
    assert argumentos == ("Programador Python", "Empresa X", "https://exemplo.com/vaga")
    assert palavras["fonte"] == "manual"
    assert gravacoes["analise"] == (42, 100)


def test_a_tarefa_enviada_ao_agente_leva_o_link_e_o_utilizador(monkeypatch):
    recebidas = []

    def agente_falso(tarefa):
        recebidas.append(tarefa)
        return relatorio_valido()

    preparar(monkeypatch, agente_falso)
    api.analisar_em_segundo_plano("a1", "https://exemplo.com/vaga")

    assert "https://exemplo.com/vaga" in recebidas[0]
    assert api.GITHUB_UTILIZADOR in recebidas[0]


def test_agente_sem_relatorio_da_erro_e_nao_grava(monkeypatch):
    gravacoes = preparar(monkeypatch, lambda tarefa: None)

    api.analisar_em_segundo_plano("a1", "https://exemplo.com/vaga")

    assert api.ANALISES["a1"]["estado"] == "erro"
    assert "relatório válido" in api.ANALISES["a1"]["mensagem"]
    assert gravacoes == {}


def test_excecao_no_agente_da_erro_com_o_nome_do_erro(monkeypatch):
    def agente_a_falhar(tarefa):
        raise ValueError("falhou")

    preparar(monkeypatch, agente_a_falhar)
    api.analisar_em_segundo_plano("a1", "https://exemplo.com/vaga")

    assert api.ANALISES["a1"]["estado"] == "erro"
    assert "ValueError" in api.ANALISES["a1"]["mensagem"]


def test_chave_recusada_da_uma_mensagem_clara(monkeypatch):
    def agente_com_chave_ma(tarefa):
        resposta = httpx.Response(401, request=httpx.Request("POST", "https://api.anthropic.com"))
        raise anthropic.AuthenticationError("chave inválida", response=resposta, body=None)

    preparar(monkeypatch, agente_com_chave_ma)
    api.analisar_em_segundo_plano("a1", "https://exemplo.com/vaga")

    assert api.ANALISES["a1"]["estado"] == "erro"
    assert "ANTHROPIC_API_KEY" in api.ANALISES["a1"]["mensagem"]


# ---------- PUT /vagas/{id}/candidatura: validação (antes de chegar à base de dados) ----------

def test_estado_de_candidatura_invalido_da_422(cliente):
    resposta = cliente.put("/vagas/1/candidatura", json={"estado": "xpto"})
    assert resposta.status_code == 422


def test_candidatura_sem_estado_da_422(cliente):
    resposta = cliente.put("/vagas/1/candidatura", json={"notas": "só notas"})
    assert resposta.status_code == 422


def test_id_de_vaga_que_nao_e_numero_da_422(cliente):
    resposta = cliente.put("/vagas/abc/candidatura", json={"estado": "oferta"})
    assert resposta.status_code == 422

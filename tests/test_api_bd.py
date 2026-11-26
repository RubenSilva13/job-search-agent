import pytest
from fastapi.testclient import TestClient

import api
from ajudas import criar_vaga, criar_vaga_analisada, relatorio_valido
from base_de_dados import calcular_custo, guardar_analise, registar_execucao


@pytest.fixture
def cliente(bd):
    # o fixture "bd" garante a base de dados de teste, vazia, antes de cada teste
    return TestClient(api.app)


def titulos(resposta):
    return [vaga["titulo"] for vaga in resposta.json()]


# ---------- GET /vagas ----------

def test_lista_vazia_quando_nao_ha_vagas(cliente):
    assert cliente.get("/vagas").json() == []


def test_lista_ordena_por_score_e_so_traz_vagas_analisadas(cliente):
    criar_vaga_analisada("Meio", ("cumpre", "falta"))          # 50
    criar_vaga_analisada("Melhor", ("cumpre",))                # 100
    criar_vaga_analisada("Pior", ("falta",))                   # 0
    criar_vaga("Sem analise")

    resposta = cliente.get("/vagas")

    assert titulos(resposta) == ["Melhor", "Meio", "Pior"]
    assert [vaga["score"] for vaga in resposta.json()] == [100, 50, 0]


def test_lista_usa_so_a_analise_mais_recente_de_cada_vaga(cliente):
    vaga_id = criar_vaga("Reanalisada")
    guardar_analise(vaga_id, relatorio_valido(("falta",)))      # 0, a mais antiga
    guardar_analise(vaga_id, relatorio_valido(("cumpre",)))     # 100, a mais recente

    vagas = cliente.get("/vagas").json()

    assert len(vagas) == 1
    assert vagas[0]["score"] == 100


def test_lista_traz_os_campos_que_o_painel_usa(cliente):
    criar_vaga_analisada("Vaga A")

    vaga = cliente.get("/vagas").json()[0]

    for campo in ("id", "titulo", "empresa", "localizacao", "regime", "url", "score", "candidatura_estado"):
        assert campo in vaga


# ---------- GET /vagas/{id} ----------

def test_detalhe_traz_o_relatorio_completo(cliente):
    vaga_id = criar_vaga_analisada("Vaga A", ("cumpre", "falta"))

    vaga = cliente.get(f"/vagas/{vaga_id}").json()

    assert vaga["titulo"] == "Vaga A"
    assert vaga["score"] == 50
    assert vaga["relatorio"]["resumo_empresa"] == "Uma empresa."
    assert [item["estado"] for item in vaga["relatorio"]["requisitos"]] == ["cumpre", "falta"]
    assert vaga["candidatura_estado"] is None


def test_detalhe_de_vaga_sem_analise_da_404(cliente):
    vaga_id = criar_vaga("Sem analise")
    assert cliente.get(f"/vagas/{vaga_id}").status_code == 404


def test_detalhe_de_vaga_inexistente_da_404(cliente):
    assert cliente.get("/vagas/999999").status_code == 404


# ---------- PUT /vagas/{id}/candidatura ----------

def test_candidatura_e_criada_e_aparece_no_detalhe_e_na_lista(cliente):
    vaga_id = criar_vaga_analisada("Vaga A")

    resposta = cliente.put(f"/vagas/{vaga_id}/candidatura", json={"estado": "entrevista", "notas": "falar com a Ana"})

    assert resposta.status_code == 200
    detalhe = cliente.get(f"/vagas/{vaga_id}").json()
    assert detalhe["candidatura_estado"] == "entrevista"
    assert detalhe["candidatura_notas"] == "falar com a Ana"
    assert cliente.get("/vagas").json()[0]["candidatura_estado"] == "entrevista"


def test_candidatura_de_vaga_inexistente_da_404(cliente):
    resposta = cliente.put("/vagas/999999/candidatura", json={"estado": "oferta"})
    assert resposta.status_code == 404


def test_so_existe_uma_candidatura_por_vaga(cliente):
    vaga_id = criar_vaga_analisada("Vaga A")

    cliente.put(f"/vagas/{vaga_id}/candidatura", json={"estado": "por_candidatar"})
    cliente.put(f"/vagas/{vaga_id}/candidatura", json={"estado": "candidatado"})

    # o segundo pedido atualiza a mesma candidatura, em vez de criar outra (e de dar erro)
    assert cliente.get(f"/vagas/{vaga_id}").json()["candidatura_estado"] == "candidatado"


def test_data_da_candidatura_fica_preenchida_ao_candidatar(cliente):
    vaga_id = criar_vaga_analisada("Vaga A")

    resposta = cliente.put(f"/vagas/{vaga_id}/candidatura", json={"estado": "candidatado"})

    assert resposta.json()["data_candidatura"] is not None


def test_por_candidatar_ainda_nao_tem_data(cliente):
    vaga_id = criar_vaga_analisada("Vaga A")

    resposta = cliente.put(f"/vagas/{vaga_id}/candidatura", json={"estado": "por_candidatar"})

    assert resposta.json()["data_candidatura"] is None


def test_a_data_aparece_quando_a_vaga_passa_a_candidatado(cliente):
    vaga_id = criar_vaga_analisada("Vaga A")

    cliente.put(f"/vagas/{vaga_id}/candidatura", json={"estado": "por_candidatar"})
    resposta = cliente.put(f"/vagas/{vaga_id}/candidatura", json={"estado": "candidatado"})

    assert resposta.json()["data_candidatura"] is not None


def test_a_data_mantem_se_quando_o_estado_avanca(cliente):
    vaga_id = criar_vaga_analisada("Vaga A")

    data = cliente.put(f"/vagas/{vaga_id}/candidatura", json={"estado": "candidatado"}).json()["data_candidatura"]
    depois = cliente.put(f"/vagas/{vaga_id}/candidatura", json={"estado": "entrevista"}).json()

    assert depois["data_candidatura"] == data


def test_notas_vazias_apagam_as_notas(cliente):
    vaga_id = criar_vaga_analisada("Vaga A")

    cliente.put(f"/vagas/{vaga_id}/candidatura", json={"estado": "candidatado", "notas": "uma nota"})
    cliente.put(f"/vagas/{vaga_id}/candidatura", json={"estado": "candidatado", "notas": None})

    assert cliente.get(f"/vagas/{vaga_id}").json()["candidatura_notas"] is None


def test_apagar_a_vaga_apaga_a_candidatura(cliente):
    from base_de_dados import abrir_ligacao

    vaga_id = criar_vaga_analisada("Vaga A")
    cliente.put(f"/vagas/{vaga_id}/candidatura", json={"estado": "candidatado"})

    with abrir_ligacao() as ligacao:
        ligacao.execute("DELETE FROM vagas WHERE id = %s", (vaga_id,))
        quantas = ligacao.execute("SELECT count(*) FROM candidaturas").fetchone()[0]

    assert quantas == 0


# ---------- GET /custos ----------

def test_custos_sem_execucoes(cliente):
    custos = cliente.get("/custos").json()

    assert custos["resumo"]["execucoes"] == 0
    assert custos["por_dia"] == []
    assert custos["ferramentas"] == []
    assert custos["mais_caras"] == []


def test_custos_somam_as_execucoes(cliente):
    vaga_id = criar_vaga_analisada("Vaga A")
    barata = [
        {"tipo": "modelo", "duracao_ms": 1000, "tokens_entrada": 10_000, "tokens_saida": 500},
        {"tipo": "ferramenta", "nome": "ler_portfolio", "duracao_ms": 3000},
    ]
    cara = [
        {"tipo": "modelo", "duracao_ms": 2000, "tokens_entrada": 100_000, "tokens_saida": 5_000},
        {"tipo": "ferramenta", "nome": "ler_portfolio", "duracao_ms": 5000},
        {"tipo": "ferramenta", "nome": "pesquisar_web", "duracao_ms": 1000, "erro": "Erro: sem rede"},
    ]
    registar_execucao("claude-haiku-5-5", "ok", 4000, barata, vaga_id)
    registar_execucao("claude-haiku-5-5", "erro", 8000, cara)

    custos = cliente.get("/custos").json()

    resumo = custos["resumo"]
    assert resumo["execucoes"] == 2
    assert (resumo["ok"], resumo["sem_relatorio"], resumo["erro"]) == (1, 0, 1)
    assert resumo["tokens_entrada"] == 110_000
    assert resumo["tokens_saida"] == 5_500
    esperado = calcular_custo("claude-haiku-5-5", 110_000, 5_500)
    assert resumo["custo_total"] == pytest.approx(esperado)

    # as ferramentas, das mais lentas para as mais rápidas (média: ler_portfolio 4000, pesquisar_web 1000)
    assert [item["nome"] for item in custos["ferramentas"]] == ["ler_portfolio", "pesquisar_web"]
    assert custos["ferramentas"][0]["chamadas"] == 2
    assert custos["ferramentas"][1]["erros"] == 1

    # onde vai o tempo: 3000 + 5000 + 1000 de ferramentas, e 1000 + 2000 de modelo
    tempos = {item["tipo"]: item["total_ms"] for item in custos["tempos"]}
    assert tempos == {"ferramenta": 9000, "modelo": 3000}

    # a mais cara primeiro; a que tem vaga mostra o título e a outra "(sem vaga)"
    assert [item["vaga"] for item in custos["mais_caras"]] == ["(sem vaga)", "Vaga A"]
    assert len(custos["por_dia"]) == 1
    assert custos["por_dia"][0]["execucoes"] == 2

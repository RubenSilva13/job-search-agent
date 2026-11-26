from datetime import datetime

import pytest
from psycopg.rows import dict_row

from ajudas import criar_vaga, criar_vaga_analisada, relatorio_valido
from base_de_dados import (
    abrir_ligacao,
    calcular_custo,
    guardar_analise,
    registar_execucao,
    vagas_por_analisar,
)


def ler(consulta, parametros=()):
    """Corre uma consulta na base de dados de teste e devolve as linhas como dicionários."""
    with abrir_ligacao() as ligacao:
        return ligacao.cursor(row_factory=dict_row).execute(consulta, parametros).fetchall()


# ---------- calcular_custo (não precisa de base de dados) ----------

def test_custo_do_haiku():
    # preços do config.py: 0.10 $ por milhão de tokens de entrada e 0.50 $ de saída
    assert calcular_custo("claude-haiku-5-5", 1_000_000, 1_000_000) == pytest.approx(0.60)


def test_custo_de_modelo_desconhecido_e_none():
    assert calcular_custo("modelo-que-nao-existe", 1000, 1000) is None


# ---------- guardar_vaga ----------

def test_guardar_vaga_devolve_o_id(bd):
    assert criar_vaga("Vaga A") > 0


def test_mesmo_url_nao_cria_outra_vaga(bd):
    primeiro = criar_vaga("Vaga A", url="https://exemplo.com/a")
    segundo = criar_vaga("Vaga A com outro titulo", url="https://exemplo.com/a")

    assert segundo == primeiro
    vagas = ler("SELECT titulo FROM vagas")
    assert len(vagas) == 1
    assert vagas[0]["titulo"] == "Vaga A com outro titulo"


def test_guardar_outra_vez_nao_apaga_o_que_ja_la_estava(bd):
    # o recolhedor guarda a data, o regime e a decisão do filtro; o agente depois guarda só o título
    criar_vaga("Vaga A", url="https://exemplo.com/a", regime="hibrido", aceite=True,
               motivo_filtro="Braga", publicada_em=datetime(2026, 11, 1))
    criar_vaga("Vaga A", url="https://exemplo.com/a")

    vaga = ler("SELECT regime, aceite, motivo_filtro, publicada_em FROM vagas")[0]
    assert vaga["regime"] == "hibrido"
    assert vaga["aceite"] is True
    assert vaga["motivo_filtro"] == "Braga"
    assert vaga["publicada_em"] == datetime(2026, 11, 1)


def test_guardar_outra_vez_com_valor_novo_atualiza(bd):
    criar_vaga("Vaga A", url="https://exemplo.com/a", regime="hibrido")
    criar_vaga("Vaga A", url="https://exemplo.com/a", regime="remoto")

    assert ler("SELECT regime FROM vagas")[0]["regime"] == "remoto"


# ---------- guardar_analise ----------

def test_guardar_analise_grava_o_score_e_o_relatorio_com_o_score(bd):
    vaga_id = criar_vaga("Vaga A")
    guardar_analise(vaga_id, relatorio_valido(("cumpre", "falta")))

    analise = ler("SELECT score, relatorio FROM analises")[0]
    assert analise["score"] == 50
    # o score também tem de estar dentro do JSON do relatório (é um computed_field)
    assert analise["relatorio"]["score"] == 50
    assert analise["relatorio"]["empresa"] == "Empresa X"


def test_apagar_a_vaga_apaga_as_analises(bd):
    vaga_id = criar_vaga_analisada("Vaga A")

    with abrir_ligacao() as ligacao:
        ligacao.execute("DELETE FROM vagas WHERE id = %s", (vaga_id,))

    assert ler("SELECT * FROM analises") == []


# ---------- vagas_por_analisar ----------

def test_por_analisar_so_traz_aceites_sem_analise(bd):
    criar_vaga("Aceite sem analise", aceite=True, publicada_em=datetime(2026, 11, 1))
    criar_vaga("Recusada", aceite=False, publicada_em=datetime(2026, 11, 2))
    criar_vaga("Nunca filtrada", publicada_em=datetime(2026, 11, 3))   # aceite fica a NULL
    vaga_analisada = criar_vaga("Aceite ja analisada", aceite=True, publicada_em=datetime(2026, 11, 4))
    guardar_analise(vaga_analisada, relatorio_valido())

    titulos = [vaga["titulo"] for vaga in vagas_por_analisar(10)]

    assert titulos == ["Aceite sem analise"]


def test_por_analisar_ordena_das_mais_recentes_e_respeita_o_limite(bd):
    criar_vaga("Antiga", aceite=True, publicada_em=datetime(2026, 10, 1))
    criar_vaga("Recente", aceite=True, publicada_em=datetime(2026, 11, 20))
    criar_vaga("Meio", aceite=True, publicada_em=datetime(2026, 11, 1))

    todas = [vaga["titulo"] for vaga in vagas_por_analisar(10)]
    duas = [vaga["titulo"] for vaga in vagas_por_analisar(2)]

    assert todas == ["Recente", "Meio", "Antiga"]
    assert duas == ["Recente", "Meio"]


# ---------- registar_execucao ----------

PASSOS = [
    {"tipo": "modelo", "duracao_ms": 1000, "tokens_entrada": 10_000, "tokens_saida": 500},
    {"tipo": "ferramenta", "nome": "ler_portfolio", "duracao_ms": 3000},
    {"tipo": "ferramenta", "nome": "pesquisar_web", "duracao_ms": 500, "erro": "Erro: sem rede"},
    {"tipo": "modelo", "duracao_ms": 2000, "tokens_entrada": 20_000, "tokens_saida": 1500},
]


def test_registar_execucao_soma_tokens_e_calcula_o_custo(bd):
    registar_execucao("claude-haiku-5-5", "ok", 7000, PASSOS)

    execucao = ler("SELECT * FROM execucoes")[0]
    assert execucao["tokens_entrada"] == 30_000
    assert execucao["tokens_saida"] == 2_000
    # só as chamadas ao modelo contam como "passos" da execução
    assert execucao["passos"] == 2
    assert execucao["resultado"] == "ok"
    assert float(execucao["custo_estimado"]) == pytest.approx(calcular_custo("claude-haiku-5-5", 30_000, 2_000))


def test_registar_execucao_guarda_cada_passo_por_ordem(bd):
    registar_execucao("claude-haiku-5-5", "ok", 7000, PASSOS)

    passos = ler("SELECT numero, tipo, nome, erro FROM passos ORDER BY numero")
    assert [passo["numero"] for passo in passos] == [1, 2, 3, 4]
    assert [passo["tipo"] for passo in passos] == ["modelo", "ferramenta", "ferramenta", "modelo"]
    assert passos[1]["nome"] == "ler_portfolio"
    assert passos[2]["erro"] == "Erro: sem rede"


def test_registar_execucao_de_modelo_sem_preco_fica_sem_custo(bd):
    registar_execucao("modelo-desconhecido", "erro", 100, PASSOS[:1])

    assert ler("SELECT custo_estimado FROM execucoes")[0]["custo_estimado"] is None


def test_resultado_invalido_e_recusado_pela_base_de_dados(bd):
    # o CHECK da tabela só aceita ok, sem_relatorio e erro
    with pytest.raises(Exception):
        registar_execucao("claude-haiku-5-5", "talvez", 100, PASSOS[:1])

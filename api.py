import uuid
from typing import Literal

import anthropic
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from psycopg.rows import dict_row
from pydantic import BaseModel

from agente import correr_agente
from base_de_dados import abrir_ligacao, guardar_analise, guardar_vaga
from config import GITHUB_UTILIZADOR

app = FastAPI(title="job-search-agent")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET", "PUT", "POST"],
    allow_headers=["Content-Type"],
)


# Os mesmos valores do CHECK da tabela candidaturas (schema.sql).
class PedidoCandidatura(BaseModel):
    estado: Literal["por_candidatar", "candidatado", "entrevista", "oferta", "recusada", "desistiu"]
    notas: str | None = None


CONSULTA_VAGAS = """
    SELECT DISTINCT ON (vagas.id)
        vagas.id,
        vagas.titulo,
        vagas.empresa,
        vagas.localizacao,
        vagas.regime,
        vagas.url,
        vagas.publicada_em,
        analises.score,
        analises.criada_em AS analisada_em,
        candidaturas.estado AS candidatura_estado
    FROM vagas
    JOIN analises ON analises.vaga_id = vagas.id
    LEFT JOIN candidaturas ON candidaturas.vaga_id = vagas.id
    ORDER BY vagas.id, analises.criada_em DESC
"""


@app.get("/saude")
def saude():
    """Diz que a API está viva. Não toca na base de dados: o Docker pergunta isto de poucos em poucos segundos."""
    return {"ok": True}


@app.get("/vagas")
def listar_vagas():
    """Vagas analisadas, da maior para a menor pontuação."""
    with abrir_ligacao() as ligacao:
        cursor = ligacao.cursor(row_factory=dict_row)
        cursor.execute(CONSULTA_VAGAS)
        vagas = cursor.fetchall()
    vagas.sort(key=lambda vaga: vaga["score"], reverse=True)
    return vagas


@app.get("/vagas/{vaga_id}")
def ler_vaga(vaga_id: int):
    """Uma vaga com o relatório completo da análise mais recente."""
    with abrir_ligacao() as ligacao:
        cursor = ligacao.cursor(row_factory=dict_row)
        cursor.execute(
            """
            SELECT vagas.id, vagas.titulo, vagas.empresa, vagas.localizacao,
                   vagas.regime, vagas.url, vagas.publicada_em,
                   analises.score, analises.relatorio, analises.criada_em AS analisada_em,
                   candidaturas.estado AS candidatura_estado,
                   candidaturas.notas AS candidatura_notas,
                   candidaturas.data_candidatura
            FROM vagas
            JOIN analises ON analises.vaga_id = vagas.id
            LEFT JOIN candidaturas ON candidaturas.vaga_id = vagas.id
            WHERE vagas.id = %s
            ORDER BY analises.criada_em DESC
            LIMIT 1
            """,
            (vaga_id,),
        )
        vaga = cursor.fetchone()
    if vaga is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada ou sem análise")
    return vaga


# Análises pedidas pelo painel: id -> {"estado", "vaga_id", "mensagem"}.
# Fica em memória: perde-se quando a API reinicia.
ANALISES = {}


class PedidoAnalise(BaseModel):
    url: str


def analisar_em_segundo_plano(analise_id: str, url: str):
    """Corre o agente sobre o link, grava a vaga e a análise, e atualiza o estado."""
    analise = ANALISES[analise_id]
    tarefa = f"Analisa esta vaga para o utilizador do GitHub {GITHUB_UTILIZADOR}: {url}"
    try:
        relatorio = correr_agente(tarefa)
        if relatorio is None:
            analise["estado"] = "erro"
            analise["mensagem"] = "O agente não conseguiu entregar um relatório válido."
            return
        vaga_id = guardar_vaga(
            relatorio.vaga,
            relatorio.empresa,
            url,
            localizacao=relatorio.localizacao,
            fonte="manual",
        )
        guardar_analise(vaga_id, relatorio)
        analise["vaga_id"] = vaga_id
        analise["estado"] = "pronta"
    except anthropic.AuthenticationError:
        analise["estado"] = "erro"
        analise["mensagem"] = "A chave da API da Anthropic foi recusada. Verifica a ANTHROPIC_API_KEY."
    except Exception as erro:
        analise["estado"] = "erro"
        analise["mensagem"] = f"A análise falhou ({type(erro).__name__})."


@app.post("/analises")
def pedir_analise(pedido: PedidoAnalise, tarefas: BackgroundTasks):
    """Arranca a análise de uma vaga a partir do link. Responde logo; a análise corre em segundo plano."""
    url = pedido.url.strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="O link tem de começar por http:// ou https://")

    # uma de cada vez: cada análise gasta dinheiro da chave da Anthropic
    if any(analise["estado"] == "a_analisar" for analise in ANALISES.values()):
        raise HTTPException(status_code=409, detail="Já há uma análise a decorrer. Espera que acabe.")

    analise_id = uuid.uuid4().hex
    ANALISES[analise_id] = {"estado": "a_analisar", "vaga_id": None, "mensagem": None}
    tarefas.add_task(analisar_em_segundo_plano, analise_id, url)
    return {"id": analise_id}


@app.get("/analises/{analise_id}")
def ler_analise(analise_id: str):
    """Como vai uma análise pedida: a_analisar, pronta (com vaga_id) ou erro (com mensagem)."""
    analise = ANALISES.get(analise_id)
    if analise is None:
        raise HTTPException(status_code=404, detail="Análise não encontrada")
    return analise


@app.get("/custos")
def ler_custos():
    """Custos e tempos das análises: as mesmas consultas do custos.py, em JSON."""
    with abrir_ligacao() as ligacao:
        cursor = ligacao.cursor(row_factory=dict_row)

        cursor.execute(
            "SELECT count(*) AS execucoes, "
            "count(*) FILTER (WHERE resultado = 'ok') AS ok, "
            "count(*) FILTER (WHERE resultado = 'sem_relatorio') AS sem_relatorio, "
            "count(*) FILTER (WHERE resultado = 'erro') AS erro, "
            "coalesce(sum(tokens_entrada), 0) AS tokens_entrada, "
            "coalesce(sum(tokens_saida), 0) AS tokens_saida, "
            "sum(custo_estimado) AS custo_total, "
            "avg(custo_estimado) AS custo_medio, "
            "avg(duracao_ms) AS duracao_media_ms "
            "FROM execucoes"
        )
        resumo = cursor.fetchone()

        cursor.execute(
            "SELECT iniciada_em::date AS dia, count(*) AS execucoes, sum(custo_estimado) AS custo "
            "FROM execucoes GROUP BY 1 ORDER BY 1 DESC LIMIT 7"
        )
        por_dia = cursor.fetchall()

        cursor.execute(
            "SELECT nome, count(*) AS chamadas, avg(duracao_ms) AS media_ms, "
            "max(duracao_ms) AS max_ms, count(erro) AS erros "
            "FROM passos WHERE tipo = 'ferramenta' "
            "GROUP BY nome ORDER BY avg(duracao_ms) DESC"
        )
        ferramentas = cursor.fetchall()

        cursor.execute("SELECT tipo, sum(duracao_ms) AS total_ms FROM passos GROUP BY tipo")
        tempos = cursor.fetchall()

        cursor.execute(
            "SELECT coalesce(v.titulo, '(sem vaga)') AS vaga, e.custo_estimado, "
            "e.tokens_entrada, e.tokens_saida, e.duracao_ms "
            "FROM execucoes e LEFT JOIN vagas v ON v.id = e.vaga_id "
            "ORDER BY e.custo_estimado DESC NULLS LAST LIMIT 3"
        )
        mais_caras = cursor.fetchall()

    return {
        "resumo": resumo,
        "por_dia": por_dia,
        "ferramentas": ferramentas,
        "tempos": tempos,
        "mais_caras": mais_caras,
    }


@app.put("/vagas/{vaga_id}/candidatura")
def guardar_candidatura(vaga_id: int, pedido: PedidoCandidatura):
    """Cria ou atualiza a candidatura de uma vaga (uma por vaga)."""
    with abrir_ligacao() as ligacao:
        cursor = ligacao.cursor(row_factory=dict_row)
        cursor.execute("SELECT 1 FROM vagas WHERE id = %s", (vaga_id,))
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")
        # Upsert: insere, ou, se a vaga já tem candidatura, atualiza.
        # A data só é preenchida quando o estado passa a 'candidatado' e ainda não havia data.
        cursor.execute(
            """
            INSERT INTO candidaturas (vaga_id, estado, notas, data_candidatura)
            VALUES (%s, %s, %s, CASE WHEN %s = 'candidatado' THEN CURRENT_DATE END)
            ON CONFLICT (vaga_id) DO UPDATE SET
                estado = EXCLUDED.estado,
                notas = EXCLUDED.notas,
                data_candidatura = COALESCE(
                    candidaturas.data_candidatura,
                    CASE WHEN EXCLUDED.estado = 'candidatado' THEN CURRENT_DATE END
                )
            RETURNING estado, notas, data_candidatura
            """,
            (vaga_id, pedido.estado, pedido.notas, pedido.estado),
        )
        candidatura = cursor.fetchone()
    return candidatura

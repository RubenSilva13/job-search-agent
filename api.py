from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from psycopg.rows import dict_row

from base_de_dados import abrir_ligacao

app = FastAPI(title="job-search-agent")

# O Next.js corre noutra porta (3000). O browser só deixa a página chamar esta API
# se a API disser que aceita pedidos vindos dessa origem.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET"],
)

# Uma linha por vaga, com a análise mais recente (DISTINCT ON fica com a primeira
# linha de cada vaga, e o ORDER BY põe a análise mais recente primeiro).
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
        analises.criada_em AS analisada_em
    FROM vagas
    JOIN analises ON analises.vaga_id = vagas.id
    ORDER BY vagas.id, analises.criada_em DESC
"""


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
                   analises.score, analises.relatorio, analises.criada_em AS analisada_em
            FROM vagas
            JOIN analises ON analises.vaga_id = vagas.id
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

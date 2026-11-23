"""Escolhe as vagas da avaliação e prepara os ficheiros para as classificares à mão.

Gera dois ficheiros nesta pasta:
- casos.md: o que se lê (cada vaga com o link e o texto completo). Não vai para o GitHub.
- notas.csv: o que se preenche (a coluna 'nota'). Nunca é reescrito se já existir.

A escolha usa uma semente fixa: correr outra vez dá exatamente as mesmas vagas.
Não olha para nenhum score do agente, para não o favorecer.
"""
import csv
import os
import random
import sys

PASTA = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(PASTA))

from psycopg.rows import dict_row
from base_de_dados import abrir_ligacao

TOTAL_DE_CASOS = 24
SEMENTE = 42
PALAVRAS_JUNIOR = ["junior", "júnior", "recém", "recem", "estágio", "estagio"]


def ler_vagas_aceites():
    """As vagas que passaram o filtro, que são as que o agente analisa na prática."""
    with abrir_ligacao() as ligacao:
        with ligacao.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                "SELECT id, titulo, empresa, localizacao, regime, url, publicada_em, descricao "
                "FROM vagas WHERE aceite AND descricao IS NOT NULL ORDER BY id"
            )
            return cursor.fetchall()


def e_obrigatoria(vaga):
    """Vagas explicitamente júnior ou em Braga: entram sempre, para a amostra ter casos que podem servir."""
    titulo = vaga["titulo"].lower()
    local = (vaga["localizacao"] or "").lower()
    return any(palavra in titulo for palavra in PALAVRAS_JUNIOR) or "braga" in local


def escolher(vagas):
    obrigatorias = [vaga for vaga in vagas if e_obrigatoria(vaga)][:TOTAL_DE_CASOS]
    outras = [vaga for vaga in vagas if not e_obrigatoria(vaga)]

    sorteador = random.Random(SEMENTE)
    sorteadas = sorteador.sample(outras, TOTAL_DE_CASOS - len(obrigatorias))

    escolhidas = obrigatorias + sorteadas
    sorteador.shuffle(escolhidas)           # ordem misturada: a posição não denuncia nada
    return escolhidas, len(obrigatorias), len(sorteadas)


def cerca_para(texto):
    """Uma cerca de crases mais comprida do que qualquer sequência de crases dentro do texto."""
    maior = 0
    atual = 0
    for letra in texto:
        if letra == "`":
            atual += 1
            maior = max(maior, atual)
        else:
            atual = 0
    return "`" * max(3, maior + 1)


def escrever_casos_md(casos):
    linhas = [
        "# Avaliação: classifica estas vagas",
        "",
        "Para cada vaga, pergunta-te: **se estivesses a procurar emprego hoje, candidatavas-te?**",
        "",
        "- `serve`: sim, candidatava-me sem hesitar",
        "- `talvez`: candidatava-me, mas com dúvidas, ou faltam-me coisas importantes",
        "- `nao`: não me candidatava",
        "",
        "Escreve a nota na coluna `nota` do ficheiro `notas.csv`, na linha com o mesmo `id`.",
        "Decide pelo teu julgamento sobre a vaga e o teu perfil. **Não corras o agente nem leias relatórios dele** até acabares.",
        "",
        "| # | id | vaga | empresa | local | regime |",
        "|---|---|---|---|---|---|",
    ]
    for numero, vaga in enumerate(casos, start=1):
        linhas.append(
            f"| {numero} | {vaga['id']} | {vaga['titulo'][:60]} | {vaga['empresa'][:30]} | "
            f"{vaga['localizacao'] or '-'} | {vaga['regime'] or '-'} |"
        )

    for numero, vaga in enumerate(casos, start=1):
        cerca = cerca_para(vaga["descricao"])
        linhas += [
            "",
            f"## Caso {numero} · id {vaga['id']} · {vaga['titulo']} ({vaga['empresa']})",
            "",
            f"- Local: {vaga['localizacao'] or 'não indicado'} | Regime: {vaga['regime'] or 'não indicado'}",
            f"- Publicada em: {vaga['publicada_em']}",
            f"- Link: {vaga['url']}",
            "",
            cerca,
            vaga["descricao"],
            cerca,
        ]

    with open(os.path.join(PASTA, "casos.md"), "w", encoding="utf-8") as ficheiro:
        ficheiro.write("\n".join(linhas) + "\n")


def escrever_notas_csv(casos):
    caminho = os.path.join(PASTA, "notas.csv")
    if os.path.exists(caminho):
        print("notas.csv já existe: não foi alterado, para não perderes as tuas notas.")
        return

    with open(caminho, "w", encoding="utf-8-sig", newline="") as ficheiro:
        escritor = csv.writer(ficheiro)
        escritor.writerow(["id", "vaga", "empresa", "nota"])
        for vaga in casos:
            escritor.writerow([vaga["id"], vaga["titulo"], vaga["empresa"], ""])


if __name__ == "__main__":
    vagas = ler_vagas_aceites()
    casos, obrigatorias, sorteadas = escolher(vagas)

    escrever_casos_md(casos)
    escrever_notas_csv(casos)

    print(f"{len(vagas)} vagas aceites disponíveis.")
    print(f"{len(casos)} casos escolhidos: {obrigatorias} obrigatórios (júnior ou Braga) e {sorteadas} sorteados (semente {SEMENTE}).")
    print(f"{len(vagas) - len(casos)} ficam de reserva para um conjunto de teste, mais tarde.")

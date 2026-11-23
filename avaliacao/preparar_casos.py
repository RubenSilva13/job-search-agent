"""Escolhe as vagas da avaliação e prepara os ficheiros para as classificares à mão.

Dois modos:
    python avaliacao/preparar_casos.py           # o conjunto principal (24 vagas)
    python avaliacao/preparar_casos.py --teste   # o conjunto de teste (vagas que nunca viste nem o agente)

Cada modo gera dois ficheiros nesta pasta:
- casos.md / casos_teste.md: o que se lê (cada vaga com o link e o texto completo). Não vão para o GitHub.
- notas.csv / notas_teste.csv: o que se preenche. Nunca são reescritos se já existirem.

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
TOTAL_DE_TESTE = 15
SEMENTE = 42
PALAVRAS_JUNIOR = ["junior", "júnior", "recém", "recem", "estágio", "estagio"]

CAMPOS = "id, titulo, empresa, localizacao, regime, url, publicada_em, descricao"


def ler_vagas_aceites():
    """As vagas que passaram o filtro, que são as que o agente analisa na prática."""
    with abrir_ligacao() as ligacao:
        with ligacao.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                f"SELECT {CAMPOS} FROM vagas WHERE aceite AND descricao IS NOT NULL ORDER BY id"
            )
            return cursor.fetchall()


def ler_ids_do_ficheiro(nome_do_ficheiro):
    """Os ids das vagas, pela ordem em que estão nas notas."""
    with open(os.path.join(PASTA, nome_do_ficheiro), encoding="utf-8-sig", newline="") as ficheiro:
        return [int(linha["id"]) for linha in csv.DictReader(ficheiro)]


def ler_vagas_por_ids(ids):
    """As vagas com estes ids, pela mesma ordem dos ids."""
    with abrir_ligacao() as ligacao:
        with ligacao.cursor(row_factory=dict_row) as cursor:
            cursor.execute(f"SELECT {CAMPOS} FROM vagas WHERE id = ANY(%s)", (ids,))
            por_id = {vaga["id"]: vaga for vaga in cursor.fetchall()}
    return [por_id[id_vaga] for id_vaga in ids]


def existe(nome_do_ficheiro):
    return os.path.exists(os.path.join(PASTA, nome_do_ficheiro))


def ler_vagas_nunca_analisadas(ids_a_excluir):
    """Vagas aceites que o agente nunca analisou: nem tu nem ele as viram."""
    with abrir_ligacao() as ligacao:
        with ligacao.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                f"SELECT {CAMPOS} FROM vagas "
                "WHERE aceite AND descricao IS NOT NULL "
                "AND NOT (id = ANY(%s)) "
                "AND NOT EXISTS (SELECT 1 FROM analises WHERE analises.vaga_id = vagas.id) "
                "ORDER BY id",
                (ids_a_excluir,),
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


def escolher_teste(vagas):
    """No conjunto de teste não há vagas obrigatórias: são todas as que o agente nunca viu."""
    sorteador = random.Random(SEMENTE)
    escolhidas = list(vagas)
    if len(escolhidas) > TOTAL_DE_TESTE:
        escolhidas = sorteador.sample(escolhidas, TOTAL_DE_TESTE)
    sorteador.shuffle(escolhidas)
    return escolhidas


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


INSTRUCOES_PRINCIPAL = [
    "Para cada vaga, pergunta-te: **se estivesses a procurar emprego hoje, candidatavas-te?**",
    "",
    "- `serve`: sim, candidatava-me sem hesitar",
    "- `talvez`: candidatava-me, mas com dúvidas, ou faltam-me coisas importantes",
    "- `nao`: não me candidatava",
    "",
    "Escreve a nota na coluna `nota` do ficheiro `notas.csv`, na linha com o mesmo `id`.",
]

INSTRUCOES_TESTE = [
    "Cada vaga tem **duas perguntas**, que são diferentes. Responde às duas, separadamente.",
    "",
    "**1. `nota`: se estivesses a procurar emprego hoje, candidatavas-te?** (inclui o interesse e",
    "a vontade de aprender o que falta)",
    "",
    "- `serve`: sim, candidatava-me sem hesitar",
    "- `talvez`: candidatava-me, mas com dúvidas",
    "- `nao`: não me candidatava",
    "",
    "**2. `cobertura`: quanto do que a vaga pede já está PROVADO no teu GitHub ou no teu perfil?**",
    "Ignora o interesse e o que aprenderias. Só conta o que já tens, escrito num README ou no perfil.",
    "",
    "- `alta`: quase tudo o que pede, já tens",
    "- `media`: tens cerca de metade",
    "- `baixa`: tens pouco do que pede",
    "",
    "Escreve as duas na linha da vaga em `notas_teste.csv` (colunas `nota` e `cobertura`).",
]


def escrever_casos_md(casos, nome_do_ficheiro, instrucoes):
    linhas = ["# Avaliação: classifica estas vagas", ""] + instrucoes + [
        "",
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

    with open(os.path.join(PASTA, nome_do_ficheiro), "w", encoding="utf-8") as ficheiro:
        ficheiro.write("\n".join(linhas) + "\n")


def escrever_notas_csv(casos, nome_do_ficheiro, colunas_a_preencher):
    caminho = os.path.join(PASTA, nome_do_ficheiro)
    if os.path.exists(caminho):
        print(f"{nome_do_ficheiro} já existe: não foi alterado, para não perderes as tuas notas.")
        return

    with open(caminho, "w", encoding="utf-8-sig", newline="") as ficheiro:
        escritor = csv.writer(ficheiro)
        escritor.writerow(["id", "vaga", "empresa"] + colunas_a_preencher)
        for vaga in casos:
            escritor.writerow([vaga["id"], vaga["titulo"], vaga["empresa"]] + [""] * len(colunas_a_preencher))


if __name__ == "__main__":
    # Se as notas já existem, o conjunto está fechado: lê-se dali e NÃO se escolhe outra vez.
    # A base de dados vai ganhando vagas, e uma nova escolha daria outro conjunto.
    if "--teste" in sys.argv:
        if existe("notas_teste.csv"):
            casos = ler_vagas_por_ids(ler_ids_do_ficheiro("notas_teste.csv"))
            print(f"notas_teste.csv já existe: {len(casos)} casos lidos dali, sem escolher outra vez.")
        else:
            candidatas = ler_vagas_nunca_analisadas(ler_ids_do_ficheiro("notas.csv"))
            casos = escolher_teste(candidatas)
            print(f"{len(candidatas)} vagas aceites que o agente nunca analisou (fora do conjunto principal).")
            print(f"{len(casos)} casos de teste escolhidos (semente {SEMENTE}).")

        escrever_casos_md(casos, "casos_teste.md", INSTRUCOES_TESTE)
        escrever_notas_csv(casos, "notas_teste.csv", ["nota", "cobertura"])
    else:
        if existe("notas.csv"):
            casos = ler_vagas_por_ids(ler_ids_do_ficheiro("notas.csv"))
            print(f"notas.csv já existe: {len(casos)} casos lidos dali, sem escolher outra vez.")
        else:
            vagas = ler_vagas_aceites()
            casos, obrigatorias, sorteadas = escolher(vagas)
            print(f"{len(vagas)} vagas aceites disponíveis.")
            print(f"{len(casos)} casos escolhidos: {obrigatorias} obrigatórios (júnior ou Braga) e {sorteadas} sorteados (semente {SEMENTE}).")

        escrever_casos_md(casos, "casos.md", INSTRUCOES_PRINCIPAL)
        escrever_notas_csv(casos, "notas.csv", ["nota"])

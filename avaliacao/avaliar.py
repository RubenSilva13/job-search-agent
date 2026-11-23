"""Avalia se o score do agente concorda com as notas dadas à mão.

Uso:
    python avaliacao/avaliar.py --so 2 --reps 1   # piloto com 2 casos (gasta chamadas pagas)
    python avaliacao/avaliar.py --reps 3          # a avaliação completa (gasta chamadas pagas)
    python avaliacao/avaliar.py --resumo          # só calcula as métricas, não gasta nada

Cada análise é escrita em resultados.jsonl logo que acaba. Se o programa for interrompido,
volta a correr só o que falta. As falhas (rede, API) vão para erros.jsonl e são repetidas.
"""
import argparse
import csv
import json
import os
import random
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

PASTA = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(PASTA))

import anthropic
from psycopg.rows import dict_row
from agente import ciclo_do_agente
from analise_diaria import montar_tarefa
from base_de_dados import abrir_ligacao, calcular_custo
from config import MODELO

CAMINHO_NOTAS = os.path.join(PASTA, "notas.csv")
CAMINHO_RESULTADOS = os.path.join(PASTA, "resultados.jsonl")
CAMINHO_ERROS = os.path.join(PASTA, "erros.jsonl")
CAMINHO_RESUMO = os.path.join(PASTA, "resumo.md")

VALOR_DA_NOTA = {"serve": 2, "talvez": 1, "nao": 0}
trinco = threading.Lock()


# ---------------------------------------------------------------------------
# Ler os casos
# ---------------------------------------------------------------------------

def ler_notas():
    """Devolve a lista de (id, nota) pela ordem do ficheiro, a validar cada nota."""
    notas = []
    with open(CAMINHO_NOTAS, encoding="utf-8-sig", newline="") as ficheiro:
        for linha in csv.DictReader(ficheiro):
            nota = linha["nota"].strip().lower()
            if nota not in VALOR_DA_NOTA:
                raise ValueError(f"nota inválida na vaga {linha['id']}: '{linha['nota']}'")
            notas.append((int(linha["id"]), nota))
    return notas


def ler_vagas(ids):
    with abrir_ligacao() as ligacao:
        with ligacao.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                "SELECT id, titulo, empresa, url, localizacao, regime, descricao "
                "FROM vagas WHERE id = ANY(%s)", (ids,)
            )
            return {vaga["id"]: vaga for vaga in cursor.fetchall()}


def ler_linhas(caminho):
    if not os.path.exists(caminho):
        return []
    with open(caminho, encoding="utf-8") as ficheiro:
        return [json.loads(linha) for linha in ficheiro if linha.strip()]


def acrescentar_linha(caminho, linha):
    with trinco:
        with open(caminho, "a", encoding="utf-8") as ficheiro:
            ficheiro.write(json.dumps(linha, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Correr as análises
# ---------------------------------------------------------------------------

def analisar(vaga, repeticao):
    """Corre o ciclo do agente numa vaga. Devolve a linha de resultados, ou levanta a exceção."""
    passos = []
    inicio = time.perf_counter()
    relatorio = ciclo_do_agente(montar_tarefa(vaga), passos)
    duracao = time.perf_counter() - inicio

    chamadas = [passo for passo in passos if passo["tipo"] == "modelo"]
    tokens_entrada = sum(passo["tokens_entrada"] for passo in chamadas)
    tokens_saida = sum(passo["tokens_saida"] for passo in chamadas)

    linha = {
        "id": vaga["id"],
        "rep": repeticao,
        "status": "ok" if relatorio is not None else "sem_relatorio",
        "score": relatorio.score if relatorio is not None else None,
        "estados": dict(Counter(item.estado for item in relatorio.requisitos)) if relatorio else {},
        "modelo": MODELO,
        "chamadas_modelo": len(chamadas),
        "pesquisas_web": sum(1 for passo in passos if passo.get("nome") == "pesquisar_web"),
        "latencia_s": round(duracao, 1),
        "tokens_entrada": tokens_entrada,
        "tokens_saida": tokens_saida,
        "custo_usd": calcular_custo(MODELO, tokens_entrada, tokens_saida),
    }
    return linha


def correr(notas, reps, so, trabalhadores):
    if so:
        notas = notas[:so]

    vagas = ler_vagas([id_vaga for id_vaga, _ in notas])
    ja_feitos = {(linha["id"], linha["rep"]) for linha in ler_linhas(CAMINHO_RESULTADOS)}
    tarefas = [
        (vagas[id_vaga], repeticao)
        for id_vaga, _ in notas
        for repeticao in range(reps)
        if (id_vaga, repeticao) not in ja_feitos
    ]
    print(f"{len(notas)} casos x {reps} repetições: {len(ja_feitos)} já feitas, {len(tarefas)} por fazer.")

    feitas = 0
    with ThreadPoolExecutor(max_workers=trabalhadores) as pool:
        futuros = {pool.submit(analisar, vaga, repeticao): (vaga, repeticao) for vaga, repeticao in tarefas}

        for futuro in as_completed(futuros):
            vaga, repeticao = futuros[futuro]
            try:
                linha = futuro.result()
            except anthropic.AuthenticationError:
                # a chave foi recusada: vai falhar em todas, por isso pára-se já
                pool.shutdown(wait=False, cancel_futures=True)
                print("\nA chave da API foi recusada. Verifica a ANTHROPIC_API_KEY no .env.")
                sys.exit(1)
            except Exception as erro:
                # falha de infraestrutura: não é um resultado, fica à parte e repete-se na próxima vez
                acrescentar_linha(CAMINHO_ERROS, {
                    "id": vaga["id"], "rep": repeticao,
                    "falha": type(erro).__name__, "mensagem": str(erro)[:200],
                })
                print(f"  falhou: vaga {vaga['id']} rep {repeticao} ({type(erro).__name__})")
                continue

            acrescentar_linha(CAMINHO_RESULTADOS, linha)
            feitas += 1
            print(f"  [{feitas}/{len(tarefas)}] vaga {linha['id']} rep {repeticao}: "
                  f"score {linha['score']}, {linha['latencia_s']} s, ${linha['custo_usd']:.4f}")


# ---------------------------------------------------------------------------
# As métricas
# ---------------------------------------------------------------------------

def posicoes(valores):
    """A posição de cada valor na ordem crescente. Nos empates, a média das posições."""
    ordem = sorted(range(len(valores)), key=lambda i: valores[i])
    resultado = [0.0] * len(valores)
    inicio = 0
    while inicio < len(ordem):
        fim = inicio
        while fim + 1 < len(ordem) and valores[ordem[fim + 1]] == valores[ordem[inicio]]:
            fim += 1
        media = (inicio + fim) / 2 + 1
        for k in range(inicio, fim + 1):
            resultado[ordem[k]] = media
        inicio = fim + 1
    return resultado


def correlacao(a, b):
    n = len(a)
    media_a = sum(a) / n
    media_b = sum(b) / n
    cov = sum((x - media_a) * (y - media_b) for x, y in zip(a, b))
    var_a = sum((x - media_a) ** 2 for x in a)
    var_b = sum((y - media_b) ** 2 for y in b)
    if var_a == 0 or var_b == 0:
        return None
    return cov / (var_a * var_b) ** 0.5


def spearman(casos):
    """Correlação de ordem entre a nota (0, 1, 2) e o score médio. casos: [(nota, score), ...]"""
    return correlacao(posicoes([c[0] for c in casos]), posicoes([c[1] for c in casos]))


def separacao(casos):
    """Em que fração dos pares (serve, nao) a vaga 'serve' tem score maior. 0,5 = ao acaso."""
    serve = [score for nota, score in casos if nota == 2]
    nao = [score for nota, score in casos if nota == 0]
    if not serve or not nao:
        return None
    pontos = 0.0
    for a in serve:
        for b in nao:
            pontos += 1.0 if a > b else 0.5 if a == b else 0.0
    return pontos / (len(serve) * len(nao))


def intervalo(funcao, casos, repeticoes=2000):
    """Intervalo de 95% por reamostragem: repete a conta com casos escolhidos ao acaso, com reposição."""
    sorteador = random.Random(1)
    valores = []
    for _ in range(repeticoes):
        amostra = [sorteador.choice(casos) for _ in casos]
        valor = funcao(amostra)
        if valor is not None:
            valores.append(valor)
    valores.sort()
    return valores[int(0.025 * len(valores))], valores[int(0.975 * len(valores)) - 1]


def formatar(valor, casas=2):
    return "-" if valor is None else f"{valor:.{casas}f}"


def resumo():
    notas = dict(ler_notas())
    vagas = ler_vagas(list(notas))
    linhas = ler_linhas(CAMINHO_RESULTADOS)
    erros = ler_linhas(CAMINHO_ERROS)

    por_vaga = {}
    for linha in linhas:
        if linha["status"] == "ok":
            por_vaga.setdefault(linha["id"], []).append(linha["score"])

    sem_relatorio = sum(1 for linha in linhas if linha["status"] != "ok")
    casos = []
    nomes = {}
    for id_vaga, scores in por_vaga.items():
        casos.append((VALOR_DA_NOTA[notas[id_vaga]], sum(scores) / len(scores)))
        nomes[id_vaga] = sum(scores) / len(scores)

    saida = ["# Resultado da avaliação", ""]
    saida.append(f"{len(linhas)} análises ({len(por_vaga)} vagas), {sem_relatorio} sem relatório, "
                 f"{len(erros)} falhas de infraestrutura registadas.")
    saida.append(f"Custo total: ${sum(l['custo_usd'] or 0 for l in linhas):.3f} | "
                 f"tempo médio por análise: {sum(l['latencia_s'] for l in linhas) / max(len(linhas), 1):.1f} s")
    saida.append("")

    rho = spearman(casos)
    auc = separacao(casos)
    saida.append("## O score concorda contigo?")
    saida.append("")
    saida.append("| Métrica | Valor | Intervalo de 95% |")
    saida.append("|---|---|---|")
    if rho is not None:
        inferior, superior = intervalo(spearman, casos)
        saida.append(f"| Correlação de ordem (0 = ao acaso, 1 = acordo total) | {formatar(rho)} | {formatar(inferior)} a {formatar(superior)} |")
    if auc is not None:
        inferior, superior = intervalo(separacao, casos)
        saida.append(f"| Separação serve / nao (0,50 = ao acaso, 1 = perfeita) | {formatar(auc)} | {formatar(inferior)} a {formatar(superior)} |")
    saida.append("")

    saida.append("| A tua nota | Vagas | Score médio do agente |")
    saida.append("|---|---|---|")
    for nome, valor in [("serve", 2), ("talvez", 1), ("nao", 0)]:
        scores = [score for nota, score in casos if nota == valor]
        media = sum(scores) / len(scores) if scores else None
        saida.append(f"| {nome} | {len(scores)} | {formatar(media, 1)} |")
    saida.append("")

    amplitudes = [max(s) - min(s) for s in por_vaga.values() if len(s) >= 2]
    saida.append("## O score é estável?")
    saida.append("")
    if amplitudes:
        saida.append(f"Repetindo a mesma vaga, o score varia em média **{sum(amplitudes) / len(amplitudes):.1f} pontos** "
                     f"(amplitude entre o menor e o maior), no máximo {max(amplitudes)} pontos; "
                     f"{sum(1 for a in amplitudes if a >= 10)} de {len(amplitudes)} vagas variam 10 pontos ou mais.")
    else:
        saida.append("Faltam repetições para medir a estabilidade.")
    saida.append("")

    saida.append("## Onde o agente e tu discordam mais")
    saida.append("")
    ordenadas = sorted(nomes.items(), key=lambda par: par[1])
    serve_baixas = [(i, s) for i, s in ordenadas if notas[i] == "serve"][:3]
    nao_altas = [(i, s) for i, s in reversed(ordenadas) if notas[i] == "nao"][:3]
    saida.append("Vagas que tu marcaste `serve` e o agente avaliou mais baixo:")
    for id_vaga, score in serve_baixas:
        saida.append(f"- {score:.0f}: {vagas[id_vaga]['titulo']} ({vagas[id_vaga]['empresa']})")
    saida.append("")
    saida.append("Vagas que tu marcaste `nao` e o agente avaliou mais alto:")
    for id_vaga, score in nao_altas:
        saida.append(f"- {score:.0f}: {vagas[id_vaga]['titulo']} ({vagas[id_vaga]['empresa']})")

    texto = "\n".join(saida)
    print(texto)
    with open(CAMINHO_RESUMO, "w", encoding="utf-8") as ficheiro:
        ficheiro.write(texto + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Avalia o agente contra as notas dadas à mão.")
    parser.add_argument("--reps", type=int, default=3, help="repetições por vaga")
    parser.add_argument("--so", type=int, default=0, help="só os primeiros N casos (piloto)")
    parser.add_argument("--trabalhadores", type=int, default=3, help="análises em paralelo")
    parser.add_argument("--resumo", action="store_true", help="só calcula as métricas")
    argumentos = parser.parse_args()

    if argumentos.resumo:
        resumo()
    else:
        correr(ler_notas(), argumentos.reps, argumentos.so, argumentos.trabalhadores)

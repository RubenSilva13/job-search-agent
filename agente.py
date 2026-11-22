import json
import os
import re
import time
from datetime import datetime
import anthropic
import psycopg
from pydantic import ValidationError
from base_de_dados import guardar_vaga, guardar_analise, registar_execucao
from config import ANTHROPIC_API_KEY, MODELO, MAX_PASSOS, MAX_TOKENS
from ferramentas import FERRAMENTAS, DESCRICOES
from modelos import Relatorio

cliente = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM = (
    "És um assistente de carreira que avalia vagas de emprego para um programador.\n"
    "Para cada vaga:\n"
    "1. Se a tarefa já trouxer o texto do anúncio, usa-o e não chames ler_pagina_web. "
    "Caso contrário, lê o anúncio com ler_pagina_web. "
    "Se a tarefa indicar o local e o regime, são dados da fonte: usa-os na localização do relatório "
    "e para avaliar requisitos de local ou de regime, e não digas que o anúncio não os indica.\n"
    "2. Lê o portfólio completo do utilizador com ler_portfolio (uma só vez).\n"
    "3. Lê o perfil do utilizador com ler_perfil (uma só vez).\n"
    "4. Pesquisa a empresa com pesquisar_web, uma só vez. Se não encontrares informação útil, "
    "não repitas a pesquisa: diz no resumo da empresa que não foi possível confirmar e avança.\n"
    "5. Entrega o resultado chamando entregar_relatorio. Nunca respondas em texto.\n\n"
    "Regras do relatório:\n"
    "- Inclui cada requisito do anúncio exatamente uma vez, com o texto do anúncio. "
    "Não inventes requisitos que não estão no anúncio.\n"
    "- Estados: 'cumpre' (há prova clara num repositório ou no perfil); 'parcial' (há prova de algo próximo, "
    "ou o perfil indica um nível inferior ao pedido); 'falta' (competência técnica que não aparece "
    "em nenhum repositório nem no perfil); "
    "'nao_confirmado' (algo que nem o GitHub nem o perfil mostram, como soft skills).\n"
    "- A evidência indica a origem e o que lá está escrito: o repositório e o README, ou o campo do perfil "
    "(por exemplo, 'perfil, línguas: Inglês B2/C1'). Respeita sempre o nível que o perfil indica. "
    "Nunca deduzas a partir de nomes, "
    "nem afirmes deploy, produção ou micro-serviços se não estiver escrito.\n"
    "- Score de 0 a 100: a percentagem dos requisitos técnicos principais que o utilizador cumpre, "
    "sem contar os 'nao_confirmado'.\n"
    "- As sugestões só podem referir factos que estão no portfólio ou no perfil. "
    "Não inventes experiências, atividades nem resultados.\n"
    "- Responde em português de Portugal."
)

DESCRICAO_RELATORIO = {
    "name": "entregar_relatorio",
    "description": "Entrega o relatório final da análise da vaga. "
                   "Chama esta ferramenta uma única vez, no fim, quando tiveres toda a informação.",
    "input_schema": Relatorio.model_json_schema(),
}

TODAS_AS_DESCRICOES = DESCRICOES + [DESCRICAO_RELATORIO]

SIMBOLOS = {"cumpre": "✅", "parcial": "🟡", "falta": "❌", "nao_confirmado": "❔"}


def executar_ferramenta(nome, argumentos):
    """Executa uma ferramenta normal. Devolve sempre texto, mesmo em caso de erro."""
    if nome not in FERRAMENTAS:
        return f"Erro: a ferramenta '{nome}' não existe."

    funcao = FERRAMENTAS[nome]
    try:
        return funcao(**argumentos)
    except Exception as erro:
        return f"Erro ao executar '{nome}': {erro}"


def validar_relatorio(argumentos):
    """Devolve (relatorio, None) se o relatório for válido, ou (None, erro) se não for."""
    try:
        relatorio = Relatorio.model_validate(argumentos)
    except ValidationError as erro:
        mensagem = (
            "O relatório tem erros e não foi aceite. "
            f"Corrige-os e volta a chamar entregar_relatorio:\n{erro}"
        )
        return None, mensagem

    return relatorio, None


def pedir_ao_modelo(mensagens, forcar_relatorio):
    """Pede ao modelo a próxima ação. No último passo, obriga-o a entregar o relatório."""
    if forcar_relatorio:
        escolha = {"type": "tool", "name": "entregar_relatorio"}
    else:
        escolha = {"type": "auto"}

    resposta = cliente.messages.create(
        model=MODELO,
        max_tokens=MAX_TOKENS,
        system=SYSTEM,
        messages=mensagens,
        tools=TODAS_AS_DESCRICOES,
        tool_choice=escolha,
    )
    return resposta

def registar_no_fim(resultado, inicio, passos_registados, vaga_id):
    """Guarda na base de dados a execuçao que acabou. Se falhar, avisa."""
    duracao_ms = int((time.perf_counter()- inicio  ) * 1000)

    try:
        registar_execucao(MODELO, resultado, duracao_ms, passos_registados, vaga_id)
    except psycopg.Error as erro:
        print(f"Nao foi possisvel registar a execuçao ({type(erro).__name__}).")

def correr_agente(tarefa, vaga_id=None):
    passos_registados = []
    inicio = time.perf_counter()

    mensagens = [
        {"role": "user", "content": tarefa},
    ]
    cache = {}

    for passo in range(1, MAX_PASSOS + 1):
        print(f"\n--- Passo {passo} ---")

        ultimo_passo = passo == MAX_PASSOS

        inicio_chamada = time.perf_counter()
        resposta = pedir_ao_modelo(mensagens, forcar_relatorio=ultimo_passo)
        passos_registados.append({
            "tipo": "modelo",
            "duracao_ms": int((time.perf_counter() - inicio_chamada) * 1000),
            "tokens_entrada": resposta.usage.input_tokens,
            "tokens_saida": resposta.usage.output_tokens,
        })


        # a API exige que o pedido do assistente fique no histórico, tal como veio
        mensagens.append({"role": "assistant", "content": resposta.content})

        pedidos = []
        for bloco in resposta.content:
            if bloco.type == "tool_use":
                pedidos.append(bloco)

        # o modelo respondeu em texto: lembrá-lo de que tem de entregar o relatório
        if not pedidos:
            print("💬 Respondeu em texto. A pedir o relatório estruturado.")
            mensagens.append({
                "role": "user",
                "content": "Não respondas em texto. Entrega o resultado chamando entregar_relatorio.",
            })
            continue

        resultados = []

        for pedido in pedidos:
            nome = pedido.name
            argumentos = pedido.input
            erro_na_ferramenta = False

            if nome == "entregar_relatorio":
                print("📋 entregar_relatorio(...)")
                relatorio, erro = validar_relatorio(argumentos)

                if relatorio is not None:
                    registar_no_fim("ok", inicio, passos_registados, vaga_id)
                    return relatorio 

                print(f"   ↳ ❌ Relatório recusado: {erro[:300]}")
                resultado = erro
                erro_na_ferramenta = True

            else:
                argumentos_texto = json.dumps(argumentos, ensure_ascii=False, sort_keys=True)
                print(f"🔧 {nome}({argumentos_texto})")
                chave = (nome, argumentos_texto)
                if chave in cache:
                    resultado = cache[chave]
                    print("   (já tinha este resultado, reutilizado)")
                else:
                    inicio_ferramenta = time.perf_counter()
                    resultado = executar_ferramenta(nome, argumentos)
                    passos_registados.append ({
                        "tipo": "ferramenta",
                        "nome": nome,
                        "duracao_ms": int((time.perf_counter() - inicio_ferramenta) * 1000),
                        "erro": resultado if resultado.startswith("Erro") else None,
                     })

                    cache[chave] = resultado
                print(f"   ↳ {resultado[:150]}...")

            resultados.append({
                "type": "tool_result",
                "tool_use_id": pedido.id,
                "content": resultado,
                "is_error": erro_na_ferramenta,
            })

        # todos os resultados deste passo vão juntos, numa só mensagem do utilizador
        mensagens.append({"role": "user", "content": resultados})
    
    registar_no_fim("sem_relatorio", inicio, passos_registados, vaga_id)
    return None  # nem no último passo conseguiu entregar um relatório válido


def guardar_relatorio(relatorio, url=None):
    """Guarda o relatório num ficheiro JSON na pasta relatorios/, com o link da vaga."""
    os.makedirs("relatorios", exist_ok=True)

    data = datetime.now().strftime("%Y-%m-%d_%H-%M")
    nome_empresa = relatorio.empresa.replace(" ", "_")
    caminho = os.path.join("relatorios", f"{data}_{nome_empresa}.json")

    # o link vem do código e não do modelo: é a chave da vaga, tem de ser exato
    dados = {"url": url, **relatorio.model_dump()}

    with open(caminho, "w", encoding="utf-8") as ficheiro:
        json.dump(dados, ficheiro, ensure_ascii=False, indent=2)

    return caminho


def mostrar_relatorio(relatorio, url=None):
    print("\n" + "=" * 60)
    print(f"{relatorio.vaga} — {relatorio.empresa}")
    if url:
        print(f"Link: {url}")
    print(f"Score: {relatorio.score}/100")
    print("=" * 60)

    for item in relatorio.requisitos:
        simbolo = SIMBOLOS[item.estado]
        print(f"{simbolo} {item.requisito}")
        if item.evidencia:
            print(f"     ↳ {item.evidencia}")

    print(f"\nEmpresa: {relatorio.resumo_empresa}")

    print("\nSugestões:")
    for sugestao in relatorio.sugestoes:
        print(f"  - {sugestao}")


def extrair_url(tarefa):
    """Devolve o primeiro link que aparece na tarefa, ou None se não houver nenhum."""
    encontrado = re.search(r"https?://\S+", tarefa)
    if encontrado is None:
        return None

    return encontrado.group(0).rstrip(".,;)>]")


def guardar_na_base(relatorio, tarefa):
    """Guarda a vaga e a análise na base de dados. Se não conseguir, avisa e continua."""
    url = extrair_url(tarefa)
    if url is None:
        print("\n⚠️  A tarefa não tem nenhum link, por isso a vaga não foi guardada na base de dados.")
        return

    try:
        vaga_id = guardar_vaga(
            relatorio.vaga,
            relatorio.empresa,
            url,
            localizacao=relatorio.localizacao,
            fonte="manual",
        )
        analise_id = guardar_analise(vaga_id, relatorio)
    except psycopg.Error as erro:
        print(f"\n⚠️  Não foi possível guardar na base de dados ({erro}).")
        return

    print(f"🗄️  Base de dados: vaga {vaga_id}, análise {analise_id}")


if __name__ == "__main__":
    tarefa = input("Tarefa: ")
    relatorio = correr_agente(tarefa)

    if relatorio is None:
        print("\n❌ O agente não conseguiu entregar um relatório válido.")
    else:
        url = extrair_url(tarefa)
        mostrar_relatorio(relatorio, url)
        caminho = guardar_relatorio(relatorio, url)
        print(f"\n💾 Guardado em {caminho}")
        guardar_na_base(relatorio, tarefa)

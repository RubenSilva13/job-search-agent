import json
import os
from datetime import datetime
from groq import Groq
from pydantic import ValidationError
from config import GROQ_API_KEY, MODELO, MAX_PASSOS
from ferramentas import FERRAMENTAS, DESCRICOES
from modelos import Relatorio

cliente = Groq(api_key=GROQ_API_KEY)

SYSTEM = (
    "És um assistente de carreira que avalia vagas de emprego para um programador.\n"
    "Para cada vaga:\n"
    "1. Lê o anúncio com ler_pagina_web.\n"
    "2. Lê o portfólio completo do utilizador com ler_portfolio (uma só vez).\n"
    "3. Pesquisa a empresa com pesquisar_web.\n"
    "4. Entrega o resultado chamando entregar_relatorio. Nunca respondas em texto.\n\n"
    "Regras do relatório:\n"
    "- Inclui cada requisito do anúncio exatamente uma vez, com o texto do anúncio. "
    "Não inventes requisitos que não estão no anúncio.\n"
    "- Estados: 'cumpre' (há prova clara num repositório); 'parcial' (há prova de algo próximo, "
    "mas não exatamente o pedido); 'falta' (competência técnica que não aparece em nenhum repositório); "
    "'nao_confirmado' (algo que o GitHub não pode mostrar, como formação, línguas ou soft skills).\n"
    "- A evidência indica o repositório e o que está escrito no README. Nunca deduzas a partir de nomes, "
    "nem afirmes deploy, produção ou micro-serviços se não estiver escrito.\n"
    "- Score de 0 a 100: a percentagem dos requisitos técnicos principais que o utilizador cumpre, "
    "sem contar os 'nao_confirmado'.\n"
    "- Responde em português de Portugal."
)

DESCRICAO_RELATORIO = {
    "type": "function",
    "function": {
        "name": "entregar_relatorio",
        "description": "Entrega o relatório final da análise da vaga. "
                       "Chama esta ferramenta uma única vez, no fim, quando tiveres toda a informação.",
        "parameters": Relatorio.model_json_schema(),
    },
}

TODAS_AS_DESCRICOES = DESCRICOES + [DESCRICAO_RELATORIO]

SIMBOLOS = {"cumpre": "✅", "parcial": "🟡", "falta": "❌", "nao_confirmado": "❔"}


def executar_ferramenta(nome, argumentos_texto):
    """Executa uma ferramenta normal. Devolve sempre texto, mesmo em caso de erro."""
    if nome not in FERRAMENTAS:
        return f"Erro: a ferramenta '{nome}' não existe."

    try:
        argumentos = json.loads(argumentos_texto)
    except json.JSONDecodeError:
        return "Erro: os argumentos não são JSON válido."

    funcao = FERRAMENTAS[nome]
    try:
        return funcao(**argumentos)
    except Exception as erro:
        return f"Erro ao executar '{nome}': {erro}"


def validar_relatorio(argumentos_texto):
    """Devolve (relatorio, None) se o relatório for válido, ou (None, erro) se não for."""
    try:
        dados = json.loads(argumentos_texto)
    except json.JSONDecodeError:
        return None, "Erro: o relatório não é JSON válido. Volta a chamar entregar_relatorio."

    try:
        relatorio = Relatorio.model_validate(dados)
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
        escolha = {"type": "function", "function": {"name": "entregar_relatorio"}}
    else:
        escolha = "auto"

    resposta = cliente.chat.completions.create(
        model=MODELO,
        messages=mensagens,
        tools=TODAS_AS_DESCRICOES,
        tool_choice=escolha,
    )
    return resposta.choices[0].message


def guardar_pedido_no_historico(mensagens, mensagem):
    """Guarda no histórico as ferramentas que o modelo pediu (a API exige-o)."""
    chamadas = []
    for chamada in mensagem.tool_calls:
        chamadas.append({
            "id": chamada.id,
            "type": "function",
            "function": {
                "name": chamada.function.name,
                "arguments": chamada.function.arguments,
            },
        })
    mensagens.append({
        "role": "assistant",
        "content": mensagem.content or "",
        "tool_calls": chamadas,
    })


def correr_agente(tarefa):
    mensagens = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": tarefa},
    ]
    cache = {}

    for passo in range(1, MAX_PASSOS + 1):
        print(f"\n--- Passo {passo} ---")

        ultimo_passo = passo == MAX_PASSOS
        mensagem = pedir_ao_modelo(mensagens, forcar_relatorio=ultimo_passo)

        # o modelo respondeu em texto: lembrá-lo de que tem de entregar o relatório
        if not mensagem.tool_calls:
            print("💬 Respondeu em texto. A pedir o relatório estruturado.")
            mensagens.append({"role": "assistant", "content": mensagem.content or ""})
            mensagens.append({
                "role": "user",
                "content": "Não respondas em texto. Entrega o resultado chamando entregar_relatorio.",
            })
            continue

        guardar_pedido_no_historico(mensagens, mensagem)

        for chamada in mensagem.tool_calls:
            nome = chamada.function.name
            argumentos_texto = chamada.function.arguments

            if nome == "entregar_relatorio":
                print("📋 entregar_relatorio(...)")
                relatorio, erro = validar_relatorio(argumentos_texto)

                if relatorio is not None:
                    return relatorio  # relatório válido: o ciclo termina aqui

                print(f"   ↳ ❌ Relatório recusado: {erro[:300]}")
                resultado = erro

            else:
                print(f"🔧 {nome}({argumentos_texto})")
                chave = (nome, argumentos_texto)
                if chave in cache:
                    resultado = cache[chave]
                    print("   (já tinha este resultado, reutilizado)")
                else:
                    resultado = executar_ferramenta(nome, argumentos_texto)
                    cache[chave] = resultado
                print(f"   ↳ {resultado[:150]}...")

            mensagens.append({
                "role": "tool",
                "tool_call_id": chamada.id,
                "content": resultado,
            })

    return None  # nem no último passo conseguiu entregar um relatório válido


def guardar_relatorio(relatorio):
    """Guarda o relatório num ficheiro JSON na pasta relatorios/."""
    os.makedirs("relatorios", exist_ok=True)

    data = datetime.now().strftime("%Y-%m-%d_%H-%M")
    nome_empresa = relatorio.empresa.replace(" ", "_")
    caminho = os.path.join("relatorios", f"{data}_{nome_empresa}.json")

    with open(caminho, "w", encoding="utf-8") as ficheiro:
        ficheiro.write(relatorio.model_dump_json(indent=2))

    return caminho


def mostrar_relatorio(relatorio):
    print("\n" + "=" * 60)
    print(f"{relatorio.vaga} — {relatorio.empresa}")
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


if __name__ == "__main__":
    tarefa = input("Tarefa: ")
    relatorio = correr_agente(tarefa)

    if relatorio is None:
        print("\n❌ O agente não conseguiu entregar um relatório válido.")
    else:
        mostrar_relatorio(relatorio)
        caminho = guardar_relatorio(relatorio)
        print(f"\n💾 Guardado em {caminho}")
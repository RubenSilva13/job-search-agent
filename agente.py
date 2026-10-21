import json
from groq import Groq
from config import GROQ_API_KEY, MODELO, MAX_PASSOS
from ferramentas import FERRAMENTAS, DESCRICOES


cliente = Groq(api_key=GROQ_API_KEY)

SYSTEM = (
    "És um assistente de carreira que analisa o portfólio de programadores no GitHub.\n"
    "Usa as ferramentas para ir buscar informação real; nunca inventes projetos nem tecnologias.\n"
    "Baseia cada conclusão no que leste e indica de que repositório veio.\n"
    "Se uma ferramenta falhar ou não devolver informação, diz claramente que não conseguiste confirmar. "
    "Nunca deduzas tecnologias ou competências a partir do nome de um repositório.\n"
    "Podes pedir várias ferramentas no mesmo passo, por exemplo ler vários READMEs de uma vez.\n"
    "Nunca exageres a experiência do utilizador: se algo não está explicitamente nos READMEs "
    "(por exemplo, deploy, produção ou utilizadores reais), não o afirmes.\n"
    "Responde em português de Portugal."
)

def executar_ferramenta(nome, argumentos_texto):
    """Executa a ferramenta pedida pelo modelo. Devolve sempre texto, mesmo em caso de erro."""
    if nome not in FERRAMENTAS:
        return f"Erro: a ferramenta '{nome}' nao existe."

    try:
        argumentos = json.loads(argumentos_texto)
    except json.JSONDecodeError:
        return "Erro: os argumentos nao sao JSON validos."

    funcao = FERRAMENTAS[nome]
    try:
        return funcao(**argumentos)
    except Exception as erro:
        return f"Erro ao executar '{nome}': {erro}"


def correr_agente(tarefa):
    mensagens = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": tarefa},
    ]
    cache = {}

    for passo in range(1, MAX_PASSOS +1):
        print(f"\n - Passo {passo} -")

        resposta = cliente.chat.completions.create(
            model=MODELO,
            messages=mensagens,
            tools=DESCRICOES,
            tool_choice="auto",
            parallel_tool_calls=True,
        )
        mensagem = resposta.choices[0].message

        if not mensagem.tool_calls:
            print("Resposta Final")
            return mensagem.content

        chamadas = []
        for chamada in mensagem.tool_calls:
            chamadas.append({
                "id": chamada.id,
                "type":"function",
                "function": {
                    "name": chamada.function.name,
                    "arguments": chamada.function.arguments,
                },
            })
        mensagens.append({
            "role":"assistant",
            "content": mensagem.content or "",
            "tool_calls": chamadas,
        })

        for chamada in mensagem.tool_calls:
            nome = chamada.function.name
            argumentos_texto = chamada.function.arguments
            print(f" {nome}({argumentos_texto})")

            chave = (nome, argumentos_texto)
            if chave in cache:
                resultado = cache[chave]
                print("  (ja tinha este resultado, reutilizado)")
            else:
                resultado = executar_ferramenta(nome, argumentos_texto)
                cache[chave]= resultado
            print(f"  {resultado[:150]}")

            mensagens.append({
                "role":"tool",
                "tool_call_id":chamada.id,
                "content": resultado,
            })
        
    print("\n Limite de passos atingido. A pedir uma resposta final com o que já foi recolhido.")

    mensagens.append({
        "role": "user",
        "content": "Atingiste o limite de passos. Responde agora com o que já descobriste, "
                   "e indica claramente o que ficou por confirmar.",
    })

    resposta = cliente.chat.completions.create(
        model=MODELO,
        messages=mensagens,
    )
    return resposta.choices[0].message.content


if __name__ == "__main__":
    tarefa = input("Tarefa: ")
    resultado_final = correr_agente(tarefa)
    print("\n" + resultado_final)



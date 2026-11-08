from agente import correr_agente, guardar_relatorio
from base_de_dados import vagas_por_analisar, guardar_analise
from config import GITHUB_UTILIZADOR

LIMITE_DIARIO = 5


def montar_tarefa(vaga):
    """Escreve a tarefa para o agente, ja com o texto do anuncio"""
    return (
        f"Analisa esta vaga para o utilizador do GitHub {GITHUB_UTILIZADOR}.\n"
        f"Link: {vaga['url']}\n"
        f"Titulo: {vaga['titulo']} | Empresa: {vaga['empresa']}\n"
        f"Descricao: {vaga['descricao']}\n"
    )

def analisar_novas(limite=LIMITE_DIARIO):
    """Analisa, ate ao limite, as vagas aceites que ainda nao tem analise"""
    vagas = vagas_por_analisar(limite)
    print(f"{len(vagas)} vagas para analisar.")

    for vaga in vagas:
        print(f"\n === {vaga['titulo']} -- {vaga['empresa']} ===")

        try:
            relatorio = correr_agente(montar_tarefa(vaga))
        except Exception as erro:
            print(f"Falhou ({type(erro).__name__}), passo à seguinte.")
            continue

        if relatorio is None:
            print("O agente nao entregou um relatorio valido.")
            continue

        guardar_relatorio(relatorio)
        guardar_analise(vaga["id"], relatorio)
        print(f"Analise guardada com score {relatorio.score}.")


if __name__ == "__main__":
    analisar_novas()


    
import sys
from datetime import datetime
import psycopg
from analise_diaria import analisar_novas, LIMITE_DIARIO
from base_de_dados import abrir_ligacao
from recolha import recolher_e_guardar


def base_de_dados_disponivel():
    """Diz se a base de dados responde."""

    try:
        with abrir_ligacao() as ligacao:
            ligacao.execute("SELECT 1")
    except psycopg.Error as erro:
        print(f"Base de dados indisponivel ({type(erro).__name__}). O Docker Desktop esta aberto?")
        return False

    return True

def correr_diario(limite_analises=LIMITE_DIARIO):
    """Recolhe novas vagas e analisa as que ainda nao foram analisadas."""
    print(f"=== Execuçao diaria: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")


    if not base_de_dados_disponivel():
        sys.exit(1)

    try:
        recolher_e_guardar()
    except Exception as erro:
        print(f"A recolha falhou ({type(erro).__name__}). Sigo para a analise.")

    analisar_novas(limite_analises)

    print(f"=== Fim da execuçao diaria: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")




if __name__ == "__main__":
    correr_diario()
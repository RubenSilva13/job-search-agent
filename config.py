import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
ITJOBS_API_KEY = os.environ.get("ITJOBS_API_KEY")

GITHUB_UTILIZADOR = "RubenSilva13"

# Os valores à direita são os de hoje. Só mudam se a variável de ambiente existir
# (os testes e o Docker usam isso para apontar para outra base de dados).
BD_UTILIZADOR = os.environ.get("BD_UTILIZADOR", "agente")
BD_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
BD_NOME = os.environ.get("BD_NOME", "job_search")
BD_SERVIDOR = os.environ.get("BD_SERVIDOR", "127.0.0.1")
BD_PORTA = int(os.environ.get("BD_PORTA", "5432"))

MODELO = "claude-haiku-5-5"

PRECOS = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-opus-5-5": (4.00, 20.00),
}

MAX_PASSOS = 10
MAX_TOKENS = 8000


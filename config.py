import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

BD_UTILIZADOR = "agente"
BD_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
BD_NOME = "job_search"
BD_SERVIDOR = "127.0.0.1"
BD_PORTA = 5432

MODELO = "claude-haiku-5-5"

MAX_PASSOS = 10
MAX_TOKENS = 8000


import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

MODELO = "claude-haiku-5-5"

MAX_PASSOS = 10
MAX_TOKENS = 8000


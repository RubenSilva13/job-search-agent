import os
from pathlib import Path

import psycopg
import pytest

# O api.py importa o agente.py, que cria o cliente da Anthropic logo ao ser importado.
# Os testes nunca chamam o modelo, mas o import não pode falhar numa máquina sem .env
# (por exemplo, na CI). setdefault só preenche se a variável ainda não existir.
os.environ.setdefault("ANTHROPIC_API_KEY", "chave-falsa-so-para-os-testes")

# SEGURANÇA: todos os testes usam uma base de dados à parte. Isto tem de acontecer antes de
# qualquer "import config", porque é o config.py que lê o nome da base de dados.
# Assim, mesmo por engano, um teste nunca escreve na base de dados real (job_search).
NOME_BD_TESTE = "job_search_teste"
os.environ["BD_NOME"] = NOME_BD_TESTE

import config  # noqa: E402  (tem de vir depois de definir BD_NOME)

SCHEMA = Path(__file__).parent.parent / "schema.sql"


def ligar(nome_da_base):
    """Abre uma ligação ao PostgreSQL com os dados do config.py, à base de dados indicada."""
    return psycopg.connect(
        host=config.BD_SERVIDOR,
        port=config.BD_PORTA,
        dbname=nome_da_base,
        user=config.BD_UTILIZADOR,
        password=config.BD_PASSWORD,
        connect_timeout=5,
        autocommit=True,
    )


@pytest.fixture(scope="session")
def base_de_teste():
    """Cria (se faltar) a base de dados de teste e as tabelas. Uma vez por sessão de testes."""
    try:
        # liga-se à base de manutenção "postgres" só para poder criar a de teste
        with ligar("postgres") as ligacao:
            existe = ligacao.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s", (NOME_BD_TESTE,)
            ).fetchone()
            if not existe:
                ligacao.execute(f'CREATE DATABASE "{NOME_BD_TESTE}"')
    except psycopg.OperationalError as erro:
        # Na CI a base de dados tem de existir: falhar é melhor do que saltar em silêncio.
        if os.environ.get("CI"):
            raise
        pytest.skip(f"PostgreSQL indisponível ({type(erro).__name__}): abre o Docker para correr estes testes.")

    with ligar(NOME_BD_TESTE) as ligacao:
        ligacao.execute(SCHEMA.read_text(encoding="utf-8"))


@pytest.fixture
def bd(base_de_teste):
    """Dá a cada teste uma base de dados vazia (as tabelas ficam, as linhas desaparecem)."""
    with ligar(NOME_BD_TESTE) as ligacao:
        ligacao.execute(
            "TRUNCATE vagas, analises, candidaturas, execucoes, passos RESTART IDENTITY CASCADE"
        )

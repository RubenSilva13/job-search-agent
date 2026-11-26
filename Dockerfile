# Imagem da API (FastAPI).
FROM python:3.13-slim

# PYTHONUNBUFFERED: os prints aparecem logo nos logs do contentor
# PYTHONDONTWRITEBYTECODE: não escreve ficheiros .pyc dentro da imagem
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# As dependências primeiro: enquanto o requirements.txt não mudar, o Docker reutiliza esta camada
# e não volta a descarregar tudo a cada alteração ao código.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# O código da API e do agente (os .py da raiz). Os testes, o frontend, o .env e o venv
# ficam de fora (ver .dockerignore).
COPY *.py schema.sql perfil.json ./

# Não corre como administrador dentro do contentor.
RUN useradd --create-home --uid 1000 app
USER app

EXPOSE 8000

# 0.0.0.0: aceita ligações de fora do contentor (com 127.0.0.1 o Docker não conseguia chegar lá)
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

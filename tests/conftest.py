import os

# O api.py importa o agente.py, que cria o cliente da Anthropic logo ao ser importado.
# Os testes nunca chamam o modelo, mas o import não pode falhar numa máquina sem .env
# (por exemplo, na CI). setdefault só preenche se a variável ainda não existir.
os.environ.setdefault("ANTHROPIC_API_KEY", "chave-falsa-so-para-os-testes")

import json
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from config import BD_UTILIZADOR, BD_PASSWORD, BD_NOME, BD_SERVIDOR, BD_PORTA


def abrir_ligacao():
    """Abre ligação à base de dados PostgreSQL"""
    ligacao = psycopg.connect(
        host=BD_SERVIDOR,
        port=BD_PORTA,
        dbname=BD_NOME,
        user=BD_UTILIZADOR,
        password=BD_PASSWORD,
        connect_timeout=5,
    )
    return ligacao


def testar_ligacao():
    """Pergunta à base de dados a versão e imprime a resposta"""
    with abrir_ligacao() as ligacao:
        with ligacao.cursor() as cursor:
            cursor.execute("SELECT version()")
            linha = cursor.fetchone()
            print(linha[0])


def separar_nome_nivel(texto):
    """Separa 'Python (bom domínio)' em ('Python', 'bom domínio')"""
    if " (" not in texto:
        return texto, None

    nome, resto = texto.rsplit(" (", 1)
    nivel = resto.rstrip(")")
    return nome, nivel


def carregar_perfil_ficheiro(caminho="perfil.json"):
    """Lê o perfil.json e escreve-o nas tabelas, substituindo o que lá estava"""
    with open(caminho, "r", encoding="utf-8") as ficheiro:
        perfil = json.load(ficheiro)

    with abrir_ligacao() as ligacao:
        with ligacao.cursor() as cursor:

            # perfil: uma só linha (id = 1). Se já existir, atualiza.
            cursor.execute(
                "INSERT INTO perfil (id, nome, localizacao, disponibilidade, resumo, preferencias) "
                "VALUES (1, %s, %s, %s, %s, %s) "
                "ON CONFLICT (id) DO UPDATE SET "
                "nome = EXCLUDED.nome, localizacao = EXCLUDED.localizacao, "
                "disponibilidade = EXCLUDED.disponibilidade, resumo = EXCLUDED.resumo, "
                "preferencias = EXCLUDED.preferencias",

                (perfil["nome"], perfil["localizacao"], perfil["disponibilidade"], perfil["resumo"], Jsonb(perfil.get("preferencias", {}))),
            )

            # tabelas de listas: apaga o que havia e volta a inserir
            cursor.execute("DELETE FROM formacao")
            for item in perfil["formacao"]:
                cursor.execute(
                    "INSERT INTO formacao (curso, instituicao, grau, ano_inicio, ano_fim, estado) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (item["curso"], item["instituicao"], item["grau"],
                     item["ano_inicio"], item["ano_fim"], item["estado"]),
                )

            cursor.execute("DELETE FROM linguas")
            for item in perfil["linguas"]:
                cursor.execute(
                    "INSERT INTO linguas (lingua, nivel) VALUES (%s, %s)",
                    (item["lingua"], item["nivel"]),
                )

            cursor.execute("DELETE FROM experiencia")
            for item in perfil["experiencia"]:
                cursor.execute(
                    "INSERT INTO experiencia (funcao, empresa, ano_inicio, ano_fim, descricao) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (item["funcao"], item["empresa"], item["ano_inicio"],
                     item["ano_fim"], item["descricao"]),
                )

            # competências: os três tipos vêm de listas dentro de perfil["competencias"]
            cursor.execute("DELETE FROM competencias")
            tipos = {"linguagens": "linguagem", "ferramentas": "ferramenta", "soft_skills": "soft_skill"}
            for chave, tipo in tipos.items():
                for texto in perfil["competencias"][chave]:
                    nome, detalhe = separar_nome_nivel(texto)

                    # nas soft skills o que está entre parênteses é a prova, não o nível
                    if tipo == "soft_skill":
                        nivel = None
                        evidencia = detalhe
                    else:
                        nivel = detalhe
                        evidencia = None

                    cursor.execute(
                        "INSERT INTO competencias (tipo, nome, nivel, evidencia) "
                        "VALUES (%s, %s, %s, %s)",
                        (tipo, nome, nivel, evidencia),
                    )


def ler_perfil_da_base():
    """Lê o perfil das tabelas e devolve-o como dicionário. Devolve None se ainda não foi carregado."""
    with abrir_ligacao() as ligacao:
        
        with ligacao.cursor(row_factory=dict_row) as cursor:

            cursor.execute(
                "SELECT nome, localizacao, disponibilidade, resumo, preferencias FROM perfil WHERE id = 1"
            )
            perfil = cursor.fetchone()
            if perfil is None:
                return None

            cursor.execute(
                "SELECT curso, instituicao, grau, ano_inicio, ano_fim, estado "
                "FROM formacao ORDER BY id"
            )
            perfil["formacao"] = cursor.fetchall()

            cursor.execute("SELECT lingua, nivel FROM linguas ORDER BY id")
            perfil["linguas"] = cursor.fetchall()

            cursor.execute(
                "SELECT funcao, empresa, ano_inicio, ano_fim, descricao "
                "FROM experiencia ORDER BY id"
            )
            perfil["experiencia"] = cursor.fetchall()

            # competências: o tipo da tabela decide em que lista fica cada uma
            cursor.execute("SELECT tipo, nome, nivel, evidencia FROM competencias ORDER BY id")
            listas = {"linguagem": "linguagens", "ferramenta": "ferramentas", "soft_skill": "soft_skills"}
            competencias = {"linguagens": [], "ferramentas": [], "soft_skills": []}

            for linha in cursor.fetchall():
                item = {"nome": linha["nome"]}
                if linha["nivel"]:
                    item["nivel"] = linha["nivel"]
                if linha["evidencia"]:
                    item["evidencia"] = linha["evidencia"]
                competencias[listas[linha["tipo"]]].append(item)

            perfil["competencias"] = competencias

    return perfil


if __name__ == "__main__":
    carregar_perfil_ficheiro()
    print("Perfil carregado na base de dados.")

import re
import unicodedata


def normalizar(texto):
    """Põe em minúsculas e tira os acentos: 'Júnior' -> 'junior'."""
    decomposto = unicodedata.normalize("NFD", texto.lower())
    return "".join(letra for letra in decomposto if unicodedata.category(letra) != "Mn")


# palavras já normalizadas (sem acentos, em minúsculas e sem pontos)
PALAVRAS_SENIOR = ["senior", "sr", "lead", "leader", "principal", "head", "mid", "pleno", "architect"]

# funções que não são técnicas (gestão, vendas, recrutamento): não estão ligadas à licenciatura
PALAVRAS_EXCLUIDAS = ["manager", "pmo", "sales", "venda", "vendas", "recrutamento", "recruiter", "formador", "formadores"]
PALAVRAS_JUNIOR = ["junior", "jr", "trainee", "estagio", "estagiario", "intern", "internship", "entry level", "entry-level"]


def tem_palavra(texto, palavras):
    """Diz se alguma das palavras aparece no texto como palavra inteira."""
    for palavra in palavras:
        if re.search(rf"\b{palavra}\b", texto):
            return True
    return False


def classificar_senioridade(vaga):
    """Devolve 'junior', 'senior' ou 'indefinida', olhando para o título."""
    titulo = normalizar(vaga["titulo"])

    if tem_palavra(titulo, PALAVRAS_SENIOR):
        return "senior"
    if tem_palavra(titulo, PALAVRAS_JUNIOR):
        return "junior"

    return "indefinida"


def palavra_excluida(vaga):
    """Devolve a primeira palavra excluída que aparece no título, ou None se não aparecer nenhuma."""
    titulo = normalizar(vaga["titulo"])

    for palavra in PALAVRAS_EXCLUIDAS:
        if re.search(rf"\b{palavra}\b", titulo):
            return palavra

    return None


def avaliar_localizacao(vaga, preferencias):
    """Vê se o local e o regime da vaga servem. Devolve (aceite, motivo, prioridade)."""
    locais_da_vaga = [normalizar(local) for local in vaga["localizacoes"]]

    for preferencia in preferencias["localizacoes"]:
        local = normalizar(preferencia["local"])

        # "qualquer local" aceita-se em qualquer sítio; os outros têm de estar nos locais da vaga
        if local == "qualquer local":
            local_serve = True
        else:
            local_serve = any(local in local_vaga for local_vaga in locais_da_vaga)

        regime_serve = vaga["regime"] in preferencia["regimes"]

        if local_serve and regime_serve:
            motivo = f"{preferencia['local']}, {vaga['regime']}"
            return True, motivo, preferencia["prioridade"]

    return False, "local ou regime fora das preferências", None


def filtrar_vaga(vaga, preferencias):
    """Decide se a vaga merece ser analisada. Devolve um dicionário com a decisão e o motivo."""
    senioridade = classificar_senioridade(vaga)
    if senioridade == "senior":
        return {"aceite": False, "motivo": "título de nível sénior", "prioridade": None}

    excluida = palavra_excluida(vaga)
    if excluida is not None:
        return {"aceite": False, "motivo": f"função fora da área ('{excluida}')", "prioridade": None}

    aceite, motivo, prioridade = avaliar_localizacao(vaga, preferencias)
    if not aceite:
        return {"aceite": False, "motivo": motivo, "prioridade": None}

    # as de senioridade indefinida também passam: quase nenhum anúncio diz o nível
    return {"aceite": True, "motivo": f"{motivo}, senioridade {senioridade}", "prioridade": prioridade}


if __name__ == "__main__":
    from recolha import recolher_itjobs
    from base_de_dados import ler_perfil_da_base

    preferencias = ler_perfil_da_base()["preferencias"]
    vagas = recolher_itjobs(100)

    aceites = 0

    for vaga in vagas:
        decisao = filtrar_vaga(vaga, preferencias)
        sinal = "✅" if decisao["aceite"] else "❌"
        print(f"{sinal} {vaga['titulo'][:50]} | {vaga['localizacoes']} | {vaga['regime']} -> {decisao['motivo']}")

        if decisao["aceite"]:
            aceites += 1

    print(f"\nTotal de vagas aceites: {aceites}/{len(vagas)}")

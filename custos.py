from psycopg.rows import dict_row
from base_de_dados import abrir_ligacao


def dolares(valor):
    """Escreve um valor em dólares, ou um traço se não houver valor."""
    if valor is None:
        return "-"
    return f"${float(valor):.4f}"


def segundos(milissegundos):
    """Converte milissegundos em segundos, com uma casa decimal."""
    if milissegundos is None:
        return "-"
    return f"{float(milissegundos) / 1000:.1f} s"


def mostrar_custos():
    """Mostra quanto custaram e quanto demoraram as análises do agente."""
    with abrir_ligacao() as ligacao:
        with ligacao.cursor(row_factory=dict_row) as cursor:

            cursor.execute(
                "SELECT count(*) AS execucoes, "
                "count(*) FILTER (WHERE resultado = 'ok') AS ok, "
                "count(*) FILTER (WHERE resultado = 'sem_relatorio') AS sem_relatorio, "
                "count(*) FILTER (WHERE resultado = 'erro') AS erro, "
                "coalesce(sum(tokens_entrada), 0) AS tokens_entrada, "
                "coalesce(sum(tokens_saida), 0) AS tokens_saida, "
                "sum(custo_estimado) AS custo_total, "
                "avg(custo_estimado) AS custo_medio, "
                "avg(duracao_ms) AS duracao_media "
                "FROM execucoes"
            )
            resumo = cursor.fetchone()

            if resumo["execucoes"] == 0:
                print("Ainda não há execuções registadas. Corre 'python diario.py' primeiro.")
                return

            print("=== RESUMO ===")
            print(f"Análises registadas : {resumo['execucoes']} "
                  f"({resumo['ok']} com relatório, {resumo['sem_relatorio']} sem relatório, {resumo['erro']} com erro)")
            print(f"Tokens              : {resumo['tokens_entrada']:,} de entrada, {resumo['tokens_saida']:,} de saída")
            print(f"Custo total         : {dolares(resumo['custo_total'])}")
            print(f"Custo médio         : {dolares(resumo['custo_medio'])} por análise")
            print(f"Duração média       : {segundos(resumo['duracao_media'])} por análise")

            cursor.execute(
                "SELECT iniciada_em::date AS dia, count(*) AS execucoes, sum(custo_estimado) AS custo "
                "FROM execucoes GROUP BY 1 ORDER BY 1 DESC LIMIT 7"
            )
            print("\n=== CUSTO POR DIA (últimos 7 dias com análises) ===")
            for linha in cursor.fetchall():
                print(f"{linha['dia']} : {linha['execucoes']} análise(s), {dolares(linha['custo'])}")

            cursor.execute(
                "SELECT nome, count(*) AS chamadas, avg(duracao_ms) AS media_ms, "
                "max(duracao_ms) AS max_ms, count(erro) AS erros "
                "FROM passos WHERE tipo = 'ferramenta' "
                "GROUP BY nome ORDER BY avg(duracao_ms) DESC"
            )
            print("\n=== FERRAMENTAS (das mais lentas para as mais rápidas) ===")
            for linha in cursor.fetchall():
                print(f"{linha['nome']:<22} {linha['chamadas']:>3} chamada(s) | "
                      f"média {segundos(linha['media_ms'])} | máx. {segundos(linha['max_ms'])} | {linha['erros']} erro(s)")

            cursor.execute(
                "SELECT tipo, sum(duracao_ms) AS total_ms FROM passos GROUP BY tipo"
            )
            tempos = {linha["tipo"]: float(linha["total_ms"] or 0) for linha in cursor.fetchall()}
            tempo_total = sum(tempos.values())
            if tempo_total > 0:
                print("\n=== ONDE VAI O TEMPO ===")
                for tipo, total in sorted(tempos.items(), key=lambda par: -par[1]):
                    print(f"{tipo:<11}: {segundos(total)} ({total / tempo_total * 100:.0f}%)")

            cursor.execute(
                "SELECT left(coalesce(v.titulo, '(sem vaga)'), 40) AS vaga, e.custo_estimado, "
                "e.tokens_entrada, e.tokens_saida, e.duracao_ms "
                "FROM execucoes e LEFT JOIN vagas v ON v.id = e.vaga_id "
                "ORDER BY e.custo_estimado DESC NULLS LAST LIMIT 3"
            )
            print("\n=== AS 3 ANÁLISES MAIS CARAS ===")
            for linha in cursor.fetchall():
                print(f"{dolares(linha['custo_estimado'])} | {linha['vaga']} | "
                      f"{linha['tokens_entrada']:,} + {linha['tokens_saida']:,} tokens | {segundos(linha['duracao_ms'])}")


if __name__ == "__main__":
    mostrar_custos()

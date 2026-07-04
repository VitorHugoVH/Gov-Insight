import os
import plotext as plt
from tabulate import tabulate
from db import get_connection


# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================

def executar_consulta_real(query):
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query)
        resultado = cur.fetchall()
        return resultado
    except Exception as e:
        raise e
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def formatar_real(valor):
    if valor is None:
        return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def abreviar_orgao(nome):
    """Abrevia nomes de órgãos para exibição no gráfico."""
    substituicoes = {
        "CÂMARA MUNICIPAL DE BALNEÁRIO GAIVOTA":            "CÂMARA MUNICIPAL",
        "PREFEITURA MUNICIPAL BALNEÁRIO GAIVOTA":           "PREFEITURA",
        "FUNDO MUNICIPAL DE SAÚDE BALNEÁRIO GAIVOTA":      "FMS SAÚDE",
        "GABINETE DO PREFEITO MUNICIPAL":                   "GAB. PREFEITO",
        "SECRETARIA DE EDUCAÇÃO":                           "SEC. EDUCAÇÃO",
        "SECRETARIA MEIO AMBIENTE E DESENV. ECON. SUSTENT.":"SEC. MEIO AMBIENTE",
        "SECRETARIA DE ADMINISTRAÇÃO E FINANÇAS":           "SEC. ADM. FINANÇAS",
        "SECRETARIA DE SAÚDE":                              "SEC. SAÚDE",
        "SECRETARIA DE OBRAS":                              "SEC. OBRAS",
        "SECRETARIA DE ASSISTÊNCIA SOCIAL":                 "SEC. ASSIST. SOCIAL",
    }
    return substituicoes.get(nome, nome[:20] if nome else "")


def exibir_grafico_com_legenda(labels, valores, titulo, cor, formatar_fn=None):
    """Exibe gráfico de barras com legenda numerada abaixo."""
    plt.clear_data()
    plt.plotsize(110, 30)

    # Usa números como labels no eixo X para evitar sobreposição
    numeros = [str(i) for i in range(1, len(labels) + 1)]
    plt.bar(numeros, valores, color=cor)
    plt.title(titulo)
    plt.show()

    # Legenda manual com nomes completos e valores
    print("\nLegenda:")
    for i, (label, valor) in enumerate(zip(labels, valores), 1):
        valor_fmt = formatar_fn(valor) if formatar_fn else str(valor)
        print(f"  {i}. {label:<45} {valor_fmt}")
    print()


# ==============================================================================
# [1] RELATÓRIO 1: TOTAL DE DIÁRIAS POR ÓRGÃO
# ==============================================================================

def relatorio_diarias_por_orgao():
    print("\n⚡ Executando Consulta 1: Gastos com Diárias (Agregação: SUM)...")

    query = """
        SELECT
            COALESCE(s.nome_orgao, d.nome_entidade) AS local,
            SUM(d.valor_unitario * d.quantidade)    AS total
        FROM gov.diarias d
        LEFT JOIN gov.servidores s ON d.matricula = s.matricula
        LEFT JOIN gov.orgao o      ON s.nome_orgao = o.nome_orgao
        WHERE d.valor_unitario > 0
        GROUP BY COALESCE(s.nome_orgao, d.nome_entidade)
        ORDER BY total DESC
        LIMIT 5;
    """

    try:
        dados = executar_consulta_real(query)
        if not dados:
            print("\n⚠️ Sem registros de diárias no banco.")
            return

        print("\n💰 REPORT 1: MAIORES GASTOS COM DIÁRIAS POR ÓRGÃO")
        tab = [[r[0], formatar_real(r[1])] for r in dados]
        print(tabulate(tab, headers=["Órgão/Lotação", "Total em Diárias"], tablefmt="fancy_grid"))

        labels = [abreviar_orgao(r[0]) for r in dados]
        valores = [float(r[1]) for r in dados]
        exibir_grafico_com_legenda(labels, valores, "Total em Diárias por Órgão", "indigo", formatar_real)

    except Exception as e:
        print(f"\n❌ Erro ao executar consulta 1: {e}")


# ==============================================================================
# [2] RELATÓRIO 2: MÉDIA DE CONTRATOS POR ENTIDADE
# ==============================================================================

def relatorio_media_contratos_obras():
    print("\n⚡ Executando Consulta 2: Média de Contratos por Entidade...")

    query = """
        SELECT
            nome_entidade,
            AVG(valor_final) AS media,
            COUNT(*)         AS qtd
        FROM gov.contratos
        WHERE valor_final > 0
          AND nome_entidade IS NOT NULL
        GROUP BY nome_entidade
        ORDER BY media DESC
        LIMIT 5;
    """

    try:
        dados = executar_consulta_real(query)
        if not dados:
            print("\n⚠️ Sem registros de contratos no banco.")
            return

        print("\n🏗️ REPORT 2: MÉDIA DOS VALORES DE CONTRATOS POR ENTIDADE")
        tab = [[r[0], formatar_real(r[1]), r[2]] for r in dados]
        print(tabulate(tab, headers=["Entidade", "Média do Valor", "Qtd Contratos"], tablefmt="fancy_grid"))

        labels = [abreviar_orgao(r[0]) for r in dados]
        valores = [float(r[1]) for r in dados]
        exibir_grafico_com_legenda(labels, valores, "Média de Valor de Contrato por Entidade", "green", formatar_real)

    except Exception as e:
        print(f"\n❌ Erro ao executar consulta 2: {e}")


# ==============================================================================
# [3] RELATÓRIO 3: VOLUME DE LICITAÇÕES POR ENTIDADE
# ==============================================================================

def relatorio_volume_licitacoes_orgao():
    print("\n⚡ Executando Consulta 3: Volume de Licitações por Entidade...")

    query = """
        SELECT
            nome_entidade,
            COUNT(DISTINCT numero_do_processo) AS total_licitacoes
        FROM gov.licitacoes
        WHERE nome_entidade IS NOT NULL
        GROUP BY nome_entidade
        ORDER BY total_licitacoes DESC
        LIMIT 5;
    """

    try:
        dados = executar_consulta_real(query)
        if not dados:
            print("\n⚠️ Sem registros de licitações no banco.")
            return

        print("\n📦 REPORT 3: QUANTIDADE DE LICITAÇÕES POR ENTIDADE")
        tab = [[r[0], r[1]] for r in dados]
        print(tabulate(tab, headers=["Entidade", "Qtd Licitações"], tablefmt="fancy_grid"))

        labels = [abreviar_orgao(r[0]) for r in dados]
        valores = [int(r[1]) for r in dados]
        exibir_grafico_com_legenda(labels, valores, "Quantidade de Licitações por Entidade", "blue")

    except Exception as e:
        print(f"\n❌ Erro ao executar consulta 3: {e}")


# ==============================================================================
# MENU
# ==============================================================================

def exibir_submenu_relatorios():
    while True:
        print("\n" + "=" * 50)
        print("📊 SUBMENU - RELATÓRIOS E ANÁLISES GRÁFICAS")
        print("=" * 50)
        print("[1] 💰 Relatório 1: Total de Diárias por Órgão")
        print("[2] 🏗️  Relatório 2: Média de Contratos por Entidade")
        print("[3] 📦 Relatório 3: Volume de Licitações por Entidade")
        print("[0] ⬅️  Voltar ao Menu Principal")
        print("=" * 50)

        opcao = input("Escolha um relatório para visualizar: ").strip()

        if opcao == "1":
            relatorio_diarias_por_orgao()
        elif opcao == "2":
            relatorio_media_contratos_obras()
        elif opcao == "3":
            relatorio_volume_licitacoes_orgao()
        elif opcao == "0":
            print("\n⬅️ Retornando ao Menu Principal...")
            break
        else:
            print("\n⚠️ Opção inválida! Escolha entre 0 e 3.")


if __name__ == "__main__":
    exibir_submenu_relatorios()
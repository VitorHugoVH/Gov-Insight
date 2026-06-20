# gov_insight/src/analytics.py
import plotext as plt
from tabulate import tabulate
from db import get_connection

def formatar_real(valor):
    """Formata número para padrão de moeda R$"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def executar_e_plotar_maiores_gastos_individuais():
    """Busca as 5 maiores despesas individuais"""
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT id, LEFT(COALESCE(descricao, 'Despesa Geral'), 30), valor_pago FROM despesa WHERE valor_pago > 0 ORDER BY valor_pago DESC LIMIT 5;"
    cur.execute(query)
    dados = cur.fetchall()
    
    if dados:
        print("\n📊 REPORT 1: TOP 5 MAIORES DESPESAS")
        # Exibe formatado em tabela
        tab_dados = [[r[0], r[1], formatar_real(r[2])] for r in dados]
        print(tabulate(tab_dados, headers=["ID", "Descrição", "Valor"], tablefmt="fancy_grid"))
        
        plt.clear_data()
        plt.bar([f"ID {r[0]}" for r in dados], [float(r[2]) for r in dados], color="indigo")
        plt.title("Maiores Gastos Individuais")
        plt.show()
    cur.close()
    conn.close()

def executar_e_plotar_salarios_por_cargo():
    """Analisa a média salarial por cargo, tratando valores nulos"""
    conn = get_connection()
    cur = conn.cursor()
    # Adicionamos COALESCE para garantir que nulos virem 0
    query = """
        SELECT cargo, AVG(COALESCE(remuneracao, 0)) as media 
        FROM servidor 
        GROUP BY cargo 
        HAVING AVG(COALESCE(remuneracao, 0)) > 0
        ORDER BY media DESC LIMIT 5;
    """
    cur.execute(query)
    dados = cur.fetchall()
    
    if dados:
        print("\n💰 REPORT 2: MÉDIA SALARIAL POR CARGO (TOP 5)")
        # Garantimos que r[1] seja tratado como float antes de formatar
        tab_dados = [[r[0][:20], formatar_real(float(r[1] or 0))] for r in dados]
        print(tabulate(tab_dados, headers=["Cargo", "Média Salarial"], tablefmt="fancy_grid"))
        
        plt.clear_data()
        plt.bar([r[0][:10] for r in dados], [float(r[1] or 0) for r in dados], color="green")
        plt.title("Média Salarial por Cargo")
        plt.show()
    else:
        print("\n💰 MÉDIA SALARIAL: Sem dados válidos para processar.")
    
    cur.close()
    conn.close()

def executar_e_plotar_gastos_por_orgao():
    """Agrega o total gasto por órgão"""
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT o.nome, SUM(d.valor_pago) as total
        FROM despesa d
        JOIN orgao o ON d.orgao_id = o.id
        GROUP BY o.nome
        HAVING SUM(d.valor_pago) > 0
        ORDER BY total DESC LIMIT 5;
    """
    cur.execute(query)
    dados = cur.fetchall()
    
    if dados:
        print("\n📊 REPORT 3: GASTOS POR ÓRGÃO (TOP 5)")
        tab_dados = [[r[0][:20], formatar_real(r[1])] for r in dados]
        print(tabulate(tab_dados, headers=["Órgão", "Total Pago"], tablefmt="fancy_grid"))
        
        plt.clear_data()
        plt.bar([r[0][:10] for r in dados], [float(r[1]) for r in dados], color="blue")
        plt.title("Maiores Gastos por Órgão")
        plt.show()
    cur.close()
    conn.close()

def executar_e_plotar_maiores_gastos():
    """Função mestre que executa os relatórios"""
    executar_e_plotar_maiores_gastos_individuais()
    executar_e_plotar_salarios_por_cargo()
    executar_e_plotar_gastos_por_orgao()
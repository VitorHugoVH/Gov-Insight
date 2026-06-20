# gov_insight/src/check_db.py
from db import get_connection

def verificar_tabelas():
    conn = get_connection()
    cur = conn.cursor()
    
    tabelas = ['orgao', 'fornecedor', 'despesa', 'servidor', 'diaria']
    
    print("\n🔍 CONTAGEM DE REGISTROS NO BANCO DE DADOS:")
    print("=" * 45)
    
    for tabela in tabelas:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {tabela};")
            total = cur.fetchone()[0]
            print(f"📌 Tabela '{tabela}': {total} registros")
        except Exception as e:
            print(f"❌ Erro ao ler tabela '{tabela}': {e}")
            conn.rollback()
            
    print("=" * 45)
    cur.close()
    conn.close()

if __name__ == "__main__":
    verificar_tabelas()
# gov_insight/src/check_empty.py
import psycopg2

def checar_tabelas_vazias():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="transparencia",
            user="govinsight",
            password="govinsight@2026"
        )
        cursor = conn.cursor()
        
        # Busca todas as tabelas criadas no schema public
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tabelas = cursor.fetchall()
        
        print("\n📊 STATUS DAS TABELAS NO BANCO DE DADOS:")
        print("=" * 50)
        
        vazias = []
        for tabela in tabelas:
            nome_tab = tabela[0]
            cursor.execute(f'SELECT COUNT(*) FROM "{nome_tab}";')
            qtd = cursor.fetchone()[0]
            
            status = "✅ POPULADA" if qtd > 0 else "❌ VAZIA"
            print(f"- Tabela: {nome_tab:<25} | Registros: {qtd:<5} | {status}")
            
            if qtd == 0:
                vazias.append(nome_tab)
                
        print("=" * 50)
        print(f"Total de tabelas vazias encontradas: {len(vazias)}")
        
        cursor.close()
        conn.close()
        return vazias
    except Exception as e:
        print(f"Erro ao conectar ou consultar o banco: {e}")
        return []

if __name__ == "__main__":
    checar_tabelas_vazias()
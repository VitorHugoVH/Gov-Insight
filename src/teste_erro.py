# gov_insight/src/teste_erro.py
import os
import pandas as pd
import psycopg2

def testar_insercao_real():
    conn = psycopg2.connect(
        host="localhost", database="transparencia", user="govinsight", password="govinsight@2026"
    )
    cursor = conn.cursor()
    
    # Vamos pegar o arquivo de diárias como cobaia
    caminho = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "diarias", "diarias.CSV"))
    
    print("📋 Lendo primeiras linhas do CSV de diárias...")
    df = pd.read_csv(caminho, sep=";", encoding="iso-8859-1")
    
    # Mostra colunas do CSV
    df.columns = [str(col).strip().lower() for col in df.columns]
    print(f"Colunas encontradas no CSV: {list(df.columns)}")
    
    # Mostra colunas da tabela no banco
    cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='diaria';")
    colunas_banco = cursor.fetchall()
    print(f"Colunas reais da tabela 'diaria' no Postgres: {colunas_banco}")
    
    # Tenta inserir a PRIMEIRA linha e joga o erro na tela
    primeira_linha = df.iloc[0]
    colunas_validas = [col for col in df.columns if col in [c[0] for c in colunas_banco]]
    
    colunas_str = ", ".join([f'"{c}"' for c in colunas_validas])
    placeholders = ", ".join(["%s"] * len(colunas_validas))
    valores = [None if pd.isna(primeira_linha[c]) else str(primeira_linha[c]) for col in colunas_validas]
    
    query = f'INSERT INTO "diaria" ({colunas_str}) VALUES ({placeholders})'
    
    print("\n⚡ Tentando executar query de teste...")
    try:
        cursor.execute(query, valores)
        conn.commit()
        print("✅ Inseriu com sucesso?! Ué.")
    except Exception as e:
        print("\n❌ ERRO DO POSTGRES IDENTIFICADO:")
        print("="*60)
        print(e)
        print("="*60)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    testar_insercao_real()
import os
import sys
import subprocess
from dotenv import load_dotenv
from google import genai
from google.genai import types
from setup_db import create_tables
from tabulate import tabulate
import re

from db import get_connection  # <-- Importado para executar o DROP diretamente se necessário
from carga_dados import carregar_tudo
from analytics import exibir_submenu_relatorios
from crud import exibir_menu_crud 

# Carrega as variáveis do arquivo .env
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON_VENV = sys.executable

def eliminar_todas_as_tabelas():
    conn = get_connection()
    cur = conn.cursor()

    # ⚠️ NUNCA dropar public — extensões como unaccent vivem lá
    cur.execute("DROP SCHEMA IF EXISTS gov CASCADE;")
    cur.execute("CREATE SCHEMA IF NOT EXISTS public;")
    cur.execute("GRANT ALL ON SCHEMA public TO PUBLIC;")

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Schema gov removido.")

def executar_sql_seguro(conn, sql):
    """Executa apenas SELECT e WITH (CTEs) — nunca permite escrita."""
    sql_limpo = sql.strip().lstrip("-— \n").rstrip(";")

    # Rejeita qualquer comando de escrita
    palavras_proibidas = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE"]
    sql_upper = sql_limpo.upper()
    for palavra in palavras_proibidas:
        if palavra in sql_upper:
            return None, f"Comando '{palavra}' não permitido."

    # Aceita SELECT e WITH (CTEs)
    sql_inicio = sql_upper.lstrip()
    if not (sql_inicio.startswith("SELECT") or sql_inicio.startswith("WITH")):
        return None, "Apenas consultas SELECT ou WITH são permitidas."

    try:
        cur = conn.cursor()
        cur.execute(sql_limpo)
        colunas = [desc[0] for desc in cur.description]
        linhas = cur.fetchall()
        cur.close()
        return colunas, linhas
    except Exception as e:
        conn.rollback()
        return None, str(e)


def extrair_sqls(texto):
    """Extrai blocos ```sql e divide por ; se houver múltiplas queries."""
    blocos = re.findall(r"```sql\s*(.*?)```", texto, re.DOTALL | re.IGNORECASE)
    queries = []
    for bloco in blocos:
        # Divide por ; para separar múltiplas queries no mesmo bloco
        partes = [q.strip() for q in bloco.split(";") if q.strip()]
        queries.extend(partes)
    return queries


def iniciar_chat_ia():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n❌ Erro: GEMINI_API_KEY não encontrada no .env!")
        input("Pressione Enter para voltar...")
        return

    schema_path = os.path.join(BASE_DIR, "db", "schema.sql")
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
    except Exception:
        schema_sql = "(schema não encontrado)"

    system_prompt = f"""Você é o GovInsight-AI, assistente especialista em auditoria de contas públicas do município de Balneário Gaivota - SC.

O banco PostgreSQL usa o schema 'gov' com as seguintes tabelas:

{schema_sql}

Regras:
- Sempre prefixe tabelas com 'gov.' nas queries
- Quando gerar SQL, coloque cada query em um bloco ```sql separado
- Após gerar as queries, aguarde os resultados que serão enviados automaticamente
- Com os resultados em mãos, faça a análise de auditoria completa
- Aponte anomalias, riscos e recomendações com base nos dados reais retornados
- Use linguagem clara mas técnica
"""

    print("\n🤖 Inicializando GovInsight-AI...")

    try:
        conn = get_connection()
        client = genai.Client(api_key=api_key)
        chat = client.chats.create(
            model="gemini-3.1-flash-lite",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt
            )
        )

        print("Conectado! Digite sua pergunta ou 'sair' para voltar.")
        print("-" * 70)

        while True:
            pergunta = input("\nVocê 👤: ").strip()
            if pergunta.lower() in ['sair', 'exit', 'voltar']:
                break
            if not pergunta:
                continue

            # 1ª chamada: IA gera o SQL
            print("IA 🤖: Analisando...", end="\r")
            resposta = chat.send_message(pergunta)
            texto = resposta.text

            # Extrai e executa os SQLs gerados
            sqls = extrair_sqls(texto)
            if sqls:
                resultados_texto = ""
                for i, sql in enumerate(sqls, 1):
                    colunas, linhas = executar_sql_seguro(conn, sql)
                    if colunas is None:
                        resultados_texto += f"\nQuery {i} — ERRO: {linhas}\n"
                    elif not linhas:
                        resultados_texto += f"\nQuery {i} — Nenhum resultado encontrado.\n"
                    else:
                        resultados_texto += f"\nQuery {i} — {len(linhas)} resultado(s):\n"
                        resultados_texto += tabulate(linhas, headers=colunas, tablefmt="simple") + "\n"

                # 2ª chamada: IA analisa os resultados reais
                followup = f"Resultados das queries executadas no banco real:\n{resultados_texto}\nFaça a análise de auditoria completa com base nesses dados."
                print("IA 🤖: Interpretando resultados...", end="\r")
                analise = chat.send_message(followup)
                print(f"IA 🤖:\n{analise.text}")
            else:
                # Sem SQL — resposta puramente textual
                print(f"IA 🤖:\n{texto}")

            print("-" * 70)

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        input("Pressione Enter para retornar...")
    finally:
        if conn:
            conn.close()

def exibir_menu():
    print("\n" + "="*50)
    print("🏛️   GOV_INSIGHT - PORTAL DE TRANSPARÊNCIA INTEGRA")
    print("="*50)
    print("[1] 🔥 Eliminar Todas as Tabelas do Banco de Dados")  # <-- Nova opção explícita de destruição
    print("[2] 🛠️  Criar Estrutura de Tabelas (Zerar Banco)")
    print("[3] 📥 Executar Carga de Dados (Processar CSVs)")
    print("[4] 📊 Exibir Painel Gráfico Analítico (Plotext)")
    print("[5] 🛠️  Gerenciar Dados Manualmente (CRUD)") 
    print("[6] 🤖 Conversar com o Assistente de IA (Gemini)")            
    print("[0] ❌ Sair do Sistema")
    print("="*50)

def main():
    while True:
        exibir_menu()
        try:
            opcao = input("Escolha uma opção: ").strip()
            
            if opcao == "1":
                eliminar_todas_as_tabelas()
            elif opcao == "2":
                print("\n⚡ Criando estrutura de tabelas a partir do zero...")
                try:
                    create_tables()
                except Exception as e:
                    print(f"❌ ERRO ao criar tabelas: {e}")
            elif opcao == "3":
                print("\n⚡ Iniciando processo ETL...")
                carregar_tudo()
            elif opcao == "4":
                print("\n⚡ Gerando relatórios e gráficos...")
                exibir_submenu_relatorios()
            elif opcao == "5":
                exibir_menu_crud() 
            elif opcao == "6":
                iniciar_chat_ia()
            elif opcao == "0":
                print("\n👋 Encerrando o Gov_Insight. Até logo!")
                sys.exit(0)
            else:
                print("\n❌ Opção inválida! Digite um número de 0 a 6.")
        except KeyboardInterrupt:
            print("\n\n👋 Sistema interrompido. Saindo...")
            sys.exit(0)

if __name__ == "__main__":
    main()

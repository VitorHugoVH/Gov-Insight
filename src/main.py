# gov_insight/src/main.py
import os
import sys
import subprocess
from dotenv import load_dotenv
from google import genai
from google.genai import types

from carga_dados import carregar_tudo
from analytics import executar_e_plotar_maiores_gastos

# Carrega as variáveis do arquivo .env
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON_VENV = sys.executable

def iniciar_chat_ia():
    """Chama o assistente de IA integrado ao Portal de Transparência"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n❌ Erro: A variável 'GEMINI_API_KEY' não foi encontrada no arquivo .env!")
        input("Pressione Enter para voltar ao menu...")
        return

    print("\n🤖 Inicializando o Assistente Gov_Insight via Gemini...")
    try:
        # Nova sintaxe oficial do SDK do google-genai
        client = genai.Client(api_key=api_key)
        
        # Cria uma sessão interativa de chat injetando a persona do sistema
        chat = client.chats.create(
                    model="gemini-2.0-flash", # Ajustado para uma versão mais estável
                    config=types.GenerateContentConfig(
                        system_instruction=(
                            "Você é o GovInsight-AI, um assistente especialista em auditoria de contas públicas "
                            "e portais de transparência municipal. O banco de dados possui as tabelas: "
                            "servidor, contrato, licitacao, despesa, receita e patrimonio. "
                            "Seja prestativo, use termos técnicos de contabilidade pública, "
                            "mas explique de forma simples e direta para o usuário."
                        )
                    )
                )
        
        print("\nConectado! Converse com a IA sobre transparência pública (ou digite 'sair' para voltar ao menu).")
        print("-" * 70)
        
        while True:
            pergunta = input("\nVocê 👤: ").strip()
            if pergunta.lower() in ['sair', 'exit', 'voltar']:
                break
            if not pergunta:
                continue
                
            print("IA 🤖: Pensando...", end="\r")
            resposta = chat.send_message(pergunta)
            print(f"IA 🤖: {resposta.text}")
            print("-" * 70)
            
    except Exception as e:
        print(f"\n❌ Falha na comunicação com o Gemini: {e}")
        input("Pressione Enter para retornar...")

def exibir_menu():
    print("\n" + "="*50)
    print("🏛️  GOV_INSIGHT - PORTAL DE TRANSPARÊNCIA INTEGRA")
    print("="*50)
    print("[1] 🔄 Inicializar/Resetar Banco de Dados (Postgres)")
    print("[2] 📥 Executar Carga de Dados (Processar CSVs)")
    print("[3] 📊 Exibir Painel Gráfico Analítico (Plotext)")
    print("[4] 🤖 Conversar com o Assistente de IA (Gemini)")
    print("[0] ❌ Sair do Sistema")
    print("="*50)

def main():
    while True:
        exibir_menu()
        try:
            opcao = input("Escolha uma opção: ").strip()
            
            if opcao == "1":
                print("\n⚡ Recriando estrutura de tabelas...")
                script_path = os.path.join(BASE_DIR, "src", "setup_db.py")
                subprocess.run([PYTHON_VENV, script_path])
            elif opcao == "2":
                print("\n⚡ Iniciando processo ETL...")
                carregar_tudo()
            elif opcao == "3":
                print("\n⚡ Gerando relatórios e gráficos...")
                executar_e_plotar_maiores_gastos()
            elif opcao == "4":
                iniciar_chat_ia()
            elif opcao == "0":
                print("\n👋 Encerrando o Gov_Insight. Até logo!")
                sys.exit(0)
            else:
                print("\n❌ Opção inválida! Digite um número de 0 a 4.")
        except KeyboardInterrupt:
            print("\n\n👋 Sistema interrompido. Saindo...")
            sys.exit(0)

if __name__ == "__main__":
    main()
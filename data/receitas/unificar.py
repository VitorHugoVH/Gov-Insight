import os
import pandas as pd

# Lista com os anos e as pastas correspondentes
anos = [2024, 2025, 2026]

# Lista para armazenar os DataFrames de cada ano
dfs = []

print("Iniciando a unificação dos arquivos de receitas...\n")

for ano in anos:
    caminho_arquivo = os.path.join(str(ano), f"receitas_{ano}.CSV")

    if os.path.exists(caminho_arquivo):
        print(f" -> Lendo arquivo do ano {ano}: {caminho_arquivo}")
        try:
            # CORREÇÃO AQUI: adicionados sep=';' e encoding='utf-8'
            # Se ainda der erro de caracteres estranhos, mude 'utf-8' para 'latin1'
            df = pd.read_csv(caminho_arquivo, sep=";", encoding="utf-8")

            # Cria a nova coluna 'ano'
            df["ano"] = ano

            dfs.append(df)

        except Exception as e:
            print(f"    [ERRO] Falha ao ler {caminho_arquivo}: {e}")
    else:
        print(f" -> [AVISO] Arquivo esperado não encontrado: {caminho_arquivo}")

if dfs:
    print("\nCombinando todos os dados em um único arquivo...")
    df_final = pd.concat(dfs, ignore_index=True)

    arquivo_saida = "receitas_unificado.csv"

    # Salvando também com o separador correto para manter o padrão
    df_final.to_csv(arquivo_saida, index=False, sep=";", encoding="utf-8")

    print(f"\n[SUCESSO] Processo concluído!")
    print(f" -> Arquivo gerado: {os.path.abspath(arquivo_saida)}")
    print(f" -> Total de registros unificados: {len(df_final)} linhas.")
else:
    print(
        "\n[ERRO] Nenhum dado pôde ser processado. O arquivo unificado não foi criado."
    )
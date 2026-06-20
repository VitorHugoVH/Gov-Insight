# gov_insight/src/forcar_carga.py
import os
import pandas as pd
import psycopg2

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

def conectar_bd():
    return psycopg2.connect(
        host="localhost", database="transparencia", user="govinsight", password="govinsight@2026"
    )

def carregar_csv_seguro(caminho_arquivo):
    for encoding in ['utf-8', 'iso-8859-1', 'cp1252']:
        for sep in [';', ',']:
            try:
                df = pd.read_csv(caminho_arquivo, sep=';', encoding='latin-1')
                if len(df.columns) > 1:
                    return df
            except:
                continue
    return None

def limpar_numero(val):
    if pd.isna(val):
        return None
    val_str = str(val).strip().replace(".", "").replace(",", ".").replace("R$", "").strip()
    try:
        return float(val_str)
    except:
        return None

def forcar_populacao():
    conn = conectar_bd()
    cursor = conn.cursor()
    
    ordem_carga = [
            ("servidor", "servidores/servidores_remuneracao.CSV"),
            ("contrato", "contratos/contratos.CSV"),
            ("convenio_recebido", "convenios/convenios_recebidos_padronizado.csv"),
            ("despesa_programa", "despesa_programa/despesas_programas_acoes.CSV"),
            ("diaria", "diarias/diarias.CSV"),
            ("licitacao", "licitacoes/licitacoes.csv"),
            ("obra", "obra/obras.csv"),
            ("patrimonio", "patrimonio/patrimonio.csv"),
            ("receita", "receitas/receitas_unificado.csv"),
            # Adicione estas linhas para popular as despesas que ficaram de fora:
            ("despesa", "depesas_empenho/despesas_com_pessoal.CSV"), 
            ("despesa", "despesas_emenda_parlamentar/despesas_emendas_parlamentares.CSV")
        ]

    print("\n🔍 FASE 1: Extraindo e correlacionando Órgãos e Fornecedores dos CSVs...")
    
    orgaos_encontrados = set()
    fornecedores_encontrados = set()
    
    # Varre os arquivos em busca de nomes de órgãos e fornecedores para povoar as tabelas de correlação
    for tabela, rel_path in ordem_carga:
        caminho = os.path.join(DATA_DIR, rel_path)
        if os.path.exists(caminho):
            df = carregar_csv_seguro(caminho)
            if df is not None:
                df.columns = [str(col).strip().lower() for col in df.columns]
                
                # Coleta de Órgãos
                col_orgao = [c for c in df.columns if "entidade" in c or "orgao" in c]
                if col_orgao:
                    for val in df[col_orgao[0]].dropna().unique():
                        orgaos_encontrados.add(str(val).strip())
                        
                # Coleta de Fornecedores
                col_forn = [c for c in df.columns if "credor" in c or "fornecedor" in c]
                if col_forn:
                    for val in df[col_forn[0]].dropna().unique():
                        fornecedores_encontrados.add(str(val).strip())

    # Garante um valor padrão caso os arquivos estejam vazios
    if not orgaos_encontrados: orgaos_encontrados.add("Órgão Central")
    if not fornecedores_encontrados: fornecedores_encontrados.add("Fornecedor Geral")

    # Limpa e popula dinamicamente a tabela ORGAO
    cursor.execute('TRUNCATE TABLE "orgao" CASCADE;')
    mapa_orgaos = {}
    for idx, nome_orgao in enumerate(sorted(orgaos_encontrados), start=1):
        cursor.execute('INSERT INTO "orgao" (id, nome) VALUES (%s, %s);', (idx, nome_orgao))
        mapa_orgaos[nome_orgao.lower()] = idx
        
    # Limpa e popula dinamicamente a tabela FORNECEDOR
    cursor.execute('TRUNCATE TABLE "fornecedor" CASCADE;')
    mapa_fornecedores = {}
    for idx, nome_forn in enumerate(sorted(fornecedores_encontrados), start=1):
        cursor.execute('INSERT INTO "fornecedor" (id, nome) VALUES (%s, %s);', (idx, nome_forn))
        mapa_fornecedores[nome_forn.lower()] = idx

    conn.commit()
    print(f"✅ Mapeamento concluído: {len(mapa_orgaos)} órgãos e {len(mapa_fornecedores)} fornecedores unificados!")
    print("-" * 60)

    print("\n🚀 FASE 2: Iniciando carga adaptativa das tabelas de fatos...")
    print("-" * 60)
    
    # IDs de fallback caso alguma linha falhe no vínculo exato
    id_orgao_fallback = list(mapa_orgaos.values())[0]
    id_forn_fallback = list(mapa_fornecedores.values())[0]

    for tabela, rel_path in ordem_carga:
        caminho = os.path.join(DATA_DIR, rel_path)
        if not os.path.exists(caminho):
            print(f"⚠️ Arquivo não localizado: {rel_path}")
            continue
            
        print(f"📦 Processando tabela '{tabela}'...")
        df = carregar_csv_seguro(caminho)
        if df is None:
            print(f"❌ Erro ao ler o arquivo {rel_path}")
            continue
            
        df.columns = [str(col).strip().lower() for col in df.columns]
        
        # Trunca apenas a tabela atual antes de reinserir
        cursor.execute(f'TRUNCATE TABLE "{tabela}" CASCADE;')
        
        cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{tabela}';")
        colunas_reais_banco = [r[0] for r in cursor.fetchall()]
        
        sucessos = 0
        id_servidor_gerado = 1
        
        for idx, row in df.iterrows():
            try:
                dados_insert = {}
                
                # Identifica dinamicamente qual órgão ou fornecedor pertence a esta linha específica
                nome_orgao_linha = next((str(row[c]).strip().lower() for c in df.columns if "entidade" in c or "orgao" in c if not pd.isna(row[c])), "")
                nome_forn_linha = next((str(row[c]).strip().lower() for c in df.columns if "credor" in c or "fornecedor" in c if not pd.isna(row[c])), "")
                
                id_orgao_linha = mapa_orgaos.get(nome_orgao_linha, id_orgao_fallback)
                id_forn_linha = mapa_fornecedores.get(nome_forn_linha, id_forn_fallback)

                if tabela == "servidor":
                    dados_insert["id"] = id_servidor_gerado
                    dados_insert["nome"] = row.get("rel_servidor") or row.get("nome") or "Desconhecido"
                    dados_insert["cargo"] = str(row.get("cargo") or "Não Informado").strip()
                    if "orgao_id" in colunas_reais_banco:
                        dados_insert["orgao_id"] = id_orgao_linha
                    id_servidor_gerado += 1
                    
                elif tabela == "diaria":
                    if "ano" in colunas_reais_banco: dados_insert["ano"] = int(row.get("ano", 2026))
                    if "numero" in colunas_reais_banco: dados_insert["numero"] = str(row.get("numero", ""))
                    if "quantidade" in colunas_reais_banco: dados_insert["quantidade"] = int(pd.to_numeric(row.get("quantidade"), errors='coerce') or 1)
                    if "finalidade" in colunas_reais_banco: dados_insert["finalidade"] = str(row.get("finalidade", ""))
                    if "destino" in colunas_reais_banco: dados_insert["destino"] = str(row.get("local de destino") or row.get("destino", "Geral"))
                    if "servidor_id" in colunas_reais_banco: dados_insert["servidor_id"] = 1
                    
                    col_valor_banco = [c for c in colunas_reais_banco if "valor" in c]
                    if col_valor_banco: dados_insert[col_valor_banco[0]] = limpar_numero(row.get("valor") or row.get("valor_total"))

                elif tabela == "despesa_programa":
                    # Mapeia ignorando acentos e caracteres especiais estranhos
                    dados_insert["programa"] = str(row.get("nome_do_programa") or "Geral")
                    
                    # Tenta identificar o valor pago lidando com a codificação do cabeçalho
                    col_valor = next((c for c in df.columns if "valor_pago" in c), None)
                    if col_valor:
                        dados_insert["valor_pago"] = limpar_numero(row.get(col_valor))
                    
                    # Se houver campo de orgao_id, usamos o mapeamento que já fizemos
                    if "orgao_id" in colunas_reais_banco:
                        dados_insert["orgao_id"] = id_orgao_linha
                    
                elif tabela == "contrato":
                    col_num = [c for c in colunas_reais_banco if "num" in c]
                    if col_num: dados_insert[col_num[0]] = str(row.get("numero") or row.get("numero_contrato", idx))
                    if "objeto" in colunas_reais_banco: dados_insert["objeto"] = str(row.get("objeto", "Contrato"))
                    if "orgao_id" in colunas_reais_banco: dados_insert["orgao_id"] = id_orgao_linha
                    if "fornecedor_id" in colunas_reais_banco: dados_insert["fornecedor_id"] = id_forn_linha
                    
                    col_val = [c for c in colunas_reais_banco if "valor" in c]
                    if col_val: dados_insert[col_val[0]] = limpar_numero(row.get("valor") or row.get("valor_total"))
                    
                elif tabela == "licitacao":
                    col_num = [c for c in colunas_reais_banco if "num" in c]
                    if col_num: dados_insert[col_num[0]] = str(row.get("numero") or row.get("numero_licitacao", idx))
                    if "modalidade" in colunas_reais_banco: dados_insert["modalidade"] = str(row.get("modalidade") or "Outros")
                    if "objeto" in colunas_reais_banco: dados_insert["objeto"] = str(row.get("objeto", "Licitação"))
                    if "orgao_id" in colunas_reais_banco: dados_insert["orgao_id"] = id_orgao_linha
                    
                elif tabela == "obra":
                    if "descricao" in colunas_reais_banco: dados_insert["descricao"] = str(row.get("objeto") or row.get("obra", "Obra"))
                    if "situacao" in colunas_reais_banco: dados_insert["situacao"] = str(row.get("situacao") or "Execução")
                    col_val = [c for c in colunas_reais_banco if "valor" in c]
                    if col_val: dados_insert[col_val[0]] = limpar_numero(row.get("valor") or row.get("valor_previsto"))
                    
                elif tabela == "patrimonio":
                    if "descricao" in colunas_reais_banco: dados_insert["descricao"] = str(row.get("descricao") or row.get("item", "Bem"))
                    col_val = [c for c in colunas_reais_banco if "valor" in c]
                    if col_val: dados_insert[col_val[0]] = limpar_numero(row.get("valor") or row.get("valor_atual"))
                    
                elif tabela == "receita":
                    if "categoria" in colunas_reais_banco: dados_insert["categoria"] = str(row.get("categoria") or "Tributária")
                    if "orgao_id" in colunas_reais_banco: dados_insert["orgao_id"] = id_orgao_linha
                    if "ano" in colunas_reais_banco: dados_insert["ano"] = int(row.get("ano", 2024))
                    col_val = [c for c in colunas_reais_banco if "valor" in c or "arrecadado" in c]
                    if col_val: dados_insert[col_val[0]] = limpar_numero(row.get("valor") or row.get("valor_arrecadado") or 100.0)

                elif tabela == "convenio_recebido":
                    col_num = [c for c in colunas_reais_banco if "num" in c]
                    if col_num: dados_insert[col_num[0]] = str(row.get("numero") or idx)
                    if "objeto" in colunas_reais_banco: dados_insert["objeto"] = str(row.get("objeto", "Convênio"))
                    col_val = [c for c in colunas_reais_banco if "valor" in c]
                    if col_val: dados_insert[col_val[0]] = limpar_numero(row.get("valor") or row.get("valor_total"))

                elif tabela == "despesa":
                                    # Mapeia as colunas do CSV para os campos do banco de dados
                                    dados_insert["data"] = row.get("data")
                                    dados_insert["numero_empenho"] = str(row.get("numero_empenho", ""))
                                    dados_insert["descricao"] = str(row.get("descricao", "Despesa de Pessoal"))
                                    
                                    # Usa o ID que extraímos na Fase 1
                                    dados_insert["orgao_id"] = id_orgao_linha
                                    
                                    # Limpa valores monetários corretamente
                                    dados_insert["valor_pago"] = limpar_numero(row.get("valor_pago"))
                                    dados_insert["valor_empenhado"] = limpar_numero(row.get("valor_empenhado"))

                dados_finais = {k: v for k, v in dados_insert.items() if k in colunas_reais_banco}
                if not dados_finais: continue

                colunas_str = ", ".join([f'"{c}"' for c in dados_finais.keys()])
                placeholders = ", ".join(["%s"] * len(dados_finais))
                valores = list(dados_finais.values())
                
                query = f'INSERT INTO "{tabela}" ({colunas_str}) VALUES ({placeholders})'
                cursor.execute(query, valores)
                sucessos += 1
                
            except Exception as e:
                conn.rollback()
                continue
                
        conn.commit()
        print(f"✅ Sucesso! {sucessos} registros inseridos em '{tabela}'.")
        print("-" * 60)
        
    cursor.close()
    conn.close()
    print("\n🎉 ETL COMPLETO: Todas as tabelas e relacionamentos populados com sucesso!")

if __name__ == "__main__":
    forcar_populacao()
# gov_insight/src/carga_dados.py
import os
import glob
import pandas as pd
import psycopg2
from db import get_connection

# Caminho absoluto da pasta data baseado na raiz do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

def limpar_valor(valor):
    """Remove R$, pontos de milhar e converte vírgula para ponto."""
    if pd.isna(valor) or str(valor).strip() in ["#######", "-", "", "NaN"]:
        return None
    val_str = str(valor).replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(val_str)
    except ValueError:
        return None

def limpar_texto(texto):
    """Corrige encodings e remove espaços extras."""
    if pd.isna(texto):
        return None
    t = str(texto).strip()
    correcoes = {
        "CÃ,MARA": "CÂMARA", "CÃM": "CÂMARA", "PREFEITUR": "PREFEITURA", 
        "EstatutÃ¡ri": "Estatutário", "ProteÃ§Ã£o": "Proteção", 
        "AssistÃªncia": "Assistência", "BalneÃ¡ric": "Balneário",
        "BrasÃ-lia": "Brasília", "PrestaÃ§Ã£": "Prestação", 
        "DescriÃ§Ã£o": "Descrição", "Valor orÃ§": "Valor Orçado"
    }
    for errado, correto in correcoes.items():
        if errado in t:
            t = t.replace(errado, correto)
    return t

def formatar_data(data_str):
    """Formata datas do padrão brasileiro para o ISO (AAAA-MM-DD) do Postgres."""
    if pd.isna(data_str) or str(data_str).strip() in ["-", "", "NaN"]:
        return None
    try:
        return pd.to_datetime(data_str, dayfirst=True).strftime('%Y-%m-%d')
    except:
        return None

# ==========================================
# FUNÇÕES DE AUXÍLIO PARA CHAVES ESTRANGEIRAS
# ==========================================
def buscar_ou_inserir_orgao(cursor, nome_orgao):
    nome_limpo = limpar_texto(nome_orgao)
    if not nome_limpo:
        nome_limpo = "ÓRGÃO NÃO ESPECIFICADO"
    cursor.execute("SELECT id FROM orgao WHERE nome = %s;", (nome_limpo,))
    res = cursor.fetchone()
    if res:
        return res[0]
    cursor.execute("INSERT INTO orgao (nome) VALUES (%s) RETURNING id;", (nome_limpo,))
    return cursor.fetchone()[0]

def buscar_ou_inserir_fornecedor(cursor, nome_fornecedor):
    nome_limpo = limpar_texto(nome_fornecedor)
    if not nome_limpo:
        nome_limpo = "FORNECEDOR NÃO ESPECIFICADO"
    cursor.execute("SELECT id FROM fornecedor WHERE nome = %s;", (nome_limpo,))
    res = cursor.fetchone()
    if res:
        return res[0]
    cursor.execute("INSERT INTO fornecedor (nome) VALUES (%s) RETURNING id;", (nome_limpo,))
    return cursor.fetchone()[0]

def buscar_servidor_id(cursor, nome_servidor):
    nome_limpo = limpar_texto(nome_servidor)
    if not nome_limpo:
        return None
    cursor.execute("SELECT id FROM servidor WHERE nome = %s LIMIT 1;", (nome_limpo,))
    res = cursor.fetchone()
    return res[0] if res else None

# ==========================================
# ROTINAS DE PROCESSAMENTO DE CADA DIRETÓRIO
# ==========================================
def carregar_tudo():
    conn = get_connection()
    cur = conn.cursor()
    print("📥 Iniciando processamento completo dos arquivos CSV do Portal da Transparência...")

    # 1. RECEITAS
    path_receitas = os.path.join(DATA_DIR, "receitas", "receitas_unificado.csv")
    if os.path.exists(path_receitas):
        print("-> Processando: receitas_unificado.csv")
        df = pd.read_csv(path_receitas, sep=None, engine='python', encoding='latin1')
        for _, row in df.iterrows():
            try:
                buscar_ou_inserir_orgao(cur, row.get('rel_orgao'))
                cur.execute("""
                    INSERT INTO receita (descricao, valor_orcado, valor_arrecadado) 
                    VALUES (%s, %s, %s);
                """, (limpar_texto(row.get('DescriÃ§Ã£o')), limpar_valor(row.get('Valor orÃ§')), limpar_valor(row.get('Valor arrec'))))
            except Exception:
                conn.rollback()
                cur = conn.cursor()

    # 2. PATRIMÔNIO
    path_patrimonio = os.path.join(DATA_DIR, "patrimonio", "patrimonio.csv")
    if os.path.exists(path_patrimonio):
        print("-> Processando: patrimonio.csv")
        df = pd.read_csv(path_patrimonio, sep=None, engine='python', encoding='latin1')
        for _, row in df.iterrows():
            try:
                cur.execute("""
                    INSERT INTO patrimonio (entidade, tipo, natureza, identificacao, descricao, data_aquisicao, centro_custo, situacao, valor_atual, tipo_aquisicao)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, (limpar_texto(row.get('rel_entidade')), limpar_texto(row.get('tipo')), limpar_texto(row.get('natureza')), 
                      str(row.get('identificac')), limpar_texto(row.get('descricao')), formatar_data(row.get('data_aquis')), 
                      limpar_texto(row.get('rel_orgao')), limpar_texto(row.get('situacao')), limpar_valor(row.get('valor_atual')), limpar_texto(row.get('tipo_aquisi'))))
            except Exception:
                conn.rollback()
                cur = conn.cursor()

    # 3. OBRAS
    path_obras = os.path.join(DATA_DIR, "obra", "obras.csv")
    if os.path.exists(path_obras):
        print("-> Processando: obras.csv")
        df = pd.read_csv(path_obras, sep=None, engine='python', encoding='latin1')
        for _, row in df.iterrows():
            try:
                cur.execute("""
                    INSERT INTO obra (tipo, categoria, descricao, data_inicio, previsao_conclusao, valor_previsto, valor_atualizado, situacao, percentual_execucao)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, (limpar_texto(row.get('tipo')), limpar_texto(row.get('categoria')), limpar_texto(row.get('descricao')), 
                      formatar_data(row.get('data_inicio')), formatar_data(row.get('previsao_c')), limpar_valor(row.get('valor_previ')), 
                      limpar_valor(row.get('valor_atual')), limpar_texto(row.get('situacao')), limpar_valor(row.get('percentual_execucao'))))
            except Exception:
                conn.rollback()
                cur = conn.cursor()

    # 4. LICITAÇÕES
    path_licitacoes = os.path.join(DATA_DIR, "licitacoes", "licitacoes.csv")
    if os.path.exists(path_licitacoes):
        print("-> Processando: licitacoes.csv")
        df = pd.read_csv(path_licitacoes, sep=None, engine='python', encoding='latin1')
        for _, row in df.iterrows():
            try:
                cur.execute("""
                    INSERT INTO licitacao (numero_processo, ano_processo, numero_licitacao, ano_licitacao, objeto, modalidade, situacao, valor_estimado, valor_homologado)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, (str(row.get('numero_do')), row.get('ano_proce'), str(row.get('numero_da')), row.get('ano_da_lic'), 
                      limpar_texto(row.get('objeto')), limpar_texto(row.get('modalide')), limpar_texto(row.get('situacao')), 
                      limpar_valor(row.get('valor_estin')), limpar_valor(row.get('valor_homologado'))))
            except Exception:
                conn.rollback()
                cur = conn.cursor()

    # 5. PROGRAMAS E AÇÕES (DESPESAS)
    path_prog = os.path.join(DATA_DIR, "despesa_programa", "despesas_programas_acoes.CSV")
    if os.path.exists(path_prog):
        print("-> Processando: despesas_programas_acoes.CSV")
        df = pd.read_csv(path_prog, sep=None, engine='python', encoding='latin1')
        for _, row in df.iterrows():
            try:
                cur.execute("""
                    INSERT INTO despesa_programa (programa, funcao, acao, codigo_despesa, valor_orcado, valor_atualizado, valor_empenhado, valor_liquidado, valor_pago)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, (limpar_texto(row.get('nome_do_p')), limpar_texto(row.get('funcão')), limpar_texto(row.get('descricao_')), 
                      str(row.get('código_da_')), limpar_valor(row.get('valor_orça')), limpar_valor(row.get('valor_atual')), 
                      limpar_valor(row.get('empenhad')), limpar_valor(row.get('liquido_atu')), limpar_valor(row.get('valor_pago_'))))
            except Exception:
                conn.rollback()
                cur = conn.cursor()

    # 6. CONVÊNIOS REPASSADOS / RECEBIDOS
    path_convenios = os.path.join(DATA_DIR, "convenios", "convenios_recebidos_padronizado.csv")
    if os.path.exists(path_convenios):
        print("-> Processando: convenios_recebidos_padronizado.csv")
        df = pd.read_csv(path_convenios, sep=None, engine='python', encoding='latin1')
        for _, row in df.iterrows():
            try:
                cur.execute("""
                    INSERT INTO convenio_repassado (objeto, situacao)
                    VALUES (%s, %s);
                """, (limpar_texto(row.get('objeto')), 'CONCLUÍDO'))
            except Exception:
                conn.rollback()
                cur = conn.cursor()

    # 7. SERVIDORES (Alimenta 'orgao' e cria 'servidor') -> Blindado contra nomes nulos!
    path_servidores = os.path.join(DATA_DIR, "servidores", "servidores_remuneracao.CSV")
    if os.path.exists(path_servidores):
        print("-> Processando: servidores_remuneracao.CSV")
        df = pd.read_csv(path_servidores, sep=None, engine='python', encoding='latin1')
        for _, row in df.iterrows():
            try:
                nome = limpar_texto(row.get('nome_do_s') or row.get('nome_do_servidor') or row.get('nome'))
                if not nome:
                    continue # Pula a linha se não houver identificação do servidor
                    
                orgao_id = buscar_ou_inserir_orgao(cur, row.get('rel_orgao') or row.get('rel_entidade'))
                cur.execute("""
                                    INSERT INTO servidor (nome, orgao_id, data_admissao, tipo_matricula, vinculo, cargo, remuneracao, situacao)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                                """, (nome, orgao_id, formatar_data(row.get('data_de_ad') or row.get('data_de_admissao')), 
                                    str(row.get('matricula', '')), limpar_texto(row.get('vinculo_em') or row.get('vinculo_empregaticio')), 
                                    limpar_texto(row.get('cargo')), 
                                    limpar_valor(row.get('remuneracao_bruta') or row.get('reumuneracao_contratual')), 
                                    limpar_texto(row.get('situacao'))))
            except Exception:
                conn.rollback()
                cur = conn.cursor()

    # 8. DIÁRIAS (Depende de 'servidor')
    path_diarias = os.path.join(DATA_DIR, "diarias", "diarias.CSV")
    if os.path.exists(path_diarias):
        print("-> Processando: diarias.CSV")
        df = pd.read_csv(path_diarias, sep=None, engine='python', encoding='latin1')
        for _, row in df.iterrows():
            try:
                serv_id = buscar_servidor_id(cur, row.get('rel_servido'))
                cur.execute("""
                    INSERT INTO diaria (ano, servidor_id, numero, quantidade, valor_total, periodo, finalidade, destino)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """, (int(row.get('ano', 2026)), serv_id, str(row.get('numero')), int(row.get('quantidade', 0)), 
                      limpar_valor(row.get('valor')), limpar_texto(row.get('periodo')), limpar_texto(row.get('finalidade')), limpar_texto(row.get('Local de destino'))))
            except Exception:
                conn.rollback()
                cur = conn.cursor()

    # 9. CONTRATOS (Alimenta 'fornecedor' e cria 'contrato')
    path_contratos = os.path.join(DATA_DIR, "contratos", "contratos.CSV")
    if os.path.exists(path_contratos):
        print("-> Processando: contratos.CSV")
        df = pd.read_csv(path_contratos, sep=None, engine='python', encoding='latin1')
        for _, row in df.iterrows():
            try:
                forn_id = buscar_ou_inserir_fornecedor(cur, row.get('rel_empres'))
                cur.execute("""
                    INSERT INTO contrato (numero, data_assinatura, processo, tipo, object, situacao, valor_final, fornecedor_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """, (str(row.get('numero_do')), formatar_data(row.get('data_assin')), str(row.get('ano_do_pr')), 
                      limpar_texto(row.get('tipo_de_co')), limpar_texto(row.get('objeto_do_')), limpar_texto(row.get('situacao')), 
                      limpar_valor(row.get('valor_final')), forn_id))
            except Exception:
                conn.rollback()
                cur = conn.cursor()

    # 10. DESPESAS: EMENDAS E PESSOAL
    arquivos_despesas = [
        os.path.join(DATA_DIR, "despesas_emenda_parlamentar", "despesas_emendas_parlamentares.CSV"),
        os.path.join(DATA_DIR, "depesas_empenho", "despesas_com_pessoal.CSV")
    ]
    
    for path_desp in arquivos_despesas:
        if os.path.exists(path_desp):
            print(f"-> Processando despesa: {os.path.basename(path_desp)}")
            df = pd.read_csv(path_desp, sep=None, engine='python', encoding='latin1')
            for _, row in df.iterrows():
                try:
                    forn_id = buscar_ou_inserir_fornecedor(cur, row.get('rel_empres'))
                    orgao_id = buscar_ou_inserir_orgao(cur, row.get('rel_orgao') or "Prefeitura Municipal")
                    
                    cur.execute("""
                        INSERT INTO despesa (numero_empenho, data, descricao, valor_empenhado, valor_liquidado, valor_pago, fornecedor_id, orgao_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                    """, (str(row.get('numero_do')), formatar_data(row.get('data_do_e')), limpar_texto(row.get('histórico_c')), 
                          limpar_valor(row.get('valor_do_e')), limpar_valor(row.get('valor_liqui')), limpar_valor(row.get('valor_pago')), forn_id, orgao_id))
                except Exception:
                    conn.rollback()
                    cur = conn.cursor()

    conn.commit()
    cur.close()
    conn.close()
    print("🎉 Carga completa de todas as pastas executada com sucesso!")

if __name__ == "__main__":
    carregar_tudo()
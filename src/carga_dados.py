import os
import pandas as pd
from db import get_connection
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


# =====================================================
# FUNÇÕES AUXILIARES
# =====================================================

def limpar_percentual(valor):
    v = limpar_valor(valor)
    if v > 100:
        v = v / 100
    return round(v, 2)


def normalizar_nome(texto: str):
    if not texto:
        return None
    texto = texto.strip().upper()
    texto = " ".join(texto.split())
    return texto


def limpar_nome_servidor(nome):
    if not nome:
        return None
    nome = re.sub(r"^\d{2,3}\.\d{3}\.\d{3}\s*", "", nome)
    nome = re.sub(r"^[\d.\-/]+\s*", "", nome)
    return normalizar_nome_pessoa(nome)


def normalizar_nome_pessoa(nome):
    if not nome:
        return None
    nome = str(nome)
    nome = nome.strip()
    nome = re.sub(r"\s+", " ", nome)
    nome = nome.upper()
    return nome


def limpar_texto(valor):
    if valor is None or pd.isna(valor):
        return ""
    return str(valor).strip()


def normalizar_orgao(nome):
    if nome is None or pd.isna(nome):
        return None
    nome = str(nome)
    nome = " ".join(nome.split()).strip().upper()
    nome = nome.replace("  ", " ")
    return nome or None


def normalizar_orgao_servidores(nome):
    """Normaliza o nome do órgão vindo do CSV de servidores,
    consolidando variações como 'CAMARA VEREADORES' no nome canônico."""
    if not nome or pd.isna(nome):
        return None

    nome = str(nome).strip().upper()
    nome = " ".join(nome.split())

    substituicoes = {
        "CAMARA VEREADORES":        "CÂMARA MUNICIPAL DE BALNEÁRIO GAIVOTA",
        "CÂMARA DE VEREADORES":     "CÂMARA MUNICIPAL DE BALNEÁRIO GAIVOTA",
        "CAMARA DE VEREADORES":     "CÂMARA MUNICIPAL DE BALNEÁRIO GAIVOTA",
        "CAMARA MUNICIPAL":         "CÂMARA MUNICIPAL DE BALNEÁRIO GAIVOTA",
    }

    return substituicoes.get(nome, nome)


def normalizar_entidade(nome):
    if nome is None or pd.isna(nome):
        return None

    nome = str(nome).strip().upper()

    substituicoes = {
        # Prefeitura
        "PREFEITURA MUNICIPAL DE BALNEÁRIO GAIVOTA":
            "PREFEITURA MUNICIPAL BALNEÁRIO GAIVOTA",
        "PREFEITURA MUNICIPAL DE BALNEARIO GAIVOTA":
            "PREFEITURA MUNICIPAL BALNEÁRIO GAIVOTA",

        # Fundo de Saúde — todas as variações conhecidas
        "FUNDO MUNICIPAL DE SAUDE":
            "FUNDO MUNICIPAL DE SAÚDE BALNEÁRIO GAIVOTA",
        "FUNDO MUNICIPAL DE SAÚDE":
            "FUNDO MUNICIPAL DE SAÚDE BALNEÁRIO GAIVOTA",
        "FUNDO MUNICIPAL DE SAUDE BALNEARIO GAIVOTA":
            "FUNDO MUNICIPAL DE SAÚDE BALNEÁRIO GAIVOTA",
        "FUNDO MUNICIPAL DE SAÚDE BALNEÁRIO GAIVOTA":
            "FUNDO MUNICIPAL DE SAÚDE BALNEÁRIO GAIVOTA",
        "FUNDO MUNICIPAL SAÚDE BALNEÁRIO GAIVOTA":
            "FUNDO MUNICIPAL DE SAÚDE BALNEÁRIO GAIVOTA",
        "FUNDO MUNICIPAL SAUDE BALNEARIO GAIVOTA":
            "FUNDO MUNICIPAL DE SAÚDE BALNEÁRIO GAIVOTA",

        # Câmara — todas as variações conhecidas
        "CAMARA MUNICIPAL DE BALNEARIO GAIVOTA":
            "CÂMARA MUNICIPAL DE BALNEÁRIO GAIVOTA",
        "CÂMARA MUNICIPAL BALNEÁRIO GAIVOTA":
            "CÂMARA MUNICIPAL DE BALNEÁRIO GAIVOTA",
        "CAMARA MUNICIPAL BALNEARIO GAIVOTA":
            "CÂMARA MUNICIPAL DE BALNEÁRIO GAIVOTA",
        "CAMARA VEREADORES":
            "CÂMARA MUNICIPAL DE BALNEÁRIO GAIVOTA",
        "CÂMARA DE VEREADORES":
            "CÂMARA MUNICIPAL DE BALNEÁRIO GAIVOTA",
        "CAMARA DE VEREADORES":
            "CÂMARA MUNICIPAL DE BALNEÁRIO GAIVOTA",
    }

    return substituicoes.get(nome, nome)


def limpar_valor(valor):
    if valor is None or pd.isna(valor):
        return 0.0
    valor = str(valor).strip()
    if valor in ["", "-", " -"]:
        return 0.0
    valor = (
        valor.replace("R$", "")
             .replace(".", "")
             .replace(",", ".")
             .strip()
    )
    try:
        return float(valor)
    except:
        return 0.0


def limpar_inteiro(valor):
    if valor is None or pd.isna(valor):
        return None
    valor = str(valor).strip()
    if valor in ["", "-", " -", "nan", "None"]:
        return None
    try:
        return int(float(valor))
    except:
        return None


def formatar_data(data_str):
    if data_str is None or pd.isna(data_str):
        return None
    data_str = str(data_str).strip()
    if data_str in ["", "-", " -"]:
        return None
    try:
        return pd.to_datetime(data_str, dayfirst=True).strftime("%Y-%m-%d")
    except:
        return None


# =====================================================
# LEITURA CSV
# =====================================================

def ler_csv(caminho):
    try:
        df = pd.read_csv(caminho, sep=None, engine="python", encoding="utf-8")
    except:
        df = pd.read_csv(caminho, sep=None, engine="python", encoding="latin1")
    df.columns = df.columns.str.strip().str.lower()
    return df


# =====================================================
# CADASTROS BASE
# =====================================================

def popular_cadastros_base(conn):
    cur = conn.cursor()

    entidades = set()
    orgaos = set()
    empresas = set()

    arquivos = [
        "contratos/contratos.CSV",
        "licitacoes/licitacoes.csv",
        "servidores/servidores_remuneracao.CSV",
        "diarias/diarias.CSV",
        "obra/obras.csv",
        "patrimonio/patrimonio.csv",
        "convenios/convenios_recebidos.csv",
        "despesa_programa/despesas_programas_acoes.CSV",
        "receitas/receitas_unificado.csv",
        "depesas_empenho/despesas_com_pessoal.CSV",
        "despesas_emenda_parlamentar/despesas_emendas_parlamentares.CSV",
    ]

    for arquivo in arquivos:
        caminho = os.path.join(DATA_DIR, arquivo)
        if not os.path.exists(caminho):
            continue

        df = ler_csv(caminho)

        if "rel_entidade" in df.columns:
            entidades.update(
                normalizar_entidade(x)
                for x in df["rel_entidade"].dropna().astype(str)
            )

        for col in ["rel_orgao", "órgão", "rel_orgao_concedente"]:
            if col in df.columns:
                # CSV de servidores usa normalização especial para órgãos
                if "servidores" in arquivo:
                    orgaos.update(
                        normalizar_orgao_servidores(x)
                        for x in df[col].dropna().astype(str)
                    )
                else:
                    orgaos.update(
                        normalizar_orgao(x)
                        for x in df[col].dropna().astype(str)
                    )

        if "rel_empresas" in df.columns:
            empresas.update(
                x.strip().upper()
                for x in df["rel_empresas"].dropna().astype(str)
            )

    for e in entidades:
        cur.execute("""
            INSERT INTO gov.entidades (nome_entidade)
            VALUES (%s)
            ON CONFLICT DO NOTHING
        """, (e,))

    for o in orgaos:
        cur.execute("""
            INSERT INTO gov.orgao (nome_orgao, nome_entidade)
            VALUES (%s, NULL)
            ON CONFLICT DO NOTHING
        """, (o,))

    i = 1
    for emp in empresas:
        cur.execute("""
            INSERT INTO gov.empresas (cpf_cnpj, nome_empresa)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (f"SEM_CNPJ_{i}", emp))
        i += 1

    conn.commit()
    cur.close()
    print("✅ Cadastros base concluídos.")


# =====================================================
# CONTRATOS
# =====================================================

def carregar_contratos(conn, df):
    cur = conn.cursor()
    total = 0
    erros = 0
    ignorados = 0

    for _, row in df.iterrows():
        try:
            nome_entidade = normalizar_entidade(row.get("rel_entidade"))
            numero_contrato = limpar_inteiro(row.get("numero_do_contrato"))
            numero_processo = limpar_inteiro(row.get("numero_do_processo"))
            data_assinatura = formatar_data(row.get("data_assinatura"))

            if (
                numero_contrato is None
                or numero_processo is None
                or data_assinatura is None
            ):
                ignorados += 1
                continue

            cur.execute("""
                INSERT INTO gov.contratos (
                    numero_do_contrato,
                    numero_do_processo,
                    data_de_assinatura,
                    nome_entidade,
                    valor_final
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """, (
                numero_contrato,
                numero_processo,
                data_assinatura,
                nome_entidade,
                limpar_valor(row.get("valor_final"))
            ))

            total += 1

        except Exception as e:
            conn.rollback()
            erros += 1

    conn.commit()
    cur.close()
    print(f"✅ Contratos inseridos: {total}")


# =====================================================
# LICITAÇÕES
# =====================================================

def carregar_licitacoes(conn):
    caminho = os.path.join(DATA_DIR, "licitacoes", "licitacoes.csv")
    if not os.path.exists(caminho):
        return

    df = ler_csv(caminho)
    cur = conn.cursor()
    total = 0
    erros = 0

    for _, row in df.iterrows():
        try:
            numero_processo = limpar_inteiro(row.get("numero_do_processo"))
            numero_licitacao = limpar_inteiro(row.get("numero_da_licitacao"))
            data_criacao = formatar_data(row.get("data_de_criacao"))

            if (
                numero_processo is None
                or numero_licitacao is None
                or data_criacao is None
            ):
                continue

            cur.execute("""
                INSERT INTO gov.licitacoes (
                    numero_do_processo,
                    numero_da_licitacao,
                    nome_entidade,
                    ano_processo,
                    ano_da_licitacao,
                    objeto,
                    modalidade,
                    data_de_abertura,
                    data_de_publicacao,
                    tipo_de_objeto,
                    forma_de_julgamento,
                    data_de_homologacao,
                    situacao,
                    data_de_anulacao,
                    data_de_criacao,
                    data_do_julgamento,
                    data_da_revogacao,
                    forma_de_contratacao,
                    valor_estimado,
                    valor_homologado
                )
                VALUES (
                    %s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s
                )
                ON CONFLICT DO NOTHING
            """, (
                numero_processo,
                numero_licitacao,
                str(normalizar_entidade(row.get("rel_entidade"))).strip(),
                limpar_inteiro(row.get("ano_processo")),
                limpar_inteiro(row.get("ano_da_licitacao")),
                row.get("objeto"),
                row.get("modalide"),
                formatar_data(row.get("data_de_abertura")),
                formatar_data(row.get("data_de_publicacao")),
                row.get("tipo_de_objeto"),
                row.get("forma_de_julgamento"),
                formatar_data(row.get("data_da_homologacao")),
                row.get("situacao"),
                formatar_data(row.get("data_de_anulacao")),
                data_criacao,
                formatar_data(row.get("data_do_julgamento")),
                formatar_data(row.get("data_da_revogacao")),
                row.get("forma_de_contratacao"),
                limpar_valor(row.get("valor_estimado")),
                limpar_valor(row.get("valor_homologado"))
            ))

            total += 1

        except Exception as e:
            conn.rollback()
            erros += 1

    conn.commit()
    cur.close()
    print(f"✅ Licitações inseridas: {total}")


# =====================================================
# SERVIDORES
# =====================================================

def carregar_servidores(conn):
    caminho = os.path.join(DATA_DIR, "servidores", "servidores_remuneracao.CSV")
    if not os.path.exists(caminho):
        return

    df = ler_csv(caminho)
    cur = conn.cursor()
    total = 0
    erros = 0

    for _, row in df.iterrows():
        try:
            matricula = limpar_inteiro(row.get("matricula"))
            if not matricula:
                continue

            nome = normalizar_nome_pessoa(row.get("nome_do_servidor"))

            cur.execute("""
                INSERT INTO gov.servidores (
                    matricula,
                    nome_entidade,
                    nome_orgao,
                    nome_do_servidor,
                    cargo,
                    vinculo_empregaticio,
                    nivel_salarial,
                    organograma,
                    contribuicao_empregado_rgps,
                    contribuicao_empregado_rat_fat,
                    contribuicao_patronal_rgps,
                    data_de_admissao,
                    situacao,
                    remuneracao_contratual,
                    remuneracao_bruta,
                    remuneracao_liquida,
                    efetivo_em_cargo_comissionado
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (matricula)
                DO UPDATE SET
                    nome_do_servidor               = EXCLUDED.nome_do_servidor,
                    cargo                          = EXCLUDED.cargo,
                    vinculo_empregaticio           = EXCLUDED.vinculo_empregaticio,
                    nivel_salarial                 = EXCLUDED.nivel_salarial,
                    organograma                    = EXCLUDED.organograma,
                    contribuicao_empregado_rgps    = EXCLUDED.contribuicao_empregado_rgps,
                    contribuicao_empregado_rat_fat = EXCLUDED.contribuicao_empregado_rat_fat,
                    contribuicao_patronal_rgps     = EXCLUDED.contribuicao_patronal_rgps,
                    data_de_admissao               = EXCLUDED.data_de_admissao,
                    situacao                       = EXCLUDED.situacao,
                    remuneracao_contratual         = EXCLUDED.remuneracao_contratual,
                    remuneracao_bruta              = EXCLUDED.remuneracao_bruta,
                    remuneracao_liquida            = EXCLUDED.remuneracao_liquida,
                    efetivo_em_cargo_comissionado  = EXCLUDED.efetivo_em_cargo_comissionado
            """, (
                matricula,
                normalizar_entidade(row.get("rel_entidade")),
                str(normalizar_orgao_servidores(row.get("rel_orgao", ""))).strip(),
                nome,
                row.get("cargo"),
                row.get("vinculo_empregaticio"),
                row.get("nivel_salarial"),
                row.get("organograma"),
                limpar_valor(row.get("contribuicao_empregado_rgps")),
                limpar_valor(row.get("contribuicao_empregado_rat_fat")),
                limpar_valor(row.get("contribuicao_patronal_rgps")),
                formatar_data(row.get("data_de_admissao")),
                row.get("situacao"),
                limpar_valor(row.get("remuneracao_contratual")),
                limpar_valor(row.get("remuneracao_bruta")),
                limpar_valor(row.get("remuneracao_liquida")),
                row.get("efetivo_em_cargo_comissionado")
            ))

            total += 1

        except Exception as e:
            conn.rollback()
            erros += 1

    conn.commit()
    cur.close()
    print(f"✅ Servidores processados: {total}")


# =====================================================
# DIÁRIAS
# =====================================================

def carregar_diarias(conn):
    path = os.path.join(DATA_DIR, "diarias", "diarias.CSV")
    if not os.path.exists(path):
        return

    df = ler_csv(path)
    cur = conn.cursor()
    total = 0
    sem_servidor = 0
    erros_sql = 0

    for _, row in df.iterrows():
        try:
            numero = limpar_inteiro(row.get("numero"))
            if not numero:
                continue

            nome_servidor = limpar_nome_servidor(row.get("rel_servidor"))
            entidade = normalizar_entidade(row.get("rel_entidade"))

            # Busca exata primeiro
            cur.execute("""
                SELECT matricula
                FROM gov.servidores
                WHERE gov.unaccent_immutable(UPPER(TRIM(nome_do_servidor)))
                    = gov.unaccent_immutable(%s)
                LIMIT 1
            """, (nome_servidor,))
            row_srv = cur.fetchone()

            # Fallback fuzzy se não encontrou
            if not row_srv:
                cur.execute("""
                    SELECT matricula, nome_do_servidor,
                        public.similarity(
                            gov.unaccent_immutable(UPPER(TRIM(nome_do_servidor))),
                            gov.unaccent_immutable(%s)
                        ) AS sim
                    FROM gov.servidores
                    ORDER BY sim DESC
                    LIMIT 1
                """, (nome_servidor,))
                row_fuzzy = cur.fetchone()
                if row_fuzzy and row_fuzzy[2] >= 0.6:
                    row_srv = row_fuzzy

            matricula_servidor = row_srv[0] if row_srv else None

            if matricula_servidor is None:
                sem_servidor += 1

            cur.execute("""
                INSERT INTO gov.diarias (
                    numero,
                    nome_entidade,
                    matricula,
                    cnpj_cpf,
                    quantidade,
                    valor_unitario,
                    data_inicial,
                    data_final,
                    finalidade,
                    local_de_origem,
                    local_de_destino
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (numero) DO NOTHING
            """, (
                numero,
                entidade,
                matricula_servidor,
                limpar_texto(row.get("cnpj/cpf credor"))[:50],
                limpar_inteiro(row.get("quantidade")),
                limpar_valor(row.get("valor_unitario")),
                formatar_data(row.get("data_inicial")),
                formatar_data(row.get("data_final")),
                row.get("finalidade"),
                row.get("local de origem"),
                row.get("local de destino"),
            ))

            total += 1

        except Exception as e:
            conn.rollback()
            erros_sql += 1

    conn.commit()
    cur.close()
    print(f"✅ Diárias inseridas: {total}")


# =====================================================
# PATRIMÔNIO
# =====================================================

def carregar_patrimonio(conn):
    path = os.path.join(DATA_DIR, "patrimonio", "patrimonio.csv")
    if not os.path.exists(path):
        return

    df = ler_csv(path)
    cur = conn.cursor()
    total = 0
    erros = 0

    for _, row in df.iterrows():
        try:
            identificacao = limpar_inteiro(row.get("identificacao"))
            if identificacao is None:
                continue

            cur.execute("""
                INSERT INTO gov.patrimonio (
                    identificacao,
                    nome_entidade,
                    nome_orgao,
                    tipo,
                    natureza,
                    descricao,
                    data_aquisicao,
                    situacao,
                    valor_atual,
                    tipo_aquisicao
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT DO NOTHING;
            """, (
                identificacao,
                normalizar_entidade(row.get("rel_entidade")),
                normalizar_orgao(row.get("rel_orgao")),
                row.get("tipo"),
                row.get("natureza"),
                row.get("descricao"),
                formatar_data(row.get("data_aquisicao")),
                row.get("situacao"),
                limpar_valor(row.get("valor_atual")),
                row.get("tipo_aquisicao")
            ))

            total += 1

        except Exception as e:
            conn.rollback()
            erros += 1

    conn.commit()
    cur.close()
    print(f"✅ Patrimônios inseridos: {total}")


# =====================================================
# OBRAS
# =====================================================

def carregar_obras(conn):
    path = os.path.join(DATA_DIR, "obra", "obras.csv")
    if not os.path.exists(path):
        return

    df = ler_csv(path)
    cur = conn.cursor()
    total = 0
    erros = 0

    for _, row in df.iterrows():
        try:
            cur.execute("""
                INSERT INTO gov.obras (
                    id_obra,
                    nome_entidade,
                    tipo,
                    categoria,
                    descricao,
                    data_inicio,
                    previsao_conclusao,
                    valor_previsto,
                    valor_alterado,
                    valor_atualizado,
                    situacao,
                    percentual_execucao
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT DO NOTHING;
            """, (
                limpar_inteiro(row.get("id_obra")),
                normalizar_entidade(row.get("rel_entidade")),
                row.get("tipo"),
                row.get("categoria"),
                row.get("descricao"),
                formatar_data(row.get("data_inicio")),
                formatar_data(row.get("previsao_conclusao")),
                limpar_valor(row.get("valor_previsto")),
                limpar_valor(row.get("valor_alterado")),
                limpar_valor(row.get("valor_atualizado")),
                row.get("situacao"),
                limpar_percentual(row.get("percentual_execucao"))
            ))

            total += 1

        except Exception as e:
            conn.rollback()
            erros += 1

    conn.commit()
    cur.close()
    print(f"✅ Obras inseridas: {total}")

# =====================================================
# CONVÊNIOS
# =====================================================

def carregar_convenios(conn):
    path = os.path.join(DATA_DIR, "convenios", "convenios_recebidos.csv")
    if not os.path.exists(path):
        return

    df = ler_csv(path)
    cur = conn.cursor()
    total = 0
    erros = 0

    for _, row in df.iterrows():
        try:
            orgao = normalizar_orgao(row.get("rel_orgao_concedente"))

            cur.execute("""
                INSERT INTO gov.convenios (
                    numero_convenio_recebido,
                    nome_orgao,
                    objeto,
                    data_assinatura,
                    tipo,
                    vigencia,
                    valor,
                    contrapartida
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT DO NOTHING;
            """, (
                limpar_texto(row.get("numero_do_convenio_recebido")),
                orgao,
                limpar_texto(row.get("objeto")),
                formatar_data(row.get("data_assinatura")),
                limpar_texto(row.get("tipo")),
                limpar_texto(row.get("vigencia")),
                limpar_valor(row.get("valor")),
                limpar_valor(row.get("contrapartida"))
            ))

            total += 1

        except Exception as e:
            conn.rollback()
            erros += 1

    conn.commit()
    cur.close()
    print(f"✅ Convênios inseridos: {total}")

# =====================================================
# DESPESAS COM PESSOAL
# =====================================================

def carregar_despesas_pessoal(conn):
    path = os.path.join(DATA_DIR, "depesas_empenho", "despesas_com_pessoal.CSV")
    if not os.path.exists(path):
        return

    df = ler_csv(path)
    cur = conn.cursor()
    total = 0
    erros = 0

    for _, row in df.iterrows():
        try:
            numero = limpar_inteiro(row.get("numero_empenho"))
            if numero is None:
                continue

            cur.execute("""
                INSERT INTO gov.despesas_com_pessoal (
                    numero_empenho,
                    data_despesa,
                    rel_orgao,
                    detalhamento_do_elemento,
                    descricao,
                    valor_empenhado,
                    valor_liquido,
                    valor_pago
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT DO NOTHING;
            """, (
                numero,
                formatar_data(row.get("data")),
                normalizar_orgao(row.get("rel_orgao")),
                limpar_texto(row.get("detalhamento_do_elemento")),
                limpar_texto(row.get("descricao")),
                limpar_valor(row.get("valor_empenhado")),
                limpar_valor(row.get("valor_liquido")),
                limpar_valor(row.get("valor_pago")),
            ))

            total += 1

        except Exception as e:
            conn.rollback()
            erros += 1

    conn.commit()
    cur.close()
    print(f"✅ Despesas com pessoal inseridas: {total}")

# =====================================================
# DESPESAS PROGRAMAS E AÇÕES
# =====================================================

def carregar_despesas_programas(conn):
    path = os.path.join(DATA_DIR, "despesa_programa", "despesas_programas_acoes.CSV")
    if not os.path.exists(path):
        return

    df = ler_csv(path)
    # Normaliza nomes de colunas com caracteres especiais
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"[^\w\s]", "", regex=True)
        .str.replace(r"\s+", "_", regex=True)
    )

    cur = conn.cursor()
    total = 0
    erros = 0

    for _, row in df.iterrows():
        try:
            codigo = (
                limpar_inteiro(row.get("cdigo_da_despesa"))
                or limpar_inteiro(row.get("codigo_da_despesa"))
            )
            if codigo is None:
                continue

            cur.execute("""
                INSERT INTO gov.despesas_programas_acoes (
                    codigo_da_despesa,
                    nome_entidade,
                    nome_do_programa,
                    funcao,
                    descricao_programa,
                    valor_orcado_despesa,
                    valor_atualizado_despesa,
                    empenhado_atualizado_despesa,
                    liquido_atualizado_da_despesa,
                    valor_pago_atualizado_despesa
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT DO NOTHING;
            """, (
                codigo,
                normalizar_entidade(row.get("rel_entidade")),
                limpar_texto(row.get("nome_do_programa")),
                limpar_texto(row.get("funcao")),
                limpar_texto(row.get("descricao_programa")),
                limpar_valor(row.get("valor_orado_despesa")
                    or row.get("valor_orcado_despesa")),
                limpar_valor(row.get("valor_atualizado_despesa")),
                limpar_valor(row.get("empenhado_atualizado_da_despesa")
                    or row.get("empenhado_atualizado_despesa")),
                limpar_valor(row.get("liquido_atualizado_da_despesa")),
                limpar_valor(row.get("valor_pago_atualizado_despesa")),
            ))

            total += 1

        except Exception as e:
            conn.rollback()
            erros += 1

    conn.commit()
    cur.close()

# =====================================================
# EMENDAS PARLAMENTARES
# =====================================================

def carregar_emendas_parlamentares(conn):
    path = os.path.join(DATA_DIR, "despesas_emenda_parlamentar", "despesas_emendas_parlamentares.CSV")
    if not os.path.exists(path):
        return

    df = ler_csv(path)
    # Normaliza colunas com caracteres especiais
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"[^\w\s]", "", regex=True)
        .str.replace(r"\s+", "_", regex=True)
    )

    cur = conn.cursor()
    total = 0
    erros = 0

    for _, row in df.iterrows():
        try:
            numero = limpar_inteiro(row.get("numero_do_empenho"))
            if numero is None:
                continue

            nome_empresa = limpar_texto(row.get("rel_empresas")).strip().upper() or None

            cur.execute("""
                INSERT INTO gov.emendas_parlamentares (
                    numero_do_empenho,
                    data_do_empenho,
                    historico_do_empenho,
                    nome_empresa,
                    valor_empenho,
                    valor_liquidado,
                    valor_pago,
                    saldo_a_pagar
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT DO NOTHING;
            """, (
                numero,
                formatar_data(row.get("data_do_empenho")),
                limpar_texto(row.get("histrico_do_empenho")
                    or row.get("historico_do_empenho")),
                nome_empresa,
                limpar_valor(row.get("valor_do_empenho")
                    or row.get("valor_empenho")),
                limpar_valor(row.get("valor_liquidado")),
                limpar_valor(row.get("valor_pago")),
                limpar_valor(row.get("saldo_a_pagar")),
            ))

            total += 1

        except Exception as e:
            conn.rollback()
            erros += 1

    conn.commit()
    cur.close()
    print(f"✅ Emendas parlamentares inseridas: {total}")

# =====================================================
# RECEITAS
# =====================================================

def carregar_receitas(conn):
    path = os.path.join(DATA_DIR, "receitas", "receitas_unificado.csv")
    if not os.path.exists(path):
        return

    # Lê com utf-8 primeiro, fallback latin1
    try:
        df = pd.read_csv(path, sep=None, engine="python", encoding="utf-8")
    except Exception:
        df = pd.read_csv(path, sep=None, engine="python", encoding="latin1")

    # Normaliza colunas: minúsculo, sem acentos, espaços viram _
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.encode("ascii", errors="ignore")
        .str.decode("ascii")
        .str.replace(r"[^\w]", "_", regex=True)
        .str.replace(r"_+", "_", regex=True)
        .str.strip("_")
    )

    cur = conn.cursor()
    total = 0
    erros = 0

    for _, row in df.iterrows():
        try:
            id_receita = limpar_inteiro(row.get("id_receita"))
            if id_receita is None:
                continue

            # Busca o valor orçado em variações possíveis do nome da coluna
            valor_orcado = limpar_valor(
                row.get("valor_or_ado_r_")
                or row.get("valor_orcado_r_")
                or row.get("valor_or_ado")
                or row.get("valor_orcado")
                or 0
            )

            realizado = limpar_valor(
                row.get("realizado__")
                or row.get("realizado_")
                or row.get("realizado")
                or 0
            )

            cur.execute("""
                INSERT INTO gov.receitas (
                    id_receita,
                    nome_orgao,
                    descricao_natureza_receita,
                    categoria_economica,
                    origem_da_receita,
                    especie_da_receita,
                    tipo_da_receita,
                    desdobramento_nivel_1,
                    desdobramento_nivel_2,
                    desdobramento_nivel_3,
                    forma_de_ingresso,
                    valor_orcado,
                    realizado_percentual,
                    ano
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT DO NOTHING;
            """, (
                id_receita,
                normalizar_orgao(row.get("rel_orgao")),
                limpar_texto(row.get("descri_o_natureza_receita")
                    or row.get("descricao_natureza_receita")),
                limpar_texto(row.get("categoria_econ_mica")
                    or row.get("categoria_economica")),
                limpar_texto(row.get("origem_da_receita")),
                limpar_texto(row.get("especie_da_receita")),
                limpar_texto(row.get("tipo_da_receita")),
                limpar_texto(row.get("desdobramento_n_vel_1")
                    or row.get("desdobramento_nivel_1")),
                limpar_texto(row.get("desdobramento_n_vel_2")
                    or row.get("desdobramento_nivel_2")),
                limpar_texto(row.get("desdobramento_n_vel_3")
                    or row.get("desdobramento_nivel_3")),
                limpar_texto(row.get("forma_de_ingresso")),
                valor_orcado,
                realizado,
                limpar_inteiro(row.get("ano")),
            ))

            total += 1

        except Exception as e:
            conn.rollback()
            erros += 1

    conn.commit()
    cur.close()
    print(f"✅ Receitas inseridas: {total}")

# =====================================================
# FUNÇÃO PRINCIPAL
# =====================================================

def carregar_tudo():
    conn = None

    try:
        conn = get_connection()

        cur = conn.cursor()
        cur.execute("SET search_path TO gov;")
        cur.close()

        path_contratos = os.path.join(DATA_DIR, "contratos", "contratos.CSV")
        df_contratos = ler_csv(path_contratos)

        popular_cadastros_base(conn)
        carregar_licitacoes(conn)
        carregar_contratos(conn, df_contratos)
        carregar_servidores(conn)
        carregar_diarias(conn)
        carregar_patrimonio(conn)
        carregar_obras(conn)
        carregar_convenios(conn)
        carregar_despesas_pessoal(conn)
        carregar_despesas_programas(conn)
        carregar_emendas_parlamentares(conn)
        carregar_receitas(conn)

        print("\n✅ Processamento finalizado!")

    except Exception as e:
        if conn:
            conn.rollback()

    finally:
        if conn:
            conn.close()
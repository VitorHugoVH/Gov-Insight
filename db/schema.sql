-- Database: gov_insight

CREATE SCHEMA IF NOT EXISTS gov;

SET search_path TO gov;

CREATE TABLE entidades (
    nome_entidade VARCHAR(255) PRIMARY KEY
);

CREATE TABLE orgao (
    nome_orgao VARCHAR(255) PRIMARY KEY,
    nome_entidade VARCHAR(255) REFERENCES entidades(nome_entidade)
);

CREATE TABLE empresas (
    cpf_cnpj VARCHAR(14) PRIMARY KEY,
    nome_empresa VARCHAR(255) UNIQUE
);

CREATE TABLE licitacoes (
    numero_do_processo INTEGER,
    numero_da_licitacao INTEGER,
    nome_entidade VARCHAR(255) REFERENCES entidades(nome_entidade),
    ano_processo INTEGER,
    ano_da_licitacao INTEGER,
    objeto TEXT,
    modalidade VARCHAR(50),
    data_de_abertura DATE,
    data_de_publicacao DATE,
    tipo_de_objeto TEXT,
    forma_de_julgamento TEXT,
    data_de_homologacao DATE,
    situacao VARCHAR(20),
    data_de_anulacao DATE,
    data_de_criacao DATE,
    data_do_julgamento DATE,
    data_da_revogacao DATE,
    forma_de_contratacao TEXT,
    valor_estimado NUMERIC(12,2),
    valor_homologado NUMERIC(12,2),

    PRIMARY KEY (
        numero_do_processo,
        numero_da_licitacao,
        data_de_criacao
    )
);

CREATE TABLE contratos (
    numero_do_contrato INTEGER,
    numero_do_processo INTEGER,
    numero_da_licitacao INTEGER,
    data_de_criacao_licitacao DATE,

    nome_empresa VARCHAR(255) REFERENCES empresas(nome_empresa),
    nome_entidade VARCHAR(255) REFERENCES entidades(nome_entidade),

    ano INTEGER,
    competencia DATE,
    ano_do_processo INTEGER,
    data_de_assinatura DATE,
    tipo_de_contrato VARCHAR(100),
    objeto_do_contrato TEXT,
    vigencia_inicial DATE,
    vigencia_final DATE,
    situacao TEXT,
    valor_final NUMERIC(12,2),
    instrumento_de_contrato TEXT,

    PRIMARY KEY (
        numero_do_contrato,
        numero_do_processo,
        data_de_assinatura
    ),

    FOREIGN KEY (
        numero_do_processo,
        numero_da_licitacao,
        data_de_criacao_licitacao
    )
    REFERENCES licitacoes (
        numero_do_processo,
        numero_da_licitacao,
        data_de_criacao
    )
);

CREATE TABLE servidores (
    matricula                     INTEGER PRIMARY KEY,
    nome_entidade                 VARCHAR(255) REFERENCES gov.entidades(nome_entidade),
    nome_orgao                    VARCHAR(255) REFERENCES gov.orgao(nome_orgao),
    nome_do_servidor              TEXT,          -- ← SEM UNIQUE (homônimos existem)
    cargo                         TEXT,
    vinculo_empregaticio          TEXT,
    nivel_salarial                TEXT,
    organograma                   TEXT,
    contribuicao_empregado_rgps   NUMERIC(12,2),
    contribuicao_empregado_rat_fat NUMERIC(12,2),
    contribuicao_patronal_rgps    NUMERIC(12,2),
    data_de_admissao              DATE,
    situacao                      TEXT,
    remuneracao_contratual        NUMERIC(12,2),
    remuneracao_bruta             NUMERIC(12,2),
    remuneracao_liquida           NUMERIC(12,2),
    efetivo_em_cargo_comissionado TEXT
);

CREATE INDEX idx_servidores_nome
    ON gov.servidores
    USING btree (gov.unaccent_immutable(UPPER(TRIM(nome_do_servidor))));

CREATE TABLE diarias (
    numero           INTEGER PRIMARY KEY,
    nome_entidade    VARCHAR(255) REFERENCES gov.entidades(nome_entidade),
    matricula        INTEGER REFERENCES gov.servidores(matricula),  -- ← FK por matricula
    cnpj_cpf         VARCHAR(50),
    quantidade       INTEGER,
    valor_unitario   NUMERIC(12,2),
    data_inicial     DATE,
    data_final       DATE,
    finalidade       TEXT,
    local_de_origem  TEXT,
    local_de_destino TEXT
);

CREATE TABLE convenios (
    numero_convenio_recebido TEXT PRIMARY KEY,
    nome_orgao VARCHAR(255) REFERENCES orgao(nome_orgao),
    objeto TEXT,
    data_assinatura DATE,
    tipo TEXT,
    vigencia TEXT,
    valor NUMERIC(12,2),
    contrapartida NUMERIC(12,2)
);

CREATE TABLE despesas_com_pessoal (
    numero_empenho INTEGER PRIMARY KEY,
    data_despesa DATE,
    rel_orgao VARCHAR(255) REFERENCES orgao(nome_orgao),
    detalhamento_do_elemento TEXT,
    descricao TEXT,
    valor_empenhado NUMERIC(12,2),
    valor_liquido NUMERIC(12,2),
    valor_pago NUMERIC(12,2)
);

CREATE TABLE despesas_programas_acoes (
    codigo_da_despesa INTEGER PRIMARY KEY,
    nome_entidade VARCHAR(255) REFERENCES entidades(nome_entidade),
    nome_do_programa VARCHAR(255),
    funcao VARCHAR(255),
    descricao_programa TEXT,
    valor_orcado_despesa NUMERIC(12,2),
    valor_atualizado_despesa NUMERIC(12,2),
    empenhado_atualizado_despesa NUMERIC(12,2),
    liquido_atualizado_da_despesa NUMERIC(12,2),
    valor_pago_atualizado_despesa NUMERIC(12,2)
);

CREATE TABLE obras (
    id_obra INTEGER PRIMARY KEY,
    nome_entidade VARCHAR(255) REFERENCES entidades(nome_entidade),
    tipo VARCHAR(255),
    categoria VARCHAR(255),
    descricao TEXT,
    data_inicio DATE,
    previsao_conclusao DATE,
    valor_previsto NUMERIC(12,2),
    valor_alterado NUMERIC(12,2),
    valor_atualizado NUMERIC(12,2),
    situacao VARCHAR(255),
    percentual_execucao NUMERIC(8,2)
);

CREATE TABLE patrimonio (
    identificacao INTEGER PRIMARY KEY,
    nome_entidade VARCHAR(255) REFERENCES entidades(nome_entidade),
    nome_orgao VARCHAR(255) REFERENCES orgao(nome_orgao),
    tipo VARCHAR(255),
    natureza VARCHAR(255),
    descricao TEXT,
    data_aquisicao DATE,
    situacao VARCHAR(255),
    valor_atual NUMERIC(12,2),
    tipo_aquisicao VARCHAR(255)
);

CREATE TABLE receitas (
    id_receita INTEGER PRIMARY KEY,
    nome_orgao VARCHAR(255) REFERENCES orgao(nome_orgao),
    descricao_natureza_receita TEXT,
    categoria_economica VARCHAR(255),
    origem_da_receita VARCHAR(255),
    especie_da_receita VARCHAR(255),
    tipo_da_receita VARCHAR(255),
    desdobramento_nivel_1 TEXT,
    desdobramento_nivel_2 TEXT,
    desdobramento_nivel_3 TEXT,
    forma_de_ingresso VARCHAR(255),
    valor_orcado NUMERIC(12,2),
    realizado_percentual NUMERIC(12,2),
    ano INTEGER
);

CREATE TABLE emendas_parlamentares (
    numero_do_empenho INTEGER PRIMARY KEY,
    data_do_empenho DATE,
    historico_do_empenho TEXT,
    nome_empresa VARCHAR(255) REFERENCES empresas(nome_empresa),
    valor_empenho NUMERIC(12,2),
    valor_liquidado NUMERIC(12,2),
    valor_pago NUMERIC(12,2),
    saldo_a_pagar NUMERIC(12,2)
);
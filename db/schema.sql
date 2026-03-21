DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

-- =========================
-- TABELA: ORGAO
-- =========================
CREATE TABLE orgao (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL
);

-- =========================
-- TABELA: FORNECEDOR
-- =========================
CREATE TABLE fornecedor (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    documento TEXT
);

-- =========================
-- TABELA: SERVIDOR
-- =========================
CREATE TABLE servidor (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    orgao_id INT REFERENCES orgao(id),
    data_admissao DATE,
    tipo_matricula TEXT,
    vinculo TEXT,
    carga_horaria_mensal INT,
    carga_horaria_semanal INT,
    cargo TEXT,
    remuneracao NUMERIC,
    situacao TEXT
);

-- =========================
-- TABELA: LICITACAO
-- =========================
CREATE TABLE licitacao (
    id SERIAL PRIMARY KEY,
    numero_processo TEXT,
    ano_processo INT,
    numero_licitacao TEXT,
    ano_licitacao INT,
    data_publicacao DATE,
    objeto TEXT,
    modalidade TEXT,
    situacao TEXT,
    valor_estimado NUMERIC,
    valor_homologado NUMERIC
);

-- =========================
-- TABELA: CONTRATO
-- =========================
CREATE TABLE contrato (
    id SERIAL PRIMARY KEY,
    numero TEXT,
    data_assinatura DATE,
    processo TEXT,
    tipo TEXT,
    objeto TEXT,
    fornecedor_id INT REFERENCES fornecedor(id),
    situacao TEXT,
    valor_final NUMERIC
);

-- =========================
-- TABELA: RECEITA
-- =========================
CREATE TABLE receita (
    id SERIAL PRIMARY KEY,
    data DATE,
    natureza TEXT,
    descricao TEXT,
    valor_orcado NUMERIC,
    valor_arrecadado NUMERIC
);

-- =========================
-- TABELA: RECEITA TRIBUTARIA
-- =========================
CREATE TABLE receita_tributaria (
    id SERIAL PRIMARY KEY,
    ano INT,
    contribuinte TEXT,
    documento TEXT,
    valor NUMERIC
);

-- =========================
-- TABELA: CONVENIO RECEBIDO
-- =========================
CREATE TABLE convenio_recebido (
    id SERIAL PRIMARY KEY,
    numero TEXT,
    orgao_concedente TEXT,
    objeto TEXT,
    data_assinatura DATE,
    tipo TEXT,
    beneficiario TEXT,
    vigencia TEXT,
    valor NUMERIC,
    contrapartida NUMERIC
);

-- =========================
-- TABELA: CONVENIO REPASSADO
-- =========================
CREATE TABLE convenio_repassado (
    id SERIAL PRIMARY KEY,
    numero TEXT,
    beneficiario TEXT,
    objeto TEXT,
    data_assinatura DATE,
    vigencia TEXT,
    valor NUMERIC,
    contrapartida NUMERIC,
    valor_atualizado NUMERIC,
    valor_recebido NUMERIC
);

-- =========================
-- TABELA: DESPESA
-- =========================
CREATE TABLE despesa (
    id SERIAL PRIMARY KEY,
    numero_empenho TEXT,
    data DATE,
    orgao_id INT REFERENCES orgao(id),
    fornecedor_id INT REFERENCES fornecedor(id),
    descricao TEXT,
    valor_empenhado NUMERIC,
    valor_liquidado NUMERIC,
    valor_pago NUMERIC
);

-- =========================
-- TABELA: DESPESA PROGRAMA
-- =========================
CREATE TABLE despesa_programa (
    id SERIAL PRIMARY KEY,
    programa TEXT,
    funcao TEXT,
    acao TEXT,
    codigo_despesa TEXT,
    valor_orcado NUMERIC,
    valor_atualizado NUMERIC,
    valor_empenhado NUMERIC,
    valor_liquidado NUMERIC,
    valor_pago NUMERIC
);

-- =========================
-- TABELA: DIARIA
-- =========================
CREATE TABLE diaria (
    id SERIAL PRIMARY KEY,
    ano INT,
    servidor_id INT REFERENCES servidor(id),
    numero TEXT,
    quantidade INT,
    valor_total NUMERIC,
    periodo TEXT,
    finalidade TEXT,
    destino TEXT
);

-- =========================
-- TABELA: OBRA
-- =========================
CREATE TABLE obra (
    id SERIAL PRIMARY KEY,
    tipo TEXT,
    categoria TEXT,
    descricao TEXT,
    data_inicio DATE,
    previsao_conclusao DATE,
    valor_previsto NUMERIC,
    valor_atualizado NUMERIC,
    situacao TEXT,
    percentual_execucao NUMERIC
);

-- =========================
-- TABELA: PATRIMONIO
-- =========================
CREATE TABLE patrimonio (
    id SERIAL PRIMARY KEY,
    entidade TEXT,
    tipo TEXT,
    natureza TEXT,
    identificacao TEXT,
    descricao TEXT,
    data_aquisicao DATE,
    centro_custo TEXT,
    situacao TEXT,
    valor_atual NUMERIC,
    tipo_aquisicao TEXT
);

-- =========================
-- TABELA: TRANSFERENCIA
-- =========================
CREATE TABLE transferencia (
    id SERIAL PRIMARY KEY,
    numero TEXT,
    data DATE,
    orgao_concedente TEXT,
    fonte TEXT,
    finalidade TEXT,
    valor NUMERIC
);

-- TABELA DE STAGE (Área temporária / Dados Brutos da API)

CREATE TABLE IF NOT EXISTS stage_cotacoes (
    _ingestion_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    _run_id VARCHAR(50),
    _source_endpoint VARCHAR(255),
      moeda TEXT,
    moeda_fiat TEXT,
    timestamp_ms TEXT,
    data_referencia TEXT,
    preco TEXT,
    market_cap TEXT,
    volume_total TEXT
);

-- TABELAS DIMENSÃO (Informações de cadastro e datas)

CREATE TABLE IF NOT EXISTS dim_tempo (
    data_id DATE PRIMARY KEY,
    ano INT NOT NULL,
    mes INT NOT NULL,
    nome_mes VARCHAR(20) NOT NULL,
    dia INT NOT NULL,
    dia_semana VARCHAR(20) NOT NULL,
    trimestre INT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_moeda (
    moeda_id VARCHAR(50) PRIMARY KEY,
    simbolo VARCHAR(10) NOT NULL,
    nome VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_fiat (
    fiat_id VARCHAR(10) PRIMARY KEY,
    nome VARCHAR(50) NOT NULL,
    simbolo_monetario VARCHAR(5) NOT NULL
);

-- TABELAS FATO (Os números e cotações do dia a dia)

CREATE TABLE IF NOT EXISTS fato_cotacoes (
    id SERIAL PRIMARY KEY,
    data_id DATE NOT NULL,
    moeda_id VARCHAR(50) NOT NULL,
    fiat_id VARCHAR(10) NOT NULL,
    preco NUMERIC(18, 4) NOT NULL,
    market_cap NUMERIC(24, 2),
    volume_total NUMERIC(24, 2),
    data_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_fato_tempo FOREIGN KEY (data_id) REFERENCES dim_tempo (data_id),
    CONSTRAINT fk_fato_moeda FOREIGN KEY (moeda_id) REFERENCES dim_moeda (moeda_id),
    CONSTRAINT fk_fato_fiat FOREIGN KEY (fiat_id) REFERENCES dim_fiat (fiat_id),
    CONSTRAINT unq_cotacao_dia UNIQUE (data_id, moeda_id, fiat_id)
);

CREATE TABLE IF NOT EXISTS fato_projecoes (
    id SERIAL PRIMARY KEY,
    data_projecao DATE NOT NULL,
    moeda_id VARCHAR(50) NOT NULL,
    fiat_id VARCHAR(10) NOT NULL,
    preco_projetado NUMERIC(18, 4) NOT NULL,
    data_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_proj_tempo FOREIGN KEY (data_projecao) REFERENCES dim_tempo (data_id),
    CONSTRAINT fk_proj_moeda FOREIGN KEY (moeda_id) REFERENCES dim_moeda (moeda_id),
    CONSTRAINT fk_proj_fiat FOREIGN KEY (fiat_id) REFERENCES dim_fiat (fiat_id)
    CONSTRAINT unq_projecao_dia UNIQUE (data_projecao, moeda_id, fiat_id),
);
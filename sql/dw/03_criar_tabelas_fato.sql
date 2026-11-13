
USE dw_campo_real;

-- FATO GERAÇÃO
CREATE TABLE IF NOT EXISTS fato_geracao (
    id_fato_geracao BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_tempo INT NOT NULL,
    id_usina INT NOT NULL,
    id_dim_fonte INT NOT NULL,
    id_dim_submercado INT NOT NULL,
    energia_mwh DECIMAL(15,4),
    disponibilidade_mw DECIMAL(15,4),
    origem VARCHAR(100),
    recebido_em DATETIME,

    CONSTRAINT fk_fg_tempo
        FOREIGN KEY (id_tempo) REFERENCES dim_tempo(id_tempo),

    CONSTRAINT fk_fg_usina
        FOREIGN KEY (id_usina) REFERENCES dim_usina(id_dim_usina),

    CONSTRAINT fk_fg_fonte
        FOREIGN KEY (id_dim_fonte) REFERENCES dim_fonte_energia(id_dim_fonte),

    CONSTRAINT fk_fg_submercado
        FOREIGN KEY (id_dim_submercado) REFERENCES dim_submercado(id_dim_submercado),

    UNIQUE KEY uk_fato_geracao (id_tempo, id_usina)
);

-- FATO CLIMA
CREATE TABLE IF NOT EXISTS fato_clima (
    id_fato_clima BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_tempo INT NOT NULL,
    id_usina INT NOT NULL,
    temperatura_c DECIMAL(8,3),
    precipitacao_mm DECIMAL(10,3),
    velocidade_vento_kmh DECIMAL(10,3),
    radiacao_solar_wm2 DECIMAL(12,3),
    origem VARCHAR(100),
    extraido_em DATETIME,

    CONSTRAINT fk_fc_tempo
        FOREIGN KEY (id_tempo) REFERENCES dim_tempo(id_tempo),

    CONSTRAINT fk_fc_usina
        FOREIGN KEY (id_usina) REFERENCES dim_usina(id_dim_usina),

    UNIQUE KEY uk_fato_clima (id_tempo, id_usina)
);

-- FATO PREÇO
CREATE TABLE IF NOT EXISTS fato_preco (
    id_fato_preco BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_tempo INT NOT NULL,
    id_dim_submercado INT NOT NULL,
    pld_rs_mwh DECIMAL(15,4),
    mes_referencia DATE,
    periodo_comercializacao INT,
    origem VARCHAR(100),

    CONSTRAINT fk_fp_tempo
        FOREIGN KEY (id_tempo) REFERENCES dim_tempo(id_tempo),

    CONSTRAINT fk_fp_submercado
        FOREIGN KEY (id_dim_submercado) REFERENCES dim_submercado(id_dim_submercado),

    UNIQUE KEY uk_fato_preco (id_tempo, id_dim_submercado)
);

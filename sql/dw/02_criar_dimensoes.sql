
USE dw_campo_real;

-- DIMENSÃO TEMPO
CREATE TABLE IF NOT EXISTS dim_tempo (
    id_tempo INT AUTO_INCREMENT PRIMARY KEY,
    data_hora DATETIME,
    data DATE,
    dia TINYINT,
    dia_semana TINYINT,
    nome_dia_semana VARCHAR(20),
    mes TINYINT,
    nome_mes VARCHAR(20),
    trimestre TINYINT,
    ano SMALLINT,
    hora TINYINT,
    dia_util BOOLEAN,
    feriado BOOLEAN,
    estacao VARCHAR(20),
    patamar_carga VARCHAR(20),
    UNIQUE KEY uk_dim_tempo_data_hora (data_hora)
);

-- DIMENSÃO USINA (SCD TIPO 2)
CREATE TABLE IF NOT EXISTS dim_usina (
    id_dim_usina INT AUTO_INCREMENT PRIMARY KEY,
    id_usina_origem INT NOT NULL,
    cod_usina VARCHAR(50),
    nome VARCHAR(150),
    uf CHAR(2),
    municipio VARCHAR(100),
    latitude DECIMAL(10,6),
    longitude DECIMAL(10,6),
    potencia_mw DECIMAL(12,3),
    data_inicio_operacao DATE,
    situacao VARCHAR(50),
    vigencia_inicio DATETIME,
    vigencia_fim DATETIME,
    registro_atual BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE KEY uk_usina_versao (id_usina_origem, vigencia_inicio),
    INDEX idx_dim_usina_origem (id_usina_origem)
);

-- DIMENSÃO FONTE DE ENERGIA
CREATE TABLE IF NOT EXISTS dim_fonte_energia (
    id_dim_fonte INT AUTO_INCREMENT PRIMARY KEY,
    id_fonte_origem INT NOT NULL,
    cod_fonte VARCHAR(30),
    descricao VARCHAR(100),
    renovavel BOOLEAN,
    intermitente BOOLEAN,
    UNIQUE KEY uk_dim_fonte_origem (id_fonte_origem)
);

-- DIMENSÃO SUBMERCADO
CREATE TABLE IF NOT EXISTS dim_submercado (
    id_dim_submercado INT AUTO_INCREMENT PRIMARY KEY,
    cod_submercado_origem VARCHAR(20) NOT NULL,
    nome VARCHAR(100),
    regioes TEXT,
    UNIQUE KEY uk_dim_submercado_origem (cod_submercado_origem)
);

-- PERMITIR A INSERÇÃO EXPLÍCITA DA CHAVE 0
SET SESSION sql_mode = CONCAT(@@sql_mode, ',NO_AUTO_VALUE_ON_ZERO');

-- REGISTROS DESCONHECIDOS
INSERT IGNORE INTO dim_tempo (id_tempo) VALUES (0);

INSERT IGNORE INTO dim_usina (
    id_dim_usina, id_usina_origem, registro_atual
) VALUES (0, 0, TRUE);

INSERT IGNORE INTO dim_fonte_energia (
    id_dim_fonte, id_fonte_origem
) VALUES (0, 0);

INSERT IGNORE INTO dim_submercado (
    id_dim_submercado, cod_submercado_origem
) VALUES (0, 'DESCONHECIDO');

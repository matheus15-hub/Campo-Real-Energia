
USE dw_campo_real;

-- 1. CARGA DA DIMENSÃO FONTE DE ENERGIA
INSERT INTO dim_fonte_energia (
    id_fonte_origem,
    cod_fonte,
    descricao,
    renovavel,
    intermitente
)
SELECT
    f.id_fonte,
    f.cod_fonte,
    f.descricao,
    f.renovavel,
    f.intermitente
FROM campo_real_energia.fonte_energia f
WHERE NOT EXISTS (
    SELECT 1
    FROM dim_fonte_energia d
    WHERE d.id_fonte_origem = f.id_fonte
);

-- 2. CARGA DA DIMENSÃO SUBMERCADO
INSERT INTO dim_submercado (
    cod_submercado_origem,
    nome,
    regioes
)
SELECT
    s.cod_submercado,
    s.nome,
    s.regioes
FROM campo_real_energia.submercado s
WHERE NOT EXISTS (
    SELECT 1
    FROM dim_submercado d
    WHERE d.cod_submercado_origem = s.cod_submercado
);

-- 3. CARGA INICIAL DA DIMENSÃO USINA (SCD TIPO 2)
INSERT INTO dim_usina (
    id_usina_origem,
    cod_usina,
    nome,
    uf,
    municipio,
    latitude,
    longitude,
    potencia_mw,
    data_inicio_operacao,
    situacao,
    vigencia_inicio,
    vigencia_fim,
    registro_atual
)
SELECT
    u.id_usina,
    u.cod_usina,
    u.nome,
    u.uf,
    u.municipio,
    u.latitude,
    u.longitude,
    u.potencia_mw,
    u.data_inicio_operacao,
    u.situacao,
    CURRENT_TIMESTAMP,
    '9999-12-31 23:59:59',
    TRUE
FROM campo_real_energia.usina u
WHERE NOT EXISTS (
    SELECT 1
    FROM dim_usina d
    WHERE d.id_usina_origem = u.id_usina
      AND d.registro_atual = TRUE
);

SELECT COUNT(*) AS total_fontes
FROM dim_fonte_energia;

SELECT COUNT(*) AS total_submercados
FROM dim_submercado;

SELECT COUNT(*) AS total_usinas
FROM dim_usina
WHERE id_usina_origem <> 0;
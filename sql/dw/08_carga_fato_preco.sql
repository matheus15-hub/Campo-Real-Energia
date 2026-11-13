USE dw_campo_real;

INSERT INTO fato_preco (
    id_tempo,
    id_dim_submercado,
    pld_rs_mwh,
    mes_referencia,
    periodo_comercializacao,
    origem
)
SELECT
    dt.id_tempo,
    ds.id_dim_submercado,
    p.pld_rs_mwh,
    p.mes_referencia,
    p.periodo_comercializacao,
    p.origem
FROM campo_real_energia.pld_horario p
INNER JOIN dim_tempo dt
    ON dt.data_hora = p.data_hora
INNER JOIN dim_submercado ds
    ON ds.cod_submercado_origem = p.cod_submercado
WHERE NOT EXISTS (
    SELECT 1
    FROM fato_preco fp
    WHERE fp.id_tempo = dt.id_tempo
      AND fp.id_dim_submercado = ds.id_dim_submercado
);

SELECT COUNT(*) AS total_precos
FROM fato_preco;


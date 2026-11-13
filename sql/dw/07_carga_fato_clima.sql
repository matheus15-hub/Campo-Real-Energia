
USE dw_campo_real;

INSERT INTO fato_clima (
    id_tempo,
    id_usina,
    temperatura_c,
    precipitacao_mm,
    velocidade_vento_kmh,
    radiacao_solar_wm2,
    origem,
    extraido_em
)
SELECT
    dt.id_tempo,
    du.id_dim_usina,
    CAST(
        JSON_UNQUOTE(JSON_EXTRACT(r.dados_originais, '$.temperature_2m'))
        AS DECIMAL(8,3)
    ),
    CAST(
        JSON_UNQUOTE(JSON_EXTRACT(r.dados_originais, '$.precipitation'))
        AS DECIMAL(10,3)
    ),
    CAST(
        JSON_UNQUOTE(JSON_EXTRACT(r.dados_originais, '$.wind_speed_10m'))
        AS DECIMAL(10,3)
    ),
    CAST(
        JSON_UNQUOTE(JSON_EXTRACT(r.dados_originais, '$.shortwave_radiation'))
        AS DECIMAL(12,3)
    ),
    r.origem,
    r.extraido_em
FROM campo_real_energia.raw_clima_horario r
INNER JOIN dim_tempo dt
    ON dt.data_hora = r.data_hora
INNER JOIN dim_usina du
    ON du.id_usina_origem = r.id_usina
    AND du.registro_atual = TRUE
WHERE r.data_hora >= '2025-01-01 00:00:00'
  AND r.data_hora < '2026-01-01 00:00:00'
  AND NOT EXISTS (
      SELECT 1
      FROM fato_clima fc
      WHERE fc.id_tempo = dt.id_tempo
        AND fc.id_usina = du.id_dim_usina
  );

SELECT COUNT(*) AS total_clima
FROM fato_clima;

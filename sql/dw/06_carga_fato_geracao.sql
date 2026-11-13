USE dw_campo_real;

INSERT INTO fato_geracao (
    id_tempo,
    id_usina,
    id_dim_fonte,
    id_dim_submercado,
    energia_mwh,
    disponibilidade_mw,
    origem,
    recebido_em
)
SELECT
    dt.id_tempo,
    du.id_dim_usina,
    df.id_dim_fonte,
    ds.id_dim_submercado,
    m.energia_mwh,
    m.disponibilidade_mw,
    m.origem,
    m.recebido_em
FROM campo_real_energia.medicao_geracao m
INNER JOIN campo_real_energia.usina u
    ON u.id_usina = m.id_usina
INNER JOIN dim_tempo dt
    ON dt.data_hora = m.data_hora
INNER JOIN dim_usina du
    ON du.id_usina_origem = u.id_usina
    AND du.registro_atual = TRUE
INNER JOIN dim_fonte_energia df
    ON df.id_fonte_origem = u.id_fonte
INNER JOIN dim_submercado ds
    ON ds.cod_submercado_origem = u.cod_submercado
WHERE m.data_hora >= '2025-01-01 00:00:00'
  AND m.data_hora < '2026-01-01 00:00:00'
  AND NOT EXISTS (
      SELECT 1
      FROM fato_geracao fg
      WHERE fg.id_tempo = dt.id_tempo
        AND fg.id_usina = du.id_dim_usina
  );

SELECT COUNT(*) AS total_geracao
FROM fato_geracao;
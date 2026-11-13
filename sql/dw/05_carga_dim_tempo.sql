
USE dw_campo_real;

INSERT INTO dim_tempo (
    data_hora,
    data,
    dia,
    dia_semana,
    nome_dia_semana,
    mes,
    nome_mes,
    trimestre,
    ano,
    hora,
    dia_util,
    feriado,
    estacao,
    patamar_carga
)
SELECT
    h.data_hora,
    DATE(h.data_hora),
    DAY(h.data_hora),
    DAYOFWEEK(h.data_hora),
    CASE DAYOFWEEK(h.data_hora)
        WHEN 1 THEN 'Domingo'
        WHEN 2 THEN 'Segunda-feira'
        WHEN 3 THEN 'Terca-feira'
        WHEN 4 THEN 'Quarta-feira'
        WHEN 5 THEN 'Quinta-feira'
        WHEN 6 THEN 'Sexta-feira'
        WHEN 7 THEN 'Sabado'
    END,
    MONTH(h.data_hora),
    MONTHNAME(h.data_hora),
    QUARTER(h.data_hora),
    YEAR(h.data_hora),
    HOUR(h.data_hora),
    CASE
        WHEN DAYOFWEEK(h.data_hora) IN (1, 7) THEN FALSE
        WHEN EXISTS (
            SELECT 1
            FROM campo_real_energia.feriado_nacional f
            WHERE f.data = DATE(h.data_hora)
        ) THEN FALSE
        ELSE TRUE
    END,
    EXISTS (
        SELECT 1
        FROM campo_real_energia.feriado_nacional f
        WHERE f.data = DATE(h.data_hora)
    ),
    CASE
        WHEN MONTH(h.data_hora) IN (12, 1, 2) THEN 'Verao'
        WHEN MONTH(h.data_hora) IN (3, 4, 5) THEN 'Outono'
        WHEN MONTH(h.data_hora) IN (6, 7, 8) THEN 'Inverno'
        ELSE 'Primavera'
    END,
    CASE
        WHEN HOUR(h.data_hora) BETWEEN 18 AND 21 THEN 'Pesado'
        WHEN HOUR(h.data_hora) BETWEEN 7 AND 17 THEN 'Intermediario'
        ELSE 'Leve'
    END
FROM (
    SELECT DATE_ADD('2025-01-01 00:00:00',
        INTERVAL (d0.n + d1.n * 10 + d2.n * 100 + d3.n * 1000) HOUR
    ) AS data_hora
    FROM
        (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
         UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) d0
    CROSS JOIN
        (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
         UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) d1
    CROSS JOIN
        (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
         UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) d2
    CROSS JOIN
        (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
         UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) d3
) h
WHERE h.data_hora < '2026-01-01 00:00:00'
AND NOT EXISTS (
    SELECT 1
    FROM dim_tempo t
    WHERE t.data_hora = h.data_hora
);

SELECT
    COUNT(*) AS total_horas,
    MIN(data_hora) AS primeira_hora,
    MAX(data_hora) AS ultima_hora
FROM dim_tempo
WHERE ano = 2025;


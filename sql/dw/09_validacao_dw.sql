
USE dw_campo_real;

-- 1. CONFERÊNCIA DA QUANTIDADE DE REGISTROS
SELECT 'dim_tempo' AS tabela, COUNT(*) AS total FROM dim_tempo
UNION ALL
SELECT 'dim_usina', COUNT(*) FROM dim_usina
UNION ALL
SELECT 'dim_fonte_energia', COUNT(*) FROM dim_fonte_energia
UNION ALL
SELECT 'dim_submercado', COUNT(*) FROM dim_submercado
UNION ALL
SELECT 'fato_geracao', COUNT(*) FROM fato_geracao
UNION ALL
SELECT 'fato_clima', COUNT(*) FROM fato_clima
UNION ALL
SELECT 'fato_preco', COUNT(*) FROM fato_preco;

-- 2. VERIFICAÇÃO DE REGISTROS SEM DIMENSÃO CORRESPONDENTE
SELECT 'geracao - tempo' AS verificacao, COUNT(*) AS inconsistencias
FROM fato_geracao f
LEFT JOIN dim_tempo d ON d.id_tempo = f.id_tempo
WHERE d.id_tempo IS NULL

UNION ALL

SELECT 'geracao - usina', COUNT(*)
FROM fato_geracao f
LEFT JOIN dim_usina d ON d.id_dim_usina = f.id_usina
WHERE d.id_dim_usina IS NULL

UNION ALL

SELECT 'geracao - fonte', COUNT(*)
FROM fato_geracao f
LEFT JOIN dim_fonte_energia d ON d.id_dim_fonte = f.id_dim_fonte
WHERE d.id_dim_fonte IS NULL

UNION ALL

SELECT 'geracao - submercado', COUNT(*)
FROM fato_geracao f
LEFT JOIN dim_submercado d ON d.id_dim_submercado = f.id_dim_submercado
WHERE d.id_dim_submercado IS NULL

UNION ALL

SELECT 'clima - tempo', COUNT(*)
FROM fato_clima f
LEFT JOIN dim_tempo d ON d.id_tempo = f.id_tempo
WHERE d.id_tempo IS NULL

UNION ALL

SELECT 'clima - usina', COUNT(*)
FROM fato_clima f
LEFT JOIN dim_usina d ON d.id_dim_usina = f.id_usina
WHERE d.id_dim_usina IS NULL

UNION ALL

SELECT 'preco - tempo', COUNT(*)
FROM fato_preco f
LEFT JOIN dim_tempo d ON d.id_tempo = f.id_tempo
WHERE d.id_tempo IS NULL

UNION ALL

SELECT 'preco - submercado', COUNT(*)
FROM fato_preco f
LEFT JOIN dim_submercado d ON d.id_dim_submercado = f.id_dim_submercado
WHERE d.id_dim_submercado IS NULL;

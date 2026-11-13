
from sqlalchemy import text
from conexao import engine


def registrar_metrica(
    tabela,
    regra,
    total_registros,
    registros_validos,
    registros_invalidos
):
    percentual = (
        (registros_validos / total_registros) * 100
        if total_registros > 0 else 0
    )

    consulta = text("""
        INSERT INTO metricas_qualidade (
            tabela,
            regra,
            total_registros,
            registros_validos,
            registros_invalidos,
            percentual_validade
        )
        VALUES (
            :tabela,
            :regra,
            :total,
            :validos,
            :invalidos,
            :percentual
        )
        ON DUPLICATE KEY UPDATE
            total_registros = VALUES(total_registros),
            registros_validos = VALUES(registros_validos),
            registros_invalidos = VALUES(registros_invalidos),
            percentual_validade = VALUES(percentual_validade),
            executado_em = CURRENT_TIMESTAMP
    """)

    with engine.begin() as conexao:
        conexao.execute(consulta, {
            "tabela": tabela,
            "regra": regra,
            "total": total_registros,
            "validos": registros_validos,
            "invalidos": registros_invalidos,
            "percentual": percentual
        })


def verificar_geracao():
    consulta = text("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN energia_mwh >= 0
                 AND disponibilidade_mw >= 0
                 AND energia_mwh <= disponibilidade_mw
                THEN 1 ELSE 0
            END) AS validos
        FROM medicao_geracao
    """)

    with engine.connect() as conexao:
        resultado = conexao.execute(consulta).mappings().one()

    total = resultado["total"]
    validos = resultado["validos"] or 0
    invalidos = total - validos

    registrar_metrica(
        "medicao_geracao",
        "validade_energia_disponibilidade",
        total,
        validos,
        invalidos
    )

    print(f"Total: {total}")
    print(f"Registros válidos: {validos}")
    print(f"Registros inválidos: {invalidos}")

def verificar_unicidade_geracao():
    consulta = text("""
        SELECT
            COUNT(*) AS total,
            COUNT(DISTINCT CONCAT(id_usina, '|', data_hora)) AS unicos
        FROM medicao_geracao
    """)

    with engine.connect() as conexao:
        resultado = conexao.execute(consulta).mappings().one()

    total = resultado["total"]
    validos = resultado["unicos"]
    invalidos = total - validos

    registrar_metrica(
        "medicao_geracao",
        "unicidade_usina_data_hora",
        total,
        validos,
        invalidos
    )

    print("\n--- Unicidade das medições ---")
    print(f"Total: {total}")
    print(f"Registros únicos: {validos}")
    print(f"Registros duplicados: {invalidos}")

def verificar_integridade_geracao():
    consulta = text("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN u.id_usina IS NOT NULL
                THEN 1 ELSE 0
            END) AS validos
        FROM medicao_geracao m
        LEFT JOIN usina u
            ON m.id_usina = u.id_usina
    """)

    with engine.connect() as conexao:
        resultado = conexao.execute(consulta).mappings().one()

    total = resultado["total"]
    validos = resultado["validos"] or 0
    invalidos = total - validos

    registrar_metrica(
        "medicao_geracao",
        "integridade_referencial_usina",
        total,
        validos,
        invalidos
    )

    print("\n--- Integridade referencial ---")
    print(f"Total: {total}")
    print(f"Registros válidos: {validos}")
    print(f"Registros sem usina: {invalidos}")

def verificar_completude_geracao():
    consulta = text("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN id_usina IS NOT NULL
                 AND data_hora IS NOT NULL
                 AND energia_mwh IS NOT NULL
                 AND disponibilidade_mw IS NOT NULL
                 AND origem IS NOT NULL
                 AND recebido_em IS NOT NULL
                THEN 1 ELSE 0
            END) AS validos
        FROM medicao_geracao
    """)

    with engine.connect() as conexao:
        resultado = conexao.execute(consulta).mappings().one()

    total = resultado["total"]
    validos = resultado["validos"] or 0
    invalidos = total - validos

    registrar_metrica(
        "medicao_geracao",
        "completude_campos_essenciais",
        total,
        validos,
        invalidos
    )

    print("\n--- Completude dos dados ---")
    print(f"Total: {total}")
    print(f"Registros completos: {validos}")
    print(f"Registros incompletos: {invalidos}")

def verificar_consistencia_temporal():
    consulta = text("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN data_hora >= '2025-01-01 00:00:00'
                 AND data_hora <= '2025-12-31 23:00:00'
                THEN 1 ELSE 0
            END) AS validos
        FROM medicao_geracao
    """)

    with engine.connect() as conexao:
        resultado = conexao.execute(consulta).mappings().one()

    total = resultado["total"]
    validos = resultado["validos"] or 0
    invalidos = total - validos

    registrar_metrica(
        "medicao_geracao",
        "consistencia_periodo_2025",
        total,
        validos,
        invalidos
    )

    print("\n--- Consistência temporal ---")
    print(f"Total: {total}")
    print(f"Registros no período: {validos}")
    print(f"Registros fora do período: {invalidos}")

def verificar_atualidade_geracao():
    consulta = text("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN recebido_em IS NOT NULL
                 AND recebido_em >= data_hora
                THEN 1 ELSE 0
            END) AS validos
        FROM medicao_geracao
    """)

    with engine.connect() as conexao:
        resultado = conexao.execute(consulta).mappings().one()

    total = resultado["total"]
    validos = resultado["validos"] or 0
    invalidos = total - validos

    registrar_metrica(
        "medicao_geracao",
        "atualidade_data_recebimento",
        total,
        validos,
        invalidos
    )

    print("\n--- Atualidade dos dados ---")
    print(f"Total: {total}")
    print(f"Registros com recebimento válido: {validos}")
    print(f"Registros com problema: {invalidos}")

def verificar_acuracia_geracao():
    consulta = text("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN m.energia_mwh <= u.potencia_mw
                THEN 1 ELSE 0
            END) AS validos
        FROM medicao_geracao m
        INNER JOIN usina u
            ON m.id_usina = u.id_usina
    """)

    with engine.connect() as conexao:
        resultado = conexao.execute(consulta).mappings().one()

    total = resultado["total"]
    validos = resultado["validos"] or 0
    invalidos = total - validos

    registrar_metrica(
        "medicao_geracao",
        "coerencia_potencia_instalada",
        total,
        validos,
        invalidos
    )

    print("\n--- Acurácia / coerência da geração ---")
    print(f"Total: {total}")
    print(f"Registros coerentes: {validos}")
    print(f"Registros incoerentes: {invalidos}")

def verificar_completude_clima():
    consulta = text("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN id_usina IS NOT NULL
                 AND data_hora IS NOT NULL
                 AND dados_originais IS NOT NULL
                 AND JSON_LENGTH(dados_originais) > 0
                 AND origem IS NOT NULL
                 AND origem <> ''
                 AND extraido_em IS NOT NULL
                THEN 1 ELSE 0
            END) AS validos
        FROM raw_clima_horario
    """)

    with engine.connect() as conexao:
        resultado = conexao.execute(consulta).mappings().one()

    total = resultado["total"]
    validos = resultado["validos"] or 0
    invalidos = total - validos

    registrar_metrica(
        "raw_clima_horario",
        "completude_campos_climaticos",
        total,
        validos,
        invalidos
    )

    print("\n--- Completude dos dados climáticos ---")
    print(f"Total: {total}")
    print(f"Registros completos: {validos}")
    print(f"Registros incompletos: {invalidos}")

def salvar_resultado_regra(tabela, regra, resultado, descricao):
    total = resultado["total"] or 0
    validos = resultado["validos"] or 0
    invalidos = total - validos

    registrar_metrica(
        tabela,
        regra,
        total,
        validos,
        invalidos
    )

    print(f"\n--- {descricao} ---")
    print(f"Total: {total}")
    print(f"Registros válidos: {validos}")
    print(f"Registros inválidos: {invalidos}")


def executar_consulta_regra(consulta):
    with engine.connect() as conexao:
        return conexao.execute(text(consulta)).mappings().one()



def verificar_unicidade_clima():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            COUNT(DISTINCT CONCAT(
                id_usina, '|', data_hora
            )) AS validos
        FROM raw_clima_horario
    """)

    salvar_resultado_regra(
        "raw_clima_horario",
        "unicidade_usina_data_hora",
        resultado,
        "Unicidade dos dados climáticos"
    )


def verificar_integridade_clima():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN u.id_usina IS NOT NULL
                THEN 1 ELSE 0
            END) AS validos
        FROM raw_clima_horario r
        LEFT JOIN usina u
            ON r.id_usina = u.id_usina
    """)

    salvar_resultado_regra(
        "raw_clima_horario",
        "integridade_referencial_usina",
        resultado,
        "Integridade referencial climática"
    )


def verificar_validade_clima():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN JSON_VALID(dados_originais)
                 AND JSON_LENGTH(dados_originais) > 0
                THEN 1 ELSE 0
            END) AS validos
        FROM raw_clima_horario
    """)

    salvar_resultado_regra(
        "raw_clima_horario",
        "validade_estrutura_json",
        resultado,
        "Validade da estrutura JSON climática"
    )


def verificar_consistencia_clima():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN data_hora >= '2025-01-01 00:00:00'
                 AND data_hora <= '2025-12-31 23:00:00'
                THEN 1 ELSE 0
            END) AS validos
        FROM raw_clima_horario
    """)

    salvar_resultado_regra(
        "raw_clima_horario",
        "consistencia_periodo_2025",
        resultado,
        "Consistência temporal climática"
    )


def verificar_atualidade_clima():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN extraido_em IS NOT NULL
                 AND extraido_em <= CURRENT_TIMESTAMP
                THEN 1 ELSE 0
            END) AS validos
        FROM raw_clima_horario
    """)

    salvar_resultado_regra(
        "raw_clima_horario",
        "atualidade_data_extracao",
        resultado,
        "Atualidade dos registros climáticos"
    )



def verificar_completude_usina():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN cod_usina IS NOT NULL
                 AND nome IS NOT NULL AND nome <> ''
                 AND id_fonte IS NOT NULL
                 AND cod_submercado IS NOT NULL
                 AND uf IS NOT NULL
                 AND municipio IS NOT NULL
                 AND latitude IS NOT NULL
                 AND longitude IS NOT NULL
                 AND potencia_mw IS NOT NULL
                 AND data_inicio_operacao IS NOT NULL
                 AND situacao IS NOT NULL
                THEN 1 ELSE 0
            END) AS validos
        FROM usina
    """)

    salvar_resultado_regra(
        "usina",
        "completude_campos_essenciais",
        resultado,
        "Completude das usinas"
    )


def verificar_unicidade_usina():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            COUNT(DISTINCT cod_usina) AS validos
        FROM usina
    """)

    salvar_resultado_regra(
        "usina",
        "unicidade_codigo_usina",
        resultado,
        "Unicidade dos códigos das usinas"
    )


def verificar_integridade_usina():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN f.id_fonte IS NOT NULL
                 AND s.cod_submercado IS NOT NULL
                THEN 1 ELSE 0
            END) AS validos
        FROM usina u
        LEFT JOIN fonte_energia f
            ON u.id_fonte = f.id_fonte
        LEFT JOIN submercado s
            ON u.cod_submercado = s.cod_submercado
    """)

    salvar_resultado_regra(
        "usina",
        "integridade_fontes_submercados",
        resultado,
        "Integridade referencial das usinas"
    )


def verificar_validade_usina():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN potencia_mw > 0
                 AND latitude BETWEEN -90 AND 90
                 AND longitude BETWEEN -180 AND 180
                 AND situacao <> ''
                THEN 1 ELSE 0
            END) AS validos
        FROM usina
    """)

    salvar_resultado_regra(
        "usina",
        "validade_potencia_coordenadas",
        resultado,
        "Validade dos dados das usinas"
    )



def verificar_completude_paradas():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN id_usina IS NOT NULL
                 AND inicio IS NOT NULL
                 AND fim IS NOT NULL
                 AND tipo IS NOT NULL
                 AND tipo <> ''
                 AND motivo IS NOT NULL
                 AND motivo <> ''
                THEN 1 ELSE 0
            END) AS validos
        FROM parada_usina
    """)

    salvar_resultado_regra(
        "parada_usina",
        "completude_campos_essenciais",
        resultado,
        "Completude das paradas"
    )


def verificar_integridade_paradas():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN u.id_usina IS NOT NULL
                THEN 1 ELSE 0
            END) AS validos
        FROM parada_usina p
        LEFT JOIN usina u
            ON p.id_usina = u.id_usina
    """)

    salvar_resultado_regra(
        "parada_usina",
        "integridade_referencial_usina",
        resultado,
        "Integridade referencial das paradas"
    )


def verificar_consistencia_paradas():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN fim >= inicio
                THEN 1 ELSE 0
            END) AS validos
        FROM parada_usina
    """)

    salvar_resultado_regra(
        "parada_usina",
        "consistencia_intervalo_temporal",
        resultado,
        "Consistência temporal das paradas"
    )



def verificar_completude_fontes():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN cod_fonte IS NOT NULL
                 AND descricao IS NOT NULL
                 AND descricao <> ''
                 AND renovavel IS NOT NULL
                 AND intermitente IS NOT NULL
                THEN 1 ELSE 0
            END) AS validos
        FROM fonte_energia
    """)

    salvar_resultado_regra(
        "fonte_energia",
        "completude_campos_essenciais",
        resultado,
        "Completude das fontes de energia"
    )


def verificar_validade_fontes():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN renovavel IN (0, 1)
                 AND intermitente IN (0, 1)
                THEN 1 ELSE 0
            END) AS validos
        FROM fonte_energia
    """)

    salvar_resultado_regra(
        "fonte_energia",
        "validade_indicadores_booleanos",
        resultado,
        "Validade das fontes de energia"
    )



def verificar_completude_submercados():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN cod_submercado IS NOT NULL
                 AND nome IS NOT NULL
                 AND nome <> ''
                THEN 1 ELSE 0
            END) AS validos
        FROM submercado
    """)

    salvar_resultado_regra(
        "submercado",
        "completude_campos_essenciais",
        resultado,
        "Completude dos submercados"
    )


def verificar_unicidade_submercados():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            COUNT(DISTINCT cod_submercado) AS codigos_unicos,
            COUNT(DISTINCT nome) AS nomes_unicos
        FROM submercado
    """)

    total = resultado["total"]
    validos = min(
        resultado["codigos_unicos"],
        resultado["nomes_unicos"]
    )
    resultado = {
        "total": total,
        "validos": validos
    }

    salvar_resultado_regra(
        "submercado",
        "unicidade_codigo_nome",
        resultado,
        "Unicidade dos submercados"
    )



def verificar_completude_feriados():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN data IS NOT NULL
                 AND descricao IS NOT NULL
                 AND descricao <> ''
                THEN 1 ELSE 0
            END) AS validos
        FROM feriado_nacional
    """)

    salvar_resultado_regra(
        "feriado_nacional",
        "completude_campos_essenciais",
        resultado,
        "Completude dos feriados"
    )


def verificar_unicidade_feriados():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            COUNT(DISTINCT data) AS validos
        FROM feriado_nacional
    """)

    salvar_resultado_regra(
        "feriado_nacional",
        "unicidade_data_feriado",
        resultado,
        "Unicidade das datas dos feriados"
    )



def verificar_consistencia_logs():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN inicio_em IS NOT NULL
                 AND fim_em IS NOT NULL
                 AND fim_em >= inicio_em
                 AND linhas_lidas >= 0
                 AND linhas_gravadas >= 0
                 AND linhas_gravadas <= linhas_lidas
                THEN 1 ELSE 0
            END) AS validos
        FROM log_carga
    """)

    salvar_resultado_regra(
        "log_carga",
        "consistencia_execucao_carga",
        resultado,
        "Consistência dos logs de carga"
    )


def verificar_completude_logs():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN tabela IS NOT NULL
                 AND tabela <> ''
                 AND status IS NOT NULL
                 AND status <> ''
                 AND registrado_em IS NOT NULL
                THEN 1 ELSE 0
            END) AS validos
        FROM log_carga
    """)

    salvar_resultado_regra(
        "log_carga",
        "completude_campos_log",
        resultado,
        "Completude dos logs de carga"
    )



# ================================================================
# QUALIDADE DOS DADOS DE PLD - CCEE (2025 E 2026)
# ================================================================

def verificar_completude_staging_pld():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN id_ckan IS NOT NULL AND id_ckan <> ''
                 AND mes_referencia IS NOT NULL AND mes_referencia <> ''
                 AND submercado IS NOT NULL AND submercado <> ''
                 AND periodo_comercializacao IS NOT NULL AND periodo_comercializacao <> ''
                 AND dia IS NOT NULL AND dia <> ''
                 AND hora IS NOT NULL AND hora <> ''
                 AND pld_hora IS NOT NULL AND pld_hora <> ''
                 AND arquivo_origem IS NOT NULL AND arquivo_origem <> ''
                 AND carregado_em IS NOT NULL
                THEN 1 ELSE 0
            END) AS validos
        FROM stg_pld_horario
    """)

    salvar_resultado_regra(
        "stg_pld_horario",
        "completude_campos_essenciais",
        resultado,
        "Completude da staging de PLD"
    )


def verificar_unicidade_staging_pld():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            COUNT(DISTINCT CONCAT(arquivo_origem, '|', id_ckan)) AS validos
        FROM stg_pld_horario
    """)

    salvar_resultado_regra(
        "stg_pld_horario",
        "unicidade_arquivo_id_origem",
        resultado,
        "Unicidade dos identificadores na staging de PLD"
    )


def verificar_validade_staging_pld():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN mes_referencia REGEXP '^[0-9]{6}$'
                 AND periodo_comercializacao REGEXP '^[0-9]+$'
                 AND dia REGEXP '^[0-9]{1,2}$'
                 AND CAST(dia AS UNSIGNED) BETWEEN 1 AND 31
                 AND hora REGEXP '^[0-9]{1,2}$'
                 AND CAST(hora AS UNSIGNED) BETWEEN 0 AND 23
                 AND pld_hora REGEXP '^-?[0-9]+([.][0-9]+)?$'
                THEN 1 ELSE 0
            END) AS validos
        FROM stg_pld_horario
    """)

    salvar_resultado_regra(
        "stg_pld_horario",
        "validade_formatos_brutos",
        resultado,
        "Validade dos formatos na staging de PLD"
    )


def verificar_completude_pld():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN cod_submercado IS NOT NULL AND cod_submercado <> ''
                 AND data_hora IS NOT NULL
                 AND mes_referencia IS NOT NULL AND mes_referencia <> ''
                 AND periodo_comercializacao IS NOT NULL
                 AND pld_rs_mwh IS NOT NULL
                 AND origem IS NOT NULL AND origem <> ''
                THEN 1 ELSE 0
            END) AS validos
        FROM pld_horario
    """)

    salvar_resultado_regra(
        "pld_horario",
        "completude_campos_essenciais",
        resultado,
        "Completude dos registros tratados de PLD"
    )


def verificar_unicidade_pld():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            COUNT(DISTINCT CONCAT(
                cod_submercado, '|',
                DATE_FORMAT(data_hora, '%Y-%m-%d %H:%i:%s')
            )) AS validos
        FROM pld_horario
    """)

    salvar_resultado_regra(
        "pld_horario",
        "unicidade_submercado_data_hora",
        resultado,
        "Unicidade por submercado e data/hora do PLD"
    )


def verificar_integridade_pld():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN s.cod_submercado IS NOT NULL
                THEN 1 ELSE 0
            END) AS validos
        FROM pld_horario p
        LEFT JOIN submercado s
            ON p.cod_submercado = s.cod_submercado
    """)

    salvar_resultado_regra(
        "pld_horario",
        "integridade_referencial_submercado",
        resultado,
        "Integridade referencial dos submercados do PLD"
    )


def verificar_validade_pld():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN pld_rs_mwh IS NOT NULL
                 AND mes_referencia REGEXP '^[0-9]{6}$'
                 AND periodo_comercializacao > 0
                 AND data_hora >= '2025-01-01 00:00:00'
                 AND data_hora < '2027-01-01 00:00:00'
                THEN 1 ELSE 0
            END) AS validos
        FROM pld_horario
    """)

    salvar_resultado_regra(
        "pld_horario",
        "validade_preco_e_periodo",
        resultado,
        "Validade dos preços e períodos do PLD"
    )


def verificar_consistencia_mes_referencia_pld():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN mes_referencia = DATE_FORMAT(data_hora, '%Y%m')
                THEN 1 ELSE 0
            END) AS validos
        FROM pld_horario
    """)

    salvar_resultado_regra(
        "pld_horario",
        "consistencia_mes_referencia_data_hora",
        resultado,
        "Consistência entre mês de referência e data/hora do PLD"
    )


def verificar_consistencia_periodo_comercializacao_pld():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN periodo_comercializacao =
                     ((DAY(data_hora) - 1) * 24 + HOUR(data_hora) + 1)
                THEN 1 ELSE 0
            END) AS validos
        FROM pld_horario
    """)

    salvar_resultado_regra(
        "pld_horario",
        "consistencia_periodo_comercializacao",
        resultado,
        "Consistência do período de comercialização do PLD"
    )


def verificar_consistencia_periodo_pld():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN data_hora >= '2025-01-01 00:00:00'
                 AND data_hora < '2027-01-01 00:00:00'
                THEN 1 ELSE 0
            END) AS validos
        FROM pld_horario
    """)

    salvar_resultado_regra(
        "pld_horario",
        "consistencia_intervalo_2025_2026",
        resultado,
        "Consistência do intervalo de datas do PLD"
    )


def verificar_completude_horaria_pld():
    consulta = text("""
        SELECT
            COUNT(DISTINCT CASE
                WHEN cod_submercado IN ('N', 'NE', 'S', 'SE')
                THEN CONCAT(
                    cod_submercado, '|',
                    DATE_FORMAT(data_hora, '%Y-%m-%d %H:%i:%s')
                )
            END) AS combinacoes_validas,
            MAX(data_hora) AS ultima_hora
        FROM pld_horario
        WHERE data_hora >= :inicio
          AND data_hora < :fim
    """)

    periodos = [
        (2025, "2025-01-01 00:00:00", "2026-01-01 00:00:00", 8760),
        (2026, "2026-01-01 00:00:00", "2027-01-01 00:00:00", None),
    ]

    for ano, inicio, fim, horas_fixas in periodos:
        with engine.connect() as conexao:
            resultado = conexao.execute(
                consulta,
                {"inicio": inicio, "fim": fim}
            ).mappings().one()

            if horas_fixas is None:
                ultima_hora = resultado["ultima_hora"]
                if ultima_hora is None:
                    horas_esperadas = 0
                else:
                    horas_esperadas = conexao.execute(text("""
                        SELECT TIMESTAMPDIFF(
                            HOUR,
                            '2026-01-01 00:00:00',
                            :ultima_hora
                        ) + 1
                    """), {"ultima_hora": ultima_hora}).scalar_one()
                    horas_esperadas = max(0, min(int(horas_esperadas), 8760))
            else:
                horas_esperadas = horas_fixas

        total_esperado = horas_esperadas * 4
        combinacoes_validas = min(
            int(resultado["combinacoes_validas"] or 0),
            total_esperado
        )

        registrar_metrica(
            "pld_horario",
            f"completude_cobertura_horaria_{ano}",
            total_esperado,
            combinacoes_validas,
            total_esperado - combinacoes_validas
        )

        print(f"\n--- Completude da cobertura horária do PLD ({ano}) ---")
        print(f"Horários esperados: {horas_esperadas:,}")
        print(f"Combinações hora/submercado esperadas: {total_esperado:,}")
        print(f"Combinações encontradas: {combinacoes_validas:,}")
        print(f"Combinações ausentes: {total_esperado - combinacoes_validas:,}")


def verificar_cobertura_quatro_submercados_pld():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN quantidade_submercados = 4
                 AND quantidade_submercados_validos = 4
                THEN 1 ELSE 0
            END) AS validos
        FROM (
            SELECT
                data_hora,
                COUNT(DISTINCT cod_submercado) AS quantidade_submercados,
                COUNT(DISTINCT CASE
                    WHEN cod_submercado IN ('N', 'NE', 'S', 'SE')
                    THEN cod_submercado
                END) AS quantidade_submercados_validos
            FROM pld_horario
            GROUP BY data_hora
        ) AS cobertura
    """)

    salvar_resultado_regra(
        "pld_horario",
        "quatro_submercados_por_horario",
        resultado,
        "Cobertura dos quatro submercados por horário"
    )


def verificar_consistencia_staging_tratada_pld():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN EXISTS (
                SELECT 1
                FROM pld_horario p
                WHERE p.cod_submercado = CASE UPPER(s.submercado)
                    WHEN 'NORTE' THEN 'N'
                    WHEN 'NORDESTE' THEN 'NE'
                    WHEN 'SUL' THEN 'S'
                    WHEN 'SUDESTE' THEN 'SE'
                    ELSE NULL
                END
                  AND p.data_hora = DATE_ADD(
                      STR_TO_DATE(
                          CONCAT(s.mes_referencia, LPAD(s.dia, 2, '0')),
                          '%Y%m%d'
                      ),
                      INTERVAL CAST(s.hora AS UNSIGNED) HOUR
                  )
                  AND p.mes_referencia = s.mes_referencia
                  AND p.periodo_comercializacao = CAST(s.periodo_comercializacao AS UNSIGNED)
                  AND p.pld_rs_mwh = CAST(s.pld_hora AS DECIMAL(10,2))
                  AND p.origem = CONCAT('CSV_CCEE_', LEFT(s.mes_referencia, 4))
            ) THEN 1 ELSE 0 END) AS validos
        FROM stg_pld_horario s
    """)

    salvar_resultado_regra(
        "stg_pld_horario",
        "consistencia_staging_tabela_tratada",
        resultado,
        "Consistência entre staging e PLD tratado"
    )


def verificar_consistencia_dw_pld():
    resultado = executar_consulta_regra("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE
                WHEN fp.id_fato_preco IS NOT NULL
                 AND fp.pld_rs_mwh = p.pld_rs_mwh
                 AND fp.mes_referencia = STR_TO_DATE(
                     CONCAT(p.mes_referencia, '01'), '%Y%m%d'
                 )
                 AND fp.periodo_comercializacao = p.periodo_comercializacao
                 AND fp.origem = p.origem
                THEN 1 ELSE 0
            END) AS validos
        FROM pld_horario p
        LEFT JOIN dw_campo_real.dim_tempo dt
            ON dt.data_hora = p.data_hora
        LEFT JOIN dw_campo_real.dim_submercado ds
            ON ds.cod_submercado_origem = p.cod_submercado
        LEFT JOIN dw_campo_real.fato_preco fp
            ON fp.id_tempo = dt.id_tempo
           AND fp.id_dim_submercado = ds.id_dim_submercado
        WHERE p.origem IN ('CSV_CCEE_2025', 'CSV_CCEE_2026')
    """)

    salvar_resultado_regra(
        "fato_preco",
        "consistencia_fato_preco_com_pld_tratado",
        resultado,
        "Consistência entre fato_preco e PLD tratado"
    )


if __name__ == "__main__":

    # MEDICAO_GERACAO
    verificar_geracao()
    verificar_unicidade_geracao()
    verificar_integridade_geracao()
    verificar_completude_geracao()
    verificar_consistencia_temporal()
    verificar_atualidade_geracao()
    verificar_acuracia_geracao()

    # RAW_CLIMA_HORARIO
    verificar_completude_clima()
    verificar_unicidade_clima()
    verificar_integridade_clima()
    verificar_validade_clima()
    verificar_consistencia_clima()
    verificar_atualidade_clima()

    # USINA
    verificar_completude_usina()
    verificar_unicidade_usina()
    verificar_integridade_usina()
    verificar_validade_usina()

    # PARADA_USINA
    verificar_completude_paradas()
    verificar_integridade_paradas()
    verificar_consistencia_paradas()

    # FONTE_ENERGIA
    verificar_completude_fontes()
    verificar_validade_fontes()

    # SUBMERCADO
    verificar_completude_submercados()
    verificar_unicidade_submercados()

    # FERIADO_NACIONAL
    verificar_completude_feriados()
    verificar_unicidade_feriados()

    # LOG_CARGA
    verificar_consistencia_logs()
    verificar_completude_logs()

    # PLD CCEE - STAGING, TABELA TRATADA E DATA WAREHOUSE
    verificar_completude_staging_pld()
    verificar_unicidade_staging_pld()
    verificar_validade_staging_pld()
    verificar_completude_pld()
    verificar_unicidade_pld()
    verificar_integridade_pld()
    verificar_validade_pld()
    verificar_consistencia_mes_referencia_pld()
    verificar_consistencia_periodo_comercializacao_pld()
    verificar_consistencia_periodo_pld()
    verificar_completude_horaria_pld()
    verificar_cobertura_quatro_submercados_pld()
    verificar_consistencia_staging_tratada_pld()
    verificar_consistencia_dw_pld()

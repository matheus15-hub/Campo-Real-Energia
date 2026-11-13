from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from conexao import engine


# Arquivos oficiais da CCEE colocados na pasta dados/ do projeto.
PASTA_PROJETO = Path(__file__).resolve().parents[1]
ARQUIVOS = {
    2025: PASTA_PROJETO / "dados" / "2a180a6b-f092-43eb-9f82-a48798b803dc.csv",
    2026: PASTA_PROJETO / "dados" / "3f279d6b-1069-42f7-9b0a-217b084729c4.csv",
}

REGISTROS_ESPERADOS = {
    2025: 35040,
    2026: 30432,
}

MAPA_SUBMERCADOS = {
    "NORTE": "N",
    "NORDESTE": "NE",
    "SUL": "S",
    "SUDESTE": "SE",
}

COLUNAS_OBRIGATORIAS = [
    "_id",
    "MES_REFERENCIA",
    "SUBMERCADO",
    "PERIODO_COMERCIALIZACAO",
    "DIA",
    "HORA",
    "PLD_HORA",
]


SQL_INSERIR_STAGING = text("""
    INSERT INTO campo_real_energia.stg_pld_horario (
        id_ckan,
        mes_referencia,
        submercado,
        periodo_comercializacao,
        dia,
        hora,
        pld_hora,
        arquivo_origem
    )
    VALUES (
        :id_ckan,
        :mes_referencia,
        :submercado,
        :periodo_comercializacao,
        :dia,
        :hora,
        :pld_hora,
        :arquivo_origem
    )
""")

SQL_INSERIR_TRATADO = text("""
    INSERT INTO campo_real_energia.pld_horario (
        cod_submercado,
        data_hora,
        mes_referencia,
        periodo_comercializacao,
        pld_rs_mwh,
        origem
    )
    VALUES (
        :cod_submercado,
        :data_hora,
        :mes_referencia,
        :periodo_comercializacao,
        :pld_rs_mwh,
        :origem
    )
    ON DUPLICATE KEY UPDATE
        mes_referencia = VALUES(mes_referencia),
        periodo_comercializacao = VALUES(periodo_comercializacao),
        pld_rs_mwh = VALUES(pld_rs_mwh),
        origem = VALUES(origem)
""")

SQL_CARREGAR_DIM_TEMPO_2026 = text("""
    INSERT INTO dw_campo_real.dim_tempo (
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
        SELECT DATE_ADD(
            '2026-01-01 00:00:00',
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
    WHERE h.data_hora < '2027-01-01 00:00:00'
      AND NOT EXISTS (
          SELECT 1
          FROM dw_campo_real.dim_tempo t
          WHERE t.data_hora = h.data_hora
      )
""")

SQL_CARREGAR_FATO_PRECO = text("""
    INSERT INTO dw_campo_real.fato_preco (
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
        STR_TO_DATE(CONCAT(p.mes_referencia, '01'), '%Y%m%d'),
        p.periodo_comercializacao,
        p.origem
    FROM campo_real_energia.pld_horario p
    INNER JOIN dw_campo_real.dim_tempo dt
        ON dt.data_hora = p.data_hora
    INNER JOIN dw_campo_real.dim_submercado ds
        ON ds.cod_submercado_origem = p.cod_submercado
    WHERE p.origem IN ('CSV_CCEE_2025', 'CSV_CCEE_2026')
    ON DUPLICATE KEY UPDATE
        pld_rs_mwh = VALUES(pld_rs_mwh),
        mes_referencia = VALUES(mes_referencia),
        periodo_comercializacao = VALUES(periodo_comercializacao),
        origem = VALUES(origem)
""")


def validar_e_preparar_csv(caminho: Path, ano: int):
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    df = pd.read_csv(
        caminho,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig"
    )
    df.columns = [str(coluna).strip().lstrip("\ufeff") for coluna in df.columns]

    faltando = [coluna for coluna in COLUNAS_OBRIGATORIAS if coluna not in df.columns]
    if faltando:
        raise ValueError(
            f"O arquivo {caminho.name} não possui as colunas esperadas: {faltando}"
        )

    if len(df) != REGISTROS_ESPERADOS[ano]:
        raise ValueError(
            f"Quantidade inesperada no arquivo {caminho.name}: {len(df)}. "
            f"Esperado: {REGISTROS_ESPERADOS[ano]} registros."
        )

    for coluna in COLUNAS_OBRIGATORIAS:
        df[coluna] = df[coluna].astype(str).str.strip()

    # Verifica campos obrigatórios vazios.
    campos_texto = ["_id", "MES_REFERENCIA", "SUBMERCADO", "PERIODO_COMERCIALIZACAO", "DIA", "HORA", "PLD_HORA"]
    vazios = df[campos_texto].eq("").any(axis=1)
    if vazios.any():
        raise ValueError(
            f"{caminho.name}: existem {int(vazios.sum())} registros com campos vazios."
        )

    # Converte os campos numéricos e rejeita valores inválidos.
    for coluna in ["MES_REFERENCIA", "PERIODO_COMERCIALIZACAO", "DIA", "HORA"]:
        df[coluna + "_num"] = pd.to_numeric(df[coluna], errors="coerce")

    numericos_invalidos = df[[
        "MES_REFERENCIA_num",
        "PERIODO_COMERCIALIZACAO_num",
        "DIA_num",
        "HORA_num",
    ]].isna().any(axis=1)
    if numericos_invalidos.any():
        raise ValueError(
            f"{caminho.name}: existem {int(numericos_invalidos.sum())} registros com campos numéricos inválidos."
        )

    for coluna in ["MES_REFERENCIA", "PERIODO_COMERCIALIZACAO", "DIA", "HORA"]:
        if not (df[coluna + "_num"] % 1 == 0).all():
            raise ValueError(f"{caminho.name}: a coluna {coluna} contém valores não inteiros.")
        df[coluna + "_num"] = df[coluna + "_num"].astype(int)

    if not df["MES_REFERENCIA"].str.fullmatch(r"\d{6}").all():
        raise ValueError(f"{caminho.name}: MES_REFERENCIA deve estar no formato AAAAMM.")

    df["SUBMERCADO"] = df["SUBMERCADO"].str.upper()
    submercados_invalidos = sorted(set(df["SUBMERCADO"]) - set(MAPA_SUBMERCADOS))
    if submercados_invalidos:
        raise ValueError(
            f"{caminho.name}: submercados não reconhecidos: {submercados_invalidos}"
        )

    if not df["DIA_num"].between(1, 31).all():
        raise ValueError(f"{caminho.name}: existem dias fora do intervalo de 1 a 31.")
    if not df["HORA_num"].between(0, 23).all():
        raise ValueError(f"{caminho.name}: existem horas fora do intervalo de 0 a 23.")

    # Monta a data/hora a partir do mês de referência, dia e hora comercial.
    data_texto = (
        df["MES_REFERENCIA"]
        + df["DIA_num"].astype(str).str.zfill(2)
    )
    data = pd.to_datetime(data_texto, format="%Y%m%d", errors="coerce")
    if data.isna().any():
        raise ValueError(f"{caminho.name}: existem datas de calendário inválidas.")

    if not (data.dt.year == ano).all():
        raise ValueError(f"{caminho.name}: há datas que não pertencem ao ano {ano}.")
    if not (data.dt.strftime("%Y%m") == df["MES_REFERENCIA"]).all():
        raise ValueError(f"{caminho.name}: dia e mês de referência não correspondem.")

    df["data_hora"] = data + pd.to_timedelta(df["HORA_num"], unit="h")

    # O período comercial é reiniciado a cada mês: dia 1/hora 0 = período 1.
    periodo_calculado = (df["DIA_num"] - 1) * 24 + df["HORA_num"] + 1
    if not (periodo_calculado == df["PERIODO_COMERCIALIZACAO_num"]).all():
        raise ValueError(
            f"{caminho.name}: há períodos de comercialização incompatíveis com dia e hora."
        )

    # Valida os preços como números decimais, preservando a precisão do CSV.
    precos = []
    for indice, valor in enumerate(df["PLD_HORA"], start=1):
        try:
            preco = Decimal(valor.replace(",", "."))
        except (InvalidOperation, AttributeError):
            raise ValueError(
                f"{caminho.name}: PLD_HORA inválido na linha {indice}: {valor!r}"
            )
        if not preco.is_finite():
            raise ValueError(
                f"{caminho.name}: PLD_HORA não finito na linha {indice}: {valor!r}"
            )
        if abs(preco) >= Decimal("100000000"):
            raise ValueError(
                f"{caminho.name}: PLD_HORA excede a precisão da coluna DECIMAL(10,2) na linha {indice}."
            )
        precos.append(preco)
    df["preco_decimal"] = precos

    # Unicidade: um registro por submercado em cada data/hora.
    duplicados = df.duplicated(subset=["data_hora", "SUBMERCADO"], keep=False)
    if duplicados.any():
        raise ValueError(
            f"{caminho.name}: foram encontrados {int(duplicados.sum())} registros duplicados por data/hora e submercado."
        )

    # Completude temporal: nenhuma hora ausente entre o primeiro e o último horário.
    horas_esperadas = pd.date_range(
        start=df["data_hora"].min(),
        end=df["data_hora"].max(),
        freq="h"
    )
    horas_encontradas = pd.DatetimeIndex(df["data_hora"].drop_duplicates().sort_values())
    horas_ausentes = horas_esperadas.difference(horas_encontradas)
    if len(horas_ausentes) > 0:
        exemplos = [str(hora) for hora in horas_ausentes[:5]]
        raise ValueError(
            f"{caminho.name}: existem {len(horas_ausentes)} horas ausentes. Exemplos: {exemplos}"
        )

    submercados_por_hora = df.groupby("data_hora")["SUBMERCADO"].nunique()
    horas_incompletas = submercados_por_hora[submercados_por_hora != 4]
    if not horas_incompletas.empty:
        raise ValueError(
            f"{caminho.name}: existem {len(horas_incompletas)} horas sem os quatro submercados."
        )

    # Prepara linhas para a tabela tratada.
    origem = f"CSV_CCEE_{ano}"
    registros_tratados = []
    for linha in df.itertuples(index=False):
        registros_tratados.append({
            "cod_submercado": MAPA_SUBMERCADOS[linha.SUBMERCADO],
            "data_hora": linha.data_hora.to_pydatetime(),
            "mes_referencia": linha.MES_REFERENCIA,
            "periodo_comercializacao": int(linha.PERIODO_COMERCIALIZACAO_num),
            "pld_rs_mwh": linha.preco_decimal,
            "origem": origem,
        })

    # Prepara linhas brutas, mantendo os valores recebidos no CSV.
    registros_staging = []
    nome_arquivo = caminho.name
    for linha in df.itertuples(index=False):
        registros_staging.append({
            "id_ckan": linha._0,
            "mes_referencia": linha.MES_REFERENCIA,
            "submercado": linha.SUBMERCADO,
            "periodo_comercializacao": str(linha.PERIODO_COMERCIALIZACAO_num),
            "dia": str(linha.DIA_num),
            "hora": str(linha.HORA_num),
            "pld_hora": linha.PLD_HORA,
            "arquivo_origem": nome_arquivo,
        })

    print(
        f"{ano}: {len(df):,} registros validados | "
        f"{len(horas_encontradas):,} horas | "
        f"{len(submercados_por_hora)} horários com os quatro submercados"
    )
    print(
        f"    Período: {df['data_hora'].min()} até {df['data_hora'].max()}"
    )

    return registros_staging, registros_tratados


def inserir_em_lotes(conexao, comando, registros, tamanho_lote=2000):
    for inicio in range(0, len(registros), tamanho_lote):
        lote = registros[inicio:inicio + tamanho_lote]
        conexao.execute(comando, lote)


def validar_estrutura_banco(conexao):
    tabelas = [
        ("campo_real_energia", "stg_pld_horario"),
        ("campo_real_energia", "pld_horario"),
        ("campo_real_energia", "feriado_nacional"),
        ("dw_campo_real", "dim_tempo"),
        ("dw_campo_real", "dim_submercado"),
        ("dw_campo_real", "fato_preco"),
    ]

    for schema, tabela in tabelas:
        existe = conexao.execute(text("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = :schema
              AND table_name = :tabela
        """), {"schema": schema, "tabela": tabela}).scalar_one()
        if not existe:
            raise RuntimeError(f"Tabela necessária não encontrada: {schema}.{tabela}")

    codigos_existentes = set(conexao.execute(text("""
        SELECT cod_submercado_origem
        FROM dw_campo_real.dim_submercado
    """)).scalars().all())

    codigos_necessarios = set(MAPA_SUBMERCADOS.values())
    faltando = sorted(codigos_necessarios - codigos_existentes)
    if faltando:
        raise RuntimeError(
            "A dimensão dw_campo_real.dim_submercado não possui os códigos: "
            + ", ".join(faltando)
        )

    horas_2025 = conexao.execute(text("""
        SELECT COUNT(*)
        FROM dw_campo_real.dim_tempo
        WHERE data_hora >= '2025-01-01 00:00:00'
          AND data_hora < '2026-01-01 00:00:00'
    """)).scalar_one()

    if horas_2025 != 8760:
        raise RuntimeError(
            f"A dimensão de tempo deveria conter 8.760 horas de 2025, mas contém {horas_2025}. "
            "A carga foi interrompida para não gerar um DW incompleto."
        )


def executar_integracao():
    print("=" * 65)
    print("INTEGRAÇÃO DOS ARQUIVOS PLD CCEE - 2025 E 2026")
    print("=" * 65)

    staging_geral = []
    tratados_geral = []
    nomes_arquivos = []

    # Todos os CSVs são validados antes de qualquer alteração no banco.
    for ano, caminho in ARQUIVOS.items():
        staging, tratados = validar_e_preparar_csv(caminho, ano)
        staging_geral.extend(staging)
        tratados_geral.extend(tratados)
        nomes_arquivos.append(caminho.name)

    if len(tratados_geral) != sum(REGISTROS_ESPERADOS.values()):
        raise RuntimeError("A quantidade total de registros preparados não confere.")

    print("\nOs dois arquivos passaram nas validações. Iniciando a gravação no banco...")

    # Uma transação envolve staging, tabela tratada, dimensão e fato.
    # Se ocorrer erro, o MySQL desfaz as alterações desta execução.
    with engine.begin() as conexao:
        validar_estrutura_banco(conexao)

        # Reexecução segura: substitui somente as linhas desses dois arquivos na staging.
        conexao.execute(text("""
            DELETE FROM campo_real_energia.stg_pld_horario
            WHERE arquivo_origem IN (:arquivo_2025, :arquivo_2026)
        """), {
            "arquivo_2025": nomes_arquivos[0],
            "arquivo_2026": nomes_arquivos[1],
        })

        inserir_em_lotes(conexao, SQL_INSERIR_STAGING, staging_geral)
        print(f"Staging: {len(staging_geral):,} registros inseridos.")

        inserir_em_lotes(conexao, SQL_INSERIR_TRATADO, tratados_geral)
        print(f"Tabela tratada: {len(tratados_geral):,} registros processados.")

        # Acrescenta 2026 à dimensão sem apagar nem alterar as datas de 2025.
        conexao.execute(SQL_CARREGAR_DIM_TEMPO_2026)
        total_2026_dim = conexao.execute(text("""
            SELECT COUNT(*)
            FROM dw_campo_real.dim_tempo
            WHERE data_hora >= '2026-01-01 00:00:00'
              AND data_hora < '2027-01-01 00:00:00'
        """)).scalar_one()
        if total_2026_dim != 8760:
            raise RuntimeError(
                f"A dimensão de tempo de 2026 ficou com {total_2026_dim} horas; esperado: 8.760."
            )
        print(f"Dimensão tempo: {total_2026_dim:,} horas de 2026 disponíveis.")

        # Atualiza registros existentes na mesma chave, em vez de criar duplicidades.
        conexao.execute(SQL_CARREGAR_FATO_PRECO)

        total_tratado = conexao.execute(text("""
            SELECT COUNT(*)
            FROM campo_real_energia.pld_horario
            WHERE origem IN ('CSV_CCEE_2025', 'CSV_CCEE_2026')
        """)).scalar_one()

        total_fato = conexao.execute(text("""
            SELECT COUNT(*)
            FROM dw_campo_real.fato_preco
            WHERE origem IN ('CSV_CCEE_2025', 'CSV_CCEE_2026')
        """)).scalar_one()

        if total_tratado != len(tratados_geral):
            raise RuntimeError(
                f"A tabela tratada possui {total_tratado} registros para os CSVs; "
                f"esperado: {len(tratados_geral)}."
            )
        if total_fato != len(tratados_geral):
            raise RuntimeError(
                f"A fato_preco possui {total_fato} registros para os CSVs; "
                f"esperado: {len(tratados_geral)}."
            )

    print("\n" + "=" * 65)
    print("INTEGRAÇÃO CONCLUÍDA COM SUCESSO")
    print(f"Registros na staging: {len(staging_geral):,}")
    print(f"Registros na tabela tratada: {total_tratado:,}")
    print(f"Registros na fato_preco: {total_fato:,}")
    print("A dimensão de tempo de 2025 foi preservada e 2026 foi acrescentado.")
    print("=" * 65)


if __name__ == "__main__":
    try:
        executar_integracao()
    except Exception as erro:
        print("\nERRO NA INTEGRAÇÃO:")
        print(erro)
        print("Nenhuma alteração da transação foi confirmada no banco.")
        raise
    finally:
        engine.dispose()

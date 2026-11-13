import pandas as pd
from sqlalchemy import create_engine, text
from conexao import engine


SCHEMA_ORIGEM = "campo_real_energia"
SCHEMA_DW = "dw_campo_real"

# O engine principal vem de scripts/conexao.py e aponta para o banco de origem.
# O segundo engine reutiliza as mesmas credenciais para acessar o Data Warehouse.
engine_dw = create_engine(
    engine.url.set(database=SCHEMA_DW),
    pool_pre_ping=True
)


def analisar_tabela(nome_tabela, conexao, schema):
    print(f"\n{'=' * 70}")
    print(f"ANÁLISE DA TABELA: {schema}.{nome_tabela}")
    print(f"{'=' * 70}")

    consulta = text(
        f"SELECT * FROM `{schema}`.`{nome_tabela}`"
    )

    try:
        df = pd.read_sql_query(consulta, conexao)
    except Exception as erro:
        print(f"Não foi possível analisar a tabela: {erro}")
        return False

    if df.empty:
        print("Tabela sem registros.")
        return True

    print(f"\nTotal de registros: {len(df):,}".replace(",", "."))
    print(f"Total de colunas: {len(df.columns)}")
    print(
        "Memória utilizada pelo DataFrame: "
        f"{df.memory_usage(deep=True).sum() / (1024 ** 2):.2f} MB"
    )

    print("\n--- Tipos de dados ---")
    print(df.dtypes.to_string())

    print("\n--- Valores nulos por coluna ---")
    nulos = df.isnull().sum()
    print(nulos.to_string())

    print("\n--- Valores distintos por coluna ---")
    distintos = df.nunique(dropna=True)
    print(distintos.to_string())

    print("\n--- Registros totalmente duplicados ---")
    print(int(df.duplicated().sum()))

    print("\n--- Estatísticas descritivas ---")
    try:
        print(df.describe(include="all", datetime_is_numeric=True).to_string())
    except TypeError:
        # Compatibilidade com versões do pandas que não possuem
        # o parâmetro datetime_is_numeric.
        print(df.describe(include="all").to_string())

    # Resumo numérico específico para o preço de energia, quando aplicável.
    if nome_tabela in {"pld_horario", "fato_preco"}:
        coluna_preco = (
            "pld_rs_mwh" if "pld_rs_mwh" in df.columns else None
        )
        if coluna_preco:
            valores = pd.to_numeric(df[coluna_preco], errors="coerce")
            print("\n--- Resumo específico do PLD (R$/MWh) ---")
            print(f"Mínimo: {valores.min()}")
            print(f"Máximo: {valores.max()}")
            print(f"Média: {valores.mean()}")
            print(f"Mediana: {valores.median()}")

    return True


def executar_profiling():
    tabelas_origem = [
        "usina",
        "submercado",
        "fonte_energia",
        "medicao_geracao",
        "parada_usina",
        "feriado_nacional",
        "raw_clima_horario",
        "log_carga",
        "stg_pld_horario",
        "pld_horario",
    ]

    tabelas_dw = [
        "dim_tempo",
        "dim_submercado",
        "fato_preco",
    ]

    sucessos = 0
    falhas = 0

    print("=" * 70)
    print("PROFILING DOS DADOS - CAMPO REAL ENERGIA")
    print("=" * 70)

    try:
        with engine.connect() as conexao_origem:
            for tabela in tabelas_origem:
                if analisar_tabela(tabela, conexao_origem, SCHEMA_ORIGEM):
                    sucessos += 1
                else:
                    falhas += 1

        with engine_dw.connect() as conexao_dw:
            for tabela in tabelas_dw:
                if analisar_tabela(tabela, conexao_dw, SCHEMA_DW):
                    sucessos += 1
                else:
                    falhas += 1
    finally:
        engine_dw.dispose()

    print("\n" + "=" * 70)
    print("RESUMO DO PROFILING")
    print(f"Tabelas analisadas com sucesso: {sucessos}")
    print(f"Tabelas com falha na análise: {falhas}")
    print("=" * 70)


if __name__ == "__main__":
    executar_profiling()

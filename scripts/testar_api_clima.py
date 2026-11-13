import requests
import pandas as pd
from sqlalchemy import text
from conexao import engine

# Busca a primeira usina cadastrada no MySQL
with engine.connect() as conexao:
    usina = conexao.execute(
        text("""
            SELECT id_usina, cod_usina, nome, latitude, longitude
            FROM usina
            ORDER BY id_usina
            LIMIT 1
        """)
    ).mappings().first()

if not usina:
    print("Nenhuma usina encontrada no banco.")
    exit()

print(f"Testando clima da usina: {usina['nome']}")

# Configuração da API Open-Meteo
url = "https://archive-api.open-meteo.com/v1/archive"

parametros = {
    "latitude": usina["latitude"],
    "longitude": usina["longitude"],
    "start_date": "2025-01-01",
    "end_date": "2025-12-31",
    "hourly": (
        "temperature_2m,"
        "precipitation,"
        "wind_speed_10m,"
        "shortwave_radiation"
    ),
    "timezone": "America/Sao_Paulo"
}

try:
    resposta = requests.get(
        url,
        params=parametros,
        timeout=60
    )

    resposta.raise_for_status()

    dados = resposta.json()

    df = pd.DataFrame(dados["hourly"])

    print("\nConsulta realizada com sucesso!")
    print(f"Usina: {usina['nome']}")
    print(f"Total de registros: {len(df)}")

    print("\nUnidades:")
    print(dados["hourly_units"])

    print("\nPrimeiros registros:")
    print(df.head())

except requests.RequestException as erro:
    print("Erro ao consultar Open-Meteo:")
    print(erro)

except (KeyError, ValueError) as erro:
    print("Erro ao interpretar os dados:")
    print(erro)

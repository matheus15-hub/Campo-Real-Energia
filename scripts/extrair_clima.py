import json
import time
import requests

from pathlib import Path
from datetime import datetime

from sqlalchemy import text
from conexao import engine


# Carrega as configurações
pasta_projeto = Path(__file__).resolve().parent.parent
caminho_config = pasta_projeto / "config" / "config.json"

with open(caminho_config, "r", encoding="utf-8") as arquivo:
    config = json.load(arquivo)

clima_config = config["open_meteo"]

url = clima_config["url"]
data_inicio = clima_config["data_inicio"]
data_fim = clima_config["data_fim"]
fuso = clima_config["fuso_horario"]
variaveis = clima_config["variaveis"]

TABELA_RAW = "raw_clima_horario"
TAMANHO_LOTE = 1000
MAX_TENTATIVAS = 3


def buscar_usinas():
    with engine.connect() as conexao:
        resultado = conexao.execute(text("""
            SELECT id_usina, cod_usina, nome, latitude, longitude
            FROM usina
            ORDER BY id_usina
        """))

        return [dict(linha) for linha in resultado.mappings()]


def registrar_inicio(inicio):
    with engine.begin() as conexao:
        resultado = conexao.execute(
            text("""
                INSERT INTO log_carga (
                    tabela,
                    arquivo,
                    linhas,
                    status,
                    observacao,
                    inicio_em,
                    linhas_lidas,
                    linhas_gravadas
                )
                VALUES (
                    :tabela,
                    :arquivo,
                    0,
                    'EM_ANDAMENTO',
                    'Extração climática Open-Meteo',
                    :inicio,
                    0,
                    0
                )
            """),
            {
                "tabela": TABELA_RAW,
                "arquivo": "Open-Meteo API",
                "inicio": inicio
            }
        )

        return resultado.lastrowid


def consultar_clima(usina):
    parametros = {
        "latitude": float(usina["latitude"]),
        "longitude": float(usina["longitude"]),
        "start_date": data_inicio,
        "end_date": data_fim,
        "hourly": ",".join(variaveis),
        "timezone": fuso
    }

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            resposta = requests.get(
                url,
                params=parametros,
                timeout=60,
                headers={"User-Agent": "CampoRealEnergia/1.0"}
            )

            resposta.raise_for_status()

            dados = resposta.json()

            if "hourly" not in dados:
                raise ValueError("Resposta sem dados horários.")

            return dados

        except (requests.RequestException, ValueError) as erro:
            print(
                f"Tentativa {tentativa}/{MAX_TENTATIVAS} "
                f"falhou para {usina['nome']}: {erro}"
            )

            if tentativa < MAX_TENTATIVAS:
                time.sleep(5 * tentativa)

    raise RuntimeError(
        f"Não foi possível consultar a usina {usina['nome']}."
    )


def preparar_registros(usina, dados, extraido_em):
    horario = dados["hourly"]
    unidades = dados["hourly_units"]

    registros = []

    for indice, horario_texto in enumerate(horario["time"]):

        data_hora = datetime.strptime(
            horario_texto,
            "%Y-%m-%dT%H:%M"
        )

        dados_originais = {
            "time": horario_texto
        }

        for variavel in variaveis:
            valores = horario.get(variavel, [])

            if len(valores) != len(horario["time"]):
                raise ValueError(
                    f"Quantidade inconsistente na variável {variavel}."
                )

            dados_originais[variavel] = valores[indice]

        registros.append({
            "id_usina": usina["id_usina"],
            "latitude": usina["latitude"],
            "longitude": usina["longitude"],
            "data_hora": data_hora,
            "dados_originais": json.dumps(
                dados_originais,
                ensure_ascii=False
            ),
            "unidades": json.dumps(
                unidades,
                ensure_ascii=False
            ),
            "origem": "Open-Meteo",
            "extraido_em": extraido_em
        })

    return registros


def gravar_registros(registros):
    comando = text("""
        INSERT INTO raw_clima_horario (
            id_usina,
            latitude,
            longitude,
            data_hora,
            dados_originais,
            unidades,
            origem,
            extraido_em
        )
        VALUES (
            :id_usina,
            :latitude,
            :longitude,
            :data_hora,
            :dados_originais,
            :unidades,
            :origem,
            :extraido_em
        )
    """)

    total_gravado = 0

    with engine.begin() as conexao:
        for inicio in range(0, len(registros), TAMANHO_LOTE):
            lote = registros[inicio:inicio + TAMANHO_LOTE]

            conexao.execute(comando, lote)

            total_gravado += len(lote)

    return total_gravado


def finalizar_log(id_log, inicio, linhas_lidas,
                  linhas_gravadas, erros):

    fim = datetime.now()

    if not erros:
        status = "SUCESSO"
        observacao = "Extração concluída para todas as usinas."
    elif linhas_gravadas > 0:
        status = "PARCIAL"
        observacao = "Extração concluída parcialmente."
    else:
        status = "ERRO"
        observacao = "Não foi possível gravar os dados."

    with engine.begin() as conexao:
        conexao.execute(
            text("""
                UPDATE log_carga
                SET linhas = :linhas,
                    linhas_lidas = :lidas,
                    linhas_gravadas = :gravadas,
                    status = :status,
                    observacao = :observacao,
                    erro = :erro,
                    fim_em = :fim
                WHERE id_log = :id_log
            """),
            {
                "linhas": linhas_gravadas,
                "lidas": linhas_lidas,
                "gravadas": linhas_gravadas,
                "status": status,
                "observacao": observacao,
                "erro": "\n".join(erros) if erros else None,
                "fim": fim,
                "id_log": id_log
            }
        )

    print("\n========== RESULTADO ==========")
    print(f"Status: {status}")
    print(f"Linhas lidas: {linhas_lidas}")
    print(f"Linhas gravadas: {linhas_gravadas}")
    print(f"Início: {inicio}")
    print(f"Fim: {fim}")

    if erros:
        print("\nErros encontrados:")
        for erro in erros:
            print(erro)


def executar_extracao():
    inicio = datetime.now()
    linhas_lidas = 0
    linhas_gravadas = 0
    erros = []

    id_log = registrar_inicio(inicio)

    try:
        usinas = buscar_usinas()

        print(f"Total de usinas encontradas: {len(usinas)}")

        for usina in usinas:
            print(f"\nConsultando: {usina['nome']}")

            try:
                dados = consultar_clima(usina)

                registros = preparar_registros(
                    usina,
                    dados,
                    datetime.now()
                )

                linhas_lidas += len(registros)

                gravadas = gravar_registros(registros)
                linhas_gravadas += gravadas

                print(f"Registros lidos: {len(registros)}")
                print(f"Registros gravados: {gravadas}")

            except Exception as erro:
                mensagem = f"{usina['nome']}: {erro}"
                erros.append(mensagem)
                print(f"Erro: {mensagem}")

        finalizar_log(
            id_log,
            inicio,
            linhas_lidas,
            linhas_gravadas,
            erros
        )

    except Exception as erro:
        erros.append(str(erro))

        finalizar_log(
            id_log,
            inicio,
            linhas_lidas,
            linhas_gravadas,
            erros
        )


if __name__ == "__main__":
    executar_extracao()

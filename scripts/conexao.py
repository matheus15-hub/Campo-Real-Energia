
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()

url = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", "3306")),
    database=os.getenv("DB_NAME")
)

engine = create_engine(url, pool_pre_ping=True)


def testar_conexao():
    try:
        with engine.connect() as conexao:
            resultado = conexao.execute(text("SELECT DATABASE()"))
            print("Conexão realizada com sucesso!")
            print(f"Banco conectado: {resultado.scalar()}")

    except Exception as erro:
        print("Erro ao conectar ao banco:")
        print(erro)


if __name__ == "__main__":
    testar_conexao()

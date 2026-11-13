import urllib.request
import urllib.error

resource_id = "2a180a6b-f092-43eb-9f82-a48798b803dc"

print("Consultando PLD 2025...")

url = (
    "https://dadosabertos.ccee.org.br/api/3/action/"
    f"datastore_search?resource_id={resource_id}&limit=5"
)

try:
    requisicao = urllib.request.urlopen(url, timeout=30)
    resposta = requisicao.read().decode("utf-8")

    print(resposta)

except urllib.error.HTTPError as erro:
    print(f"Erro HTTP: {erro.code}")
    print(erro.read().decode("utf-8"))

except Exception as erro:
    print(f"Erro: {erro}")
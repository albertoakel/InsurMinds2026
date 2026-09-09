import requests

from src.config import (
    HTTP_TIMEOUT_SECONDS,
    OPENWEATHER_API_KEY,
    OPENWEATHER_CURRENT_URL,
)

print("Chave carregada:", bool(OPENWEATHER_API_KEY))
print("Quantidade de caracteres:", len(OPENWEATHER_API_KEY))

if not OPENWEATHER_API_KEY:
    print("❌ A chave não foi carregada.")
    raise SystemExit(1)

try:
    resposta = requests.get(
        OPENWEATHER_CURRENT_URL,
        params={
            "q": "Belém,BR",
            "appid": OPENWEATHER_API_KEY,
            "units": "metric",
            "lang": "pt_br",
        },
        timeout=HTTP_TIMEOUT_SECONDS,
    )
except requests.RequestException as erro:
    print(f"❌ Erro de conexão: {erro}")
    raise SystemExit(1)

try:
    dados = resposta.json()
except ValueError:
    dados = {}

print("Status HTTP:", resposta.status_code)
print("Mensagem da API:", dados.get("message", "Sem mensagem de erro"))

if resposta.status_code == 200:
    print("✅ Chave válida e ativa.")
    print("Cidade:", dados.get("name"))
    print("Temperatura:", dados.get("main", {}).get("temp"))
elif resposta.status_code == 401:
    print("❌ A chave foi carregada, mas o OpenWeather recusou sua autenticação.")
elif resposta.status_code == 404:
    print("❌ Localidade não encontrada.")
else:
    print("❌ A API retornou outro tipo de erro.")

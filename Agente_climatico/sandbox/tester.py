import os

import requests
from dotenv import load_dotenv

# Carrega o conteúdo do .env para os.environ
carregou = load_dotenv()

chave = os.getenv("OPENWEATHER_API_KEY", "").strip()

print("Arquivo .env encontrado:", carregou)
print("Chave carregada:", bool(chave))
print("Quantidade de caracteres:", len(chave))

if not chave:
    print("❌ A chave não foi carregada.")
    raise SystemExit(1)

try:
    resposta = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={
            "q": "Belém,BR",
            "appid": chave,
            "units": "metric",
            "lang": "pt_br",
        },
        timeout=10,
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
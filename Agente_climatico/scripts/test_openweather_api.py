"""Teste manual de integração com a API Current Weather do OpenWeather."""

import sys
from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (  # noqa: E402
    TEMPO_LIMITE_SEGUNDOS,
    OPENWEATHER_API_KEY,
    OPENWEATHER_URL,
)


def main():
    """Consulta Belém e retorna zero somente quando a integração funcionar."""
    print("Chave carregada:", bool(OPENWEATHER_API_KEY))
    print("Quantidade de caracteres:", len(OPENWEATHER_API_KEY))

    if not OPENWEATHER_API_KEY:
        print("❌ A chave não foi carregada.")
        return 1

    try:
        resposta = requests.get(
            OPENWEATHER_URL,
            params={
                "q": "Belém,BR",
                "appid": OPENWEATHER_API_KEY,
                "units": "metric",
                "lang": "pt_br",
            },
            timeout=TEMPO_LIMITE_SEGUNDOS,
        )
    except requests.RequestException as erro:
        # Não exibe a URL completa, pois ela pode conter a chave da API.
        print(f"❌ Erro de conexão ({type(erro).__name__}).")
        return 1

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
        return 0

    if resposta.status_code == 401:
        print("❌ A chave foi carregada, mas o OpenWeather recusou a autenticação.")
    elif resposta.status_code == 404:
        print("❌ Localidade não encontrada.")
    else:
        print("❌ A API retornou outro tipo de erro.")

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

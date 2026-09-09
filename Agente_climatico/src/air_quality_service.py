# """Consulta e interpretação dos dados atuais de qualidade do ar."""
#
# import os
# from pathlib import Path
#
# import requests
# from dotenv import load_dotenv
# from .config import OPENWEATHER_API_KEY
#
# BASE_DIR = Path(__file__).resolve().parent
# load_dotenv(BASE_DIR / ".env")
#
# API_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()
# AIR_POLLUTION_URL = (
#     "https://api.openweathermap.org/data/2.5/air_pollution"
# )
# TEMPO_LIMITE_SEGUNDOS = 10
# LIMITE_AQI_ALERTA = 4
#
# CLASSIFICACOES_AQI = {
#     1: "Boa",
#     2: "Razoável",
#     3: "Moderada",
#     4: "Ruim",
#     5: "Muito ruim",
# }

"""Consulta e interpretação dos dados atuais de qualidade do ar."""

import requests

from .config import (
    TEMPO_LIMITE_SEGUNDOS,
    AIR_POLLUTION_URL,
    OPENWEATHER_API_KEY,
)


LIMITE_AQI_ALERTA = 4

CLASSIFICACOES_AQI = {
    1: "Boa",
    2: "Razoável",
    3: "Moderada",
    4: "Ruim",
    5: "Muito ruim",
}

def _converter_componente(componentes, nome):
    """Converte um componente para float ou retorna None se estiver ausente."""
    valor = componentes.get(nome)
    return float(valor) if valor is not None else None


def interpretar_qualidade_ar(dados):
    """Interpreta a resposta da API de qualidade do ar do OpenWeather."""
    try:
        observacao = dados["list"][0]
        indice_aqi = int(observacao["main"]["aqi"])
        componentes = observacao["components"]
    except (KeyError, IndexError, TypeError, ValueError):
        return None

    if indice_aqi not in CLASSIFICACOES_AQI:
        return None

    try:
        return {
            "aqi_openweather": indice_aqi,
            "classificacao": CLASSIFICACOES_AQI[indice_aqi],
            "gera_alerta": indice_aqi >= LIMITE_AQI_ALERTA,
            "evento_relevante": (
                "Qualidade do Ar Ruim"
                if indice_aqi >= LIMITE_AQI_ALERTA
                else None
            ),
            "pm2_5": _converter_componente(componentes, "pm2_5"),
            "pm10": _converter_componente(componentes, "pm10"),
            "o3": _converter_componente(componentes, "o3"),
            "no2": _converter_componente(componentes, "no2"),
            "so2": _converter_componente(componentes, "so2"),
            "co": _converter_componente(componentes, "co"),
            "no": _converter_componente(componentes, "no"),
            "nh3": _converter_componente(componentes, "nh3"),
        }
    except (TypeError, ValueError):
        return None


def obter_qualidade_ar(latitude, longitude):
    """Consulta a qualidade atual do ar usando latitude e longitude."""
    if not OPENWEATHER_API_KEY:
        raise ValueError(
            "A variável OPENWEATHER_API_KEY não foi encontrada no arquivo .env."
        )

    parametros = {
        "lat": latitude,
        "lon": longitude,
        "appid": OPENWEATHER_API_KEY,
    }

    try:
        resposta = requests.get(
            AIR_POLLUTION_URL,
            params=parametros,
            timeout=TEMPO_LIMITE_SEGUNDOS,
        )
    except requests.Timeout:
        print("Tempo limite excedido ao consultar a qualidade do ar.")
        return None
    except requests.RequestException as erro:
        # Evita imprimir a URL completa, pois ela contém a chave da API.
        print(
            "Falha de conexão ao consultar a qualidade do ar "
            f"({type(erro).__name__})."
        )
        return None

    if resposta.status_code == 401:
        print("A chave do OpenWeather foi recusada na consulta de qualidade do ar.")
        return None

    if resposta.status_code == 429:
        print("O limite de consultas do OpenWeather foi excedido.")
        return None

    if not resposta.ok:
        print(
            "O OpenWeather retornou HTTP "
            f"{resposta.status_code} na consulta de qualidade do ar."
        )
        return None

    try:
        dados = resposta.json()
    except ValueError:
        print("O OpenWeather retornou uma resposta inválida sobre qualidade do ar.")
        return None

    qualidade_ar = interpretar_qualidade_ar(dados)

    if qualidade_ar is None:
        print("O OpenWeather retornou dados incompletos sobre qualidade do ar.")

    return qualidade_ar

# import os
# from pathlib import Path
#
# import requests
# from dotenv import load_dotenv
#
#
# BASE_DIR = Path(__file__).resolve().parent
# load_dotenv(BASE_DIR / ".env")
#
# API_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()
# OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

import requests

from .config import (
    TEMPO_LIMITE_SEGUNDOS,
    OPENWEATHER_API_KEY,
    OPENWEATHER_URL,
)

# Códigos do OpenWeather para chuva de intensidade forte ou superior.
CODIGOS_CHUVA_FORTE = {502, 503, 504, 522}

# Códigos 200–232 representam tempestades com trovoadas.
CODIGOS_TEMPESTADE = set(range(200, 233))

# Limiares(OMS) adotados para a simulação do MVP.
LIMITE_VENTO_FORTE_KMH = 40.0
LIMITE_CALOR_EXTREMO_C = 35.0
LIMITE_SENSACAO_CALOR_EXTREMO_C = 38.0
LIMITE_FRIO_INTENSO_C = 10.0
LIMITE_UMIDADE_BAIXA_PERCENTUAL = 30

def identificar_eventos(
    codigo_clima,
    temperatura,
    sensacao_termica,
    umidade,
    vento_kmh,
):
    """Identifica todos os eventos relevantes presentes na observação atual."""
    eventos = []

    if codigo_clima in CODIGOS_TEMPESTADE:
        eventos.append("Tempestade")
    elif codigo_clima in CODIGOS_CHUVA_FORTE:
        eventos.append("Chuva Forte")

    if vento_kmh > LIMITE_VENTO_FORTE_KMH:
        eventos.append("Ventos Fortes")

    if (
        temperatura >= LIMITE_CALOR_EXTREMO_C
        or sensacao_termica >= LIMITE_SENSACAO_CALOR_EXTREMO_C
    ):
        eventos.append("Calor Extremo")
    elif (
        temperatura <= LIMITE_FRIO_INTENSO_C
        or sensacao_termica <= LIMITE_FRIO_INTENSO_C
    ):
        eventos.append("Frio Intenso")

    if umidade <= LIMITE_UMIDADE_BAIXA_PERCENTUAL:
        eventos.append("Baixa Umidade")

    return eventos


def obter_dados_climaticos(cidade):
    """Consulta o clima atual de uma cidade e identifica eventos relevantes."""
    if not OPENWEATHER_API_KEY:
        raise ValueError(
            "A variável OPENWEATHER_API_KEY não foi encontrada no arquivo .env."
        )

    parametros = {
        "q": f"{cidade},BR",
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "pt_br",
    }

    try:
        resposta = requests.get(
            OPENWEATHER_URL,
            params=parametros,
            timeout=TEMPO_LIMITE_SEGUNDOS,
        )
    except requests.Timeout:
        print(f"Tempo limite excedido ao consultar o clima de {cidade}.")
        return None
    except requests.RequestException as erro:
        # Não imprime a exceção completa, pois ela pode conter a chave na URL.
        print(
            f"Falha de conexão ao consultar o clima de {cidade} "
            f"({type(erro).__name__})."
        )
        return None

    if resposta.status_code == 401:
        print("A chave do OpenWeather foi recusada.")
        return None

    if resposta.status_code == 404:
        print(f"Cidade não encontrada pelo OpenWeather: {cidade}.")
        return None

    if resposta.status_code == 429:
        print("O limite de consultas do OpenWeather foi excedido.")
        return None

    if not resposta.ok:
        print(
            f"O OpenWeather retornou HTTP {resposta.status_code} "
            f"para {cidade}."
        )
        return None

    try:
        dados = resposta.json()
        temperatura = float(dados["main"]["temp"])
        sensacao_termica = float(dados["main"]["feels_like"])
        umidade = int(dados["main"]["humidity"])
        vento_kmh = float(dados.get("wind", {}).get("speed", 0.0)) * 3.6
        observacao = dados["weather"][0]
        codigo_clima = int(observacao["id"])
        condicao = str(observacao["main"]).lower()
        descricao = str(observacao["description"])
        chuva_1h = float(dados.get("rain", {}).get("1h", 0.0))
        latitude = float(dados["coord"]["lat"])
        longitude = float(dados["coord"]["lon"])
    except (KeyError, IndexError, TypeError, ValueError):
        print(f"O OpenWeather retornou dados incompletos para {cidade}.")
        return None

    eventos = identificar_eventos(
        codigo_clima=codigo_clima,
        temperatura=temperatura,
        sensacao_termica=sensacao_termica,
        umidade=umidade,
        vento_kmh=vento_kmh,
    )

    # Mantém o campo antigo para compatibilidade com outras partes do projeto.
    evento_principal = eventos[0] if eventos else None

    return {
        "cidade": dados.get("name", cidade),
        "latitude": latitude,
        "longitude": longitude,
        "temperatura": temperatura,
        "sensacao_termica": sensacao_termica,
        "umidade": umidade,
        "vento": vento_kmh,
        "chuva_1h": chuva_1h,
        "codigo_clima": codigo_clima,
        "condicao": condicao,
        "descricao": descricao,
        "eventos_relevantes": eventos,
        "evento_relevante": eventos[0] if eventos else None,
    }

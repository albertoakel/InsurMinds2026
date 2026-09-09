"""Configurações gerais e caminhos do projeto."""

import os
from pathlib import Path
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
DATASET_DIR = PROJECT_ROOT / "dataset"
DEFAULT_CLIENTS_FILE = DATASET_DIR / "clientes.csv"

# Carrega explicitamente o arquivo .env localizado na raiz do projeto.
load_dotenv(ENV_FILE)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()
GROQ_MODEL = "openai/gpt-oss-20b"
GROQ_TEMPERATURE = 0.2
GROQ_MAX_RETRIES = 2

OPENWEATHER_URL = (
    "https://api.openweathermap.org/data/2.5/weather"
)
AIR_POLLUTION_URL = (
    "https://api.openweathermap.org/data/2.5/air_pollution"
)
TEMPO_LIMITE_SEGUNDOS = 10


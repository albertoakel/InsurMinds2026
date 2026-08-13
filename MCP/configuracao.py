#configuracao.py
import os
from dotenv import load_dotenv


ENV_PATH: str = '/home/akel/PycharmProjects/InsurMinds2026/.env'

def carrega_variaveis_ambiente() -> None:
    if os.path.exists(ENV_PATH):
        load_dotenv(ENV_PATH, override=True)
        print("✔ Variáveis de ambiente carregadas do arquivo .env")
    else:
        print(f"⚠ Aviso: Arquivo {ENV_PATH} não foi encontrado no diretório atual.")


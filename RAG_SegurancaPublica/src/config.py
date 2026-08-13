import os
from pathlib import Path
from dotenv import load_dotenv

# ==========================================
# CARREGA VARIÁVEIS DE AMBIENTE
# ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# ==========================================
# CONFIGURAÇÃO DE CREDENCIAIS
# ==========================================
os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN", "")

# O LangChain (Gemini) busca especificamente pela variável GOOGLE_API_KEY.
# Seu .env usa a chave não-padrão "GOOGLE_API" -> repassamos aqui.
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API", "")

# ==========================================
# CONFIGURAÇÕES DE PORTAS
# ==========================================
API_PORT = 9010
STREAMLIT_PORT = 9011

# ==========================================
# CONFIGURAÇÃO DE CAMINHOS
# ==========================================
DATA_DIR = BASE_DIR / "data"
FONTE_DIR = DATA_DIR / "fonte"

# Diretórios das duas bases já vetorizadas (usaremos apenas a "large")
#VECTORSTORE_LARGE_DIR = DATA_DIR / "vectorstore_large"
VECTORSTORE_LARGE_DIR = DATA_DIR / "vectorstore_teste_large"
VECTORSTORE_SMALL_DIR = DATA_DIR / "vectorstore_small"  # não utilizada no momento

# ==========================================
# CONFIGURAÇÃO DE MODELOS
# ==========================================
EMBEDDING_MODELS = [
    {"name": "intfloat/multilingual-e5-large-instruct", "diretorio": VECTORSTORE_LARGE_DIR},
    {"name": "intfloat/multilingual-e5-small", "diretorio": VECTORSTORE_SMALL_DIR},
]

# Modelo ativo no momento -> large (índice 0)
ACTIVE_EMBEDDING_INDEX = 0
ACTIVE_EMBEDDING = EMBEDDING_MODELS[ACTIVE_EMBEDDING_INDEX]

# Diretório do vetor efetivamente usado pelo pipeline
VECTORSTORE_DIR = ACTIVE_EMBEDDING["diretorio"]

LLM_MODELS = [
    'models/gemini-3.1-flash-lite',
    'models/gemini-2.5-flash-lite',
    'models/gemini-2.0-flash'
]

RERANK_model = [
    'cross-encoder/mmarco-mMiniLMv2-L12-H384-v1',
    'BAAI/bge-reranker-v2-m3'
]

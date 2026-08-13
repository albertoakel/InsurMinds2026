from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import time

from src.config import RERANK_model, API_PORT
from src.database import get_vector_db, construir_indice_bm25
from src.rag import answer_query_with_fallback
from sentence_transformers import CrossEncoder  # rerank


# 1. Cria a API
app = FastAPI(title="Analista de Segurança Pública (RAG)")


# 2. CARREGA O BANCO UMA ÚNICA VEZ NA MEMÓRIA (quando o servidor liga)
print(f"[{time.strftime('%H:%M:%S')}] Conectando ao ChromaDB...")
vector_db_instance = get_vector_db()
print(f"[{time.strftime('%H:%M:%S')}] Banco carregado com sucesso!")

# Inicializa o BM25 a partir dos dados do Chroma
print(f"[{time.strftime('%H:%M:%S')}] Construindo índice BM25...")
bm25_retriever_instance = construir_indice_bm25(vector_db_instance)
print(f"[{time.strftime('%H:%M:%S')}] BM25 carregado com sucesso!")

# Inicializa o Reranker
print(f"[{time.strftime('%H:%M:%S')}] Carregando Reranker: {RERANK_model[0]}...")
reranker_instance = CrossEncoder(RERANK_model[0], device='cpu')
print(f"[{time.strftime('%H:%M:%S')}] Todos os componentes carregados com sucesso!")


# 3. Modelo de uma única mensagem
class Mensagem(BaseModel):
    role: str      # 'user' ou 'assistant'
    content: str


# 4. Modelo da requisição principal (com histórico/memória)
class QueryRequest(BaseModel):
    pergunta: str
    historico: List[Mensagem] = []


# 5. Rota (endpoint) para receber perguntas
@app.post("/perguntar")
def perguntar(request: QueryRequest):
    resposta = answer_query_with_fallback(
        pergunta=request.pergunta,
        historico=request.historico,
        db=vector_db_instance,
        bm25_retriever=bm25_retriever_instance,
        reranker=reranker_instance
    )

    return {"pergunta": request.pergunta, "resposta": resposta}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", port=API_PORT, reload=True)

# Para rodar manualmente:
# uvicorn main:app --port 9010 --reload

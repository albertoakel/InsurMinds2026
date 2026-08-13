import re
import time

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from src.config import VECTORSTORE_DIR, ACTIVE_EMBEDDING


def get_embedding_function():
    return HuggingFaceEmbeddings(
        model_name=ACTIVE_EMBEDDING['name'],
        model_kwargs={"device": "cpu", "trust_remote_code": True},
        encode_kwargs={"normalize_embeddings": True, "prompt": "query: "}
    )


def get_vector_db() -> Chroma:
    """
    Diferente do Palantir (que tinha 3-4 bases/livros), aqui existe UMA única
    base vetorial: o relatório de segurança pública. Por isso get_vector_db
    retorna diretamente uma instância Chroma, e não um dicionário de bases.
    """
    t0 = time.time()
    embedding = get_embedding_function()
    print(f"Embedding: {time.time() - t0:.2f}s")
    print("==============================================================")

    db = Chroma(persist_directory=str(VECTORSTORE_DIR), embedding_function=embedding)
    total = db._collection.count()

    print(f"[DB] Relatório Segurança Pública | {total:>5} chunks | {VECTORSTORE_DIR.name}")
    print(f"[DB] Modelo                      : {ACTIVE_EMBEDDING['name']}")
    print("==============================================================")

    return db


def preprocess_portugues(texto: str) -> list[str]:
    texto_limpo = re.sub(r'[^\w\s]', '', texto.lower())
    return texto_limpo.split()


def construir_indice_bm25(db: Chroma) -> BM25Retriever:
    """Constrói o índice lexical BM25 a partir dos documentos já presentes no Chroma."""
    print(" ⏳ Construindo índice lexical (BM25)...")

    dados = db.get()  # Extrai os dados já existentes no ChromaDB
    textos = dados['documents']
    metadatas = dados['metadatas']

    documentos = [
        Document(page_content=texto, metadata=meta)
        for texto, meta in zip(textos, metadatas)
    ]

    bm25_retriever = BM25Retriever.from_documents(
        documentos,
        preprocess_func=preprocess_portugues
    )
    bm25_retriever.k = 10  # Quantidade de documentos que o BM25 vai retornar
    print(" ✅ Índice BM25 pronto!")
    return bm25_retriever

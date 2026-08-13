#make_vector_store
import os
import shutil

import re
import time
from pathlib import Path
from dotenv import load_dotenv

#import pdfplumber
from tqdm import tqdm
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

#funções auxiliares
from make_vector_aux import *


import warnings
warnings.filterwarnings('ignore')

# 0) Leituras das APIs
load_dotenv()



"""
    ROTINAS PARA CRIAR VECTOR STORE A PARTIR DE UM PDF COM TABELAS(EX: RELATORIOS)
-> 1) verify_vector_store
"""

def verify_vector_store(default_dir):

    """
    Verifica se o diretório de um Vector Store já existe.
    Oferece opções seguras: sobrescrever, criar novo ou cancelar.
    """
    if not os.path.exists(default_dir):
        os.makedirs(default_dir, exist_ok=True)
        print(f"✨ O diretório do VECTOR STORE '{default_dir}' não existia e foi criado com sucesso!")
        return default_dir

    print(f"\n⚠️  ATENÇÃO: Já existe uma pasta/diretório com o nome '{default_dir}'!")
    print("   → Sobrescrever esta pasta apagará todos os arquivos contidos nela.\n")
    print("1 - SOBRESCREVER (apaga todo conteúdo existente no diretorio)")
    print("2 - CRIAR NOVO diretório (mantém a pasta atual, usa outro nome)")
    print("3 - CANCELAR processo (não faz nenhuma alteração)")
    opcao = input("Escolha uma opção (1/2/3): ").strip()

    if opcao == "1":
        print(f"\n⚠️ Removendo permanentemente o diretório '{default_dir}'...")
        shutil.rmtree(default_dir)
        time.sleep(2)  # Pausa mínima apenas para o SO processar a exclusão
        print(f"✓ Diretório removido. NOVO banco será criado em '{default_dir}'")
        os.makedirs(default_dir, exist_ok=True)
        return default_dir

    elif opcao == "2":
        diretorio_pai = os.path.dirname(default_dir)
        # LOOP DE TENTATIVAS: Só sai daqui quando achar um nome que NÃO existe
        while True:
            nome_novo_dir = input("\nDigite o nome do NOVO diretório (ex: vector_2): ").strip()

            # Se o usuário der Enter sem digitar nada, gera um timestamp automático
            if not nome_novo_dir:
                nome_novo_dir =  f"{os.path.basename(default_dir)}_{int(time.time())}"
                print(f"Nome vazio. Gerando nome automático baseado no tempo: '{nome_novo_dir}'")

            novo_dir = os.path.join(diretorio_pai, nome_novo_dir)

            # Validação crucial: Verifica se este novo nome também já existe no disco
            if os.path.exists(novo_dir):
                print(f"❌ Erro: O diretório '{novo_dir}' TAMBÉM já existe! Escolha outro nome.")
                # O loop continua e pede o input novamente...
            else:
                print(f"✓ Novo diretório definido e disponível: '{novo_dir}'")
                os.makedirs(novo_dir, exist_ok=True)
                return novo_dir

    elif opcao == "3":
        print("\n❌ Processo cancelado pelo usuário.")
        print(f"Finalizado em: {time.strftime('%d/%m/%Y - %H:%M:%S')}")
        sys.exit(0)

    else:
        print("\n❌ Opção inválida. Processo cancelado.")
        print(f"Finalizado em: {time.strftime('%d/%m/%Y - %H:%M:%S')}")
        sys.exit(1)


def make_split_document(diretorio_fonte):

    """
    >> READ SOURCES ===================================================================================================
    ler todos os pdf dentro da fonte. e cria um unico vetor_store
    """
    docs_texto, docs_tabela = carregar_com_pdfplumber(diretorio_fonte)
    print(f"\n✔ Carregamento concluído")
    print(f"  Páginas de texto : {len(docs_texto)}")
    print(f"  Tabelas extraídas: {len(docs_tabela)}")
    print(f"# {time.strftime('%d/%m/%Y - %H:%M:%S')}")

    """
    >> SPLIT SECTION ===================================================================================================
    """
    CHUNK_SIZE    = 1000      # reduzido de 1200: texto técnico denso é mais preciso menor
    CHUNK_OVERLAP = 150
    MAX_TABLE_CHARS = 3000     # tabelas maiores que isso são divididas com repetição de cabeçalho

# ── 2a. Splitter para texto narrativo ────────────────────────────────────────
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", "!", "?", " "],
        length_function=len,)

    split_texto = text_splitter.split_documents(docs_texto)
    print(f"✔ Texto fatiado: {len(split_texto)} chunks")


# ── 2b. Splitter para tabelas (nunca corta no meio) ──────────────────────────
    def _split_tabela_grande(doc: Document, limite: int = MAX_TABLE_CHARS) -> list[Document]:
        """
        Se a tabela cabe no limite -> retorna como está (1 chunk).
        Se não cabe -> divide pelas linhas de dados, REPETINDO o cabeçalho
        em cada parte para que o embedding nunca veja uma linha sem contexto
        de coluna.
        """
        if len(doc.page_content) <= limite:
            return [doc]

        linhas = doc.page_content.split("\n")

        if len(linhas) < 4:          # tabela minúscula mesmo
            return [doc]

        cabecalho  = linhas[0] + "\n" + linhas[1]   # | col1 | col2 | ... e |---|---|...
        linhas_dados = linhas[2:]

        partes, bloco, tamanho = [], [], len(cabecalho)
        for linha in linhas_dados:
            if tamanho + len(linha) > limite and bloco:
                conteudo = cabecalho + "\n" + "\n".join(bloco)
                partes.append(Document(page_content=conteudo, metadata=dict(doc.metadata)))
                bloco, tamanho = [], len(cabecalho)
            bloco.append(linha)
            tamanho += len(linha)

        if bloco:
            conteudo = cabecalho + "\n" + "\n".join(bloco)
            partes.append(Document(page_content=conteudo, metadata=dict(doc.metadata)))

        for i, parte in enumerate(partes):
            parte.metadata["tabela_parte"] = f"{i + 1}/{len(partes)}"

        return partes


    split_tabelas = []
    for doc in docs_tabela:
        split_tabelas.extend(_split_tabela_grande(doc))
    print(f"✔ Tabelas processadas: {len(split_tabelas)} chunks")


# ── 2c. Une tudo e numera ─────────────────────────────────────────────────────
# Tabelas vão DEPOIS do texto para que chunk_id 0..N_texto sejam o narrativo
    split_documents = split_texto + split_tabelas

    for i, split in enumerate(split_documents):
        split.metadata.update({
            "chunk_id"   : i,
            "chunk_total": len(split_documents),
            "posicao"    : f"{i / len(split_documents) * 100:.0f}%",
            # "tipo" já foi definido na extração ("texto" ou "tabela")
            # garantia de que nenhum chunk fique sem o campo:
            "tipo"       : split.metadata.get("tipo", "texto"),
        })

    print(f"\n# Documento fatiado em: {time.strftime('%d/%m/%Y - %H:%M:%S')}")
    print(f"  chunk_total (texto)  : {len(split_texto)}")
    print(f"  chunk_total (tabelas): {len(split_tabelas)}")
    print(f"  chunk_total (geral)  : {len(split_documents)}")
    print("--------------------")
    return split_documents


def make_vector(split_documents,VECTORSTORE_DIR):

    if consultar_colecoes_chroma(VECTORSTORE_DIR,False)==True:
        print("Já existe uma coleção chorma no vectorstore")
        print("Base agregarar mais informação a base existente")

    else:
        print("Diretorio Vazio")



    """
    >> EMBEDDING
    """
    model1= 'intfloat/multilingual-e5-small'
    model2 = 'intfloat/multilingual-e5-large-instruct'

    embedding_model = HuggingFaceEmbeddings(
        model_name=model1,
        model_kwargs={"device": "cpu", "trust_remote_code": True},
        encode_kwargs={"normalize_embeddings": True, "prompt": "passage: "}
        )


    total = len(split_documents)
    print(f"#Finalizado EMBEDDING : {time.strftime('%H:%M:%S')}")
    print(f"#Total de CHUNKS      : {total} chunks")






    """
    >> VECTORSTORE BUILDING
    """
    print(f"\n#Iniciando Building VectorStore : {time.strftime('%H:%M:%S')}")

    batch_size = 150
    vectorstore = Chroma.from_documents(
        documents=split_documents[:batch_size],
        embedding=embedding_model,
        persist_directory=str(VECTORSTORE_DIR),
        collection_metadata={"hnsw:space": "cosine"})


    for i in tqdm(range(batch_size, total, batch_size), desc="Indexando chunks"):
        lote = split_documents[i:i + batch_size]
        vectorstore.add_documents(lote)
        print(f"  Lote {i // batch_size + 1}/{(total // batch_size) + 1} | "
                f"Chunks {i}-{min(i + batch_size, total)} | "
                f"{time.strftime('%H:%M:%S')}")

    print(f"\n#Banco criado com {vectorstore._collection.count()} chunks.")
    print(f"\n#Operação Completa : {time.strftime('%H:%M:%S')}")
    print("---------------------------------------------------------------")


if __name__ == '__main__':
    print("MAKE VECTOR STORE AGAIN")
    diretorio_store='/home/akel/PycharmProjects/InsurMinds2026/diretorio_teste/vectorstore_teste'
    diretorio_fonte='/home/akel/PycharmProjects/InsurMinds2026/diretorio_teste/fonte'

    #comando para verificar o diretorio
    #verify_vector_store(diretorio)


    #comando fazer split dos documentos
    #split_documents=make_split_document(diretorio_fonte)

    #comando para criar o vector_store
    #make_vector(split_documents, diretorio_store)


    #consultar detalhes da base
   # Resultado=consultar_colecoes_chroma(diretorio_store,False)

    diretorio_verificar='/home/akel/PycharmProjects/InsurMinds2026/notebooks/data/vectorstore_teste_large'
    Resultado=consultar_colecoes_chroma(diretorio_verificar)

    #
    # print(resultado)


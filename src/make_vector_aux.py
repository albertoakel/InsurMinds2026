import re
import time
import os

from pathlib import Path
import pdfplumber
from tqdm import tqdm
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

import warnings
warnings.filterwarnings('ignore')



def ola_Mundo():
    print('Ola caralhudo!')


TITULO_REGEX = re.compile(
    r"^(tabela|quadro|gr[aá]fico|figura)\s*[\d\.]+",
    re.IGNORECASE
)

def _tabela_para_markdown(dados: list[list]) -> str:
    """Converte lista-de-listas do pdfplumber em Markdown com cabeçalho."""
    linhas = [
        [(c or "").strip().replace("\n", " ") for c in row]
        for row in dados if any(c for c in row)
    ]
    if len(linhas) < 2:
        return ""
    cab = linhas[0]
    md  = "| " + " | ".join(cab) + " |\n"
    md += "|" + "|".join(["---"] * len(cab)) + "|\n"
    for row in linhas[1:]:
        row_adj = (row + [""] * len(cab))[:len(cab)]
        md += "| " + " | ".join(row_adj) + " |\n"
    return md

def _titulo_proximo(linhas_pagina: list[str]) -> str:
    """Retorna a legenda/título mais próximo antes de uma tabela."""
    for linha in reversed(linhas_pagina[-6:]):
        if TITULO_REGEX.search(linha):
            return linha.strip()
    return ""

def carregar_com_pdfplumber(diretorio: str | Path) -> tuple[list[Document], list[Document]]:
    """
    Retorna:
        docs_texto  -> páginas de texto narrativo (sem a área das tabelas*)
        docs_tabela -> uma tabela por Document, em Markdown

    * pdfplumber não remove automaticamente o texto da área da tabela,
      então ele aparece nos dois. Isso é aceitável: o chunk de tabela tem
      estrutura de coluna; o chunk de texto tem contexto narrativo.
    """
    docs_texto, docs_tabela = [], []
    pdfs = sorted(Path(diretorio).glob("*.pdf"))
    print(f"✔ {len(pdfs)} PDF(s) encontrado(s)")

    for pdf_path in pdfs:
        with pdfplumber.open(pdf_path) as pdf:
            for num_pag, pag in enumerate(pdf.pages):
                texto = pag.extract_text() or ""
                linhas = texto.split("\n")

                # — tabelas —
                for idx_tab, tbl in enumerate(pag.find_tables()):
                    md = _tabela_para_markdown(tbl.extract())
                    if not md:
                        continue
                    docs_tabela.append(Document(
                        page_content=md,
                        metadata={
                            "source"           : str(pdf_path),
                            "page"             : num_pag,          # mantém a chave "page" do PyPDF
                            "tipo"             : "tabela",
                            "titulo_tabela"    : _titulo_proximo(linhas),
                            "tabela_idx_pagina": idx_tab,
                        }
                    ))

                # — texto narrativo —
                if texto.strip():
                    docs_texto.append(Document(
                        page_content=texto,
                        metadata={
                            "source": str(pdf_path),
                            "page"  : num_pag,
                            "tipo"  : "texto",
                        }
                    ))

        n_tab = sum(1 for d in docs_tabela if d.metadata["source"] == str(pdf_path))
        n_txt = sum(1 for d in docs_texto  if d.metadata["source"] == str(pdf_path))
        print(f"  {pdf_path.name}: {n_txt} páginas de texto | {n_tab} tabelas")

    return docs_texto, docs_tabela
# ==========================================
# 1. EXTRAÇÃO — texto e tabelas separados
# ==========================================
def extrair_titulo_tabela(linhas_antes: list[str]) -> str:
    """Procura, nas últimas linhas antes da tabela, algo como 'Tabela 3 - Ocorrências...'."""
    for linha in reversed(linhas_antes[-5:]):
        if TITULO_TABELA_REGEX.search(linha):
            return linha.strip()
    return ""


def tabela_para_markdown(tabela: list[list]) -> str:
    """Converte uma tabela extraída pelo pdfplumber (lista de linhas) em Markdown."""
    linhas_limpas = [
        [(cel or "").strip().replace("\n", " ") for cel in linha]
        for linha in tabela
        if any(cel for cel in linha)
    ]
    if len(linhas_limpas) < 2:
        return ""

    cabecalho = linhas_limpas[0]
    corpo = linhas_limpas[1:]

    md = "| " + " | ".join(cabecalho) + " |\n"
    md += "|" + "|".join(["---"] * len(cabecalho)) + "|\n"
    for linha in corpo:
        linha_ajustada = (linha + [""] * len(cabecalho))[:len(cabecalho)]
        md += "| " + " | ".join(linha_ajustada) + " |\n"

    return md


def processar_pdf(caminho_pdf: Path) -> tuple[list[Document], list[Document]]:
    """Retorna (documentos_texto, documentos_tabela) de um único PDF."""
    docs_texto, docs_tabela = [], []

    with pdfplumber.open(caminho_pdf) as pdf:
        for num_pagina, pagina in enumerate(pdf.pages):
            texto_completo = pagina.extract_text() or ""
            linhas = texto_completo.split("\n")

            tabelas = pagina.find_tables()
            for idx_tab, tabela in enumerate(tabelas):
                dados = tabela.extract()
                md_tabela = tabela_para_markdown(dados)
                if not md_tabela:
                    continue

                titulo = extrair_titulo_tabela(linhas)

                docs_tabela.append(Document(
                    page_content=md_tabela,
                    metadata={
                        "source": str(caminho_pdf),
                        "page": num_pagina,
                        "tipo": "tabela",
                        "titulo_tabela": titulo or f"Tabela sem título (pág. {num_pagina + 1})",
                        "tabela_idx_na_pagina": idx_tab,
                    }
                ))

            # Nota: o texto da página continua incluindo os números da tabela
            # (o pdfplumber não remove automaticamente). Isso é aceitável:
            # o BM25/vetor pode até achar esse texto, mas a resposta "boa"
            # vem do chunk tipo="tabela", que tem estrutura de coluna.
            if texto_completo.strip():
                docs_texto.append(Document(
                    page_content=texto_completo,
                    metadata={
                        "source": str(caminho_pdf),
                        "page": num_pagina,
                        "tipo": "texto",
                    }
                ))

    return docs_texto, docs_tabela


def carregar_documentos(diretorio: Path) -> tuple[list[Document], list[Document]]:
    todos_texto, todas_tabelas = [], []
    pdfs = sorted(diretorio.glob("*.pdf"))
    print(f"✔ {len(pdfs)} PDF(s) encontrado(s) em {diretorio}")

    for pdf_path in pdfs:
        docs_texto, docs_tabela = processar_pdf(pdf_path)
        todos_texto.extend(docs_texto)
        todas_tabelas.extend(docs_tabela)
        print(f"  - {pdf_path.name}: {len(docs_texto)} páginas de texto | {len(docs_tabela)} tabelas")

    return todos_texto, todas_tabelas


# ==========================================
# 2. SPLIT — só o texto narrativo é fatiado
# ==========================================
def split_tabela_grande(doc: Document, limite: int = 3000) -> list[Document]:
    """Tabelas > limite de caracteres são divididas repetindo o cabeçalho em cada parte."""
    linhas = doc.page_content.split("\n")
    if len(doc.page_content) <= limite or len(linhas) < 4:
        return [doc]

    cabecalho = linhas[0] + "\n" + linhas[1]  # linha de colunas + linha separadora "---"
    corpo = linhas[2:]

    partes, bloco_atual = [], []
    tamanho_atual = len(cabecalho)

    for linha in corpo:
        if tamanho_atual + len(linha) > limite and bloco_atual:
            conteudo = cabecalho + "\n" + "\n".join(bloco_atual)
            partes.append(Document(page_content=conteudo, metadata=dict(doc.metadata)))
            bloco_atual, tamanho_atual = [], len(cabecalho)
        bloco_atual.append(linha)
        tamanho_atual += len(linha)

    if bloco_atual:
        conteudo = cabecalho + "\n" + "\n".join(bloco_atual)
        partes.append(Document(page_content=conteudo, metadata=dict(doc.metadata)))

    for i, parte in enumerate(partes):
        parte.metadata["tabela_parte"] = f"{i + 1}/{len(partes)}"

    return partes
print('#',time.strftime("%d/%m/%Y - %H:%M:%S"))



import sqlite3


# 1) A FUNÇÃO FICA LIVRE NO ESCOPO (Pode ser importada por qualquer outro script)
def consultar_colecoes_chroma(db_path0: str = '../data/chroma.sqlite3',verbose=True) -> list:
    """Consulta o banco SQLite interno do ChromaDB para listar os segmentos e UUIDs."""

    db_path=db_path0+'/chroma.sqlite3'
    if not os.path.exists(db_path):
        print(f"❌ Erro: Arquivo de banco de dados não encontrado em: '{db_path}'")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    resultados = []

    try:
        cursor.execute("SELECT id, scope, collection FROM segments")
        resultados = cursor.fetchall()
        if verbose:
            if not resultados:
                print(f"ℹ️ O banco '{db_path}' está acessível, mas nenhuma coleção foi encontrada.")
                return []

            print(f"\n📁 Pastas VÁLIDAS encontradas em '{db_path}':")
            print("-" * 60)
            for linha in resultados:
                print(f"🔹 TIPO           : {linha[1]}")
                print(f"   Pasta (UUID)   : {linha[0]}")
                print(f"   Nome Coleção   : {linha[2]}")
                print("-" * 60)

    except sqlite3.OperationalError as e:
        print(f"❌ Erro Operacional: Estrutura incompatível. Detalhes: {e}")
    finally:
        conn.close()

    return True
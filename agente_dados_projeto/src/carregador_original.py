#src/carregador_original.py
from pathlib import Path
import pandas as pd
from .xml_carregador import carregar_xmls


def ler_csv(caminho):
    configuracoes = [
        {"encoding": "utf-8", "sep": None},
        {"encoding": "utf-8-sig", "sep": None},
        {"encoding": "latin1", "sep": None},
    ]

    ultimo_erro = None

    for configuracao in configuracoes:
        try:
            tabela = pd.read_csv(
                caminho,
                engine="python",
                on_bad_lines="warn",
                **configuracao
            )

            tabela.columns = [
                str(coluna)
                .strip()
                .lower()
                .replace(" ", "_")
                for coluna in tabela.columns
            ]

            return tabela

        except Exception as erro:
            ultimo_erro = erro

    raise ValueError(
        f"Não foi possível ler o arquivo {caminho}: {ultimo_erro}"
    )


def carregar_tabelas(pasta):
    pasta = Path(pasta)
    tabelas = {}

    for caminho in pasta.rglob("*"):
        if not caminho.is_file():
            continue

        if caminho.suffix.lower() != ".csv":
            continue

        if caminho.name.lower() == "dicionario_dados.csv":
            continue

        tabela = ler_csv(caminho)

        if tabela.empty:
            raise ValueError(
                f"O arquivo {caminho.name} está vazio."
            )

        if len(tabela) > 1_000_000:
            raise ValueError(
                f"O arquivo {caminho.name} possui linhas demais."
            )

        nome_tabela = caminho.stem.lower()
        tabelas[nome_tabela] = tabela

    if not tabelas:
        raise ValueError(
            "Nenhum arquivo CSV foi encontrado no ZIP."
        )

    return tabelas


def carregar_dicionario(pasta, tabelas):
    """
    Tenta carregar o dicionário de dados.
    Se ele não existir, cria um automaticamente
    usando os nomes das colunas.
    """

    pasta = Path(pasta)
    caminho = pasta / "dicionario_dados.csv"

    if caminho.exists():
        dicionario = ler_csv(caminho)

        colunas_obrigatorias = {
            "arquivo",
            "coluna",
            "descricao",
            "tipo"
        }

        faltantes = colunas_obrigatorias - set(dicionario.columns)

        if faltantes:
            raise ValueError(
                f"O dicionário não possui estas colunas: {faltantes}"
            )

        return dicionario

    linhas = []

    for nome_tabela, tabela in tabelas.items():
        for coluna in tabela.columns:
            tipo_python = str(tabela[coluna].dtype)

            linhas.append({
                "arquivo": f"{nome_tabela}.csv",
                "coluna": coluna,
                "descricao": (
                    f"Coluna {coluna} da tabela {nome_tabela}"
                ),
                "tipo": tipo_python
            })

    if not linhas:
        raise ValueError(
            "Não foi possível criar o dicionário automaticamente."
        )

    return pd.DataFrame(linhas)

def dicionario_em_texto(dicionario):
    linhas = []

    for _, linha in dicionario.iterrows():
        linhas.append(
            f"- Arquivo: {linha['arquivo']}; "
            f"coluna: {linha['coluna']}; "
            f"descrição: {linha['descricao']}; "
            f"tipo: {linha['tipo']}"
        )

    return "\n".join(linhas)

def carregar_dados(pasta):
    """
    Carrega arquivos CSV e XML.
    """

    tabelas = {}
    erros_xml = []

    # Tenta carregar os arquivos CSV
    try:
        tabelas_csv = carregar_tabelas(pasta)
        tabelas.update(tabelas_csv)

    except ValueError as erro:
        mensagem = str(erro)

        if "Nenhum arquivo CSV" not in mensagem:
            raise

    # Procura arquivos XML
    pasta_path = Path(pasta)

    arquivos_xml = [
        caminho
        for caminho in pasta_path.rglob("*")
        if caminho.is_file()
        and caminho.suffix.lower() == ".xml"
    ]

    # Carrega os XMLs, se existirem
    if arquivos_xml:
        tabelas_xml, erros_xml = carregar_xmls(
            pasta
        )

        tabelas.update(tabelas_xml)

    if not tabelas:
        raise ValueError(
            "O ZIP não contém CSVs nem XMLs válidos."
        )

    return tabelas, erros_xml

def dicionario_em_texto(dicionario):
    linhas = []

    for _, linha in dicionario.iterrows():
        linhas.append(
            f"- Arquivo: {linha['arquivo']}; "
            f"coluna: {linha['coluna']}; "
            f"descrição: {linha['descricao']}; "
            f"tipo: {linha['tipo']}"
        )

    return "\n".join(linhas)


def carregar_dados(pasta):
    tabelas = {}
    erros_xml = []

    try:
        tabelas_csv = carregar_tabelas(pasta)
        tabelas.update(tabelas_csv)

    except ValueError as erro:
        if "Nenhum arquivo CSV" not in str(erro):
            raise

    pasta_path = Path(pasta)

    arquivos_xml = [
        caminho
        for caminho in pasta_path.rglob("*")
        if caminho.is_file()
        and caminho.suffix.lower() == ".xml"
    ]

    if arquivos_xml:
        tabelas_xml, erros_xml = carregar_xmls(pasta)
        tabelas.update(tabelas_xml)

    if not tabelas:
        raise ValueError(
            "O ZIP não contém CSVs nem XMLs válidos."
        )

    return tabelas, erros_xml
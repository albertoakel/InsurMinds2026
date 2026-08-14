#src/xml_carregador.py
from pathlib import Path
import xml.etree.ElementTree as ET

import pandas as pd


def encontrar_elemento(elemento, nome):
    """
    Procura uma tag ignorando o namespace do XML.
    """

    for filho in elemento.iter():
        nome_tag = filho.tag.split("}")[-1]

        if nome_tag == nome:
            return filho

    return None


def texto(elemento, nome, padrao=""):
    """
    Procura uma tag e devolve seu texto.
    """

    encontrado = encontrar_elemento(elemento, nome)

    if encontrado is None:
        return padrao

    if encontrado.text is None:
        return padrao

    return encontrado.text.strip()


def converter_numero(valor, padrao=0.0):
    """
    Converte texto para número.
    """

    if valor is None or valor == "":
        return padrao

    try:
        return float(str(valor).replace(",", "."))
    except ValueError:
        return padrao


def extrair_uma_nfe(caminho_xml):
    """
    Lê uma NF-e e retorna:
    - dados principais da nota;
    - dados dos produtos.
    """

    try:
        arvore = ET.parse(caminho_xml)
        raiz = arvore.getroot()

    except ET.ParseError as erro:
        raise ValueError(
            f"XML inválido: {caminho_xml.name}. Erro: {erro}"
        )

    inf_nfe = encontrar_elemento(raiz, "infNFe")

    if inf_nfe is None:
        raise ValueError(
            f"{caminho_xml.name} não possui a tag infNFe."
        )

    identificacao = encontrar_elemento(
        inf_nfe,
        "ide"
    )

    emitente = encontrar_elemento(
        inf_nfe,
        "emit"
    )

    destinatario = encontrar_elemento(
        inf_nfe,
        "dest"
    )

    totais = encontrar_elemento(
        inf_nfe,
        "ICMSTot"
    )

    if identificacao is None:
        identificacao = inf_nfe

    if emitente is None:
        emitente = inf_nfe

    if destinatario is None:
        destinatario = inf_nfe

    if totais is None:
        totais = inf_nfe

    identificador = inf_nfe.attrib.get(
        "Id",
        ""
    )

    chave_nfe = identificador.replace(
        "NFe",
        ""
    )

    dados_nota = {
        "arquivo_xml": caminho_xml.name,
        "chave_nfe": chave_nfe,
        "numero_nota": texto(identificacao, "nNF"),
        "serie": texto(identificacao, "serie"),
        "data_emissao": (
            texto(identificacao, "dhEmi")
            or texto(identificacao, "dEmi")
        ),
        "natureza_operacao": texto(
            identificacao,
            "natOp"
        ),
        "emitente_cnpj": texto(
            emitente,
            "CNPJ"
        ),
        "emitente_nome": texto(
            emitente,
            "xNome"
        ),
        "destinatario_cnpj": (
            texto(destinatario, "CNPJ")
            or texto(destinatario, "CPF")
        ),
        "destinatario_nome": texto(
            destinatario,
            "xNome"
        ),
        "valor_produtos": converter_numero(
            texto(totais, "vProd")
        ),
        "valor_nota": converter_numero(
            texto(totais, "vNF")
        )
    }

    itens = []

    for elemento in inf_nfe.iter():
        nome_tag = elemento.tag.split("}")[-1]

        if nome_tag != "det":
            continue

        produto = encontrar_elemento(
            elemento,
            "prod"
        )

        if produto is None:
            continue

        dados_item = {
            "arquivo_xml": caminho_xml.name,
            "chave_nfe": chave_nfe,
            "numero_nota": dados_nota[
                "numero_nota"
            ],
            "produto_codigo": texto(
                produto,
                "cProd"
            ),
            "produto_nome": texto(
                produto,
                "xProd"
            ),
            "ncm": texto(
                produto,
                "NCM"
            ),
            "cfop": texto(
                produto,
                "CFOP"
            ),
            "unidade": texto(
                produto,
                "uCom"
            ),
            "quantidade": converter_numero(
                texto(produto, "qCom")
            ),
            "valor_unitario": converter_numero(
                texto(produto, "vUnCom")
            ),
            "valor_produto": converter_numero(
                texto(produto, "vProd")
            )
        }

        itens.append(dados_item)

    return dados_nota, itens


def carregar_xmls(pasta):
    """
    Procura e carrega todos os XMLs da pasta.
    """

    pasta = Path(pasta)

    arquivos_xml = [
        caminho
        for caminho in pasta.rglob("*")
        if caminho.is_file()
        and caminho.suffix.lower() == ".xml"
    ]

    if not arquivos_xml:
        raise ValueError(
            "Nenhum arquivo XML foi encontrado."
        )

    notas = []
    itens = []
    erros = []

    for caminho_xml in arquivos_xml:
        try:
            dados_nota, dados_itens = extrair_uma_nfe(
                caminho_xml
            )

            notas.append(dados_nota)
            itens.extend(dados_itens)

        except Exception as erro:
            erros.append(str(erro))

    if not notas:
        raise ValueError(
            "Nenhuma NF-e pôde ser lida."
        )

    tabelas = {
        "notas_fiscais": pd.DataFrame(notas),
        "itens_nfe": pd.DataFrame(itens)
    }

    return tabelas, erros
#data_loader.py

import csv

ARQUIVO_CLIENTES = "clientes.csv"


def get_clientes():
    """Lê clientes em UTF-8 ou Latin-1."""
    clientes = []

    try:
        try:
            arquivo = open(ARQUIVO_CLIENTES, encoding="utf-8-sig")
            linhas = list(csv.DictReader(arquivo, delimiter=","))
            arquivo.close()

        except UnicodeDecodeError:
            arquivo = open(ARQUIVO_CLIENTES, encoding="latin-1")
            linhas = list(csv.DictReader(arquivo, delimiter=","))
            arquivo.close()

        for linha in linhas:
            clientes.append({
                "id": linha["id"],
                "nome": linha["nome"],
                "cidade": linha["cidade"],
                "seguro": linha["seguro"],
                "perfil": linha["perfil"],
            })

    except FileNotFoundError:
        print(f"❌ Arquivo '{ARQUIVO_CLIENTES}' não encontrado.")

    return clientes
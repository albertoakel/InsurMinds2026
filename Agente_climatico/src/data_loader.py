import csv
import io
from pathlib import Path


COLUNAS_OBRIGATORIAS = {
    "id",
    "nome",
    "cidade",
    "seguro",
    "perfil",
}


def get_clientes(fonte_csv):
    """Lê um CSV enviado pelo Streamlit ou informado por caminho."""

    if hasattr(fonte_csv, "getvalue"):
        conteudo = fonte_csv.getvalue()
    else:
        conteudo = Path(fonte_csv).read_bytes()

    try:
        texto = conteudo.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = conteudo.decode("latin-1")

    leitor_csv = csv.DictReader(
        io.StringIO(texto),
        delimiter=",",
    )

    colunas_encontradas = set(leitor_csv.fieldnames or [])
    colunas_faltantes = COLUNAS_OBRIGATORIAS - colunas_encontradas

    if colunas_faltantes:
        faltantes = ", ".join(sorted(colunas_faltantes))
        raise ValueError(
            f"O CSV não possui as colunas obrigatórias: {faltantes}."
        )

    clientes = []

    for linha in leitor_csv:
        idade_texto = (linha.get("idade") or "").strip()
        idade = None
        if idade_texto:
            try:
                idade = int(idade_texto)
            except ValueError:
                raise ValueError(
                    f"Idade inválida para o cliente "
                    f"{linha.get('nome', 'não identificado')}: {idade_texto}."
                )

            if not 0 <= idade <= 120:
                raise ValueError(
                    f"Idade fora do intervalo permitido para o cliente "
                    f"{linha.get('nome', 'não identificado')}: {idade}."
                )

        clientes.append({
            "id": linha["id"].strip(),
            "nome": linha["nome"].strip(),
            "idade": idade,
            "cidade": linha["cidade"].strip(),
            "seguro": linha["seguro"].strip(),
            "perfil": linha["perfil"].strip(),
            "telefone": linha.get("telefone", "").strip(),
        })

    return clientes
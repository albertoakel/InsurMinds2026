#src/validador.py
from pathlib import Path
import zipfile


def extrair_zip_seguro(arquivo_zip, pasta_destino, limite_total=500_000_000):
    """
    Extrai um ZIP impedindo que arquivos sejam gravados
    fora da pasta de destino.
    """

    pasta_destino = Path(pasta_destino).resolve()
    pasta_destino.mkdir(parents=True, exist_ok=True)

    total_descompactado = 0

    with zipfile.ZipFile(arquivo_zip, "r") as zip_ref:
        arquivos = zip_ref.infolist()

        if len(arquivos) > 100:
            raise ValueError("O ZIP possui arquivos demais.")

        for membro in arquivos:
            total_descompactado += membro.file_size

            if total_descompactado > limite_total:
                raise ValueError(
                    "O conteúdo descompactado ultrapassa o limite permitido."
                )

            caminho_final = (pasta_destino / membro.filename).resolve()

            if not str(caminho_final).startswith(str(pasta_destino)):
                raise ValueError(
                    f"Arquivo com caminho inválido: {membro.filename}"
                )

            if membro.is_dir():
                caminho_final.mkdir(parents=True, exist_ok=True)
            else:
                caminho_final.parent.mkdir(parents=True, exist_ok=True)

                with zip_ref.open(membro) as origem:
                    with open(caminho_final, "wb") as destino:
                        destino.write(origem.read())
#src/carregador.py
from pathlib import Path
import pandas as pd
from .xml_carregador import carregar_xmls


def ler_csv(caminho):
    """
    Lê um CSV tentando várias combinações de encoding, com
    detecção automática de separador (sep=None + engine='python').

    Já cobre os casos mais comuns no Brasil (';' e ',', UTF-8,
    UTF-8 com BOM e Latin-1), então não é necessário trocar por
    uma versão com tentativas fixas de separador.
    """
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


def remover_duplicados(df, nome_tabela="tabela", verbose=True):
    """
    Verifica e remove linhas 100% duplicadas de um DataFrame.

    Parâmetros:
    -----------
    df : pandas.DataFrame
    nome_tabela : str
        Usado apenas para identificar a tabela nos logs.
    verbose : bool
        Se True, imprime o relatório e remove as duplicatas.
        Se False, apenas calcula e retorna o df original (modo "dry run").

    Retorna:
    --------
    pandas.DataFrame : df sem duplicatas (ou o original, se verbose=False)
    """

    duplicatas_completas = df.duplicated(keep=False)
    total_duplicadas = duplicatas_completas.sum()
    linhas_unicas = (~duplicatas_completas).sum()

    if verbose:
        print(f"— {nome_tabela} —")
        print(f"Total de registros            : {df.shape[0]}")
        print(f"Total de registros duplicados  : {total_duplicadas}")
        print(f">> registros únicos            : {linhas_unicas}")
        print("-" * 42)

    if total_duplicadas == 0:
        return df

    df_out = df.drop_duplicates(keep="first").reset_index(drop=True)

    if verbose:
        print(f"✓ {nome_tabela}: {total_duplicadas} linha(s) duplicada(s) removida(s).")

    return df_out


def _converter_coluna_data(serie_original):
    """
    Converte uma coluna de datas que pode misturar formato ISO
    (ex.: "2024-01-05T10:00:00", vindo de NF-e/XML) e formato
    brasileiro (ex.: "05/01/2024", vindo de CSV).

    IMPORTANTE: usar dayfirst=True junto com format='mixed' faz o
    pandas (testado na 3.0.x) inverter mês/dia até em datas ISO
    não-ambíguas (ex.: "2024-01-05" virava 1º de maio em vez de
    5 de janeiro). Por isso as datas ISO são parseadas separadamente,
    sem dayfirst, e só o restante (formato BR, com "/") usa dayfirst=True.
    """

    serie_texto = serie_original.astype(str)
    resultado = pd.Series(pd.NaT, index=serie_original.index, dtype="datetime64[ns]")

    valida = serie_original.notna() & (serie_texto.str.lower() != "nan")

    # Datas em formato ISO (AAAA-MM-DD, com ou sem hora) — sem ambiguidade
    mascara_iso = valida & serie_texto.str.match(r"^\d{4}-\d{2}-\d{2}")
    if mascara_iso.any():
        resultado.loc[mascara_iso] = pd.to_datetime(
            serie_texto.loc[mascara_iso], format="ISO8601", errors="coerce"
        )

    # Demais formatos (ex.: DD/MM/AAAA, típico de planilhas brasileiras)
    mascara_resto = valida & ~mascara_iso
    if mascara_resto.any():
        resultado.loc[mascara_resto] = pd.to_datetime(
            serie_texto.loc[mascara_resto], dayfirst=True, errors="coerce"
        )

    return resultado


def transformar_dataframe(df, verbose=True):

    """
    Detecta e converte automaticamente colunas de um DataFrame para
    tipos apropriados (datas, valores monetários, quantidades e
    identificadores numéricos), com base no NOME da coluna.

    Funciona tanto com as tabelas vindas de CSV (colunas normalizadas
    para minúsculo/snake_case por `ler_csv`) quanto com as tabelas
    vindas de NF-e/XML (`notas_fiscais`, `itens_nfe`), pois a busca por
    palavras-chave é feita em minúsculo (case-insensitive).

    Todas as etapas são "best effort": se uma coluna esperada não
    existir na tabela, a etapa é simplesmente pulada (não gera erro).
    """

    df_t = df.copy()
    colunas_lower = {col: col.lower() for col in df_t.columns}

    if verbose:
        print("=" * 70)
        print("🔄 TRANSFORMANDO DATAFRAME")
        print("=" * 70)

    # 1. Colunas de data (qualquer coluna com "data" no nome)
    colunas_data = [c for c, low in colunas_lower.items() if "data" in low]

    for col in colunas_data:
        try:
            if df_t[col].notna().sum() == 0:
                if verbose:
                    print(f"⚠️ {col} - Coluna vazia, ignorando")
                continue

            df_t[col] = _converter_coluna_data(df_t[col])

            n_nulos = df_t[col].isna().sum()
            total = len(df_t)
            if verbose:
                print(f"✅ {col} → datetime ({total - n_nulos}/{total} linhas válidas)")

        except Exception as e:
            if verbose:
                print(f"⚠️ {col} - Não foi possível converter: {e}")

    # 2. Colunas de valores monetários (valor, total, unit[ário/ario])
    colunas_valor = [
        c for c, low in colunas_lower.items()
        if any(x in low for x in ["valor", "total", "unit"])
    ]

    for col in colunas_valor:
        try:
            if not pd.api.types.is_numeric_dtype(df_t[col]):
                serie = df_t[col].astype(str)
                serie = serie.str.replace("R$", "", regex=False)
                serie = serie.str.replace(" ", "", regex=False)
                serie = serie.str.replace(".", "", regex=False)   # milhar
                serie = serie.str.replace(",", ".", regex=False)  # decimal
                df_t[col] = pd.to_numeric(serie, errors="coerce")
                if verbose:
                    print(f"✅ {col} → float (monetário)")
            elif verbose:
                print(f"ℹ️ {col} - Já é numérico ({df_t[col].dtype})")
        except Exception as e:
            if verbose:
                print(f"⚠️ {col} - Não foi possível converter: {e}")

    # 3. Colunas de quantidade
    colunas_qtd = [
        c for c, low in colunas_lower.items()
        if any(x in low for x in ["quantidade", "qtd", "qtde"])
    ]

    for col in colunas_qtd:
        try:
            if not pd.api.types.is_numeric_dtype(df_t[col]):
                serie = df_t[col].astype(str).str.replace(",", ".", regex=False)
                df_t[col] = pd.to_numeric(serie, errors="coerce")
                if verbose:
                    print(f"✅ {col} → float")
            elif verbose:
                print(f"ℹ️ {col} - Já é numérico ({df_t[col].dtype})")
        except Exception as e:
            if verbose:
                print(f"⚠️ {col} - Não foi possível converter: {e}")

    # 4. Identificadores numéricos (série, número, cfop, ncm)
    colunas_int = [
        c for c, low in colunas_lower.items()
        if any(x in low for x in ["serie", "série", "numero", "número", "cfop", "ncm"])
    ]

    for col in colunas_int:
        try:
            if not pd.api.types.is_numeric_dtype(df_t[col]):
                serie = df_t[col].astype(str)
                serie = serie.str.replace(".", "", regex=False)
                serie = serie.str.replace(",", "", regex=False)
                df_t[col] = pd.to_numeric(serie, errors="coerce").astype("Int64")
                if verbose:
                    print(f"✅ {col} → int")
            elif verbose:
                print(f"ℹ️ {col} - Já é numérico ({df_t[col].dtype})")
        except Exception as e:
            if verbose:
                print(f"⚠️ {col} - Não foi possível converter: {e}")

    # 5. Colunas auxiliares derivadas da data de emissão (se existir)
    col_data_emissao = next(
        (c for c, low in colunas_lower.items() if "data" in low and "emis" in low),
        None
    )

    if col_data_emissao and pd.api.types.is_datetime64_any_dtype(df_t[col_data_emissao]):
        df_t["dia"] = df_t[col_data_emissao].dt.day
        df_t["hora"] = df_t[col_data_emissao].dt.hour
        df_t["dia_semana"] = df_t[col_data_emissao].dt.day_name()
        if verbose:
            print("✅ Colunas auxiliares criadas: dia, hora, dia_semana")

    # 6. Valor total do item (só se houver quantidade e valor unitário,
    #    e ainda não existir uma coluna de valor total pronta)
    col_qtd = next((c for c, low in colunas_lower.items() if low == "quantidade"), None)
    col_valor_unit = next((c for c, low in colunas_lower.items() if "unit" in low), None)
    col_valor_total = next((c for c, low in colunas_lower.items() if "total" in low), None)

    if col_qtd and col_valor_unit and not col_valor_total:
        df_t["valor_total_item"] = df_t[col_qtd] * df_t[col_valor_unit]
        if verbose:
            print("✅ Coluna auxiliar criada: valor_total_item")
    elif col_qtd and col_valor_total:
        df_t["valor_total_item"] = df_t[col_valor_total]
        if verbose:
            print("✅ Coluna auxiliar criada: valor_total_item (a partir de coluna de total existente)")

    if verbose:
        print("=" * 70)
        print("✅ TRANSFORMAÇÃO CONCLUÍDA!")
        print("=" * 70)

    return df_t


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


def carregar_dados(pasta, transformar=True, remover_duplicatas=True, verbose=True):
    """
    Carrega arquivos CSV e XML e, por padrão, aplica em seguida:
      1) transformar_dataframe  -> conversão de tipos (datas, valores, qtd, ids)
      2) remover_duplicados     -> remoção de linhas 100% duplicadas

    A transformação roda ANTES da remoção de duplicatas, pois duas linhas
    podem só parecer diferentes por causa de formatação de texto
    (ex.: "1.234,56" vs "1234,56") — depois de convertidas para número/data,
    elas podem se revelar duplicadas de fato.

    transformar / remover_duplicatas podem ser desativados (False) caso
    se queira apenas inspecionar os dados brutos.
    """

    tabelas = {}
    erros_xml = []

    # Tenta carregar os arquivos CSV
    try:
        tabelas_csv = carregar_tabelas(pasta)
        tabelas.update(tabelas_csv)

    except ValueError as erro:
        if "Nenhum arquivo CSV" not in str(erro):
            raise

    # Procura e carrega arquivos XML, se existirem
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

    # Etapa de processamento: transformação + remoção de duplicados
    for nome_tabela, tabela in tabelas.items():
        if transformar:
            tabela = transformar_dataframe(tabela, verbose=verbose)

        if remover_duplicatas:
            tabela = remover_duplicados(tabela, nome_tabela=nome_tabela, verbose=verbose)

        tabelas[nome_tabela] = tabela

    return tabelas, erros_xml
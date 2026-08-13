"""
Funções de apoio para o dashboard da Interface B.

Como as tabelas carregadas vêm de ZIPs enviados pelo usuário, não há
garantia absoluta do nome exato de cada coluna. Por isso, a localização
de colunas é feita por palavras-chave (case/acento-insensitive) em vez
de nomes fixos — se uma coluna não for encontrada, o KPI/gráfico
correspondente é simplesmente omitido, sem quebrar a página.
"""

import unicodedata

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# Paleta de cores do dashboard — tons frios/azuis, fugindo do padrão
# vermelho/laranja do Streamlit.
CORES = {
    "fundo": "#0B1F3A",
    "fundo_card": "#122A4A",
    "linha": "#1E3A5F",
    "texto": "#E8F1F8",
    "texto_suave": "#8FB4D9",
    "acento": "#2EC4B6",
    "acento_forte": "#4CC9F0",
}

# Escala contínua usada em todos os gráficos com gradiente
ESCALA_AZUL = ["#12314F", "#1B4B72", "#2472A4", "#2EC4B6", "#4CC9F0"]

# Sequência discreta (para gráficos com várias categorias/barras)
SEQUENCIA_AZUL = ["#2EC4B6", "#4CC9F0", "#3A86FF", "#1B4B72", "#8ECAE6", "#5390D9"]

LAYOUT_PADRAO = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=CORES["texto"], family="Inter, sans-serif"),
    title_font=dict(color=CORES["texto"], size=16),
    margin=dict(l=10, r=10, t=50, b=10),
    xaxis=dict(gridcolor=CORES["linha"], zerolinecolor=CORES["linha"]),
    yaxis=dict(gridcolor=CORES["linha"], zerolinecolor=CORES["linha"]),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)


def _normalizar(texto):
    texto = str(texto).lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return texto


def achar_coluna(df, *grupos_palavras):
    """
    Procura, em ordem de prioridade, a primeira coluna cujo nome
    (normalizado) contenha TODAS as palavras de algum dos grupos.

    Exemplo: achar_coluna(df, ["uf", "emit"], ["uf"]) primeiro tenta achar
    uma coluna com "uf" E "emit" no nome; se não achar nenhuma, tenta
    achar qualquer coluna que tenha só "uf".
    """
    colunas_norm = {coluna: _normalizar(coluna) for coluna in df.columns}

    for grupo in grupos_palavras:
        palavras_norm = [_normalizar(p) for p in grupo]
        for coluna, nome_norm in colunas_norm.items():
            if all(p in nome_norm for p in palavras_norm):
                return coluna

    return None


def identificar_tabelas(tabelas: dict):
    """
    Tenta identificar, entre as tabelas carregadas, qual é a tabela de
    "notas" (cabeçalho da NF-e, 1 linha por nota) e qual é a de "itens"
    (1 linha por produto/serviço da nota).

    Retorna (nome_notas, df_notas, nome_itens, df_itens); qualquer um
    dos dois pode vir como None se não for identificado.
    """
    candidata_notas = None
    candidata_itens = None

    for nome, df in tabelas.items():
        if df is None or df.empty:
            continue

        tem_valor_nota = achar_coluna(df, ["valor", "nota"]) is not None
        tem_uf = achar_coluna(df, ["uf"]) is not None
        tem_produto = achar_coluna(df, ["produto"]) is not None
        tem_ncm = achar_coluna(df, ["ncm"]) is not None
        tem_quantidade = achar_coluna(df, ["quantidade"]) is not None

        if candidata_notas is None and (tem_valor_nota or tem_uf):
            candidata_notas = nome

        if candidata_itens is None and (tem_produto or tem_ncm) and tem_quantidade:
            candidata_itens = nome

    # Se só existir uma tabela, ela serve para os dois papéis
    if candidata_notas is None and len(tabelas) >= 1:
        candidata_notas = next(iter(tabelas))
    if candidata_itens is None and len(tabelas) >= 1:
        candidata_itens = candidata_notas or next(iter(tabelas))

    df_notas = tabelas.get(candidata_notas) if candidata_notas else None
    df_itens = tabelas.get(candidata_itens) if candidata_itens else None

    return candidata_notas, df_notas, candidata_itens, df_itens


def formatar_moeda(valor):
    if valor is None or pd.isna(valor):
        return "—"
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "§").replace(".", ",").replace("§", ".")
    return f"R$ {texto}"


def formatar_numero(valor):
    if valor is None or pd.isna(valor):
        return "—"
    texto = f"{valor:,.0f}"
    return texto.replace(",", ".")


def calcular_kpis(tabelas: dict) -> dict:
    """
    Calcula os KPIs principais do painel a partir das tabelas
    carregadas. Cada chave retorna None quando o dado não pôde ser
    encontrado — quem renderiza decide como exibir isso.
    """
    nome_notas, df_notas, nome_itens, df_itens = identificar_tabelas(tabelas)

    total_notas = None
    valor_total = None
    total_itens = None
    ticket_medio = None

    if df_notas is not None:
        col_numero = achar_coluna(df_notas, ["numero", "nota"], ["numero"])
        total_notas = df_notas[col_numero].nunique() if col_numero else len(df_notas)

        col_valor_nota = achar_coluna(df_notas, ["valor", "nota"], ["valor", "total"])
        if col_valor_nota and pd.api.types.is_numeric_dtype(df_notas[col_valor_nota]):
            valor_total = df_notas[col_valor_nota].sum()

    if df_itens is not None:
        col_quantidade = achar_coluna(df_itens, ["quantidade"])
        if col_quantidade and pd.api.types.is_numeric_dtype(df_itens[col_quantidade]):
            total_itens = df_itens[col_quantidade].sum()
        else:
            total_itens = len(df_itens)

        if valor_total is None:
            col_valor_item = achar_coluna(df_itens, ["valor_total_item"], ["valor", "total"])
            if col_valor_item and pd.api.types.is_numeric_dtype(df_itens[col_valor_item]):
                valor_total = df_itens[col_valor_item].sum()

    if valor_total is not None and total_notas:
        ticket_medio = valor_total / total_notas

    return {
        "total_notas": total_notas,
        "valor_total": valor_total,
        "total_itens": total_itens,
        "ticket_medio": ticket_medio,
        "nome_notas": nome_notas,
        "nome_itens": nome_itens,
    }


def grafico_distribuicao_hora(df):
    col_hora = achar_coluna(df, ["hora"])
    if not col_hora or not pd.api.types.is_numeric_dtype(df[col_hora]):
        return None

    contagem = (
        df[col_hora]
        .dropna()
        .astype(int)
        .value_counts()
        .reindex(range(24), fill_value=0)
        .sort_index()
    )

    fig = px.bar(
        x=contagem.index,
        y=contagem.values,
        labels={"x": "Hora do dia", "y": "Qtd. de notas"},
        color=contagem.values,
        color_continuous_scale=ESCALA_AZUL,
    )
    fig.update_layout(**LAYOUT_PADRAO, title="Distribuição de Notas por Hora", coloraxis_showscale=False)
    return fig


def grafico_top_categorias(df, coluna, titulo, top_n=10):
    if not coluna:
        return None

    contagem = df[coluna].dropna().value_counts().head(top_n).sort_values(ascending=True)
    if contagem.empty:
        return None

    fig = px.bar(
        x=contagem.values,
        y=contagem.index.astype(str),
        orientation="h",
        labels={"x": "Quantidade de notas", "y": ""},
        color=contagem.values,
        color_continuous_scale=ESCALA_AZUL,
    )
    fig.update_layout(**LAYOUT_PADRAO, title=titulo, coloraxis_showscale=False)
    return fig


def grafico_valor_por_categoria(df, coluna_categoria, coluna_valor, titulo, top_n=10):
    if not coluna_categoria or not coluna_valor:
        return None
    if not pd.api.types.is_numeric_dtype(df[coluna_valor]):
        return None

    valores = (
        df.groupby(coluna_categoria)[coluna_valor]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .sort_values(ascending=True)
    )
    if valores.empty:
        return None

    fig = px.bar(
        x=valores.values,
        y=valores.index.astype(str),
        orientation="h",
        labels={"x": "Valor total (R$)", "y": ""},
        color=valores.values,
        color_continuous_scale=ESCALA_AZUL,
    )
    fig.update_layout(**LAYOUT_PADRAO, title=titulo, coloraxis_showscale=False)
    return fig


def grafico_top_produtos(df_itens, top_n=10, metrica="valor"):
    """
    metrica: "valor" (padrão) ou "quantidade" — define o critério de
    ranking dos produtos.
    """
    col_produto = achar_coluna(df_itens, ["descricao", "produto"], ["produto"])
    col_valor = achar_coluna(df_itens, ["valor_total_item"], ["valor", "total"])
    col_qtd = achar_coluna(df_itens, ["quantidade"])

    col_ranking = col_qtd if metrica == "quantidade" else col_valor
    if not col_produto or not col_ranking:
        return None
    if not pd.api.types.is_numeric_dtype(df_itens[col_ranking]):
        return None

    agregacoes = {col_ranking: "sum"}

    top = (
        df_itens.groupby(col_produto)
        .agg(agregacoes)
        .sort_values(col_ranking, ascending=False)
        .head(top_n)
        .sort_values(col_ranking, ascending=True)
    )
    if top.empty:
        return None

    rotulo_x = "Valor total (R$)" if metrica == "valor" else "Quantidade"
    titulo = f"Top {top_n} Produtos por {'Valor' if metrica == 'valor' else 'Quantidade'}"

    fig = px.bar(
        x=top[col_ranking],
        y=top.index.astype(str).str.slice(0, 40),
        orientation="h",
        labels={"x": rotulo_x, "y": ""},
        color=top[col_ranking],
        color_continuous_scale=ESCALA_AZUL,
    )
    fig.update_layout(**LAYOUT_PADRAO, title=titulo, coloraxis_showscale=False)
    return fig


def grafico_itens_por_dia(df_itens):
    col_data = achar_coluna(df_itens, ["data", "emissao"], ["data"])
    col_qtd = achar_coluna(df_itens, ["quantidade"])

    if not col_data or not pd.api.types.is_datetime64_any_dtype(df_itens[col_data]):
        return None

    serie = df_itens.copy()
    serie["_dia"] = serie[col_data].dt.date

    if col_qtd and pd.api.types.is_numeric_dtype(serie[col_qtd]):
        diario = serie.groupby("_dia")[col_qtd].sum()
        rotulo_y = "Quantidade de itens"
    else:
        diario = serie.groupby("_dia").size()
        rotulo_y = "Quantidade de linhas"

    if diario.empty:
        return None

    fig = px.bar(
        x=diario.index.astype(str),
        y=diario.values,
        labels={"x": "Dia", "y": rotulo_y},
        color=diario.values,
        color_continuous_scale=ESCALA_AZUL,
    )
    fig.update_layout(**LAYOUT_PADRAO, title="Quantidade de Itens por Dia", coloraxis_showscale=False)
    return fig

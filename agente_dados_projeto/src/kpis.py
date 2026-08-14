#src/kpis.py
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


def achar_coluna(df, *grupos_palavras, exata=False):
    """
    Procura colunas por nome normalizado. vs2

    exata=False:
        procura colunas que contenham todas as palavras do grupo.

    exata=True:
        procura correspondência exata com o nome normalizado.
    """

    colunas_norm = {
        coluna: _normalizar(coluna)
        for coluna in df.columns
    }

    for grupo in grupos_palavras:
        palavras_norm = [_normalizar(p) for p in grupo]

        for coluna, nome_norm in colunas_norm.items():

            if exata:
                if len(palavras_norm) == 1 and nome_norm == palavras_norm[0]:
                    return coluna

            else:
                if all(p in nome_norm for p in palavras_norm):
                    return coluna

    return None



def identificar_tabelas(tabelas: dict):
    """
    Identifica semanticamente as tabelas de notas fiscais e itens.

    A identificação é baseada na estrutura das colunas, e não no nome
    do arquivo.

    Tabela de notas:
        Uma linha representa uma NF.

    Tabela de itens:
        Uma linha representa um item/produto de uma NF.
    """

    candidata_notas = None
    candidata_itens = None

    melhor_score_notas = -1
    melhor_score_itens = -1

    for nome, df in tabelas.items():

        if df is None or df.empty:
            continue

        # ---------------------------------------------------------
        # Normalização dos nomes das colunas
        # ---------------------------------------------------------
        colunas = {
            _normalizar(str(c))
            for c in df.columns
        }

        # =========================================================
        # SCORE — TABELA DE NOTAS
        # =========================================================

        score_notas = 0

        # Identificador da NF
        if "chave_de_acesso" in colunas:
            score_notas += 15

        if "numero" in colunas:
            score_notas += 8

        if "serie" in colunas:
            score_notas += 5

        # Data/hora da NF
        if "data_emissao" in colunas:
            score_notas += 8

        # Valor total da NF
        if "valor_nota_fiscal" in colunas:
            score_notas += 15

        # Dados do emitente/destinatário
        if "cpf/cnpj_emitente" in colunas:
            score_notas += 3

        if "razao_social_emitente" in colunas:
            score_notas += 3

        if "uf_emitente" in colunas:
            score_notas += 3

        if "uf_destinatario" in colunas:
            score_notas += 3

        # =========================================================
        # SCORE — TABELA DE ITENS
        # =========================================================

        score_itens = 0

        # Identificação do produto
        if "numero_produto" in colunas:
            score_itens += 10

        if "descricao_do_produto/servico" in colunas:
            score_itens += 15

        # Quantidade e valores
        if "quantidade" in colunas:
            score_itens += 12

        if "unidade" in colunas:
            score_itens += 5

        if "valor_unitario" in colunas:
            score_itens += 8

        if "valor_total_item" in colunas:
            score_itens += 15

        # Informações fiscais do item
        if "codigo_ncm/sh" in colunas:
            score_itens += 5

        if "cfop" in colunas:
            score_itens += 5

        # =========================================================
        # Guarda a melhor tabela de NOTAS
        # =========================================================

        if score_notas > melhor_score_notas:
            melhor_score_notas = score_notas
            candidata_notas = nome

        # =========================================================
        # Guarda a melhor tabela de ITENS
        # =========================================================

        if score_itens > melhor_score_itens:
            melhor_score_itens = score_itens
            candidata_itens = nome

    # =============================================================
    # Evita que a mesma tabela seja escolhida para os dois papéis
    # =============================================================

    if candidata_notas == candidata_itens:

        # Procurar outra tabela para itens
        melhor_outro_score = -1
        melhor_outro_nome = None

        for nome, df in tabelas.items():

            if nome == candidata_notas:
                continue

            if df is None or df.empty:
                continue

            colunas = {
                _normalizar(str(c))
                for c in df.columns
            }

            score = 0

            if "numero_produto" in colunas:
                score += 10

            if "descricao_do_produto/servico" in colunas:
                score += 15

            if "quantidade" in colunas:
                score += 12

            if "valor_unitario" in colunas:
                score += 8

            if "valor_total_item" in colunas:
                score += 15

            if "codigo_ncm/sh" in colunas:
                score += 5

            if "cfop" in colunas:
                score += 5

            if score > melhor_outro_score:
                melhor_outro_score = score
                melhor_outro_nome = nome

        if melhor_outro_nome is not None:
            candidata_itens = melhor_outro_nome

    # =============================================================
    # Recupera os DataFrames
    # =============================================================

    df_notas = (
        tabelas.get(candidata_notas)
        if candidata_notas
        else None
    )

    df_itens = (
        tabelas.get(candidata_itens)
        if candidata_itens
        else None
    )

    return (
        candidata_notas,
        df_notas,
        candidata_itens,
        df_itens,
    )

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
    quantidade_comercializada = None
    ticket_medio = None

    if df_notas is not None:

        col_chave = achar_coluna(df_notas,["chave_de_acesso"],exata=True)
        col_numero = achar_coluna(df_notas,["numero"],exata=True)

        if col_chave:
            total_notas = df_notas[col_chave].nunique()

        elif col_numero:
            total_notas = df_notas[col_numero].nunique()

        else:
            total_notas = len(df_notas)

        # --------------------------------------------------------
        # Valor total das notas
        # --------------------------------------------------------

        col_valor_nota = achar_coluna(df_notas,["valor_nota_fiscal"],exata=True)

        # fallback para outros formatos de tabela
        if col_valor_nota is None:
            col_valor_nota = achar_coluna(
                df_notas,
                ["valor", "nota"])

        if (
            col_valor_nota
            and pd.api.types.is_numeric_dtype(
                df_notas[col_valor_nota]
            )
        ):
            valor_total = df_notas[col_valor_nota].sum()


    if df_itens is not None:

        #Quantidade de Registros de itens
        total_itens=len(df_itens)

        #soma da quantidade comercial declarada
        col_quantidade = achar_coluna(df_itens, ["quantidade"])

        if col_quantidade and pd.api.types.is_numeric_dtype(df_itens[col_quantidade]):

            quantidade_comercializada = df_itens[col_quantidade].sum()


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
        "quantidade_comercializada": quantidade_comercializada,
        "ticket_medio": ticket_medio,
        "nome_notas": nome_notas,
        "nome_itens": nome_itens,
    }


def grafico_distribuicao_hora(df):
    col_hora = achar_coluna(df, ["hora"])

    col_hora = next(
        (
            col for col in df.columns
            if _normalizar(col) == "hora"
        ),
        None
    )

    if col_hora is None:
        return None
    if not pd.api.types.is_numeric_dtype(df[col_hora]):
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

    col_produto = achar_coluna(df_itens, ["descricao", "produto"])
    col_valor = achar_coluna(df_itens, ["valor_total_item"],exata=True)
    col_qtd = achar_coluna(df_itens, ["quantidade"],exata=True)

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

    # Data de emissão da NF
    col_data = achar_coluna(df_itens, ["data", "emissao"])

    # Quantidade comercial do item
    col_qtd = achar_coluna(df_itens,["quantidade"],exata=True)

    if (
        not col_data
        or not pd.api.types.is_datetime64_any_dtype(
            df_itens[col_data]
        )
    ):
        return None


    serie = df_itens.copy()

    serie["_dia"] = serie[col_data].dt.date

    if (
        col_qtd
        and pd.api.types.is_numeric_dtype(
            serie[col_qtd]
        )
    ):
        diario = (
            serie
            .groupby("_dia")[col_qtd]
            .sum()
        )

        rotulo_y = "Quantidade comercializada"

    else:
        diario = (
            serie
            .groupby("_dia")
            .size()
        )

        rotulo_y = "Quantidade de registros de itens"

    if diario.empty:
        return None

    fig = px.bar(x=diario.index.astype(str),
                 y=diario.values,
                 labels={"x": "Data de emissão","y": rotulo_y},
                 color=diario.values,
                 color_continuous_scale=ESCALA_AZUL,)

    fig.update_layout(**LAYOUT_PADRAO,
                      title="Quantidade Comercializada por Dia",
                      coloraxis_showscale=False
    )



    return fig

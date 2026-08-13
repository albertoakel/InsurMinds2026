import os
import tempfile
import warnings
import zipfile

import streamlit as st
from dotenv import load_dotenv

from src.agente import criar_agente, executar_pergunta
from src.carregador import carregar_dados, carregar_dicionario, dicionario_em_texto
from src.validador import extrair_zip_seguro
from src.kpis import (
    achar_coluna,
    calcular_kpis,
    formatar_moeda,
    formatar_numero,
    grafico_distribuicao_hora,
    grafico_itens_por_dia,
    grafico_top_categorias,
    grafico_top_produtos,
    grafico_valor_por_categoria,
    identificar_tabelas,
)

load_dotenv()

st.set_page_config(
    page_title="Agente de Dados Fiscais",
    page_icon="📊",
    layout="wide"
)

# ----------------------------------------------------------------------
# Identidade visual — tons frios de azul/ciano. O tema base (cores de
# fundo, texto e cor primária) vem de .streamlit/config.toml; aqui só
# entram os ajustes finos que o config.toml não cobre (fontes, gradiente
# do título, cartões de KPI, destaque do chat).
# ----------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.app-header {
    padding: 1.4rem 1.8rem;
    border-radius: 14px;
    margin-bottom: 1.2rem;
    background: linear-gradient(135deg, #0B1F3A 0%, #12314F 55%, #0E4A5C 100%);
    border: 1px solid #1E3A5F;
}

.app-header h1 {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    margin: 0;
    background: linear-gradient(90deg, #E8F1F8 0%, #4CC9F0 60%, #2EC4B6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.app-header p {
    color: #8FB4D9;
    margin: 0.3rem 0 0 0;
    font-size: 0.95rem;
}

/* Cartões (containers com borda) usados nos KPIs e nos painéis */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: #1E3A5F !important;
    background-color: #0F2743;
    border-radius: 12px !important;
}

[data-testid="stMetricValue"] {
    color: #4CC9F0;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
}

[data-testid="stMetricLabel"] {
    color: #8FB4D9;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-size: 0.78rem;
}

/* Destaque do painel de chat */
.st-key-chat_container {
    border: 1px solid #2EC4B6 !important;
    box-shadow: 0 0 24px rgba(46, 196, 182, 0.15);
}

.secao-titulo {
    font-family: 'Space Grotesk', sans-serif;
    color: #E8F1F8;
    font-weight: 600;
    margin: 0.4rem 0 0.6rem 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="app-header">
    <h1> 📊 Agente Inteligente para Dados Fiscais</h1>
    <p>Envie notas fiscais (CSV ou XML), acompanhe os indicadores e converse com o assistente para explorar os dados.</p>
</div>
""", unsafe_allow_html=True)


if not os.getenv("GOOGLE_API_KEY"):
    st.warning(
        "A variável GOOGLE_API_KEY não foi encontrada "
        "no arquivo .env."
    )


if "tabelas" not in st.session_state:
    st.session_state.tabelas = None

if "dicionario" not in st.session_state:
    st.session_state.dicionario = None

if "agente" not in st.session_state:
    st.session_state.agente = None

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []


# ========================================================================
# Interface A — Carga dos dados (mantida como estava)
# ========================================================================
st.sidebar.header("Upload")

arquivo_zip = st.sidebar.file_uploader(
    "Envie um arquivo ZIP",
    type=["zip"]
)


if arquivo_zip is not None:
    try:
        with zipfile.ZipFile(arquivo_zip, "r") as zip_ref:
            st.sidebar.write("Arquivos encontrados no ZIP:")

            for nome in zip_ref.namelist():
                st.sidebar.write(nome)

    except zipfile.BadZipFile:
        st.sidebar.error(
            "O arquivo enviado não é um ZIP válido."
        )


if arquivo_zip is not None:
    tamanho_maximo = 100 * 1024 * 1024

    if arquivo_zip.size > tamanho_maximo:
        st.sidebar.error(
            "O arquivo é muito grande. O limite é de 100 MB."
        )

    elif st.sidebar.button("Processar dados"):
        try:
            arquivo_zip.seek(0)

            pasta_temporaria = tempfile.mkdtemp(
                prefix="dataset_"
            )

            extrair_zip_seguro(
                arquivo_zip,
                pasta_temporaria
            )

            tabelas, erros_xml = carregar_dados(
                pasta_temporaria
            )

            if erros_xml:
                st.sidebar.warning(
                    f"{len(erros_xml)} arquivo(s) XML "
                    "não puderam ser lidos."
                )

            caminho_dicionario = os.path.join(
                pasta_temporaria,
                "dicionario_dados.csv"
            )

            dicionario = carregar_dicionario(
                pasta_temporaria,
                tabelas
            )

            if os.path.exists(caminho_dicionario):
                st.sidebar.success(
                    "Dicionário de dados encontrado."
                )
            else:
                st.sidebar.warning(
                    "O ZIP não possui dicionário. "
                    "Um dicionário automático foi criado."
                )

            texto_dicionario = dicionario_em_texto(
                dicionario
            )

            agente = criar_agente(
                tabelas,
                texto_dicionario
            )

            st.session_state.tabelas = tabelas
            st.session_state.dicionario = dicionario
            st.session_state.agente = agente
            st.session_state.mensagens = []

            st.sidebar.success(
                "Dados carregados com sucesso!"
            )

        except Exception as erro:
            st.sidebar.error(
                f"Não foi possível processar o ZIP: {erro}"
            )


# ========================================================================
# Interface B — Painel + Chat
# ========================================================================
if st.session_state.tabelas is None:
    st.info(
        "Primeiro envie um ZIP e clique em "
        "'Processar dados' na barra lateral."
    )

else:
    tabelas = st.session_state.tabelas
    kpis_dados = calcular_kpis(tabelas)
    nome_notas, df_notas, nome_itens, df_itens = identificar_tabelas(tabelas)

    # ---------------------------- KPIs ---------------------------------
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        with st.container(border=True):
            st.metric("Notas Fiscais", formatar_numero(kpis_dados["total_notas"]))

    with col2:
        with st.container(border=True):
            st.metric("Valor Total", formatar_moeda(kpis_dados["valor_total"]))

    with col3:
        with st.container(border=True):
            st.metric("Itens Processados", formatar_numero(kpis_dados["total_itens"]))

    with col4:
        with st.container(border=True):
            st.metric("Ticket Médio", formatar_moeda(kpis_dados["ticket_medio"]))

    st.write("")

    # ------------------- Chat destacado + gráfico em foco ---------------
    col_chat, col_grafico = st.columns([3, 2])

    with col_chat:
        st.markdown('<p class="secao-titulo">🤖 Assistente de Notas Fiscais</p>', unsafe_allow_html=True)

        with st.container(height=520, border=True, key="chat_container"):
            for mensagem in st.session_state.mensagens:
                with st.chat_message(mensagem["role"]):
                    st.markdown(mensagem["content"])

            pergunta = st.chat_input(
                "Exemplo: Qual fornecedor recebeu o maior valor?"
            )

            if pergunta:
                st.session_state.mensagens.append({
                    "role": "user",
                    "content": pergunta
                })

                with st.chat_message("user"):
                    st.markdown(pergunta)

                with st.chat_message("assistant"):
                    with st.spinner("Analisando os dados..."):
                        try:
                            resposta = executar_pergunta(
                                st.session_state.agente,
                                pergunta,
                                historico_mensagens=st.session_state.mensagens[:-1]
                            )

                            st.markdown(resposta)

                            st.session_state.mensagens.append({
                                "role": "assistant",
                                "content": resposta
                            })

                        except Exception as erro:
                            st.error(
                                "Não consegui responder. "
                                "Verifique se a pergunta está relacionada "
                                "às colunas disponíveis."
                            )

                            st.caption(
                                f"Detalhe técnico: {erro}"
                            )

    with col_grafico:
        st.markdown('<p class="secao-titulo">🕒 Distribuição por Hora</p>', unsafe_allow_html=True)

        with st.container(height=520, border=True):
            fig_hora = grafico_distribuicao_hora(df_notas) if df_notas is not None else None

            if fig_hora is not None:
                st.plotly_chart(fig_hora, use_container_width=True)
            else:
                st.info("Coluna de hora não encontrada nos dados carregados.")

    st.write("")

    # --------------------------- Análises -------------------------------
    st.markdown('<p class="secao-titulo">🔎 Análises</p>', unsafe_allow_html=True)

    aba_geo, aba_produtos, aba_temporal = st.tabs(
        ["📍 Geográfico", "🏷️ Produtos", "📅 Temporal"]
    )

    with aba_geo:
        if df_notas is None:
            st.info("Nenhuma tabela com dados de UF foi identificada.")
        else:
            col_uf_emit = achar_coluna(df_notas, ["uf", "emit"], ["uf"])
            col_uf_dest = achar_coluna(df_notas, ["uf", "dest"])
            col_valor_nota = achar_coluna(df_notas, ["valor", "nota"], ["valor", "total"])

            col_a, col_b = st.columns(2)

            with col_a:
                fig = grafico_top_categorias(df_notas, col_uf_emit, "Top 10 UF — Emitente")
                if fig is not None:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Coluna de UF do emitente não encontrada.")

            with col_b:
                fig = grafico_top_categorias(df_notas, col_uf_dest, "Top 10 UF — Destinatário")
                if fig is not None:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Coluna de UF do destinatário não encontrada.")

            fig = grafico_valor_por_categoria(
                df_notas, col_uf_emit, col_valor_nota, "Valor Total por UF — Emitente"
            )
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Não foi possível calcular valor por UF com as colunas disponíveis.")

    with aba_produtos:
        if df_itens is None:
            st.info("Nenhuma tabela de itens/produtos foi identificada.")
        else:
            col_a, col_b = st.columns(2)

            with col_a:
                fig = grafico_top_produtos(df_itens, metrica="valor")
                if fig is not None:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Não foi possível montar o ranking de produtos por valor.")

            with col_b:
                fig = grafico_top_produtos(df_itens, metrica="quantidade")
                if fig is not None:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Não foi possível montar o ranking de produtos por quantidade.")

    with aba_temporal:
        if df_itens is None:
            st.info("Nenhuma tabela com datas foi identificada.")
        else:
            fig = grafico_itens_por_dia(df_itens)
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Coluna de data de emissão não encontrada ou não convertida para data.")

    # ------------------------ Detalhes técnicos --------------------------
    st.markdown("---")

    with st.expander("Clique para ver os Detalhes Técnicos do Código"):
        st.markdown("""
**Este aplicativo Streamlit foi desenvolvido para o processamento de notas
fiscais e consulta via chatbot em linguagem natural.**

- Os arquivos CSV/XML enviados no ZIP são lidos, convertidos para os
  tipos apropriados (datas, valores monetários, quantidades) e têm
  registros duplicados removidos automaticamente antes de qualquer análise.
- O assistente (aba de chat) usa um agente LangChain sobre os DataFrames
  carregados para responder perguntas em português, sempre restrito aos
  dados efetivamente presentes nas tabelas.
- Os KPIs e gráficos acima são recalculados a partir das mesmas tabelas
  usadas pelo chat — não há transformação adicional só para o painel.
""")

        st.markdown("**Variáveis dos dados carregados**")

        for nome, tabela in tabelas.items():
            st.caption(f"`{nome}` — {len(tabela)} linhas, {len(tabela.columns)} colunas")

        st.dataframe(
            st.session_state.dicionario.astype(str),
            hide_index=True
        )

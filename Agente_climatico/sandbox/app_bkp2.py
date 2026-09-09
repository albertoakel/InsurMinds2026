#app.py
import html
import streamlit as st

from ai_agent import gerar_mensagem_ia
from mock_db import get_clientes
from rules_engine import verificar_necessidade_alerta
from weather_service import obter_dados_climaticos


st.set_page_config(
    page_title="ProtegeSeguro AI",
    page_icon="🛡️",
    layout="wide",
)

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        :root {
            --page-bg: #d1d6e3;
            --surface: #f8fafc;
            --surface-soft: #eef1f6;
            --text: #172033;
            --text-soft: #475569;
            --border: #b8c0d0;
            --brand: #00a9e8;
            --button: #175cd3;
            --risk-bg: #fff2d8;
            --risk-border: #e6a700;
            --risk-text: #6b4300;
            --safe-bg: #e7f6ec;
            --safe-border: #31935a;
            --safe-text: #17623a;
            --error-bg: #fdecec;
            --error-border: #d14343;
            --error-text: #8a1c1c;
        }

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .stApp {
            background: var(--page-bg);
            color: var(--text);
        }

        .block-container {
            max-width: 1600px;
            padding-top: 4rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3, h4, h5, h6,
        .stMarkdown, .stCaption, [data-testid="stMetricLabel"],
        [data-testid="stMetricValue"], [data-testid="stMetricDelta"] {
            color: var(--text) !important;
        }

        .brand-wrap {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.2rem;
        }

        .brand-icon {
            color: var(--brand);
            font-size: 2rem;
            line-height: 1;
        }

        .brand-title {
            color: var(--text);
            font-size: 1.75rem;
            font-weight: 700;
            line-height: 1.2;
        }

        .brand-ai {
            color: var(--brand);
        }

        .subtitle {
            color: var(--text-soft);
            font-size: 0.95rem;
            margin: 0 0 1.25rem 2.75rem;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(23, 32, 51, 0.07);
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: #929db1;
            box-shadow: 0 4px 12px rgba(23, 32, 51, 0.10);
        }

        button[data-testid="baseButton-primary"] {
            background: var(--button);
            color: #ffffff !important;
            border: 0;
            border-radius: 7px;
            font-weight: 600;
            box-shadow: none;
        }

        button[data-testid="baseButton-primary"]:hover {
            background: #134ba7;
            color: #ffffff !important;
        }

        [data-testid="stSidebar"] {
            background: var(--surface) !important; /* Cor clara com contraste */
    border-right: 1px solid var(--border);
        }

        [data-testid="stSidebar"] * {
            color: var(--text);
        }

        .sidebar-title {
            color: var(--text);
            font-size: 1.05rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }

        .sidebar-count {
            color: var(--text-soft);
            font-size: 0.9rem;
            margin-bottom: 0.8rem;
        }

        .results-title {
            color: var(--text);
            font-size: 1.15rem;
            font-weight: 700;
            margin: 1.4rem 0 0.8rem;
        }

        .column-label {
            color: var(--text-soft);
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            padding: 0 0.35rem;
        }

        .client-name {
            color: var(--text);
            font-size: 1.05rem;
            font-weight: 700;
            margin-bottom: 0.3rem;
        }

        .client-meta {
            color: #334155;
            font-size: 0.84rem;
            font-weight: 600;
            margin-bottom: 0.7rem;
        }

        .body-text {
            color: var(--text-soft);
            font-size: 0.86rem;
            line-height: 1.45;
        }

        .section-title {
            color: #334155;
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            margin-bottom: 0.35rem;
            text-transform: uppercase;
        }

        .temperature {
            color: var(--text);
            font-size: 1.55rem;
            font-weight: 700;
            line-height: 1.2;
            margin-bottom: 0.25rem;
        }

        .weather-description {
            color: var(--text-soft);
            font-size: 0.9rem;
        }
        .weather-details {
            color: var(--text-soft);
            font-size: 0.82rem;
            line-height: 1.55;
            margin-top: 0.45rem;
        }
        .weather-details strong {
            color: #334155;
            font-weight: 600;}

        .risk-box, .safe-box, .error-box, .sms-box, .empty-message {
            border-radius: 8px;
            font-size: 0.86rem;
            line-height: 1.45;
            padding: 0.85rem;
            min-height: 96px;
        }

        .risk-box {
            background: var(--risk-bg);
            border-left: 4px solid var(--risk-border);
            color: var(--risk-text);
        }

        .risk-icon {
            display: block;
            font-size: 1.25rem;
            margin-bottom: 0.3rem;
        }

        .safe-box {
            background: var(--safe-bg);
            border-left: 4px solid var(--safe-border);
            color: var(--safe-text);
        }

        .error-box {
            background: var(--error-bg);
            border-left: 4px solid var(--error-border);
            color: var(--error-text);
        }

        .sms-box {
            background: var(--surface-soft);
            border: 1px solid #cbd2df;
            color: var(--text);
            white-space: normal;
        }

        .empty-message {
            background: var(--surface-soft);
            border: 1px solid #d4dae4;
            color: #64748b;
        }

        div[data-testid="stMetric"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.75rem 1rem;
        }

        div[data-testid="stProgress"] > div > div > div > div {
            background-color: var(--button);
        }

        #MainMenu {visibility: hidden;}
        #header {visibility: hidden;}
        #footer {visibility: hidden;}
        
    
        /* Garante que o header use a cor de fundo padrão do app */
        header[data-testid="stHeader"] {
            background-color: transparent !important;
        }

        /* Oculta os botões nativos (Deploy, menu de 3 pontos e rodapé) */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        [data-testid="stHeaderActionElements"] {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=600, show_spinner=False)
def buscar_clima(cidade):
    """Evita repetir consultas para a mesma cidade durante dez minutos."""
    return obter_dados_climaticos(cidade)


def texto_seguro(valor):
    """Escapa conteúdo externo antes de inseri-lo no HTML da interface."""
    return html.escape(str(valor or ""))


def formatar_mensagem(mensagem):
    """Remove aspas externas e preserva as quebras de linha da mensagem."""
    texto = str(mensagem or "").strip()
    if len(texto) >= 2 and texto[0] == texto[-1] and texto[0] in {'"', "'"}:
        texto = texto[1:-1].strip()
    return texto_seguro(texto).replace("\n", "<br>")


st.markdown(
    """
    <div class="brand-wrap">
        <div class="brand-icon">⚡</div>
        <div class="brand-title">ProtegeSeguro <span class="brand-ai">AI</span></div>
    </div>
    <p class="subtitle">Monitoramento climático e prevenção de sinistros</p>
    """,
    unsafe_allow_html=True,
)


clientes = get_clientes()

with st.sidebar:
    st.markdown(
        '<div class="sidebar-title">💼 Carteira de clientes</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="sidebar-count">{len(clientes)} segurados ativos</div>',
        unsafe_allow_html=True,
    )

    colunas_sidebar = ["nome", "cidade", "seguro"]
    st.dataframe(
        [{coluna: cliente.get(coluna, "") for coluna in colunas_sidebar} for cliente in clientes],
        hide_index=True,
        width='stretch',
        height=520,
    )
    st.caption("Fonte: clientes.csv")


if st.button("▶ Executar varredura", type="primary"):
    resultados = []
    total_clientes = len(clientes)
    status = st.empty()
    progresso = st.progress(0)

    for indice, cliente in enumerate(clientes, start=1):
        status.markdown(
            f"Analisando **{texto_seguro(cliente['nome'])}** "
            f"— {indice} de {total_clientes}"
        )

        resultado = {
            "cliente": cliente,
            "clima": None,
            "enviar_alerta": False,
            "motivo": "",
            "mensagem": "",
            "erro": "",
        }

        try:
            clima = buscar_clima(cliente["cidade"])
            resultado["clima"] = clima

            if not clima:
                resultado["erro"] = "Não foi possível obter os dados climáticos."
            else:
                enviar_alerta, motivo = verificar_necessidade_alerta(cliente, clima)
                resultado["enviar_alerta"] = enviar_alerta
                resultado["motivo"] = motivo

                if enviar_alerta:
                    try:
                        resultado["mensagem"] = gerar_mensagem_ia(
                            cliente,
                            clima,
                            motivo,
                        )
                    except Exception:
                        resultado["erro"] = (
                            "O risco foi identificado, mas não foi possível gerar o SMS."
                        )
        except Exception:
            resultado["erro"] = "Falha ao processar este segurado."

        resultados.append(resultado)
        progresso.progress(indice / total_clientes)

    st.session_state["resultados_varredura"] = resultados
    status.empty()
    progresso.empty()


resultados = st.session_state.get("resultados_varredura", [])

if resultados:
    total_alertas = sum(item["enviar_alerta"] for item in resultados)
    total_falhas = sum(bool(item["erro"]) for item in resultados)
    total_seguros = sum(
        not item["enviar_alerta"] and not item["erro"]
        for item in resultados
    )

    metrica_1, metrica_2, metrica_3, metrica_4 = st.columns(4)
    metrica_1.metric("Segurados analisados", len(resultados))
    metrica_2.metric("Alertas", total_alertas)
    metrica_3.metric("Sem risco", total_seguros)
    metrica_4.metric("Falhas", total_falhas)

    st.markdown(
        '<div class="results-title">Resultado da varredura</div>',
        unsafe_allow_html=True,
    )

    cab_1, cab_2, cab_3, cab_4 = st.columns([1.25, 1.0, 1.55, 2.2], gap="medium")
    cab_1.markdown('<div class="column-label">Segurado</div>', unsafe_allow_html=True)
    cab_2.markdown('<div class="column-label">Clima local</div>', unsafe_allow_html=True)
    cab_3.markdown('<div class="column-label">Avaliação de risco</div>', unsafe_allow_html=True)
    cab_4.markdown('<div class="column-label">Mensagem</div>', unsafe_allow_html=True)

    for item in resultados:
        cliente = item["cliente"]
        clima = item["clima"]

        with st.container(border=True):
            coluna_1, coluna_2, coluna_3, coluna_4 = st.columns(
                [1.25, 1.0, 1.55, 2.2],
                gap="medium",
            )

            with coluna_1:
                st.markdown(
                    f"""
                    <div class="client-name">{texto_seguro(cliente['nome'])}</div>
                    <div class="client-meta">
                        📍 {texto_seguro(cliente['cidade'])} | {texto_seguro(cliente['seguro'])}
                    </div>
                    <div class="body-text">{texto_seguro(cliente['perfil'])}</div>
                    """,
                    unsafe_allow_html=True,
                )

            with coluna_2:
                if clima:
                    temperatura = float(clima["temperatura"])
                    sensacao_termica = float(clima["sensacao_termica"])

                    st.markdown(
                        f"""
                        <div class="section-title">Clima local</div>
                        <div class="temperature">{temperatura:.1f} °C</div>
                        <div class="Sensação">{sensacao_termica:.1f} °C</div>
                        <div class="weather-description">
                            {texto_seguro(clima['descricao']).capitalize()}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<div class="weather-description">Dados indisponíveis</div>',
                        unsafe_allow_html=True,
                    )

            with coluna_3:
                if item["enviar_alerta"]:
                    st.markdown(
                        f"""
                        <div class="risk-box">
                            <span class="risk-icon">⚠️</span>
                            <strong>Risco:</strong> {texto_seguro(item['motivo'])}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                elif item["erro"]:
                    st.markdown(
                        f'<div class="error-box">{texto_seguro(item["erro"])}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<div class="safe-box">✅ Sem riscos detectados.</div>',
                        unsafe_allow_html=True,
                    )

            with coluna_4:
                if item["mensagem"]:
                    st.markdown(
                        f"""
                        <div class="sms-box">
                            <div class="section-title">📱 SMS</div>
                            {formatar_mensagem(item['mensagem'])}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                elif item["enviar_alerta"] and item["erro"]:
                    st.markdown(
                        f'<div class="error-box">{texto_seguro(item["erro"])}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<div class="empty-message">Nenhuma mensagem necessária.</div>',
                        unsafe_allow_html=True,
                    )

    st.markdown(
        '<p class="body-text" style="text-align:center; margin-top:1rem;">'
        'Varredura concluída.</p>',
        unsafe_allow_html=True,
    )

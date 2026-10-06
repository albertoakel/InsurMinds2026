import streamlit as st
from pathlib import Path
from datetime import datetime

from src.pipeline_multiagent import (
    receber,
    extrair,
    salvar,
    listar_apolices,
    verificar_arquivo_existente,
    comparar,
    buscar_apolice,
    BANCO_PADRAO,
)


st.set_page_config(
    page_title="D&O Comparator",
    layout="wide",
)

st.title("🛡️ Plataforma de Análise D&O")
st.markdown("Extraia e compare apólices de seguro D&O automaticamente.")


# -------------------------------------------------------------------
# Funções auxiliares da interface
# -------------------------------------------------------------------

def formatar_data(data: str) -> str:
    """Converte a data ISO do banco para uma apresentação mais amigável."""
    try:
        dt = datetime.fromisoformat(data)
        return dt.strftime("%d/%m/%Y às %H:%M")
    except (ValueError, TypeError):
        return data


def exibir_resultado(apolice, mensagem="Apólice analisada e salva com sucesso!"):
    """Exibe o resultado resumido da análise."""

    st.success(mensagem)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📋 Dados da Apólice")

        st.write(
            f"**Seguradora:** "
            f"{apolice.seguradora or 'Não identificada'}"
        )

        st.write(
            f"**Tipo de documento:** "
            f"{apolice.tipo_documento or 'Não identificado'}"
        )

        st.write(
            f"**Processo SUSEP:** "
            f"{apolice.processo_susep or 'Não identificado'}"
        )

        st.write(
            f"**Base de reclamações:** "
            f"{apolice.base_reclamacoes or 'Não identificada'}"
        )

        st.markdown("### Coberturas")

        st.write(
            f"**Cobertura A:** "
            f"{apolice.cobertura_a or 'Não identificada'}"
        )

        st.write(
            f"**Cobertura B:** "
            f"{apolice.cobertura_b or 'Não identificada'}"
        )

        st.write(
            f"**Cobertura C:** "
            f"{apolice.cobertura_c or 'Não identificada'}"
        )

        st.markdown("### Condições principais")

        st.write(
            f"**LMI:** "
            f"{apolice.lmi_texto or 'Não identificado'}"
        )

        st.write(
            f"**Limite agregado:** "
            f"{apolice.limite_agregado_texto or 'Não identificado'}"
        )

        st.write(
            f"**POS / Franquia:** "
            f"{apolice.pos_franquia or 'Não identificada'}"
        )

        st.write(
            f"**Retroatividade:** "
            f"{apolice.retroatividade or 'Não identificada'}"
        )

        st.write(
            f"**Territorialidade:** "
            f"{apolice.territorialidade or 'Não identificada'}"
        )

    with col2:
        st.subheader("Validação")

        st.metric(
            "Confiabilidade",
            apolice.confiabilidade.upper(),
        )

        if apolice.alertas:
            st.warning("Alertas:")

            for alerta in apolice.alertas:
                st.write(f"• {alerta}")


def processar_documento(arquivo, banco):
    """Executa o processamento completo e retorna a apólice extraída."""

    st.subheader("🤖 Processamento Multiagente")

    status_agentes = {
        "Agente 1 - Triagem": st.empty(),
        "Agente 2 - Extração Estrutural": st.empty(),
        "Agente 3 - Análise de Cláusulas": st.empty(),
    }

    def atualizar_agente(nome_agente, estado):
        if nome_agente not in status_agentes:
            return

        if estado == "processando":
            status_agentes[nome_agente].info(
                f"🔄 {nome_agente}: processando..."
            )

        elif estado == "concluído":
            status_agentes[nome_agente].success(
                f"✅ {nome_agente}: concluído"
            )

    caminho = Path(arquivo.name)
    caminho.write_bytes(arquivo.getvalue())

    with st.spinner("Preparando documento..."):
        dados, mime = receber(caminho)

    apolice = extrair(
        caminho,
        dados,
        mime,
        callback=atualizar_agente,
    )

    salvar(apolice, banco)

    return apolice


# -------------------------------------------------------------------
# Estado da aplicação
# -------------------------------------------------------------------

if "arquivo_pendente" not in st.session_state:
    st.session_state.arquivo_pendente = None


# -------------------------------------------------------------------
# Sidebar
# -------------------------------------------------------------------

menu = st.sidebar.selectbox(
    "Escolha uma opção",
    [
        "Upload e Análise",
        "Apólices Salvas",
        "Comparar Apólices",
    ],
)


# -------------------------------------------------------------------
# A - Upload e Análise
# -------------------------------------------------------------------

if menu == "Upload e Análise":

    st.header("Nova Apólice")

    arquivo = st.file_uploader(
        "Faça upload do PDF ou imagem",
        type=["pdf", "png", "jpg", "jpeg"],
    )

    if arquivo is not None:

        banco = Path(BANCO_PADRAO)

        # Se o usuário trocar o arquivo, cancela qualquer confirmação
        # pendente relacionada ao arquivo anterior.
        if (
            st.session_state.arquivo_pendente is not None
            and st.session_state.arquivo_pendente != arquivo.name
        ):
            st.session_state.arquivo_pendente = None

        # ---------------------------------------------------------------
        # Estado normal: documento ainda não foi enviado para análise.
        # ---------------------------------------------------------------
        if st.session_state.arquivo_pendente != arquivo.name:

            if st.button("Analisar Documento"):

                registros_existentes = verificar_arquivo_existente(
                    banco,
                    arquivo.name,
                )

                if registros_existentes:
                    # Guarda a confirmação pendente e faz um rerun.
                    st.session_state.arquivo_pendente = arquivo.name
                    st.rerun()

                # Documento novo: processa normalmente.
                apolice = processar_documento(arquivo, banco)

                exibir_resultado(apolice)

        # ---------------------------------------------------------------
        # Estado de confirmação: documento já foi processado.
        # ---------------------------------------------------------------
        else:

            registros_existentes = verificar_arquivo_existente(
                banco,
                arquivo.name,
            )

            if registros_existentes:

                ultimo = registros_existentes[0]

                (
                    id_anterior,
                    seguradora_anterior,
                    tipo_anterior,
                    data_anterior,
                ) = ultimo

                st.warning(
                    "⚠️ **Este documento já foi processado.**"
                )

                st.write(
                    f"**Arquivo:** {arquivo.name}"
                )

                st.write(
                    f"**Seguradora:** "
                    f"{seguradora_anterior or 'Não identificada'}"
                )

                st.write(
                    f"**Último processamento:** "
                    f"{formatar_data(data_anterior)}"
                )

                st.markdown(
                    "### O que você deseja fazer?"
                )

                col_cancelar, col_processar, _ = st.columns(
                    [1, 2, 5]
                )

                with col_cancelar:
                    cancelar = st.button(
                        "Cancelar",
                        key="cancelar_reprocessamento",
                    )

                with col_processar:
                    processar_novamente = st.button(
                        "🔄 Processar novamente",
                        key="processar_novamente",
                    )

                if cancelar:
                    st.session_state.arquivo_pendente = None
                    st.rerun()

                if processar_novamente:

                    apolice = processar_documento(
                        arquivo,
                        banco,
                    )

                    st.session_state.arquivo_pendente = None

                    exibir_resultado(
                        apolice,
                        "Nova análise concluída e salva com sucesso!",
                    )

            else:
                # O registro deixou de existir entre os dois estados.
                st.session_state.arquivo_pendente = None
                st.rerun()


# -------------------------------------------------------------------
# B - Apólices Salvas
# -------------------------------------------------------------------

elif menu == "Apólices Salvas":

    st.header("Base de Dados")

    registros = listar_apolices(
        Path(BANCO_PADRAO)
    )

    for reg in registros:

        (
            id_,
            nome,
            seg,
            tipo,
            confiabilidade,
            lmi,
            data,
        ) = reg

        with st.expander(
            f"📄 {seg or 'Seguradora não identificada'} — "
            f"{formatar_data(data)}"
        ):

            st.write(
                f"**Documento:** {nome}"
            )

            st.write(
                f"**Tipo:** {tipo}"
            )

            st.write(
                f"**Confiabilidade:** {confiabilidade}"
            )

            st.write(
                f"**LMI:** {lmi}"
            )

            st.write(
                f"**Processado em:** "
                f"{formatar_data(data)}"
            )


# -------------------------------------------------------------------
# C - Comparar Apólices
# -------------------------------------------------------------------

elif menu == "Comparar Apólices":

    st.header("Comparação")

    st.write(
        "Escolha duas apólices salvas para comparar."
    )

    registros = listar_apolices(
        Path(BANCO_PADRAO)
    )

    ids = [r[0] for r in registros]

    if len(ids) >= 2:
        col_a, col_b = st.columns(2)

        opcoes = {}

        for reg in registros:
            (
                id_,
                nome,
                seg,
                tipo,
                confiabilidade,
                lmi,
                data,
            ) = reg

            identificacao = (
                f"{seg or 'Seguradora não identificada'} "
                f"— {formatar_data(data)}"
            )

            opcoes[identificacao] = id_

        with col_a:
            escolha_a = st.selectbox(
                "📄 Apólice A",
                list(opcoes.keys()),
                key="a",
            )

        with col_b:
            escolha_b = st.selectbox(
                "📄 Apólice B",
                list(opcoes.keys()),
                key="b",
                index=1 if len(opcoes) > 1 else 0,
            )

        id_a = opcoes[escolha_a]
        id_b = opcoes[escolha_b]

        if st.button("Comparar"):

            a = buscar_apolice(
                Path(BANCO_PADRAO),
                id_a,
            )

            b = buscar_apolice(
                Path(BANCO_PADRAO),
                id_b,
            )

            resultados = comparar(a, b)

            st.subheader("📊 Comparação das apólices")

            # Separa exclusões das demais informações
            comparacao_principal = [
                linha for linha in resultados
                if linha["campo"] != "Exclusões exclusivas"
            ]

            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("### 📄 Apólice A")
                st.write(f"**Seguradora:** {a.seguradora}")
                st.write(f"**Documento:** {a.arquivo}")
                st.write(f"**Tipo:** {a.tipo_documento}")

            with col_b:
                st.markdown("### 📄 Apólice B")
                st.write(f"**Seguradora:** {b.seguradora}")
                st.write(f"**Documento:** {b.arquivo}")
                st.write(f"**Tipo:** {b.tipo_documento}")

            st.divider()

            # Tabela principal
            linhas_tabela = []

            for linha in comparacao_principal:

                if "ausente" in linha["diferenca"].lower():
                    resultado = "⚪ Não informado"

                elif "iguais" in linha["diferenca"].lower():
                    resultado = "🔵 Igual"

                elif linha["sinal"] == "verde":
                    resultado = "🟢 Maior — Apólice A"

                elif linha["sinal"] == "vermelho":
                    resultado = "🔴 Maior — Apólice B"

                else:
                    resultado = "🟡 Diferente — requer análise"

                valor_a = linha["a"]
                valor_b = linha["b"]

                if valor_a is None:
                    valor_a = "Não identificado"
                elif isinstance(valor_a, (int, float)) and linha["campo"] in [
                    "LMI",
                    "Limite agregado",
                ]:
                    valor_a = (
                        f"R$ {valor_a:,.2f}"
                        .replace(",", "X")
                        .replace(".", ",")
                        .replace("X", ".")
                    )

                if valor_b is None:
                    valor_b = "Não identificado"
                elif isinstance(valor_b, (int, float)) and linha["campo"] in [
                    "LMI",
                    "Limite agregado",
                ]:
                    valor_b = (
                        f"R$ {valor_b:,.2f}"
                        .replace(",", "X")
                        .replace(".", ",")
                        .replace("X", ".")
                    )

                # IMPORTANTE: este append fica dentro do for
                linhas_tabela.append(
                    {
                        "Campo": linha["campo"],
                        "Apólice A": valor_a,
                        "Apólice B": valor_b,
                        "Resultado": resultado,
                    }
                )

            st.table(linhas_tabela)



            # Exclusões
            exclusoes = next(
                (
                    linha
                    for linha in resultados
                    if linha["campo"] == "Exclusões exclusivas"
                ),
                None,
            )

            if exclusoes:
                st.subheader("🚫 Exclusões de cobertura")

                col_a, col_b = st.columns(2)

                with col_a:
                    st.markdown("**Exclusões identificadas somente na Apólice A**")

                    if exclusoes["a"]:
                        for item in exclusoes["a"]:
                            st.write(f"• {item}")
                    else:
                        st.write("Nenhuma")

                with col_b:
                    st.markdown("**Exclusões identificadas somente na Apólice B**")
                    if exclusoes["b"]:
                        for item in exclusoes["b"]:
                            st.write(f"• {item}")
                    else:
                        st.write("Nenhuma")


    else:
        st.info(
            "Você precisa salvar pelo menos 2 apólices primeiro."
        )

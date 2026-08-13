import streamlit as st
import requests

# 1. Configuração da página
st.set_page_config(page_title="Segurança Pública | Chat", page_icon="🛡️", layout="centered")
st.title("🛡️ Segurança Publica - RAG Chatbot")
st.caption("Respostas baseadas exclusivamente no relatório de segurança pública vetorizado.")

# URL da API (FastAPI) que já está rodando
API_URL = "http://127.0.0.1:9010/perguntar"

# 2. Inicializa a "memória visual" do Streamlit
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. Exibe as mensagens antigas na tela
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 4. Caixa de texto para o usuário digitar
if prompt := st.chat_input("Pergunte algo sobre o relatório de segurança pública"):

    # Exibe imediatamente a pergunta do usuário na tela
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepara o histórico para enviar para a API
    historico_para_api = st.session_state.messages.copy()

    # Salva a nova pergunta no estado do Streamlit
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Monta o pacote de dados exigido pelo FastAPI
    payload = {
        "pergunta": prompt,
        "historico": historico_para_api
    }

    # 5. Chama a API e exibe a resposta
    with st.chat_message("assistant"):
        with st.spinner("Consultando o relatório..."):
            try:
                response = requests.post(API_URL, json=payload)

                if response.status_code == 200:
                    resposta_assistente = response.json().get("resposta", "Sem resposta da API.")
                    st.markdown(resposta_assistente)

                    st.session_state.messages.append({"role": "assistant", "content": resposta_assistente})
                else:
                    st.error(f"Erro na API: Código {response.status_code}")

            except requests.exceptions.ConnectionError:
                st.error("Falha na conexão! O servidor do FastAPI (uvicorn) está rodando na porta 9010?")

# streamlit run app/app.py --server.port 9011



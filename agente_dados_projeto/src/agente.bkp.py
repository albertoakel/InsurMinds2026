src/agente.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents import create_pandas_dataframe_agent


def criar_agente(tabelas, dicionario_texto):
    # Obs: Se um modelo der erro de quota/disponibilidade,
    # você pode alternar o índice do LLM_MODELS.
    LLM_MODELS = [
        'gemini-2.0-flash',
        'gemini-2.5-flash-lite',
        'gemini-3.1-flash-lite'
    ]

    modelo = ChatGoogleGenerativeAI(
        model=LLM_MODELS[2],
        temperature=0
    )

    # CORREÇÃO AQUI: Garante que o parâmetro seja uma lista de DataFrames
    if isinstance(tabelas, dict):
        lista_dataframes = list(tabelas.values())
    else:
        lista_dataframes = tabelas

    instrucoes = f"""
Você é um analista de dados especialista em Notas Fiscais.

Regras obrigatórias:
1. Responda sempre em português.
2. Use somente os dados presentes nos DataFrames fornecidos.
3. Nunca invente valores ou informações.
4. Não altere os DataFrames originais (se necessário, faça cópias).
5. Para cálculos temporários, certifique-se de converter colunas de texto para numérico (ex: trocando vírgula por ponto).
6. Se não conseguir responder com base nos dados, explique o motivo.
7. Seja direto e exiba valores monetários formatados em Reais (R$ X.XXX,XX).
8. A SUA RESPOSTA FINAL DEVE SER APENAS O TEXTO DE RESPOSTA AO USUÁRIO. Não inclua estruturas JSON ou dicionários.

Dicionário de dados:
{dicionario_texto}
"""

    agente = create_pandas_dataframe_agent(
        modelo,
        df=lista_dataframes,  # Passa o dicionário completo! Assim o agente conhece os nomes das variáveis.
        prefix=instrucoes,
        verbose=True,
        allow_dangerous_code=True,
        agent_type="openai-tools",
        handle_parsing_errors=True,
        max_iterations=15  # 15 iterações é mais que suficiente para resolver qualquer consulta Pandas
    )

    return agente


def executar_pergunta(agente, pergunta_usuario,historico_mensagens=None):
    """
    Função auxiliar para chamar o agente e garantir que
    retorne APENAS o texto limpo, sem metadados JSON.
    """
    contexto_historico = ""
    if historico_mensagens:
        # Pega as últimas 8 mensagens (para não poluir demais o prompt)
        ultimas_mensagens = historico_mensagens[-8:]
        contexto_historico = "Histórico recente da conversa:\n"
        for msg in ultimas_mensagens:
            papel = "Usuário" if msg["role"] == "user" else "Assistente"
            contexto_historico += f"{papel}: {msg['content']}\n"
        contexto_historico += "\n"

    prompt_completo = (
        f"{contexto_historico}"
        f"Pergunta atual do usuário: {pergunta_usuario}"
    )
    resposta = agente.invoke({"input": prompt_completo})

    # Se o retorno for um dicionário do LangChain
    if isinstance(resposta, dict):
        conteudo = resposta.get("output", resposta)
    else:
        conteudo = resposta

    # Se a saída for uma lista de blocos (como o Gemini costuma devolver no openai-tools)
    if isinstance(conteudo, list) and len(conteudo) > 0:
        item = conteudo[0]
        if isinstance(item, dict) and "text" in item:
            return item["text"]
        return str(item)

    return str(conteudo)

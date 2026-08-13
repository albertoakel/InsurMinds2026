# mcp_client.py

# 1. IMPORTAÇÕES PADRÃO
import os
import asyncio
import warnings
from pathlib import Path
from uuid import uuid4
from typing import Any, List, Union

# 2. IMPORTAÇÕES DE BIBLIOTECAS DE TERCEIROS
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent as create_react_agent_graph
from langgraph.checkpoint.memory import InMemorySaver

# 3. CONFIGURAÇÕES INICIAIS
warnings.filterwarnings('ignore')
#-----------------------------------------------------------------------------


ENV_PATH = '/home/akel/PycharmProjects/InsurMinds2026/.env'
if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH, override=True)
    if os.getenv("GOOGLE_API"):
        os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API")

server_params = {
    # "local-server-tools": {
    #     "command": "C:\\Dados\\Projetos\\aulas\\agent\\.venv\\Scripts\\python.exe",
    #     "args": ["C:/Dados/Projetos/aulas/agent/src/mcp_server.py"],
    #     "transport": "stdio",
    # },
    "server-tools": {
        "url": "http://127.0.0.1:5008/sse",
        "transport": "sse",
    }
}

async def run_agent():
    # Instanciamos o modelo explicitamente com a chave
    model = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite", # Ou o modelo de sua preferência
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API")
    )
    checkpointer = InMemorySaver()

    # 1. Instanciação direta (sem o 'async with')
    client = MultiServerMCPClient(server_params)

    # 2. Obtenção assíncrona das ferramentas (com 'await')
    all_tools = await client.get_tools()

    if not all_tools:
        print("\033[31mNenhuma ferramenta disponível no servidor MCP.\033[0m")
    else:
        print("\033[31m\n==== Ferramentas MCP Carregadas ====\033[0m")
        for tool in all_tools:
            print(f'\033[35m* {tool.name} *\033[0m\n{tool.description}\n')

    prompt = """
        Sua tarefa é solucionar as perguntas do usuário, usando as ferramentas disponíveis.
        Responda sempre em português. 
        
        
        Quando utilizar a ferramenta search_arxiv_tool:
        A ferramenta retorna apenas Título, autores, link e abstract. Jamais invente qualquer uma dessas informações.
        Considere que o texto completo NÃO foi recuperado.
        É proibido inferir metodologia, experimentos, resultados ou conclusões que não estejam explicitamente descritos no abstract.
        Caso essas informações não estejam disponíveis, informe que não foi possivel. jamais quebre essa regra.
    
       
        Sobre formato de eenvio por email. Formate o corpo do e-mail estritamente nesta estrutura:
        
        **[ano] título do artigo original **
        
        **Autores:** nome dos autores
        
        Resumo do artigo...
        
        **Fonte:** [Ver no arXiv](URL_REAL)        

       **[ano] título do artigo original**
       **Autores:** nome dos autores
       Resumo do artigo...
       
    """
    agent = create_react_agent_graph(model, all_tools, checkpointer=checkpointer, prompt=prompt)

    session_id = str(uuid4())
    config = {"configurable": {"thread_id": session_id}}

    while True:
        user_input = input("\033[33mFaça a sua pergunta: \033[0m")

        if user_input.strip().lower() == "sair":
            break

        if user_input.strip().lower() == "limpar":
            print("\033c")
            continue

        print(f"\033[34mUsuário: {user_input}\033[0m")

        # Invocação do agente
        agent_response = await agent.ainvoke(
            {"messages": [("user", user_input)]},
            config=config
        )
         # Tratamento do formato da mensagem final
        last_msg = agent_response['messages'][-1].content
        if isinstance(last_msg, list):
            response_text = "".join([block.get("text", "") for block in last_msg if isinstance(block, dict)])
        else:
            response_text = str(last_msg)

        print(f"\033[32mAgente: {agent_response['messages'][-1].content}\033[0m")


if __name__ == "__main__":
    asyncio.run(run_agent())
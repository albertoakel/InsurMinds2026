#src/agente.py
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents import create_pandas_dataframe_agent


# Limita o tamanho do que o pandas imprime dentro do REPL do agente.
# Sem isso, um "print(df)" de uma tabela grande vira uma observação enorme
# que é reenviada por inteiro em TODAS as iterações seguintes do loop,
# inflando tokens e tempo de resposta a cada passo.
pd.set_option("display.max_rows", 30)
pd.set_option("display.max_columns", 20)
pd.set_option("display.width", 120)


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
        temperature=0,
        # Gemini 3.x usa "thinking_level" para controlar o quanto o modelo
        # "pensa" antes de responder. Sem isso, o padrão é "high", que é
        # caro em latência para uma tarefa de decidir chamadas de pandas.
        # "low" é o nível recomendado pelo próprio LangChain para
        # respostas mais rápidas; teste também "minimal" se o seu modelo
        # suportar (verifique com modelo.profile["reasoning_effort_levels"]).
        thinking_level="low",
    )

    # CORREÇÃO AQUI: Garante que o parâmetro seja uma lista de DataFrames
    if isinstance(tabelas, dict):
        lista_dataframes = list(tabelas.values())
    else:
        lista_dataframes = tabelas

    nomes_tabelas = list(tabelas.keys()) if isinstance(tabelas, dict) else []

    contexto_tabelas = ""

    if isinstance(tabelas, dict):

        for i, nome in enumerate(nomes_tabelas):
            contexto_tabelas += (
                f"\n- df{i + 1}: tabela '{nome}', "
                f"{len(tabelas[nome])} linhas, "
                f"colunas: {list(tabelas[nome].columns)}"
            )

    instrucoes = f"""
    Você é um analista de dados especialista em Notas Fiscais.

    Mapeamento dos DataFrames disponíveis:
    {contexto_tabelas}

    Regras obrigatórias:

    1. Responda sempre em português e use somente os dados disponíveis.
    2. Nunca invente valores, colunas ou informações.

    3. Para perguntas quantitativas, siga este fluxo:
       - identifique a entidade e a métrica solicitada;
       - escolha o DataFrame correto;
       - verifique o que cada linha representa;
       - identifique as colunas semanticamente adequadas;
       - determine a operação matemática necessária;
       - execute o cálculo usando pandas;
       - valide se o resultado responde exatamente à pergunta.

    4. Respeite a granularidade:
       - tabela de notas: documentos fiscais;
       - tabela de itens: produtos ou serviços das notas;
       - não misture granularidades sem necessidade.

    5. Para contar entidades distintas, prefira identificadores únicos
       e use nunique() quando apropriado.

    6. Quando houver colunas com nomes semelhantes, use o significado
       indicado no dicionário e não apenas correspondência parcial do nome.

    7. Não deduza resultados a partir de .head(), amostras, previews,
       quantidade de DataFrames, colunas ou linhas exibidas.

    8. Semântica importante:
       - chave_de_acesso: identificador único da nota fiscal;
       - valor_nota_fiscal: valor total da nota;
       - quantidade: quantidade comercializada do item;
       - valor_total_item: valor total do item.

    9. Para produtos e serviços, utilize a tabela de itens.
       Para documentos fiscais, valores das notas, datas, emitentes
       e destinatários, utilize preferencialmente a tabela de notas.

    10. Faça cálculos com os valores numéricos completos e arredonde
        somente na apresentação final.

    11. Se houver mais de uma interpretação razoável, use a mais compatível
        com a semântica dos dados. Se isso puder alterar substancialmente
        o resultado, informe brevemente a interpretação adotada.

    12. A resposta final deve ser direta, em linguagem natural,
        sem JSON, dicionários ou código, salvo quando solicitado.

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
        max_iterations=8,
        early_stopping_method="generate",
    )

    return agente


def executar_pergunta(agente, pergunta_usuario, historico_mensagens=None):
    """
    Função auxiliar para chamar o agente e garantir que
    retorne APENAS o texto limpo, sem metadados JSON.
    """
    contexto_historico = ""
    if historico_mensagens:

        ultimas_mensagens = historico_mensagens[-6:]
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
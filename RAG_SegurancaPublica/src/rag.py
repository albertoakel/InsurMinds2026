from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from src.config import LLM_MODELS
import time


PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """
    Você é um analista especialista em segurança pública, com sólida formação em
    estatística criminal, criminologia e políticas públicas de segurança.

    INFORMAÇÃO DA BASE DE DADOS:
    Você tem acesso restrito a um único relatório de segurança pública, já convertido
    em vetores. A base possui metadados com informações de fonte, seção/capítulo e,
    quando disponível, página.

    Responda à pergunta do usuário utilizando RESTRITAMENTE o contexto fornecido abaixo.
    Se a resposta não puder ser encontrada no contexto, diga honestamente:
    "Não encontrei essa informação no relatório fornecido." - Não invente dados,
    números, estatísticas ou tendências que não estejam no contexto.

    Diretrizes de Comportamento:
    1. Seja objetivo, técnico e preciso, especialmente ao citar números e indicadores.
    2. Para perguntas sobre INDICADORES ou ESTATÍSTICAS: sempre que disponível no
       contexto, contextualize o número (período, região/UF, variação em relação a
       períodos anteriores).
    3. Para perguntas sobre a BASE DE DADOS ou a fonte do relatório, não é necessária
       formatação especial.
    4. Mantenha neutralidade: apresente os dados sem juízo de valor político ou
       ideológico.

    Formatação Obrigatória (exceto em 3.):
    Ao final de QUALQUER resposta, cite as fontes utilizadas exatamente neste formato:
    📖 Referências: Fonte | Seção | Página (ordene da mais relevante para a menos
    relevante, uma por linha)

    ## CONTEXTO
    {contexto}"""),

    # Histórico da conversa (memória)
    MessagesPlaceholder(variable_name="historico_langchain"),

    # Pergunta atual do usuário
    ("human", "{pergunta}")
])


def answer_query_with_fallback(pergunta: str, historico: list, db, bm25_retriever, reranker) -> str:
    # 1. RECUPERAÇÃO VETORIAL (ChromaDB)
    # Como agora há apenas UMA base (não um dicionário de livros), a busca é direta.
    t0 = time.time()
    vetor_resultados = db.similarity_search(pergunta, k=8)
    t1 = time.time()
    print(f"1. Retrieval: Busca Vetorial (Chroma)                           : {t1 - t0:.2f}s")

    # 2. RECUPERAÇÃO LEXICAL (BM25)
    lexical_resultados = bm25_retriever.invoke(pergunta)
    t2 = time.time()
    print(f"2. Retrieval: Busca Lexical (BM25)                              : {t2 - t1:.2f}s")

    # 3. COMBINAÇÃO E DESDUPLICAÇÃO
    todos_resultados = vetor_resultados + lexical_resultados
    documentos_unicos = []
    conteudos_vistos = set()

    for doc in todos_resultados:
        if doc.page_content not in conteudos_vistos:
            conteudos_vistos.add(doc.page_content)
            documentos_unicos.append(doc)

    if not documentos_unicos:
        return "Não tenho informação em minha base de dados para responder a essa pergunta com segurança."

    # 4. RERANKING COM CROSS-ENCODER
    pares_rerank = [[pergunta, doc.page_content] for doc in documentos_unicos]
    scores_rerank = reranker.predict(pares_rerank)

    docs_com_scores = list(zip(documentos_unicos, scores_rerank))
    docs_com_scores.sort(key=lambda x: x[1], reverse=True)

    # Filtra os N melhores pós-rerank
    context_filtered = docs_com_scores[:5]

    t3 = time.time()
    print(f"3. Processamento: Rerank & Filtro (Cross)                       : {t3 - t2:.2f}s")

    # 5. MONTAGEM DO TEXTO DE CONTEXTO E FONTES
    context_parts = []
    for doc, score in context_filtered:
        meta = doc.metadata
        source = meta.get('source', '')
        secao = meta.get('secao', meta.get('section', ''))
        pagina = meta.get('page', meta.get('pagina', ''))

        partes_ref = [str(p) for p in [source, secao, pagina] if p]
        referencia = " | ".join(partes_ref)

        context_parts.append(f"[{referencia}]\n{doc.page_content}")

    context_text = "\n\n".join(context_parts)

    t4 = time.time()
    print(f"4. Transformação: Estruturação de Contexto                      : {t4 - t3:.2f}s")

    # 6. CONVERSÃO DO HISTÓRICO
    historico_langchain = []
    for msg in historico:
        if msg.role == 'user':
            historico_langchain.append(HumanMessage(content=msg.content))
        elif msg.role == 'assistant':
            historico_langchain.append(AIMessage(content=msg.content))

    t5 = time.time()
    print(f"5. Transformação: Adaptação de Memória                          : {t5 - t4:.2f}s")

    # 7. LOOP DE FALLBACK DAS LLMs
    for model_name in LLM_MODELS:
        try:
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                temperature=0.2,
                max_retries=2
            )

            chain = (PROMPT_TEMPLATE | llm | StrOutputParser())

            resposta = chain.invoke({
                "contexto": context_text,
                "historico_langchain": historico_langchain,
                "pergunta": pergunta
            })
            t6 = time.time()
            print(f"6. Inferência: Geração LLM ({model_name})       : {t6 - t5:.2f}s")
            print("------------------------------------------")

            return resposta

        except Exception as e:
            print(f"Modelo {model_name} falhou. Tentando próximo... Erro: {e}")
            continue

    return "Desculpe, todos os nossos serviços de IA estão instáveis no momento."

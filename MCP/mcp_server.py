# mcp_server.py

# 1. IMPORTAÇÕES PADRÃO
import re
import os
import asyncio
import warnings
from urllib.parse import quote

# 2. IMPORTAÇÕES DE BIBLIOTECAS DE TERCEIROS
import markdown

# 3. IMPORTAÇÕES DO PROJETO (módulos internos)
from mcp.server.fastmcp import FastMCP
from mcp_helpers import ArxivHelper, MailMessage, SMTPServer
from configuracao import carrega_variaveis_ambiente

# 4. CONFIGURAÇÕES INICIAIS
warnings.filterwarnings('ignore')
carrega_variaveis_ambiente()
#-------------------------------------------------------------------


async def search_arxiv_tool(query: str, max_results: int = 10) -> str:
    """
    Esta ferramenta busca por artigos científicos no site arxiv.org.
    Suporta busca por termos e intervalos de anos (ex: 2020-2025, 2015 a 2018).



    Args:
        query (str): O assunto e/ou intervalo de datas (ex: "modelling VLF Wave 2020-2025").
        max_results (int, optional): Quantidade máxima de artigos retornados. O padrão é 5.
    """

    print("=" * 80)
    print("search_arxiv_tool FOI CHAMADA")
    print("Consulta recebida:", query)
    print("=" * 80)
    try:
        arxiv_mcp_tool = ArxivHelper()

        # 1. Mapeamento de termos comuns em português
        query_map = {
            "ia": "artificial intelligence",
            "inteligencia artificial": "artificial intelligence",
            "inteligência artificial": "artificial intelligence"
        }

        # 2. Expressão regular para capturar intervalos de anos (ex: 2015-2020, 2020 a 2025)
        date_pattern = r'\b(19\d\d|20\d\d)\s*(?:-|a|até|to)\s*(19\d\d|20\d\d)\b'
        match = re.search(date_pattern, query, re.IGNORECASE)

        date_clause = ""
        clean_query = query

        if match:
            start_year, end_year = match.group(1), match.group(2)
            # Monta o filtro de data nativo da API do arXiv (YYYY0101000000 TO YYYY1231235959)
            date_clause = f"+AND+submittedDate:[{start_year}0101000000+TO+{end_year}1231235959]"
            # Remove o intervalo do texto de busca para não poluir a busca por palavras-chave
            clean_query = re.sub(date_pattern, '', query, flags=re.IGNORECASE).strip()

        # Aplica o mapeamento se necessário
       # search_term = query_map.get(clean_query.lower(), clean_query) #original
       # formatted_query = search_term.replace(" ", '+')  #original

        # 3. Monta a URL da API do arXiv com o filtro de data (se houver)
        # url = (
        #     f"{arxiv_mcp_tool.base_url}?"
        #     f"search_query=all:{formatted_query}{date_clause}&"
        #     f"start=0&max_results={max_results}&"
        #     f"sortBy=submittedDate&sortOrder=descending"
        # ) #original

        search_term = query_map.get(clean_query.lower(), clean_query)
        search_arxiv_tool
        formatted_query = quote(f'"{search_term}"')

        url = (
            f"{arxiv_mcp_tool.base_url}?"
            f"search_query=all:{formatted_query}{date_clause}&"
            f"start=0&max_results={max_results}&"
            f"sortBy=submittedDate&sortOrder=descending"
        )





        xml_data = await arxiv_mcp_tool.make_arxiv_request(url)
        if not xml_data:
            return "Não foi possível recuperar os dados do arXiv."

        papers = arxiv_mcp_tool.parse_arxiv_response(xml_data)

        print(f"Artigos encontrados: {len(papers)}")

        for i, paper in enumerate(papers, start=1):
            print(f"\nArtigo {i}")
            print("Título:", paper["title"])


        if not papers:
            return f"Nenhum artigo encontrado para a busca '{clean_query}' no período especificado."

        # Filtra e ordena por relevância
        papers = arxiv_mcp_tool.filter_relevance(
            papers,
            clean_query
        ) #new

        paper_texts = [arxiv_mcp_tool.format_paper(paper) for paper in papers]
        return "\n---\n".join(paper_texts)

    except Exception as e:
        return f"ERRO ao buscar no arXiv: {str(e)}"


def _send_mail_sync(subject: str, email_to: str, email_content: str, email_attach_file: str = None) -> str:
    """Função síncrona interna para conexão e envio SMTP."""
    username = os.getenv('SMTP_USERNAME', 'albertoakel@gmail.com')
    password = os.getenv('SMTP_PASSWORD')

    if not password:
        return "ERRO: Variável SMTP_PASSWORD não configurada no arquivo .env."

    # Configuração correta para Porta 587 do Gmail (TLS=True, SSL=False)
    smtp = SMTPServer(
        host='smtp.gmail.com',
        port=587,
        username=username,
        password=password,
        has_ssl=False,
        has_tls=True,
        has_authentication=True
    )

    sender_email = username
    sender_name = 'Alberto Akel'

    message = MailMessage(sender_email=sender_email, sender_name=sender_name)
    message.set_subject(subject=subject)

    for email in re.split(r'[,;]', email_to):
        email = email.strip()
        if email:
            message.to.add(email=email)
    #html_body = markdown.markdown(email_content)  #novo
    html_body = markdown.markdown(email_content, extensions=['nl2br']) #novo
    message.set_html_body(html_body)          #novo
    #message.set_html_body(email_content)


    # Tratamento para evitar erro quando o modelo envia a string "None" ou "null"
    if email_attach_file and str(email_attach_file).strip().lower() not in ("none", "null", ""):
        if not os.path.isfile(email_attach_file):
            return f"ERRO: Arquivo para anexo não encontrado em: {email_attach_file}"
        message.attach_file(filename=email_attach_file)

    try:
        smtp.connect()
        smtp.send(message)
        smtp.disconnect()
        return 'E-mail enviado com sucesso!'
    except Exception as e:
        return f"ERRO ao enviar e-mail: {str(e)}"


async def send_mail(subject: str, email_to: str, email_content: str, email_attach_file: str = None) -> str:
    """
    Esta ferramenta envia um e-mail para uma pessoa.

    Args:
        subject (str): Assunto do e-mail (título curto).
        email_to (str): E-mail do destinatário (pode conter múltiplos e-mails separados por "," ou ";").
        email_content (str): Conteúdo do corpo do e-mail em texto/HTML.
        email_attach_file (str, optional): Caminho absoluto de um arquivo para anexar. Padrão é None.
    """
    # Executa a função síncrona em uma thread separada sem travar o loop de eventos assíncrono
    return await asyncio.to_thread(_send_mail_sync, subject, email_to, email_content, email_attach_file)


if __name__ == "__main__":
    print("Iniciando o servidor MCP...")
    mcp = FastMCP(name="DataH_MCP", port=5008)
    print('URL para verificação: "http://localhost:5008/sse"')
    mcp.add_tool(search_arxiv_tool)
    mcp.add_tool(send_mail)
    mcp.run(transport='sse')
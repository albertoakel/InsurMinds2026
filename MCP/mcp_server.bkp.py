# mcp_server.py
import re
import os

# # Servidor MCP
from mcp.server.fastmcp import FastMCP
from mcp_helpers import ArxivHelper,MailMessage,SMTPServer

from configuracao import carrega_variaveis_ambiente

carrega_variaveis_ambiente()

import warnings
warnings.filterwarnings('ignore')



async def search_arxiv_tool(query:str, max_results:int = 5) -> str:
    """
    Esta ferramenta busca por artigos científicos no site arxiv.org

    Args:
        query (str): O assunto que deseja buscar no site.
        max_results (int, optional): Quantidade máxima de artigos retornados pelo site. O padrão é 5.
    """
    try:
        arxiv_mcp_tool = ArxivHelper()
        formatted_query = query.replace(" ", '+')

        url = f"{arxiv_mcp_tool.base_url}?search_query=all:{formatted_query}&start=0&max_results={max_results}"
        xml_data = await arxiv_mcp_tool.make_arxiv_request(url)
        if not xml_data:
            raise ValueError("Não foi capaz de recuperar os dados do arxiv.")

        papers = arxiv_mcp_tool.parse_arxiv_response(xml_data)
        if not papers:
            return FileNotFoundError("Artigos não encontrados.")

        paper_texts = [arxiv_mcp_tool.format_paper(paper) for paper in papers]
        return "\n---\n".join(paper_texts)
    except Exception as e:
        return f"ERRO: {str(e)}"


async def send_mail(subject:str, email_to:str, email_content:str, email_attach_file:str=None) -> str:
    """
    Esta ferramenta envia um e-mail para uma pessoa.

    Args:
        subject (str): É o assunto do email, e deve ser um título curto.
        email_to (str): É o e-mail para quem será enviado o email. Este argumento pode receber mais de um email, em uma string separados por "," or ";". Ex: usuario1@domain.com, usuario2@domain.com
        email_content (str): É o conteúdo do email
        email_attach_file (str, optional): É o caminho absoluto de um arquivo para anexar ao email. Se não existir anexo, o valor deve ser None. O valor padrão é None.
    """
    username=os.getenv('SMTP_USERNAME')
    password=os.getenv('SMTP_PASSWORD')
    smtp = SMTPServer(host='smtp.gmail.com', port=587, username=username, password=password, has_ssl=True, has_tls=True, has_authentication=True)

    sender_email = 'albertoakel@gmail.com'
    sender_name = 'Alberto Akel'

    message = MailMessage(sender_email=sender_email, sender_name=sender_name)
    message.set_subject(subject=subject)
    for email in re.split(r'[,;]', email_to):
        email = email.strip()
        if email:
            message.to.add(email=email)

    message.set_html_body(email_content)

    if email_attach_file is not None and email_attach_file != '' and len(email_attach_file) > 0:
        if not os.path.isfile(email_attach_file):
            raise FileNotFoundError(f"Arquivo não encontrado: {email_attach_file}")
        message.attach_file(filename=email_attach_file)

    try:
        smtp.connect()
        smtp.send(message)
        smtp.disconnect()
        return 'Email enviado com sucesso!'
    except Exception as e:
        return f"ERRO: {str(e)}"


if __name__== "__main__":
    print("Inciando o servidor...")
    mcp= FastMCP(name="DataH_MCP",port=5008)
    print(f'URL para verificacao "http://localhost:5008/sse" ')
    mcp.add_tool(search_arxiv_tool)
    mcp.add_tool(send_mail)
    mcp.run(transport='sse')

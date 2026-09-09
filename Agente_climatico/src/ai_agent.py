# ai_agent.py
# import os
# from pathlib import Path
#
# from dotenv import load_dotenv
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_groq import ChatGroq
#
# from .config import OPENWEATHER_API_KEY
# # Carrega o .env localizado na pasta do projeto
# BASE_DIR = Path(__file__).resolve().parent
# load_dotenv(BASE_DIR / ".env")
#
# if not os.getenv("GROQ_API_KEY"):
# #     raise ValueError("A variável GROQ_API_KEY não foi encontrada no arquivo .env")
#
#
# llm = ChatGroq(
#     model="openai/gpt-oss-20b",
#     temperature=0.2,
#     max_retries=2,
# )


from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from .config import (
    GROQ_API_KEY,
    GROQ_MAX_RETRIES,
    GROQ_MODEL,
    GROQ_TEMPERATURE,
)


if not GROQ_API_KEY:
    raise ValueError("A variável GROQ_API_KEY não foi encontrada no arquivo .env")


llm = ChatGroq(
    model=GROQ_MODEL,
    temperature=GROQ_TEMPERATURE,
    max_retries=GROQ_MAX_RETRIES,
)



def gerar_mensagem_ia(cliente, clima, motivo_alerta):
    """Utiliza o Groq para gerar uma mensagem preventiva personalizada."""

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
            Você é o assistente virtual proativo de uma seguradora.
            Produza um SMS com exatamente duas frases, em linguagem empática, direta e sem causar pânico.
            
            Na primeira frase, informe o nome, a cidade e o risco identificado. Cite somente os valores ambientais
            diretamente relacionados ao motivo do alerta.
            
            Na segunda frase, apresente uma ou duas medidas preventivas simples e diretamente relacionadas ao risco.
            
            Use exclusivamente os fatos fornecidos. Não invente previsões, horários, períodos do dia, sintomas, 
            consequências médicas, canais de atendimento ou serviços da seguradora.
            
            Use a idade e o perfil apenas para ajustar o tom da mensagem. Não mencione idade exata, doenças, 
            diagnósticos, medicamentos ou condições pessoais.
            
            Se houver mais de um risco no motivo, combine-os na mesma mensagem sem acrescentar riscos diferentes.
            
            Quando o motivo for qualidade do ar, mencione somente a cidade, a classificação e o AQI OpenWeather. 
            Nesse caso, não mencione temperatura, sensação térmica, umidade, PM2.5 ou PM10. Recomende apenas 
            reduzir a permanência ao ar livre e evitar atividades externas prolongadas.
            
            Quando a qualidade do ar não fizer parte do motivo, não a mencione.
            
            Retorne somente o texto do SMS, sem aspas, títulos, listas ou explicações.
            

            """
        ),
        (
            "user",
            """
            Gere um SMS para o seguinte segurado:

            Nome: {nome}
            Cidade: {cidade}
            Seguro contratado: {seguro}
            Perfil: {perfil}
            Idade: {idade}

            Condição climática atual: {clima_desc}
            Temperatura: {temp} °C
            Sensação térmica: {sensacao_termica} °C
            Umidade relativa: {umidade}%
            Qualidade do ar: {qualidade_ar}
            Motivo do alerta: {motivo}
            """
        ),
    ])

    chain = prompt | llm

    idade = cliente.get("idade")

    idade_texto = (
        f"{idade} anos"
        if idade is not None
        else "não informada"
    )

    qualidade_ar = clima.get("qualidade_ar")

    if qualidade_ar:
        pm2_5 = qualidade_ar.get("pm2_5")
        pm10 = qualidade_ar.get("pm10")

        pm2_5_texto = (
            f"{pm2_5:.1f} µg/m³"
            if pm2_5 is not None
            else "não informado"
        )

        pm10_texto = (
            f"{pm10:.1f} µg/m³"
            if pm10 is not None
            else "não informado"
        )

        qualidade_ar_texto = (
            f"{qualidade_ar['classificacao']} "
            f"(AQI OpenWeather {qualidade_ar['aqi_openweather']}); "
            f"PM2.5: {pm2_5_texto}; "
            f"PM10: {pm10_texto}"
        )
    else:
        qualidade_ar_texto = "Não consultada ou indisponível"

    resposta = chain.invoke({
        "nome": cliente["nome"],
        "idade": idade_texto,
        "cidade": cliente["cidade"],
        "seguro": cliente["seguro"],
        "perfil": cliente["perfil"],
        "clima_desc": clima["descricao"],
        "temp": f"{clima['temperatura']:.1f}",
        "sensacao_termica": f"{clima['sensacao_termica']:.1f}",
        "umidade": clima["umidade"],
        "qualidade_ar": qualidade_ar_texto,
        "motivo": motivo_alerta,
    })

    return resposta.content.strip()
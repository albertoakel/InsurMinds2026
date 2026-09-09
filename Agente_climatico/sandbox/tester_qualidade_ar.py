from ai_agent import gerar_mensagem_ia
from rules_engine import verificar_necessidade_alerta


cliente = {
    "id": "teste",
    "nome": "Cliente Teste",
    "idade": 68,
    "cidade": "Belém",
    "seguro": "Saúde / Vida",
    "perfil": "Realiza atividades cotidianas ao ar livre.",
}


cenarios = [
    {
        "aqi": 4,
        "classificacao": "Ruim",
        "pm2_5": 60.0,
        "pm10": 120.0,
    },
    {
        "aqi": 5,
        "classificacao": "Muito ruim",
        "pm2_5": 90.0,
        "pm10": 220.0,
    },
]


for cenario in cenarios:
    clima = {
        "descricao": "nublado",
        "temperatura": 28.0,
        "sensacao_termica": 30.0,
        "umidade": 60,
        "eventos_relevantes": [],
        "evento_relevante": None,
        "qualidade_ar": {
            "aqi_openweather": cenario["aqi"],
            "classificacao": cenario["classificacao"],
            "gera_alerta": True,
            "evento_relevante": "Qualidade do Ar Ruim",
            "pm2_5": cenario["pm2_5"],
            "pm10": cenario["pm10"],
        },
    }

    enviar_alerta, motivo = verificar_necessidade_alerta(
        cliente,
        clima,
    )

    print("=" * 70)
    print(f"AQI: {cenario['aqi']} — {cenario['classificacao']}")
    print(f"Alerta: {enviar_alerta}")
    print(f"Motivo: {motivo}")

    if enviar_alerta:
        mensagem = gerar_mensagem_ia(
            cliente,
            clima,
            motivo,
        )
        print(f"SMS: {mensagem}")
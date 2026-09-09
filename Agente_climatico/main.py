#main.py
from src.ai_agent import gerar_mensagem_ia
from src.air_quality_service import obter_qualidade_ar
from src.config import DEFAULT_CLIENTS_FILE
from src.data_loader import get_clientes
from src.rules_engine import verificar_necessidade_alerta
from src.weather_service import obter_dados_climaticos


def iniciar_pipeline_alertas():
    print("🌤️ Iniciando varredura climática proativa...\n")
    print("=" * 70)

    clientes = get_clientes(DEFAULT_CLIENTS_FILE)

    for cliente in clientes:
        idade = cliente.get("idade")

        idade_texto = (
            f"{idade} anos"
            if idade is not None
            else "idade não informada"
        )
        print(
            f"👤 Analisando: {cliente['nome']} | "
            f"{idade_texto} | "
            f"{cliente['cidade']} | "
            f"Seguro: {cliente['seguro']}"
        )

        # 1. Coleta dos dados climáticos
        clima = obter_dados_climaticos(cliente["cidade"])

        if not clima:
            print("   ❌ Não foi possível obter os dados climáticos.")
            print("-" * 70)
            continue

        temperatura = float(clima["temperatura"])
        sensacao = float(
            clima.get("sensacao_termica", temperatura)
        )
        umidade = clima.get("umidade", "Não informada")

        print(
            f"   ☁️ {clima['descricao'].capitalize()} | "
            f"Temperatura: {temperatura:.1f} °C | "
            f"Sensação: {sensacao:.1f} °C | "
            f"Umidade: {umidade}%"
        )
        # Consulta a qualidade do ar somente para Saúde / Vida
        if cliente["seguro"] == "Saúde / Vida":
            clima = dict(clima)

            qualidade_ar = obter_qualidade_ar(
                clima["latitude"],
                clima["longitude"],
            )

            clima["qualidade_ar"] = qualidade_ar

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

                print(
                    f"   🌫️ Qualidade do ar: "
                    f"{qualidade_ar['classificacao']} | "
                    f"AQI OpenWeather: "
                    f"{qualidade_ar['aqi_openweather']}"
                )

                print(
                    f"      PM2.5: {pm2_5_texto} | "
                    f"PM10: {pm10_texto}"
                )

            else:
                print("   🌫️ Qualidade do ar: indisponível")

        # 2 e 3. Identificação de eventos e regras de negócio
        enviar_alerta, motivo = verificar_necessidade_alerta(
            cliente,
            clima,
        )

        if enviar_alerta:
            print(f"   ⚠️ Alerta gerado: {motivo}")
            print("   🧠 Gerando mensagem com IA...")

            # 4. Geração da mensagem
            try:
                mensagem = gerar_mensagem_ia(
                    cliente,
                    clima,
                    motivo,
                )
            except Exception:
                print(
                    "   ❌ O risco foi identificado, mas não foi "
                    "possível gerar o SMS."
                )
                print("-" * 70)
                continue

            # 5. Simulação de envio
            print("\n   📱 SIMULAÇÃO DE DISPARO:")
            print(f"   ➡️ Para: {cliente['nome']}")
            print(f"   💬 SMS: {mensagem}\n")

        else:
            print("   ✅ Nenhum alerta necessário.\n")

        print("-" * 70)


if __name__ == "__main__":
    iniciar_pipeline_alertas()

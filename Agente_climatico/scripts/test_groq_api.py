"""Teste manual de integração da geração de SMS com o Groq."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main():
    """Gera uma mensagem sintética e retorna zero quando houver resposta."""
    from src.config import GROQ_API_KEY

    if not GROQ_API_KEY:
        print("❌ A variável GROQ_API_KEY não foi carregada.")
        return 1

    try:
        from src.ai_agent import gerar_mensagem_ia

        cliente = {
            "nome": "Cliente Teste",
            "idade": 65,
            "cidade": "Belém",
            "seguro": "Saúde / Vida",
            "perfil": "Perfil sintético usado somente para validação.",
        }
        clima = {
            "descricao": "nublado",
            "temperatura": 30.0,
            "sensacao_termica": 33.0,
            "umidade": 70,
            "qualidade_ar": {
                "classificacao": "Ruim",
                "aqi_openweather": 4,
                "pm2_5": 60.0,
                "pm10": 120.0,
            },
        }
        motivo = (
            "A qualidade do ar está classificada como ruim ou muito ruim, "
            "indicando a necessidade de reduzir a exposição prolongada."
        )

        mensagem = gerar_mensagem_ia(cliente, clima, motivo)
    except Exception as erro:
        print(f"❌ Falha na integração com o Groq ({type(erro).__name__}).")
        return 1

    if not mensagem.strip():
        print("❌ O Groq retornou uma mensagem vazia.")
        return 1

    print("✅ Groq respondeu com sucesso.")
    print("SMS:", mensagem)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

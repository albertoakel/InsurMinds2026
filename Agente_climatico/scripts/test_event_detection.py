"""Testes locais da identificação meteorológica e da qualidade do ar."""

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.air_quality_service import interpretar_qualidade_ar  # noqa: E402
from src.weather_service import identificar_eventos  # noqa: E402


def dados_qualidade_ar(aqi):
    return {
        "list": [
            {
                "main": {"aqi": aqi},
                "components": {
                    "pm2_5": 12.5,
                    "pm10": 20.0,
                    "o3": 30.0,
                },
            }
        ]
    }


class EventDetectionTests(unittest.TestCase):
    def test_condicao_sem_eventos(self):
        eventos = identificar_eventos(800, 28.0, 30.0, 70, 10.0)
        self.assertEqual(eventos, [])

    def test_identifica_eventos_simultaneos(self):
        eventos = identificar_eventos(202, 36.0, 39.0, 25, 45.0)
        self.assertEqual(
            eventos,
            ["Tempestade", "Ventos Fortes", "Calor Extremo", "Baixa Umidade"],
        )

    def test_respeita_limites_inclusivos(self):
        eventos = identificar_eventos(502, 35.0, 35.0, 30, 40.0)
        self.assertIn("Chuva Forte", eventos)
        self.assertIn("Calor Extremo", eventos)
        self.assertIn("Baixa Umidade", eventos)
        self.assertNotIn("Ventos Fortes", eventos)

    def test_sensacao_termica_pode_acionar_frio(self):
        eventos = identificar_eventos(800, 12.0, 9.0, 80, 5.0)
        self.assertEqual(eventos, ["Frio Intenso"])

    def test_aqi_bom_nao_gera_alerta(self):
        resultado = interpretar_qualidade_ar(dados_qualidade_ar(1))
        self.assertEqual(resultado["classificacao"], "Boa")
        self.assertFalse(resultado["gera_alerta"])
        self.assertIsNone(resultado["evento_relevante"])

    def test_aqi_quatro_gera_alerta(self):
        resultado = interpretar_qualidade_ar(dados_qualidade_ar(4))
        self.assertEqual(resultado["classificacao"], "Ruim")
        self.assertTrue(resultado["gera_alerta"])
        self.assertEqual(resultado["evento_relevante"], "Qualidade do Ar Ruim")
        self.assertEqual(resultado["pm2_5"], 12.5)

    def test_rejeita_payload_de_qualidade_incompleto(self):
        self.assertIsNone(interpretar_qualidade_ar({"list": []}))
        self.assertIsNone(interpretar_qualidade_ar(dados_qualidade_ar(8)))


if __name__ == "__main__":
    unittest.main(verbosity=2)

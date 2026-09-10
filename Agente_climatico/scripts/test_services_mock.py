"""Testes dos serviços HTTP com respostas simuladas, sem consumir APIs."""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.air_quality_service import obter_qualidade_ar  # noqa: E402
from src.weather_service import obter_dados_climaticos  # noqa: E402


class ServicesMockTests(unittest.TestCase):
    @patch("src.weather_service.OPENWEATHER_API_KEY", "chave-de-teste")
    @patch("src.weather_service.requests.get")
    def test_converte_resposta_meteorologica(self, mock_get):
        resposta = Mock(status_code=200, ok=True)
        resposta.json.return_value = {
            "name": "Belém",
            "coord": {"lat": -1.45, "lon": -48.49},
            "main": {"temp": 36.0, "feels_like": 40.0, "humidity": 28},
            "wind": {"speed": 12.0},
            "weather": [{"id": 502, "main": "Rain", "description": "chuva forte"}],
            "rain": {"1h": 8.4},
        }
        mock_get.return_value = resposta

        clima = obter_dados_climaticos("Belém")

        self.assertEqual(clima["cidade"], "Belém")
        self.assertAlmostEqual(clima["vento"], 43.2)
        self.assertEqual(
            clima["eventos_relevantes"],
            ["Chuva Forte", "Ventos Fortes", "Calor Extremo", "Baixa Umidade"],
        )
        parametros = mock_get.call_args.kwargs["params"]
        self.assertEqual(parametros["q"], "Belém,BR")

    @patch("src.weather_service.OPENWEATHER_API_KEY", "chave-de-teste")
    @patch("src.weather_service.requests.get", side_effect=requests.Timeout)
    def test_timeout_meteorologico_retorna_none(self, _mock_get):
        with patch("builtins.print"):
            self.assertIsNone(obter_dados_climaticos("Belém"))

    @patch("src.air_quality_service.OPENWEATHER_API_KEY", "chave-de-teste")
    @patch("src.air_quality_service.requests.get")
    def test_converte_resposta_de_qualidade_do_ar(self, mock_get):
        resposta = Mock(status_code=200, ok=True)
        resposta.json.return_value = {
            "list": [
                {
                    "main": {"aqi": 5},
                    "components": {"pm2_5": 90, "pm10": 220, "co": 300},
                }
            ]
        }
        mock_get.return_value = resposta

        qualidade = obter_qualidade_ar(-1.45, -48.49)

        self.assertEqual(qualidade["classificacao"], "Muito ruim")
        self.assertTrue(qualidade["gera_alerta"])
        self.assertEqual(qualidade["pm10"], 220.0)

    @patch("src.air_quality_service.OPENWEATHER_API_KEY", "chave-de-teste")
    @patch("src.air_quality_service.requests.get")
    def test_resposta_http_invalida_retorna_none(self, mock_get):
        mock_get.return_value = Mock(status_code=500, ok=False)
        with patch("builtins.print"):
            self.assertIsNone(obter_qualidade_ar(-1.45, -48.49))


if __name__ == "__main__":
    unittest.main(verbosity=2)

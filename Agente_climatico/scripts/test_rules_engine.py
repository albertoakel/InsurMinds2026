"""Testes locais das regras de decisão por tipo de seguro."""

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.rules_engine import (  # noqa: E402
    obter_eventos,
    verificar_necessidade_alerta,
)


class RulesEngineTests(unittest.TestCase):
    def test_auto_recebe_alerta_de_tempestade(self):
        cliente = {"seguro": "Auto", "idade": 35}
        clima = {"eventos_relevantes": ["Tempestade"]}

        enviar, motivo = verificar_necessidade_alerta(cliente, clima)

        self.assertTrue(enviar)
        self.assertIn("veículo", motivo)

    def test_calor_nao_afeta_apolice_auto(self):
        cliente = {"seguro": "Auto", "idade": 35}
        clima = {"eventos_relevantes": ["Calor Extremo"]}

        enviar, motivo = verificar_necessidade_alerta(cliente, clima)

        self.assertFalse(enviar)
        self.assertIn("não afetam", motivo)

    def test_residencial_combina_chuva_e_vento(self):
        cliente = {"seguro": "Residencial", "idade": 48}
        clima = {"eventos_relevantes": ["Chuva Forte", "Ventos Fortes"]}

        enviar, motivo = verificar_necessidade_alerta(cliente, clima)

        self.assertTrue(enviar)
        self.assertIn("alagamento", motivo)
        self.assertIn("destelhamento", motivo)

    def test_saude_com_faixa_etaria_prioritaria(self):
        cliente = {"seguro": "Saúde / Vida", "idade": 60}
        clima = {"eventos_relevantes": ["Baixa Umidade"]}

        enviar, motivo = verificar_necessidade_alerta(cliente, clima)

        self.assertTrue(enviar)
        self.assertIn("faixa etária", motivo)

    def test_saude_abaixo_da_faixa_nao_recebe_reforco(self):
        cliente = {"seguro": "Saúde / Vida", "idade": 59}
        clima = {"eventos_relevantes": ["Baixa Umidade"]}

        enviar, motivo = verificar_necessidade_alerta(cliente, clima)

        self.assertTrue(enviar)
        self.assertNotIn("faixa etária", motivo)

    def test_incorpora_evento_de_qualidade_do_ar_sem_duplicar(self):
        clima = {
            "eventos_relevantes": ["Qualidade do Ar Ruim"],
            "qualidade_ar": {"evento_relevante": "Qualidade do Ar Ruim"},
        }

        self.assertEqual(obter_eventos(clima), ["Qualidade do Ar Ruim"])

        cliente = {"seguro": "Saúde / Vida", "idade": 40}
        enviar, motivo = verificar_necessidade_alerta(cliente, clima)
        self.assertTrue(enviar)
        self.assertEqual(motivo.count("qualidade do ar"), 1)

    def test_mantem_compatibilidade_com_evento_legado(self):
        clima = {"evento_relevante": "Chuva Forte"}
        self.assertEqual(obter_eventos(clima), ["Chuva Forte"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

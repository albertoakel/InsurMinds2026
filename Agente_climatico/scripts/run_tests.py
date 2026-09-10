"""Executa todos os testes locais sem realizar chamadas às APIs externas."""

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

MODULOS_TESTES_LOCAIS = (
    "scripts.test_data_loader",
    "scripts.test_event_detection",
    "scripts.test_rules_engine",
    "scripts.test_services_mock",
)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main():
    carregador = unittest.TestLoader()
    suite = carregador.loadTestsFromNames(MODULOS_TESTES_LOCAIS)
    resultado = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if resultado.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())

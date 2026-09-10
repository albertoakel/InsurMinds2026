"""Testes locais para leitura e validação das bases CSV."""

import io
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_loader import get_clientes  # noqa: E402


CABECALHO = "id,nome,idade,cidade,seguro,perfil,telefone\n"


class DataLoaderTests(unittest.TestCase):
    def test_le_csv_utf8_com_bom(self):
        conteudo = (
            CABECALHO
            + "1,Lilian,44,Três Corações,Auto,Usa o carro diariamente,+5535000000000\n"
        ).encode("utf-8-sig")

        clientes = get_clientes(io.BytesIO(conteudo))

        self.assertEqual(len(clientes), 1)
        self.assertEqual(clientes[0]["nome"], "Lilian")
        self.assertEqual(clientes[0]["cidade"], "Três Corações")
        self.assertEqual(clientes[0]["idade"], 44)

    def test_fallback_para_latin1(self):
        conteudo = (
            CABECALHO
            + "2,João,35,Belém,Residencial,Mora em casa térrea,+5591000000000\n"
        ).encode("latin-1")

        clientes = get_clientes(io.BytesIO(conteudo))

        self.assertEqual(clientes[0]["nome"], "João")
        self.assertEqual(clientes[0]["cidade"], "Belém")

    def test_idade_vazia_e_telefone_opcional(self):
        conteudo = (
            "id,nome,idade,cidade,seguro,perfil\n"
            "3,Ana,,Recife,Saúde / Vida,Perfil sintético\n"
        ).encode("utf-8")

        cliente = get_clientes(io.BytesIO(conteudo))[0]

        self.assertIsNone(cliente["idade"])
        self.assertEqual(cliente["telefone"], "")

    def test_rejeita_coluna_obrigatoria_ausente(self):
        conteudo = (
            "id,nome,idade,cidade,seguro,telefone\n"
            "4,Carlos,50,Curitiba,Auto,+5541000000000\n"
        ).encode("utf-8")

        with self.assertRaisesRegex(ValueError, "perfil"):
            get_clientes(io.BytesIO(conteudo))

    def test_rejeita_idade_invalida(self):
        conteudo = (
            CABECALHO
            + "5,Sofia,setenta,Teresina,Saúde / Vida,Perfil sintético,+5586000000000\n"
        ).encode("utf-8")

        with self.assertRaisesRegex(ValueError, "Idade inválida"):
            get_clientes(io.BytesIO(conteudo))

    def test_rejeita_idade_fora_do_intervalo(self):
        conteudo = (
            CABECALHO
            + "6,Teste,121,Palmas,Auto,Perfil sintético,+5563000000000\n"
        ).encode("utf-8")

        with self.assertRaisesRegex(ValueError, "fora do intervalo"):
            get_clientes(io.BytesIO(conteudo))


if __name__ == "__main__":
    unittest.main(verbosity=2)

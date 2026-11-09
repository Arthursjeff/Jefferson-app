"""Regressões do conversor compartilhado ERP V0.6 e estoque histórico."""
import unittest

from core.conversor_erp_estoque import converter
from core.conversor_erp_pedido import sugerir_codigo
from pathlib import Path


class TestConversorErpEstoque(unittest.TestCase):
    def test_reutiliza_conversor_existente(self):
        consulta = sugerir_codigo({"codigo_erp":"42-Z42BA12T",
                                   "descricao_original":"Z1342 BA12T VALVULA SOLENOIDE"})
        self.assertEqual(consulta["codigo_sugerido"], "Z1342BA12T")
        self.assertEqual(converter("42-Z42BA12T", "Z1342 BA12T VALVULA SOLENOIDE").codigo_tecnico,
                         consulta["codigo_sugerido"])

    def test_valvulas_conferidas_pela_descricao(self):
        casos = [
            ("026BA121", "2026 BA121 VALVULA SOLENOIDE", "2026BA121"),
            ("36BA4", "2036 BA04 VALVULA SOLENOIDE", "2036BA04"),
            ("35BA4", "1335 BA04 VALVULA SOLENOIDE", "1335BA04"),
            ("42BT12T", "1342 BT12T VALVULA SOLENOIDE", "1342BT12T"),
            ("14-Z14BV8A", "Z1314 BV08A VALVULA SOLENOIDE", "Z1314BV08A"),
            ("12BS504", "2012 BS504 VALVULA SOLENOIDE", "2012BS504"),
            ("3073LH8S", "3073 LH08S VALVULA SOLENOIDE", "3073LH08S"),
        ]
        for raw, desc, codigo in casos:
            with self.subTest(raw=raw):
                saida = converter(raw, desc)
                self.assertEqual(saida.status, "CONFIRMADO")
                self.assertEqual(saida.codigo_tecnico, codigo)

    def test_kits_internos_rastreaveis(self):
        a = converter("202-0509", "K030 AR2 KIT REPARO")
        b = converter("202-0515", "K30 A02 KIT REPARO 1330")
        self.assertEqual((a.status, a.codigo_tecnico), ("CONFIRMADO", "K030AR2"))
        self.assertEqual((b.status, b.codigo_tecnico), ("CONFIRMADO", "K30A2"))

    def test_protege_ambiguidade_e_exposicao(self):
        self.assertEqual(converter("EXP35BA4", "EXP 1335 BA04 VALVULA").status, "PENDENTE")
        self.assertEqual(converter("35BA4INA-72", "1335 BA04 INA72 VALVULA SOLENOIDE").status, "DIVERGENTE")
        self.assertEqual(converter("73LH12S", "2073 LH12S VALVULA SOLENOIDE").status, "DIVERGENTE")
        self.assertNotEqual(converter("35BA4", "").status, "CONFIRMADO")

    def test_inventario_v2(self):
        fonte = (Path(__file__).resolve().parents[1] / "core" / "estoque_referencia.py").read_text(encoding="utf-8")
        self.assertIn('REFERENCIA_LABORATORIO = "ERP_2026-11-03_LAB_TRANSF_v2_CONFERIDO"', fonte)


if __name__ == "__main__":
    unittest.main()

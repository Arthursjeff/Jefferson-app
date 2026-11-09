"""Regressões do conversor ERP real e do snapshot compartilhado."""
import unittest
from core.conversor_erp_jefferson import converter, carregar_equivalencias
from core.estoque_referencia import REFERENCIA_LABORATORIO


class TestConversorErpJefferson(unittest.TestCase):
    def test_tabela_historica_recuperada(self):
        mapa = carregar_equivalencias()
        self.assertGreaterEqual(len(mapa), 3000)
        self.assertEqual(mapa["42-Z42BA12T"], "Z1342BA12T")
        self.assertEqual(mapa["12BS504"], "2012BS504")

    def test_valvulas_padrao_2026_e_2036(self):
        for raw, descricao, esperado in [
            ("026BA121", "2026 BA121 VALVULA SOLENOIDE", "2026BA121"),
            ("36BA4", "2036 BA04 VALVULA SOLENOIDE", "2036BA04"),
            ("35BA4", "1335 BA04 VALVULA SOLENOIDE", "1335BA04"),
            ("42BT12T", "1342 BT12T VALVULA SOLENOIDE", "1342BT12T"),
        ]:
            with self.subTest(raw=raw):
                resultado = converter(raw, descricao)
                self.assertEqual(resultado.status, "CONFIRMADO")
                self.assertEqual(resultado.codigo_tecnico, esperado)

    def test_prefixos_especiais_tamanho_e_variantes(self):
        exemplos = [
            ("42-Z42BA12T", "Z1342 BA12T VALVULA SOLENOIDE", "Z1342BA12T"),
            ("14-Z14BV8A", "Z1314 BV08A VALVULA SOLENOIDE", "Z1314BV08A"),
            ("12BS504", "2012 BS504 VALVULA SOLENOIDE", "2012BS504"),
            ("3073LH8S", "3073 LH08S VALVULA SOLENOIDE", "3073LH08S"),
        ]
        for raw, desc, esperado in exemplos:
            with self.subTest(raw=raw):
                x = converter(raw, desc)
                self.assertEqual((x.status, x.codigo_tecnico), ("CONFIRMADO", esperado))

    def test_kit_interno_nao_e_valvula(self):
        a = converter("202-0509", "K030 AR2 KIT REPARO")
        b = converter("202-0515", "K30 A02 KIT REPARO 1330")
        self.assertEqual((a.status, a.codigo_tecnico), ("CONFIRMADO", "K030AR2"))
        self.assertEqual((b.status, b.codigo_tecnico), ("CONFIRMADO", "K30A2"))

    def test_nao_aprovar_exposicao_ou_ambiguidade(self):
        self.assertEqual(converter("EXP35BA4", "EXP 1335 BA04 VALVULA").status, "PENDENTE")
        self.assertEqual(converter("12BA4", "VALVULA SOLENOIDE").status, "PENDENTE")
        self.assertEqual(converter("35BA4INA-72", "1335 BA04 INA72 VALVULA SOLENOIDE").status, "DIVERGENTE")
        self.assertNotEqual(converter("35BA4", "").status, "CONFIRMADO")

    def test_inventario_v2_sera_o_consultado(self):
        self.assertEqual(REFERENCIA_LABORATORIO, "ERP_2026-11-03_LAB_TRANSF_v2_CONFERIDO")


if __name__ == "__main__":
    unittest.main()

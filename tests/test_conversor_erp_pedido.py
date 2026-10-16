"""Testes de regressão do conversor ERP -> Jefferson."""
import unittest
from unittest.mock import patch

from core import conversor_erp_pedido as motor
from core.motor_erp_regras import inferir_valvula, categoria


class RegrasTests(unittest.TestCase):
    def test_inferencia_codigo_novo(self):
        self.assertEqual(inferir_valvula("026BN12"), "2026BN12")
        self.assertEqual(inferir_valvula("030-ZC030LV8T"), "ZC2030LV08T")

    def test_familia_12_ambigua(self):
        self.assertEqual(inferir_valvula("12BA04"), "")

    def test_classifica_componentes(self):
        self.assertEqual(categoria("X", "BOBINA 24 VCC"), "BOBINA")
        self.assertEqual(categoria("X", "KIT REPARO"), "KIT")

    def test_sugere_codigo_nunca_visto(self):
        with patch.object(motor, "_mapa", return_value={}):
            x = motor.sugerir_codigo({
                "codigo_erp": "026BN12",
                "descricao_original": "VALVULA SOLENOIDE",
            })
            self.assertEqual(x["codigo_sugerido"], "2026BN12")
            self.assertIn("INFERÊNCIA", x["situacao"])

    def test_historico_ainda_exige_confirmacao(self):
        with patch.object(motor, "_mapa", return_value={
            "ERP1": {"codigo_tecnico_proposto": "2030LA08",
                     "situacao": "REFERENCIA_CODIGO_NAO_AUDITADA",
                     "tipo_provavel": "VALVULA"}}):
            x = motor.sugerir_codigo({"codigo_erp": "ERP1"})
            self.assertEqual(x["codigo_inicial"], "2030LA08")
            self.assertIn("confirmar", x["situacao"])

    def test_descricao_historica_nao_e_codigo(self):
        with patch.object(motor, "_mapa", return_value={
            "ERP2": {"codigo_tecnico_proposto": "VALVULA COM BOBINA",
                     "situacao": "REFERENCIA_DESCRITIVA",
                     "tipo_provavel": "VALVULA"}}):
            x = motor.sugerir_codigo({"codigo_erp": "ERP2"})
            self.assertEqual(x["codigo_inicial"], "ERP2")
            self.assertFalse(x["codigo_sugerido"])

    def test_divergencia_historico_regra_nao_preenche(self):
        with patch.object(motor, "_mapa", return_value={
            "026BN12": {"codigo_tecnico_proposto": "1326BN12",
                        "situacao": "REFERENCIA_CODIGO_NAO_AUDITADA",
                        "tipo_provavel": "VALVULA"}}):
            x = motor.sugerir_codigo({
                "codigo_erp": "026BN12", "descricao_original": "VALVULA"})
            self.assertEqual(x["codigo_inicial"], "026BN12")
            self.assertIn("CONFLITO", x["situacao"])

    def test_divergencia_cadastro_historico_nao_preenche(self):
        with patch.object(motor, "_mapa", return_value={
            "ERP3": {"codigo_tecnico_proposto": "2030LA08",
                     "situacao": "REFERENCIA_CODIGO_NAO_AUDITADA",
                     "tipo_provavel": "VALVULA"}}):
            x = motor.sugerir_codigo({"codigo_erp": "ERP3",
                                      "codigo_tecnico_sugerido": "1330LA08"})
            self.assertEqual(x["codigo_inicial"], "ERP3")
            self.assertIn("CONFLITO", x["situacao"])

    def test_sem_conversao_de_bobina_por_regra_valvula(self):
        with patch.object(motor, "_mapa", return_value={}):
            x = motor.sugerir_codigo({
                "codigo_erp": "026BN12", "descricao_original": "BOBINA 24 VCC"})
            self.assertEqual(x["codigo_inicial"], "026BN12")

    def test_preserva_codigo_especifico_da_linha(self):
        with patch.object(motor, "_mapa", return_value={}):
            x = motor.sugerir_codigo({"codigo_erp": "ERP4",
                                      "codigo_tecnico_sugerido": "Z1335BV06A-I4"})
            self.assertEqual(x["codigo_inicial"], "Z1335BV06A-I4")


if __name__ == "__main__":
    unittest.main()

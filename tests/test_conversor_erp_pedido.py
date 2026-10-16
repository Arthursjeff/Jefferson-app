"""Execute: python -m unittest discover -s tests -p 'test_conversor_erp_pedido.py'"""
import unittest
from unittest.mock import patch
from core import conversor_erp_pedido as motor


class ConversorErpPedidoTests(unittest.TestCase):
    def test_historico_codigo_valvula_nao_auditado(self):
        with patch.object(motor, "_mapa", return_value={
            "ERP1": {"codigo_tecnico_proposto": "2030LA08",
                     "situacao": "REFERENCIA_CODIGO_NAO_AUDITADA",
                     "tipo_provavel": "VALVULA"}}):
            x = motor.sugerir_codigo({"codigo_erp": "ERP1"})
            self.assertEqual(x["codigo_inicial"], "2030LA08")
            self.assertIn("NÃO VALIDADA", x["situacao"])

    def test_descricao_historica_nao_se_torna_codigo(self):
        with patch.object(motor, "_mapa", return_value={
            "ERP2": {"codigo_tecnico_proposto": "VALVULA COM BOBINA",
                     "situacao": "REFERENCIA_DESCRITIVA",
                     "tipo_provavel": "VALVULA"}}):
            x = motor.sugerir_codigo({"codigo_erp": "ERP2"})
            self.assertEqual(x["codigo_inicial"], "ERP2")
            self.assertFalse(x["codigo_sugerido"])

    def test_conflito_nao_prioriza_fontes(self):
        with patch.object(motor, "_mapa", return_value={
            "ERP3": {"codigo_tecnico_proposto": "2030LA08",
                     "situacao": "REFERENCIA_CODIGO_NAO_AUDITADA",
                     "tipo_provavel": "VALVULA"}}):
            x = motor.sugerir_codigo({"codigo_erp": "ERP3",
                                      "codigo_tecnico_sugerido": "1330LA08"})
            self.assertEqual(x["codigo_inicial"], "ERP3")
            self.assertEqual(x["origem_sugestao"], "CONFLITO")

    def test_sugestao_da_linha_preservada(self):
        with patch.object(motor, "_mapa", return_value={}):
            x = motor.sugerir_codigo({"codigo_erp": "ERP4",
                                      "codigo_tecnico_sugerido": "Z1335BV06A-I4"})
            self.assertEqual(x["codigo_inicial"], "Z1335BV06A-I4")

    def test_nao_usa_texto_em_lugar_do_codigo(self):
        with patch.object(motor, "_mapa", return_value={}):
            x = motor.sugerir_codigo({"codigo_erp": "ERP5",
                                      "codigo_tecnico_sugerido": "VALVULA SOLENOIDE"})
            self.assertEqual(x["codigo_inicial"], "ERP5")


if __name__ == "__main__":
    unittest.main()

"""Regressões do bloqueio indevido de documentos com ajustes comerciais."""
import unittest
from core.validacao_importacao_prn import classificar_ocorrencias


class TestValidacaoImportacaoPRN(unittest.TestCase):
    def test_5120_acrescimo_nao_bloqueia(self):
        erros, avisos = classificar_ocorrencias(
            ["Diferença total cabeçalho x soma itens"], "40.05"
        )
        self.assertEqual(erros, [])
        self.assertEqual(len(avisos), 1)
        self.assertIn("R$ 40,05", avisos[0])
        self.assertIn("não discriminada", avisos[0])

    def test_total_abaixo_pode_ser_desconto_sem_bloqueio(self):
        erros, avisos = classificar_ocorrencias(
            ["Diferença total cabeçalho x soma itens"], "-25.00"
        )
        self.assertEqual(erros, [])
        self.assertIn("abaixo", avisos[0])

    def test_erros_reais_continuam_bloqueados(self):
        erros, avisos = classificar_ocorrencias(
            ["Diferença total cabeçalho x soma itens", "Documento sem itens",
             "Diferença quantidade x valor unitário", "Número repetido no PRN"], "40.05"
        )
        self.assertEqual(erros, ["Documento sem itens", "Diferença quantidade x valor unitário",
                                "Número repetido no PRN"])
        self.assertEqual(len(avisos), 1)

    def test_tolerancia_arredondamento(self):
        erros, avisos = classificar_ocorrencias([], "0.02")
        self.assertEqual((erros, avisos), ([], []))

    def test_codigo_tecnico_fica_em_aviso(self):
        erros, avisos = classificar_ocorrencias(["Código técnico não reconhecido"], "0.00")
        self.assertEqual(erros, [])
        self.assertEqual(avisos, ["Código técnico não reconhecido (ERP preservado)"])


if __name__ == "__main__":
    unittest.main()

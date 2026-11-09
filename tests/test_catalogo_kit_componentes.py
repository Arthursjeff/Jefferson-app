"""Regressões: kit montado de peças e proposta de troca sem movimentar estoque."""
import unittest

from core.catalogo_kit_componentes import (
    preparar_proposta_componentes, eh_referencia_pendente,
    pode_homologar_composicao, _quantidade, codigo_provisorio,
)


def linha(codigo="DIAF123", grupo="G2", tipo="COMPONENTE",
          descricao="Diafragma NBR", quantidade=1):
    return {"codigo": codigo, "grupo": grupo, "tipo": tipo,
            "descricao": descricao, "quantidade": quantidade}


class TestCatalogoKitComponentes(unittest.TestCase):
    def test_montagem_kit_multiplas_pecas_sem_valvula_base(self):
        dados = preparar_proposta_componentes(
            "MONTAR_KIT", "K030AR2", "", [
                linha("G2-DIAF", descricao="Diafragma Buna"),
                linha("G2-REFORCO", descricao="Reforço"),
                linha("G5-ANEL", grupo="G5", descricao="O-ring NBR", quantidade=2),
            ], "joao", "Montagem do kit pela composição conhecida no setor.",
        )
        self.assertEqual(dados["estado"], "PENDENTE")
        self.assertEqual(dados["grau"], "KIT_REPARO")
        self.assertEqual(dados["subtipo"], "MONTAGEM_COMPONENTES")
        self.assertEqual(dados["produto_final"], "K030AR2")
        self.assertEqual(dados["familia"], "2030")
        self.assertEqual(len(dados["entradas"]), 3)
        self.assertEqual(dados["saidas"], [
            {"papel": "PRODUTO", "codigo": "K030AR2", "quantidade": 1}
        ])
        self.assertEqual(dados["total_validacoes"], 0)
        self.assertIsNone(dados["validada_por"])
        self.assertEqual(dados["parametros_tecnicos"]["codigos_sem_erp"], [])
        liberado, _ = pode_homologar_composicao(dados)
        self.assertTrue(liberado)

    def test_sem_codigo_erp_guarda_proposta_mas_bloqueia_homologacao(self):
        dados = preparar_proposta_componentes(
            "MONTAR_KIT", "K030A2", "", [
                linha("", descricao="Diafragma NBR 2 polegadas"),
                linha("", grupo="G4", tipo="CARRETEL", descricao="Carretel NF Buna"),
            ], "marco", "Composição conhecida da montagem, códigos ERP a identificar.",
        )
        self.assertTrue(all(eh_referencia_pendente(x["codigo"]) for x in dados["entradas"]))
        self.assertEqual(len(dados["parametros_tecnicos"]["codigos_sem_erp"]), 2)
        self.assertEqual(dados["entradas"][1]["papel"], "CARRETEL")
        liberado, motivo = pode_homologar_composicao(dados)
        self.assertFalse(liberado)
        self.assertIn("sem código ERP", motivo)
        self.assertEqual(
            codigo_provisorio("G2", "Diafragma NBR 2 polegadas"),
            codigo_provisorio("G2", "Diafragma NBR 2 polegadas"),
        )

    def test_transformacao_valvula_com_kit_e_carretel_e_residual(self):
        dados = preparar_proposta_componentes(
            "ALTERAR_VALVULA", "2030LAR12", "2030LA12", [
                linha("K030AR2", grupo="G2", tipo="KIT", descricao="Kit reforçado"),
                linha("202-0701", grupo="G4", tipo="CARRETEL", descricao="Carretel NA"),
            ], "ricardo", "Troca de reparo e carretel conforme conjunto físico.",
            residual="2030LA12NA", destino_residual="RETORNO_IDENTIFICADO",
        )
        self.assertEqual(dados["subtipo"], "ADAPTACAO_COMPONENTES")
        self.assertEqual(dados["entradas"][0]["papel"], "BASE")
        self.assertEqual(dados["entradas"][1]["papel"], "KIT")
        self.assertEqual(dados["entradas"][2]["papel"], "CARRETEL")
        self.assertEqual(dados["saidas"][1]["codigo"], "2030LA12NA")
        self.assertEqual(dados["parametros_tecnicos"]["destino_residual"], "RETORNO_IDENTIFICADO")

    def test_quantidades_e_informacoes_invalidas(self):
        with self.assertRaises(ValueError):
            _quantidade(0)
        with self.assertRaises(ValueError):
            _quantidade("1.1234")
        with self.assertRaises(ValueError):
            preparar_proposta_componentes(
                "MONTAR_KIT", "K030A2", "", [linha("", descricao="")], "joao",
                "Justificativa técnica informada.",
            )
        with self.assertRaises(ValueError):
            preparar_proposta_componentes(
                "MONTAR_KIT", "K030A2", "2030LA12", [linha()], "joao",
                "Justificativa técnica informada.",
            )
        with self.assertRaises(ValueError):
            preparar_proposta_componentes(
                "ALTERAR_VALVULA", "2030LA12", "", [linha()], "joao",
                "Justificativa técnica informada.",
            )

    def test_receita_pendente_mesma_composicao_assinatura_estavel(self):
        args = ("MONTAR_KIT", "K030AR2", "", [
            linha("G2-DIAF", descricao="Diafragma Buna"),
            linha("G5-ANEL", grupo="G5", descricao="O-ring"),
        ])
        x = preparar_proposta_componentes(*args, "joao", "Montagem conforme conjunto.")
        y = preparar_proposta_componentes(*args, "marco", "Montagem conforme conjunto.")
        self.assertEqual(x["assinatura"], y["assinatura"])
        self.assertEqual(x["parametros_tecnicos"], y["parametros_tecnicos"])


if __name__ == "__main__":
    unittest.main()

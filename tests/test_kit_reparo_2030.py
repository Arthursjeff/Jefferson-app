import unittest
from core.transformacoes_kit_2030 import (
    parse, montar, avaliar, calcular_residual, conjunto_igual
)
from core.motor_transformacoes import avaliar as avaliar_antigo


class TestKit2030(unittest.TestCase):
    def test_escopo_e_na_nao_ina(self):
        for codigo in ("2030LA12", "2030LV16T", "2030LAR10NA", "2030LVD10",
                       "2030LAR16T", "2030LA16NAT", "2030LVR12NA"):
            self.assertIsNotNone(parse(codigo), codigo)
        for codigo in ("2030LA10", "2030LAD12", "2030LV12INA", "2030LA08",
                       "1342BV08", "2030LV20", "2030LAR16NA-I4"):
            self.assertIsNone(parse(codigo), codigo)
        self.assertEqual(montar(parse("2030LA12"), na=True), "2030LA12NA")
        self.assertEqual(montar(parse("2030LA16NAT"), na=False), "2030LA16T")

    def test_na_nf_buna_com_carretel_avulso_e_residual(self):
        estoque = {"2030LA12": 1, "CAR-NA-ERP": 2}
        mapa = {"NA": "CAR-NA-ERP", "NF": "CAR-NF-ERP"}
        r = avaliar("2030LA12NA", "NA_NF", estoque, mapa)
        self.assertEqual(r["status"], "SIMULACAO_POSSIVEL")
        self.assertEqual(r["codigo_base_esperado"], "2030LA12")
        self.assertEqual(r["doadores"][0]["codigo"], "CAR-NA-ERP")
        p = calcular_residual(r, "2030LA12", "CAR-NA-ERP", mapa)
        self.assertEqual(p["produto_residual"], "CAR-NF-ERP")
        self.assertEqual(p["tipo_residual"], "CARRETEL")
        self.assertEqual(avaliar("2030LA12NA", "NA_NF", estoque)["doadores"], [])
        with self.assertRaises(ValueError):
            calcular_residual(r, "2030LA12", "CAR-NA-ERP", {"NA": "CAR-NA-ERP"})

    def test_na_nf_viton_doadora_valvula_residual(self):
        estoque = {"2030LV12": 1, "2030LVR16NA": 2, "2030LAR12NA": 3}
        r = avaliar("2030LV12NA", "NA_NF", estoque)
        self.assertEqual(r["status"], "SIMULACAO_POSSIVEL")
        self.assertEqual([x["codigo"] for x in r["doadores"]], ["2030LVR16NA"])
        p = calcular_residual(r, "2030LV12", "2030LVR16NA")
        self.assertEqual(p["produto_residual"], "2030LVR16")

    def test_vedacao_varias_bases_mesmo_corpo(self):
        estoque = {"2030LA16T": 2, "2030LV16NAT": 1,
                   "2030LAR16T": 1, "2030LA16": 9,
                   "2030LV16": 7, "2030LV12NA": 1}
        r = avaliar("2030LV16T", "VEDACAO", estoque)
        self.assertEqual({x["codigo"] for x in r["base"]},
                         {"2030LA16T", "2030LV16NAT", "2030LAR16T"})
        self.assertIn("2030LV16", {x["codigo"] for x in r["doadores"]})
        p = calcular_residual(r, "2030LA16T", "2030LV16")
        self.assertEqual(p["produto_residual"], "2030LA16")

    def test_vedacao_respeita_reforco_e_na(self):
        estoque = {"2030LVR12": 1, "2030LAR16NA": 3,
                   "2030LAR16": 2, "2030LA16": 10,
                   "2030LAR12": 2}
        r = avaliar("2030LAR12", "VEDACAO", estoque)
        self.assertEqual(r["status"], "SIMULACAO_POSSIVEL")
        self.assertEqual({x["codigo"] for x in r["doadores"]},
                         {"2030LAR16"})
        p = calcular_residual(r, "2030LVR12", "2030LAR16")
        self.assertEqual(p["produto_residual"], "2030LVR16")
        self.assertFalse(conjunto_igual(parse("2030LAR12"), parse("2030LAR16NA")))

    def test_vedacao_residual_variante_invalida_bloqueado(self):
        estoque = {"2030LAD10": 1, "2030LAR16": 1}
        r = avaliar("2030LAR10", "VEDACAO", estoque)
        self.assertEqual(r["status"], "SIMULACAO_POSSIVEL")
        with self.assertRaises(ValueError):
            calcular_residual(r, "2030LAD10", "2030LAR16")

    def test_reforco_duas_direcoes(self):
        estoque = {"2030LV16": 2, "K030VR2": 1,
                   "2030LVR16": 2, "K030V2": 3}
        a = avaliar("2030LVR16", "REFORCO", estoque)
        self.assertEqual(a["status"], "SIMULACAO_POSSIVEL")
        self.assertEqual(a["codigo_kit_esperado"], "K030VR2")
        self.assertEqual(calcular_residual(a, "2030LV16", "K030VR2")["produto_residual"],
                         "K030V2")
        b = avaliar("2030LV16", "REFORCO", estoque)
        self.assertEqual(b["codigo_kit_esperado"], "K030V2")
        self.assertEqual(calcular_residual(b, "2030LVR16", "K030V2")["produto_residual"],
                         "K030VR2")

    def test_reforco_d_sem_regra(self):
        r = avaliar("2030LAD10", "REFORCO",
                    {"2030LAR10": 1, "K030A2": 2})
        self.assertEqual(r["status"], "EM ESTUDO")
        self.assertTrue(r["pendencias"])

    def test_corpo_torre_inalterados(self):
        r = avaliar_antigo("1342BV08T", "CORPO", "VALVULA_VALVULA", {"1342BV08": 2})
        self.assertEqual(r["codigo_base_esperado"], "1342BV08")


if __name__ == "__main__":
    unittest.main()

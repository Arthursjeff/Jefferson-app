import unittest
from core.transformacoes_kit_2030 import parse, avaliar, calcular_residual
from components.internos.carretel import identificar_conjunto_carretel

class TestKit1330(unittest.TestCase):
    def test_escopo_uma_polegada(self):
        for codigo in ("1330LA10", "1330LV10NA", "1330LAR10T", "1330LVR10NAT"):
            self.assertIsNotNone(parse(codigo), codigo)
        for codigo in ("1330LA08", "1330LA12", "1330LAD10", "1330LA16"):
            self.assertIsNone(parse(codigo), codigo)

    def test_carretel_compartilhado_g4(self):
        self.assertEqual(
            identificar_conjunto_carretel("1330", "NA")["identidade"],
            identificar_conjunto_carretel("2030", "NA")["identidade"],
        )

    def test_1330_na_nf_buna_carretel_e_residual(self):
        estoque = {"1330LA10": 2, "CAR-NA": 1}
        m = {"NA": "CAR-NA", "NF": "CAR-NF"}
        r = avaliar("1330LA10NA", "NA_NF", estoque, m)
        self.assertEqual(r["status"], "SIMULACAO_POSSIVEL")
        self.assertEqual(r["codigo_base_esperado"], "1330LA10")
        self.assertEqual(calcular_residual(r, "1330LA10", "CAR-NA", m)["produto_residual"],
                         "CAR-NF")

    def test_viton_carretel_entre_1330_e_2030(self):
        estoque = {"1330LV10": 1, "2030LV16NA": 1, "1330LA10NA": 8}
        r = avaliar("1330LV10NA", "NA_NF", estoque)
        self.assertEqual([d["codigo"] for d in r["doadores"]], ["2030LV16NA"])
        self.assertEqual(
            calcular_residual(r, "1330LV10", "2030LV16NA")["produto_residual"],
            "2030LV16",
        )

    def test_vedacao_1330_multiplas_bases_e_doadora_reforcada(self):
        estoque = {"1330LVR10": 1, "1330LAR10NA": 2,
                   "1330LAR10T": 2, "1330LA10": 10
        r = avaliar("1330LAR10", "VEDACAO", estoque)
        self.assertEqual({x["codigo"] for x in r["base"]},
                         {"1330LVR10", "1330LAR10NA", "1330LA10"})
        self.assertEqual({x["codigo"] for x in r["doadores"]}, {"1330LAR10T"})
        self.assertEqual(
            calcular_residual(r, "1330LVR10", "1330LAR10T")["produto_residual"],
            "1330LVR10T",
        )

    def test_vedacao_nao_aceita_conjunto_sem_reforco(self):
        r = avaliar("1330LVR10", "VEDACAO",
                    {"1330LAR10": 2, "1330LV10": 5})
        self.assertNotIn("1330LV10", {x["codigo"] for x in r["doadores"]})

    def test_reforco_bidirecional_1330_k30_nao_k030(self):
        estoque = {"1330LV10": 2, "1330LVR10": 1,
                   "K30VR2": 1, "K30V2": 1, "K030VR2": 5}
        r = avaliar("1330LVR10", "REFORCO", estoque)
        self.assertEqual(r["codigo_kit_esperado"], "K30VR2")
        self.assertEqual(calcular_residual(r, "1330LV10", "K30VR2")["produto_residual"],
                         "K30V2")
        r2 = avaliar("1330LV10", "REFORCO", estoque)
        self.assertEqual(r2["codigo_kit_esperado"], "K30V2")
        self.assertEqual(calcular_residual(r2, "1330LVR10", "K30V2")["produto_residual"],
                         "K30VR2")
        self.assertEqual([x["codigo"] for x in r["doadores"]], ["K30VR2"])

    def test_isolamento_base_1330_2030(self):
        r = avaliar("1330LA10NA", "NA_NF", {"2030LAR10": 5, "CAR-NA": 2},
                    {"NA": "CAR-NA", "NF": "CAR-NF"})
        self.assertFalse(r["base"])

if __name__ == "__main__":
    unittest.main()

import unittest
from components.internos.torre import identificar_sistema_torre, identificar_conjunto_torre, FAMILIAS_SISTEMA_GENERICO
from components.internos.regras_g1 import resolver_g1
from core.motor_transformacoes import avaliar, calcular_residual_torre, diagnosticar_componentes_torre


class TestTorreG1(unittest.TestCase):
    def test_1335_exclusiva_em_ambos_materiais(self):
        self.assertNotIn("1335", FAMILIAS_SISTEMA_GENERICO)
        for material in ("LATAO", "INOX"):
            s = identificar_sistema_torre("1335", material)
            self.assertEqual(s["tipo"], "EXCLUSIVO_FAMILIA")
            self.assertEqual(s["grupo"], "1335")
            for construcao in ("REGULAR", "Z", "INA", "Z INA"):
                g = resolver_g1("1335", material, construcao=construcao)
                self.assertEqual(g["torre_externa"]["grupo"], "1335")
                self.assertEqual(g["torre_externa"]["material"], material)
                self.assertTrue(g["torre_externa"]["fora_kit_reparo"])

    def test_standard_1327_1342_compartilha_grupo(self):
        self.assertEqual(identificar_sistema_torre("1327", "LATAO")["grupo"],
                         identificar_sistema_torre("1342", "LATAO")["grupo"])

    def test_prioridade_mesma_familia_depois_1327(self):
        estoque = {
            "1342BV08": 1, "Z1342BV10": 2, "Z1327BV04": 10,
            "Z1342BA10": 30, "Z1342IV10": 50,
            "Z1335BV08": 100,
        }
        r = avaliar("Z1342BV08", "TORRE", "VALVULA_VALVULA", estoque)
        self.assertEqual(r["status"], "SIMULACAO_POSSIVEL")
        self.assertEqual(r["base"][0]["codigo"], "1342BV08")
        self.assertEqual([(x["codigo"], x["prioridade"]) for x in r["doadores"]],
                         [("Z1342BV10", 1), ("Z1327BV04", 2)])
        self.assertEqual([x["codigo"] for x in r["doadores_combinadas"]],
                         ["Z1342BA10"])
        self.assertEqual(calcular_residual_torre(r, "Z1342BV10")["produto_residual"],
                         "1342BV10")

    def test_1335_somente_doadora_da_propria_familia(self):
        estoque = {
            "1335BV04": 1, "Z1335BV06": 1,
            "Z1342BV08": 4, "Z1327BV04": 9,
        }
        r = avaliar("Z1335BV04", "TORRE", "VALVULA_VALVULA", estoque)
        self.assertEqual([x["codigo"] for x in r["doadores"]], ["Z1335BV06"])
        self.assertEqual(r["grupo_torre"], "1335")

    def test_z_ina_nao_equivale_a_z_simples(self):
        estoque = {"1335BV04INA": 1, "Z1335BV06INA": 3,
                   "Z1335BV06": 10}
        r = avaliar("Z1335BV04INA", "TORRE", "VALVULA_VALVULA", estoque)
        self.assertEqual([x["codigo"] for x in r["doadores"]], ["Z1335BV06INA"])
        self.assertEqual(r["codigo_base_esperado"], "1335BV04")

    def test_sem_combinada_como_transformacao_simples(self):
        estoque = {"1342BV08": 1, "Z1342BA10": 2}
        r = avaliar("Z1342BV08", "TORRE", "VALVULA_VALVULA", estoque)
        self.assertFalse(r["doadores"])
        self.assertEqual(len(r["doadores_combinadas"]), 1)
        with self.assertRaises(ValueError):
            calcular_residual_torre(r, "Z1342BA10")


    def test_diagnostico_g1_nao_homologa_componentes_internos(self):
        saldo = {"1342BV08": 1, "Z1342BV10": 1}
        r = avaliar("Z1342BV08", "TORRE", "VALVULA_VALVULA", saldo)
        diag = diagnosticar_componentes_torre(r, "Z1342BV10")
        self.assertEqual(diag["status_engenharia"], "PENDENTE_HOMOLOGACAO_G1")
        self.assertEqual(diag["torre_externa"], "IDENTIDADE_LOGICA_COINCIDENTE")
        self.assertEqual(diag["produto_residual_previsto"], "1342BV10")
        nomes = {x["componente"] for x in diag["componentes_internos"]}
        self.assertTrue({"nucleo_movel", "assento", "mola_nucleo"} <= nomes)
        self.assertTrue(all(x["requer_conferencia"] for x in diag["componentes_internos"]))

    def test_diagnostico_z_ina_aponta_conferencia_obrigatoria(self):
        saldo = {"1335BV04": 1, "Z1335BV06INA": 2}
        r = avaliar("Z1335BV04INA", "TORRE", "VALVULA_VALVULA", saldo)
        self.assertEqual(r["status"], "SIMULACAO_POSSIVEL")
        diag = diagnosticar_componentes_torre(r, "Z1335BV06INA")
        self.assertTrue(diag["envolve_ina"])
        self.assertEqual(diag["construcao_destino"], "Z_INA")
        self.assertEqual(diag["produto_residual_previsto"], "1335BV06")
        self.assertTrue(any(x["base_destino_diferente"]
                            for x in diag["componentes_internos"]))

    def test_diagnostico_rejeita_origem_nao_validada(self):
        saldo = {"1342BV08": 1, "Z1342BV10": 1}
        r = avaliar("Z1342BV08", "TORRE", "VALVULA_VALVULA", saldo)
        with self.assertRaises(ValueError):
            diagnosticar_componentes_torre(r, "Z1335BV08")


if __name__ == "__main__":
    unittest.main()

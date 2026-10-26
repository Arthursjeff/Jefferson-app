import unittest
from components.internos.torre import identificar_sistema_torre, identificar_conjunto_torre, FAMILIAS_SISTEMA_GENERICO
from components.internos.regras_g1 import resolver_g1
from core.motor_transformacoes import avaliar, calcular_residual_torre, diagnosticar_componentes_torre, _g1_normalizar_identidade


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


    def test_troca_integral_g1_mesma_familia(self):
        saldo = {"1342BV08": 1, "Z1342BV10": 1}
        r = avaliar("Z1342BV08", "TORRE", "VALVULA_VALVULA", saldo)
        diag = diagnosticar_componentes_torre(r, "Z1342BV10")
        self.assertEqual(diag["tipo_troca"], "CONJUNTO_G1_COMPLETO")
        self.assertEqual(diag["status_engenharia"], "COMPATIVEL_G1")
        self.assertEqual(diag["divergencias"], [])
        self.assertEqual(diag["produto_residual_previsto"], "1342BV10")

    def test_troca_integral_z_ina(self):
        saldo = {"1335BV04": 1, "Z1335BV06INA": 2}
        r = avaliar("Z1335BV04INA", "TORRE", "VALVULA_VALVULA", saldo)
        diag = diagnosticar_componentes_torre(r, "Z1335BV06INA")
        self.assertTrue(diag["envolve_ina"])
        self.assertEqual(diag["construcao_destino"], "Z_INA")
        self.assertEqual(diag["status_engenharia"], "COMPATIVEL_G1")

    def test_diagnostico_rejeita_origem_nao_validada(self):
        saldo = {"1342BV08": 1, "Z1342BV10": 1}
        r = avaliar("Z1342BV08", "TORRE", "VALVULA_VALVULA", saldo)
        with self.assertRaises(ValueError):
            diagnosticar_componentes_torre(r, "Z1335BV08")

    def test_familias_genericas_1327_1342_sao_realmente_permutaveis(self):
        saldo = {"1342BV08": 1, "Z1327BV04": 2}
        r = avaliar("Z1342BV08", "TORRE", "VALVULA_VALVULA", saldo)
        self.assertEqual(r["status"], "SIMULACAO_POSSIVEL")
        self.assertEqual([v["codigo"] for v in r["doadores"]], ["Z1327BV04"])
        d = diagnosticar_componentes_torre(r, "Z1327BV04")
        self.assertEqual(d["status_engenharia"], "COMPATIVEL_G1")
        self.assertEqual(d["produto_residual_previsto"], "1327BV04")

    def test_retirar_z_por_permuta_integral(self):
        saldo = {"Z1342BV08": 1, "1342BV10": 1}
        r = avaliar("1342BV08", "TORRE", "VALVULA_VALVULA", saldo)
        self.assertEqual(r["status"], "SIMULACAO_POSSIVEL")
        d = calcular_residual_torre(r, "1342BV10")
        self.assertEqual(d["valvula_base"], "Z1342BV08")
        self.assertEqual(d["produto_residual"], "Z1342BV10")

    def test_substituir_ina_por_z_sem_desmontar_g1(self):
        saldo = {"1342BV08INA": 1, "Z1342BV10": 1}
        r = avaliar("Z1342BV08", "TORRE", "VALVULA_VALVULA", saldo)
        self.assertEqual(r["status"], "SIMULACAO_POSSIVEL")
        d = calcular_residual_torre(r, "Z1342BV10", "1342BV08INA")
        self.assertEqual(d["produto_residual"], "1342BV10INA")

    def test_diferentes_bases_podem_ser_selecionadas(self):
        saldo = {"1342BV08": 1, "1342BV08INA": 1, "Z1342BV10": 1}
        r = avaliar("Z1342BV08", "TORRE", "VALVULA_VALVULA", saldo)
        self.assertEqual(len(r["base"]), 2)
        self.assertEqual(len(r["doadores"][0]["bases_compativeis"]), 2)
        self.assertEqual(calcular_residual_torre(r, "Z1342BV10")["produto_residual"], "1342BV10")
        self.assertEqual(calcular_residual_torre(r, "Z1342BV10", "1342BV08INA")["produto_residual"], "1342BV10INA")

    def test_303_e_304_sao_a_unica_excecao_de_material(self):
        mola_303 = {"grupo": "GENERICO", "construcao": "Z", "material": "INOX 303"}
        mola_304 = dict(mola_303, material="INOX 304")
        self.assertEqual(_g1_normalizar_identidade("mola_nucleo", mola_303),
                         _g1_normalizar_identidade("mola_nucleo", mola_304))
        self.assertNotEqual(_g1_normalizar_identidade("nucleo_movel", mola_303),
                            _g1_normalizar_identidade("nucleo_movel", mola_304))
        self.assertNotEqual(_g1_normalizar_identidade("mola_nucleo", mola_303),
                            _g1_normalizar_identidade("mola_nucleo",
                                                       dict(mola_303, material="INOX 316")))

    def test_1335_final_especial_distingue_nucleo_e_assento(self):
        normal = resolver_g1("1335", "LATAO", construcao="Z", vedacao="V", final=None)
        especial = resolver_g1("1335", "LATAO", construcao="Z", vedacao="V", final="A")
        self.assertEqual(normal["torre_externa"], especial["torre_externa"])
        self.assertNotEqual(normal["componentes_internos"]["nucleo_movel"],
                            especial["componentes_internos"]["nucleo_movel"])
        self.assertNotEqual(normal["componentes_internos"]["assento"],
                            especial["componentes_internos"]["assento"])

    def test_1323_nao_troca_finais_distintos(self):
        saldo = {"1323BV04D": 1, "Z1323BV06U": 1}
        r = avaliar("Z1323BV04D", "TORRE", "VALVULA_VALVULA", saldo)
        self.assertEqual(r["status"], "BASE_LOCALIZADA")
        self.assertEqual(r["doadores"], [])

    def test_nao_cruza_materiais_de_torre_externa(self):
        saldo = {"1342IV08": 1, "Z1342BV10": 1}
        r = avaliar("Z1342IV08", "TORRE", "VALVULA_VALVULA", saldo)
        self.assertEqual(r["status"], "BASE_LOCALIZADA")
        self.assertEqual(r["doadores"], [])

    def test_1390_inox_exclusiva_nao_eh_generica(self):
        saldo = {"1342IV08": 1, "Z1390IV10": 1}
        r = avaliar("Z1342IV08", "TORRE", "VALVULA_VALVULA", saldo)
        self.assertEqual(r["doadores"], [])


if __name__ == "__main__":
    unittest.main()

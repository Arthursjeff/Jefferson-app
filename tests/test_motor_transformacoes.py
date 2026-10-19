import unittest
from core.motor_transformacoes import normalizar, consolidar_estoque, avaliar, corpo_oposto, chave_corpo, localizar_doadores_corpo


class TestLaboratorioTransformacoes(unittest.TestCase):
    def test_normalizacao_sem_mudar_componente(self):
        self.assertEqual(normalizar("Z-1335 BE 04"), "Z1335BE04")
        self.assertEqual(normalizar("ZC1335BA04-I4"), "ZC1335BA04-I4")
        self.assertEqual(normalizar("1335BA04-72"), "1335BA04-72")

    def test_estoque_com_series_agrupadas(self):
        saldo, series, invalidos = consolidar_estoque([
            {"codigo": "1335BE04", "quantidade": 2, "numero_serie": "A"},
            {"codigo": "1335BE04", "quantidade": 3, "numero_serie": "B"},
            {"codigo": "Z1335BE04", "quantidade": -2},
        ])
        self.assertEqual(saldo["1335BE04"], 5)
        self.assertEqual(len(series["1335BE04"]), 2)
        self.assertEqual(invalidos, [3])

    def test_base_sem_z_localizada_sem_doadores_homologados(self):
        saldo = {"1335BE04": 5, "Z1335BA04": 2}
        r = avaliar("Z1335BE04", "TORRE", "VALVULA_VALVULA", saldo)
        self.assertEqual(r["base"][0]["codigo"], "1335BE04")
        self.assertFalse(r["doadores"])
        self.assertEqual(r["status"], "BASE_LOCALIZADA")

    def test_doador_so_quando_regra_explicita(self):
        regras = {"1335": {"torre": {
            "base_sem_z": True, "doadores_confirmados": ["Z1335BA04"]}}}
        r = avaliar("Z1335BE04", "TORRE", "VALVULA_VALVULA",
                    {"1335BE04": 3, "Z1335BA04": 2}, regras)
        self.assertEqual(r["status"], "SIMULACAO_POSSIVEL")

    def test_corpo_bsp_busca_base_npt(self):
        r = avaliar("1342BV08", "CORPO", "VALVULA_VALVULA",
                    {"1342BV08T": 7})
        self.assertEqual(r["base"][0]["codigo"], "1342BV08T")
        self.assertEqual(r["conexao_destino"], "BSP")
        self.assertEqual(r["conexao_base"], "NPT")
        self.assertEqual(r["status"], "BASE_LOCALIZADA")

    def test_corpo_npt_busca_base_bsp(self):
        r = avaliar("1342BV08T", "CORPO", "VALVULA_VALVULA",
                    {"1342BV08": 2})
        self.assertEqual(r["base"][0]["codigo"], "1342BV08")
        self.assertEqual(r["conexao_destino"], "NPT")

    def test_corpo_preserva_torre_e_indicador(self):
        self.assertEqual(corpo_oposto("Z1335BE04TINA"),
                         ("NPT", "BSP", "Z1335BE04INA"))
        self.assertEqual(corpo_oposto("Z1335BE04INA"),
                         ("BSP", "NPT", "Z1335BE04TINA"))

    def test_doadores_mesma_familia_tamanho_rosca(self):
        estoque = {
            "1342BV08": 4, "1342BA08T": 3,
            "1342BV08TINA": 2, "1342BE08T": 7,
            "1342BE06T": 10, "1335BE08T": 20,
        }
        r = avaliar("1342BV08T", "CORPO", "VALVULA_VALVULA", estoque)
        self.assertEqual(r["base"][0]["codigo"], "1342BV08")
        self.assertEqual({v["codigo"] for v in r["doadores"]},
                         {"1342BA08T", "1342BV08TINA", "1342BE08T"})
        self.assertEqual(r["status"], "SIMULACAO_POSSIVEL")
        self.assertEqual(r["doadores"][0]["codigo"], "1342BE08T")

    def test_doadores_no_sentido_npt_para_bsp(self):
        r = avaliar("1342BV08", "CORPO", "VALVULA_VALVULA",
                    {"1342BV08T": 1, "1342BE08": 2, "1342BE08T": 3})
        self.assertEqual(r["base"][0]["codigo"], "1342BV08T")
        self.assertEqual([x["codigo"] for x in r["doadores"]], ["1342BE08"])

    def test_formato_desconhecido_nao_e_doador(self):
        self.assertIsNone(chave_corpo("1342BE08B"))
        self.assertEqual(localizar_doadores_corpo("1342BV08T",
                                                  {"1342BE08B": 5}), [])

    def test_corpo_nao_inventa_para_codigos_ambiguos(self):
        self.assertIsNone(corpo_oposto("Z1335BE04B"))
        self.assertIsNone(corpo_oposto("SEM_FAMILIA"))
        r = avaliar("1342BV08T", "CORPO", "VALVULA_VALVULA", {})
        self.assertFalse(r["base"])
        self.assertEqual(r["codigo_base_esperado"], "1342BV08")

    def test_sem_regras_vedacao_nao_inventa_compatibilidade(self):
        r = avaliar("Z1335BE04", "VEDACAO", "VALVULA_KIT",
                    {"Z1335BA04": 4})
        self.assertFalse(r["doadores"])
        self.assertIn("ainda não cadastrada", " ".join(r["pendencias"]))


if __name__ == "__main__":
    unittest.main()

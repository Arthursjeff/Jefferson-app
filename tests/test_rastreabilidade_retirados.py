"""Regressões da pesquisa de rastreabilidade em Retirados (sem banco real)."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch


class BancoFalso:
    def __init__(self, itens=None, series=None):
        self.dados = {
            "fila_pedido_itens": itens or [],
            "fila_pedido_series": series or [],
        }
        self.consultas = []

    def table(self, tabela):
        banco = self

        class Consulta:
            def select(self, colunas):
                self.colunas = colunas
                return self

            def in_(self, coluna, valores):
                self.coluna = coluna
                self.valores = list(valores)
                return self

            def order(self, coluna):
                self.ordem = coluna
                return self

            def execute(self):
                banco.consultas.append((tabela, self.coluna, list(self.valores)))
                registros = [item for item in banco.dados[tabela]
                             if item[self.coluna] in self.valores]
                return SimpleNamespace(data=registros)

        return Consulta()


class TestRastreabilidadeRetirados(unittest.TestCase):
    def test_series_multiplas_sem_numero_e_historico_legado(self):
        from modules.modulo_01.rastreabilidade import consultar_rastreabilidade_pedidos
        itens = [
            {"id": 11, "pedido_id": 1, "ordem": 1, "codigo": "1342BA12",
             "tensao": "24 Vcc", "quantidade": 3},
            {"id": 12, "pedido_id": 2, "ordem": 1, "codigo": "BOBINA",
             "tensao": None, "quantidade": 4},
            {"id": 13, "pedido_id": 3, "ordem": 1, "codigo": "2030",
             "tensao": None, "quantidade": 1},
        ]
        series = [
            {"pedido_item_id": 11, "numero_serie": "0012", "sem_numero": False, "quantidade": 1},
            {"pedido_item_id": 11, "numero_serie": "0013", "sem_numero": False, "quantidade": 2},
            {"pedido_item_id": 12, "numero_serie": None, "sem_numero": True, "quantidade": 4},
        ]
        banco = BancoFalso(itens, series)
        with patch("modules.modulo_01.rastreabilidade.supabase", banco):
            resultado = consultar_rastreabilidade_pedidos([1, 2, 3, 4, 1])

        self.assertEqual(len(resultado[1]), 2)
        self.assertEqual([r["Número de série"] for r in resultado[1]], ["0012", "0013"])
        self.assertEqual([r["Qtd. série"] for r in resultado[1]], ["1", "2"])
        self.assertEqual(resultado[1][0]["Qtd. item"], "3")
        self.assertEqual(resultado[2][0]["Número de série"], "Sem número de série")
        self.assertEqual(resultado[2][0]["Qtd. série"], "4")
        self.assertEqual(resultado[3][0]["Número de série"], "Não registrado")
        self.assertEqual(resultado[4], [])
        self.assertEqual(len(banco.consultas), 2)

    def test_lista_vazia_nao_consulta_banco(self):
        from modules.modulo_01.rastreabilidade import consultar_rastreabilidade_pedidos
        banco = BancoFalso()
        with patch("modules.modulo_01.rastreabilidade.supabase", banco):
            self.assertEqual(consultar_rastreabilidade_pedidos([]), {})
        self.assertEqual(banco.consultas, [])

    def test_consulta_em_lotes_para_muitos_pedidos(self):
        from modules.modulo_01.rastreabilidade import consultar_rastreabilidade_pedidos
        itens = [{"id": i + 1000, "pedido_id": i, "ordem": 1,
                  "codigo": "TESTE", "tensao": None, "quantidade": 1}
                 for i in range(1, 402)]
        banco = BancoFalso(itens)
        with patch("modules.modulo_01.rastreabilidade.supabase", banco):
            resultado = consultar_rastreabilidade_pedidos(range(1, 402))
        self.assertEqual(len(resultado), 401)
        self.assertEqual(len(banco.consultas), 6)
        self.assertTrue(all(len(ids) <= 200 for _, _, ids in banco.consultas))


if __name__ == "__main__":
    unittest.main()

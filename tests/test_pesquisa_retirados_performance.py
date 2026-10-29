"""Testes da busca de retirados: consultas leves e filtro de movimentações."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch


class QueryFalsa:
    def __init__(self, registros):
        self.registros = registros
        self.filtros = []
        self.intervalos = []
        self.campos = None

    def select(self, campos):
        self.campos = campos
        return self

    def eq(self, nome, valor):
        self.filtros.append((nome, valor))
        return self

    def in_(self, nome, valores):
        self.filtros.append((nome, list(valores)))
        return self

    def order(self, *args, **kwargs):
        return self

    def range(self, inicio, fim):
        self.intervalos.append((inicio, fim))
        self.inicio = inicio
        self.fim = fim
        return self

    def execute(self):
        registros = self.registros
        for campo, valor in self.filtros:
            if isinstance(valor, list):
                registros = [r for r in registros if r[campo] in valor]
            else:
                registros = [r for r in registros if r[campo] == valor]
        if hasattr(self, "inicio"):
            registros = registros[self.inicio:self.fim+1]
        return SimpleNamespace(data=registros)


class TestPesquisaRetirados(unittest.TestCase):
    def test_busca_pontual_filtra_antes_das_movimentacoes(self):
        from modules.modulo_01 import service
        pedidos = [
            {"id": 1, "numero_pedido": "123/26", "cliente": "ACME", "nota_fiscal": None},
            {"id": 2, "numero_pedido": "999/26", "cliente": "OUTRO", "nota_fiscal": "52000"},
        ]
        mov = {1: {"usuario": "Joao", "criado_em": "2026-10-28T12:00:00"}}
        with (
            patch.object(service, "listar_retirados_para_pesquisa", return_value=pedidos),
            patch.object(service, "_mapa_retiradas", return_value=mov) as consultar,
            patch.object(service, "obter_pedidos", side_effect=AssertionError("Não carregar tudo")),
        ):
            resultado = service.pesquisar_historico_retirados("123")
        self.assertEqual([p["id"] for p in resultado], [1])
        consultar.assert_called_once_with(pedido_ids=[1])

    def test_sem_correspondencias_nao_busca_movimentacoes(self):
        from modules.modulo_01 import service
        with (
            patch.object(service, "listar_retirados_para_pesquisa", return_value=[
                {"id": 1, "numero_pedido": "123", "cliente": "CLIENTE", "nota_fiscal": None},
            ]),
            patch.object(service, "_mapa_retiradas") as movimentos,
        ):
            self.assertEqual(service.pesquisar_historico_retirados("nao existe"), [])
        movimentos.assert_not_called()

    def test_busca_ampla_nao_monta_filtro_in_enorme(self):
        from modules.modulo_01 import service
        pedidos = [{"id": i, "numero_pedido": str(i), "cliente": "CLIENTE",
                    "nota_fiscal": None} for i in range(201)]
        mov = {i: {"usuario": "Joao", "criado_em": "2026-10-28T12:00:00"}
               for i in range(201)}
        with (
            patch.object(service, "listar_retirados_para_pesquisa", return_value=pedidos),
            patch.object(service, "_mapa_retiradas", return_value=mov) as consultar,
        ):
            resultado = service.pesquisar_historico_retirados("CLIENTE")
        self.assertEqual(len(resultado), 201)
        consultar.assert_called_once_with()

    def test_lista_retirados_e_paginada_sem_ignorar_pedidos_antigos(self):
        from core.pedidos import listar_retirados_para_pesquisa
        dados = [{"id": i, "numero_pedido": str(i), "cliente": "X",
                  "nota_fiscal": None, "status": "ATIVO",
                  "setor_atual": "RETIRADO"} for i in range(1001)]
        consulta = QueryFalsa(dados)
        with patch("core.pedidos.supabase") as banco:
            banco.table.return_value = consulta
            resultado = listar_retirados_para_pesquisa()
        self.assertEqual(len(resultado), 1001)
        self.assertEqual(consulta.intervalos, [(0, 999), (1000, 1999)])
        self.assertEqual(consulta.campos, "id,numero_pedido,cliente,nota_fiscal")

    def test_movimentacoes_filtradas_pelos_pedidos(self):
        from core.pedidos import listar_movimentacoes_destino
        registros = [
            {"pedido_id": 1, "destino": "RETIRADO", "origem": "EMBALADO",
             "tipo_evento": "MOVIMENTACAO"},
            {"pedido_id": 2, "destino": "RETIRADO", "origem": "EMBALADO",
             "tipo_evento": "MOVIMENTACAO"},
        ]
        consulta = QueryFalsa(registros)
        with patch("core.pedidos.supabase") as banco:
            banco.table.return_value = consulta
            encontrados = listar_movimentacoes_destino(
                "RETIRADO", origem="EMBALADO", pedido_ids=[1]
            )
        self.assertEqual([r["pedido_id"] for r in encontrados], [1])
        self.assertIn(("pedido_id", [1]), consulta.filtros)

    def test_ids_vazios_nao_chama_o_banco(self):
        from core.pedidos import listar_movimentacoes_destino
        with patch("core.pedidos.supabase") as banco:
            self.assertEqual(listar_movimentacoes_destino("RETIRADO", pedido_ids=[]), [])
            banco.table.assert_not_called()


if __name__ == "__main__":
    unittest.main()

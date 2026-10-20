"""Regressões das otimizações: sem acessar ou modificar o Supabase real."""
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo


class TestOtimizacaoFila(unittest.TestCase):
    def test_desativa_notificacoes_sem_impedir_alertas(self):
        from core.notificacoes import criar_notificacao_para_setor
        with patch("core.notificacoes.criar_notificacao") as inserir:
            resultado = criar_notificacao_para_setor(1, "MONTAGEM", "ALERTA", "Aviso")
        self.assertEqual(resultado, [])
        inserir.assert_not_called()

    def test_consulta_versao_em_uma_linha(self):
        from core.fila_revisao import obter_versao_fila
        query = MagicMock()
        query.select.return_value = query
        query.eq.return_value = query
        query.limit.return_value = query
        query.execute.return_value.data = [{"versao": 42}]
        with patch("core.fila_revisao.supabase") as banco:
            banco.table.return_value = query
            self.assertEqual(obter_versao_fila(), 42)
            query.select.assert_called_once_with("versao")
            query.limit.assert_called_once_with(1)

    def test_filtro_da_fila_aplicado_no_banco(self):
        from core.pedidos import listar_pedidos
        query = MagicMock()
        query.eq.return_value = query
        query.neq.return_value = query
        query.in_.return_value = query
        query.order.return_value = query
        query.execute.return_value.data = [{"id": 5}]
        with patch("core.pedidos.supabase") as banco:
            banco.table.return_value.select.return_value = query
            resultado = listar_pedidos("ATIVO", excluir_setor="RETIRADO")
            self.assertEqual(resultado, [{"id": 5}])
            query.eq.assert_called_with("status", "ATIVO")
            query.neq.assert_called_once_with("setor_atual", "RETIRADO")

    def test_lista_vazia_de_ids_nao_consulta_banco(self):
        from core.pedidos import listar_pedidos
        with patch("core.pedidos.supabase") as banco:
            self.assertEqual(listar_pedidos(ids=[]), [])
            banco.table.assert_not_called()

    def test_retirados_antigos_nao_entram_no_kanban(self):
        from modules.modulo_01 import service
        data = (datetime.now(ZoneInfo("America/Sao_Paulo"))
                - timedelta(hours=1)).isoformat()
        pedidos_abertos = [{"id": 1, "setor_atual": "PEDIDO"},
                           {"id": 2, "setor_atual": "FATURADO"}]
        retirados = [{"id": 3, "setor_atual": "RETIRADO"},
                     {"id": 4, "setor_atual": "PEDIDO"}]
        with (patch.object(service, "_mapa_retiradas", return_value={
                  3: {"criado_em": data, "usuario": "João"}}),
              patch.object(service, "listar_pedidos",
                  side_effect=[pedidos_abertos, retirados]) as listar,
              patch.object(service, "enriquecer_pedidos",
                  side_effect=lambda pedidos: pedidos),
              patch.object(service, "_mapa_status_expedicao",
                  return_value={})):
            estados = service.obter_pedidos_por_estado()
        self.assertEqual([p["id"] for p in estados["RETIRADO"]], [3])
        self.assertEqual([p["id"] for p in estados["PEDIDO"]], [1])
        self.assertEqual([p["id"] for p in estados["FATURADO"]], [2])
        self.assertEqual(listar.call_count, 2)
        self.assertEqual(listar.call_args_list[0].kwargs,
                         {"status": "ATIVO", "excluir_setor": "RETIRADO"})
        self.assertEqual(listar.call_args_list[1].kwargs,
                         {"status": "ATIVO", "ids": [3]})

    def test_expedicao_consulta_apenas_pedidos_relevantes(self):
        from modules.modulo_01 import service
        pedidos = [{"id": 5, "setor_atual": "FATURADO"},
                   {"id": 6, "setor_atual": "PEDIDO"}]
        with patch.object(service, "listar_movimentacoes_tipo",
                          return_value=[]) as buscar:
            self.assertEqual(service._mapa_status_expedicao(pedidos), {})
            buscar.assert_called_once_with("STATUS_EXPEDICAO", pedido_ids=[5])

    def test_sem_montados_nao_busca_status_expedicao(self):
        from modules.modulo_01 import service
        with patch.object(service, "listar_movimentacoes_tipo",
                          return_value=[]) as buscar:
            self.assertEqual(service._mapa_status_expedicao([]), {})
            buscar.assert_called_once_with("STATUS_EXPEDICAO", pedido_ids=[])


if __name__ == "__main__":
    unittest.main()

"""Testes da fotografia histórica e da política de acesso, sem banco real."""
import importlib
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

fake_db = types.ModuleType("core.database")
fake_db.supabase = MagicMock()
with patch.dict(sys.modules, {"core.database": fake_db}):
    ref = importlib.import_module("core.estoque_referencia")
    cat = importlib.import_module("core.catalogo_transformacoes")

from core.permissoes import tem_acesso_modulo


class TestEstoqueReferencia(unittest.TestCase):
    def test_todas_pessoas_montagem_acessam_laboratorio(self):
        for nome in ("joao", "ricardo", "marco"):
            self.assertTrue(tem_acesso_modulo(nome, "MONTAGEM", "Laboratório de Transformações"))
        self.assertFalse(tem_acesso_modulo("joao", "MONTAGEM", "Inteligência Comercial"))
        self.assertFalse(tem_acesso_modulo("carla", "VENDAS", "Laboratório de Transformações"))
        self.assertTrue(tem_acesso_modulo("arthur", "ADMINISTRADOR", "Laboratório de Transformações"))

    def test_carregamento_estoque_historico(self):
        fake = MagicMock()
        tabela_inventarios = MagicMock()
        tabela_itens = MagicMock()
        for tabela in (tabela_inventarios, tabela_itens):
            tabela.select.return_value = tabela
            tabela.eq.return_value = tabela
            tabela.order.return_value = tabela
            tabela.limit.return_value = tabela
            tabela.range.return_value = tabela
        tabela_inventarios.execute.return_value.data = [
            {"id": "inventario-historico", "referencia_externa": ref.REFERENCIA_LABORATORIO}
        ]
        tabela_itens.execute.return_value.data = [
            {"codigo": "1335BA04", "quantidade": "8"},
            {"codigo": "1335BA04", "quantidade": 2},
            {"codigo": "Z1342BA12T", "quantidade": "1"},
        ]
        fake.table.side_effect = lambda nome: (
            tabela_inventarios if nome == "estoque_inventarios" else tabela_itens)
        with patch.object(ref, "supabase", fake):
            meta, saldos = ref.carregar_estoque_referencia()
        self.assertEqual(meta["id"], "inventario-historico")
        self.assertEqual(saldos["1335BA04"], 10)
        self.assertEqual(saldos["Z1342BA12T"], 1)

    def test_proposta_montagem_pendente_nao_homologada(self):
        resultado = {"tipo": "CORPO", "destino": "1335BA04", "familia": "1335"}
        simu = {"produto_final": "1335BA04", "valvula_base": "1335BA04T",
                "valvula_doadora": "1335BA06", "produto_residual": "1335BA06T"}
        item = cat.preparar_receita(resultado, simu, "joao", estado="PENDENTE")
        self.assertEqual(item["estado"], "PENDENTE")
        self.assertEqual(item["total_validacoes"], 0)
        self.assertIsNone(item["validada_por"])
        self.assertIsNone(item["primeira_validacao_em"])

    def test_nao_admin_nao_homologa(self):
        with self.assertRaises(PermissionError):
            cat.homologar_pendente("abc", "joao", "MONTAGEM")


if __name__ == "__main__":
    unittest.main()

"""Testes isolados de persistência de kit; nenhum contato real com o Supabase."""
import importlib
import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from core.catalogo_kit_componentes import preparar_proposta_componentes

fake_db = types.ModuleType("core.database")
fake_db.supabase = MagicMock()
with patch.dict(sys.modules, {"core.database": fake_db}):
    banco = importlib.import_module("core.catalogo_transformacoes")


def proposta():
    return preparar_proposta_componentes(
        "MONTAR_KIT", "K030AR2", "", [
            {"grupo": "G2", "tipo": "COMPONENTE", "codigo": "",
             "descricao": "Diafragma NBR com reforco", "quantidade": 1}
        ], "marco", "Kit usado na montagem da linha 2030.",
    )


def mock_tabela(respostas):
    supa = MagicMock()
    tabela = MagicMock()
    tabela.select.return_value = tabela
    tabela.eq.return_value = tabela
    tabela.limit.return_value = tabela
    tabela.update.return_value = tabela
    tabela.insert.return_value = tabela
    tabela.execute.side_effect = [SimpleNamespace(data=x) for x in respostas]
    supa.table.return_value = tabela
    return supa, tabela


class TestComponentesKitSupabase(unittest.TestCase):
    def test_registra_proposta_apenas_pendente(self):
        dados = proposta()
        supa, tabela = mock_tabela([[], [{"id": "nova", "estado": "PENDENTE"}]])
        with patch.object(banco, "supabase", supa):
            retorno, nova = banco.registrar_proposta_componentes_kit(dados)
        self.assertTrue(nova)
        self.assertEqual(retorno["id"], "nova")
        inserido = tabela.insert.call_args.args[0]
        self.assertEqual(inserido["estado"], "PENDENTE")
        self.assertEqual(inserido["total_validacoes"], 0)
        self.assertEqual(inserido["entradas"][0]["papel"], "COMPONENTE")
        tabela.update.assert_not_called()

    def test_impede_homologacao_de_referencia_temporaria(self):
        dados = proposta()
        supa, tabela = mock_tabela([[dados]])
        with patch.object(banco, "supabase", supa):
            with self.assertRaisesRegex(ValueError, "sem código ERP"):
                banco.homologar_pendente("uuid", "arthur", "ADMINISTRADOR")
        tabela.update.assert_not_called()

    def test_admin_substitui_referencia_antes_de_homologar(self):
        dados = proposta()
        codigo_temporario = dados["entradas"][0]["codigo"]
        supa, tabela = mock_tabela([[dados], [{"id": "uuid", "estado": "PENDENTE"}]])
        with patch.object(banco, "supabase", supa):
            atualizado = banco.corrigir_referencias_kit_pendente(
                "uuid", {codigo_temporario: "G2-DIAF-ERP"}, "arthur", "ADMINISTRADOR")
        self.assertEqual(atualizado["id"], "uuid")
        escrita = tabela.update.call_args.args[0]
        self.assertEqual(escrita["entradas"][0]["codigo"], "G2-DIAF-ERP")
        self.assertEqual(escrita["parametros_tecnicos"]["codigos_sem_erp"], [])
        self.assertFalse(escrita["parametros_tecnicos"]["componentes"][0]["sem_codigo_erp"])
        self.assertNotIn("estado", escrita)

    def test_montagem_nao_pode_corrigir_referencias(self):
        with self.assertRaises(PermissionError):
            banco.corrigir_referencias_kit_pendente("uuid", {}, "marco", "MONTAGEM")


if __name__ == "__main__":
    unittest.main()

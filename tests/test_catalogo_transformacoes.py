"""Testes isolados: nenhuma conexão ou gravação no Supabase real."""
import importlib
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


# Evita carregar credenciais e abrir cliente do banco nos testes.
falso_banco = types.ModuleType("core.database")
falso_banco.supabase = MagicMock()
with patch.dict(sys.modules, {"core.database": falso_banco}):
    catalogo = importlib.import_module("core.catalogo_transformacoes")


def exemplo():
    return (
        {"tipo": "TORRE", "familia": "1335", "destino": "Z1335BE04",
         "grupo_torre": "1335", "construcao_torre": "Z",
         "metodo": "VALVULA_VALVULA"},
        {"produto_final": "Z1335BE04", "valvula_base": "1335BE04",
         "valvula_doadora": "Z1335BA04", "produto_residual": "1335BA04"},
    )


class TestCatalogoTransformacoes(unittest.TestCase):
    def test_schema_existente_e_identidade_da_receita(self):
        resultado, simulacao = exemplo()
        registro = catalogo.preparar_receita(resultado, simulacao, "ricardo")
        self.assertEqual(registro["grau"], "TORRE")
        self.assertEqual(registro["subtipo"], "G1_INTEGRAL")
        self.assertEqual(registro["estado"], "VALIDADA")
        self.assertEqual(registro["total_validacoes"], 1)
        self.assertEqual(registro["entradas"][0]["papel"], "BASE")
        self.assertEqual(registro["entradas"][1]["codigo"], "Z1335BA04")
        self.assertEqual(registro["saidas"][0]["papel"], "PRODUTO")
        self.assertEqual(registro["saidas"][1]["papel"], "RESIDUAL")
        self.assertEqual(registro["validada_por"], "ricardo")
        self.assertEqual(registro["assinatura"],
                         catalogo.preparar_receita(resultado, simulacao, "arthur")["assinatura"])
        trocada = dict(simulacao, valvula_base="Z1335BA04",
                       valvula_doadora="1335BE04")
        self.assertNotEqual(registro["assinatura"],
                            catalogo.preparar_receita(resultado, trocada, "ricardo")["assinatura"])

    def test_grau_de_kit_no_banco(self):
        resultado, simulacao = exemplo()
        resultado.update(tipo="KIT", operacao="NA_NF")
        simulacao = dict(simulacao, origem=simulacao.pop("valvula_doadora"))
        reg = catalogo.preparar_receita(resultado, simulacao, "arthur")
        self.assertEqual(reg["grau"], "KIT_REPARO")
        self.assertEqual(reg["subtipo"], "NA_NF")

    def test_saldos_consideram_consumo_duplicado(self):
        receita = {"entradas": [
            {"codigo": "A", "quantidade": 1}, {"codigo": "A", "quantidade": 1}
        ]}
        self.assertFalse(catalogo.disponibilidade_receita(receita, {"A": 1}))
        self.assertTrue(catalogo.disponibilidade_receita(receita, {"A": 2}))

    def test_duplicidade_nao_cria_nova_receita(self):
        resultado, simulacao = exemplo()
        fake = MagicMock()
        busca = fake.table.return_value.select.return_value
        busca.eq.return_value = busca
        busca.limit.return_value = busca
        busca.execute.return_value.data = [
            dict(catalogo.preparar_receita(resultado, simulacao, "ricardo"),
                 id="ja-existe")
        ]
        with patch.object(catalogo, "supabase", fake):
            receita, nova = catalogo.registrar_receita(resultado, simulacao, "arthur")
        self.assertFalse(nova)
        self.assertEqual(receita["id"], "ja-existe")
        fake.table.return_value.insert.assert_not_called()


    def test_comparacao_respeita_canonizacao_do_trigger(self):
        resultado, simulacao = exemplo()
        dados = catalogo.preparar_receita(resultado, simulacao, "arthur")
        existente = dict(dados)
        existente["entradas"] = list(reversed(dados["entradas"]))
        existente["saidas"] = [
            dict(x, quantidade=1.0) for x in reversed(dados["saidas"])
        ]
        existente["assinatura"] = "SHA256-GERADO-PELO-POSTGRES"
        self.assertTrue(catalogo._mesma_receita(existente, dados))

    def test_insercao_com_campos_corretos(self):
        resultado, simulacao = exemplo()
        fake = MagicMock()
        busca = fake.table.return_value.select.return_value
        busca.eq.return_value = busca
        busca.limit.return_value = busca
        busca.execute.return_value.data = []
        fake.table.return_value.insert.return_value.execute.return_value.data = [{"id": "novo"}]
        with patch.object(catalogo, "supabase", fake):
            receita, nova = catalogo.registrar_receita(resultado, simulacao, "arthur")
        self.assertTrue(nova)
        self.assertEqual(receita["id"], "novo")
        payload = fake.table.return_value.insert.call_args.args[0]
        self.assertEqual(payload["produto_final"], "Z1335BE04")
        self.assertEqual(len(payload["saidas"]), 2)


if __name__ == "__main__":
    unittest.main()

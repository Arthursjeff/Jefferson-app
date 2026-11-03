"""Regressão: captura de foto sem consultas administrativas desnecessárias."""
import ast
from pathlib import Path
import unittest


ARQUIVO_APP = Path(__file__).resolve().parents[1] / "app.py"


def funcao_do_app(nome):
    arvore = ast.parse(ARQUIVO_APP.read_text(encoding="utf-8"))
    return next(
        node for node in arvore.body
        if isinstance(node, ast.FunctionDef) and node.name == nome
    )


def chamadas(funcao):
    nomes = set()
    for node in ast.walk(funcao):
        if not isinstance(node, ast.Call):
            continue
        destino = node.func
        if isinstance(destino, ast.Name):
            nomes.add(destino.id)
        elif isinstance(destino, ast.Attribute):
            nomes.add(destino.attr)
    return nomes


class TestModalFoto(unittest.TestCase):
    def test_modal_nao_busca_itens_ou_series(self):
        nomes = chamadas(funcao_do_app("modal_foto_obrigatoria"))
        self.assertFalse(
            {"listar_itens_pedido", "listar_series", "data_editor"} & nomes
        )

    def test_foto_continua_obrigatoria_e_pedido_avanca(self):
        nomes = chamadas(funcao_do_app("modal_foto_obrigatoria"))
        self.assertIn("camera_input", nomes)
        self.assertIn("salvar_foto_e_avancar", nomes)
        self.assertIn("fechar_modal_foto", nomes)

    def test_edicao_administrativa_permanece_isolada(self):
        nomes = chamadas(funcao_do_app("modal_editar_pedido"))
        self.assertIn("listar_itens_pedido", nomes)
        self.assertIn("listar_series", nomes)
        self.assertIn("data_editor", nomes)


if __name__ == "__main__":
    unittest.main()

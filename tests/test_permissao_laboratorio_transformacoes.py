import unittest

from core.permissoes import tem_acesso_modulo


class TestPermissaoLaboratorioTransformacoes(unittest.TestCase):
    def test_ricardo_tem_acesso(self):
        self.assertTrue(tem_acesso_modulo("ricardo", "MONTAGEM", "Laboratório de Transformações"))

    def test_admin_tem_acesso(self):
        self.assertTrue(tem_acesso_modulo("arthur", "ADMINISTRADOR", "Laboratório de Transformações"))

    def test_toda_montagem_recebe_acesso(self):
        for usuario in ("joao", "ricardo", "marco"):
            self.assertTrue(tem_acesso_modulo(usuario, "MONTAGEM", "Laboratório de Transformações"))
        self.assertFalse(tem_acesso_modulo("amanda", "VENDAS", "Laboratório de Transformações"))

    def test_permissa_anterior_ricardo_preservada(self):
        self.assertTrue(tem_acesso_modulo("ricardo", "MONTAGEM", "Inteligência Comercial"))


if __name__ == "__main__":
    unittest.main()

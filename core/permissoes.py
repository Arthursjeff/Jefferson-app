"""Permissões individuais adicionais, sem alterar o grupo principal."""

PERMISSOES_EXTRAS = {
    "ricardo": {"Inteligência Comercial"},
}


def tem_acesso_modulo(usuario: str, setor: str, modulo: str) -> bool:
    if setor == "ADMINISTRADOR":
        return True
    login = (usuario or "").strip().lower()
    return modulo in PERMISSOES_EXTRAS.get(login, set())

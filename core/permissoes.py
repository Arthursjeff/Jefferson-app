"""Permissões individuais adicionais, sem alterar o grupo principal."""

PERMISSOES_EXTRAS = {
    "ricardo": {"Inteligência Comercial", "Laboratório de Transformações"},
    "jaqueline": {"Consertos", "Atualização ERP"},
}


def tem_acesso_modulo(usuario: str, setor: str, modulo: str) -> bool:
    if setor == "ADMINISTRADOR":
        return True
    if setor == "MONTAGEM" and modulo in {"Laboratório de Transformações", "Consertos"}:
        return True
    login = (usuario or "").strip().lower()
    return modulo in PERMISSOES_EXTRAS.get(login, set())

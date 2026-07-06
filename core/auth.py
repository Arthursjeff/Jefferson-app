USUARIOS = {
    "arthur": {
        "senha": "Turico1710*",
        "nome": "Arthur",
        "setor": "VENDAS",
    },
    "amanda": {
        "senha": "1234",
        "nome": "Amanda",
        "setor": "VENDAS",
    },
    "carla": {
        "senha": "123456",
        "nome": "Carla",
        "setor": "VENDAS",
    },
    "jaqueline": {
        "senha": "POL1",
        "nome": "Jaqueline",
        "setor": "VENDAS",
    },
    "marilene": {
        "senha": "K42A4",
        "nome": "Marilene",
        "setor": "VENDAS",
    },
    "romulo": {
        "senha": "1234",
        "nome": "Romulo",
        "setor": "VENDAS",
    },
    "joao": {
        "senha": "1234",
        "nome": "João",
        "setor": "MONTAGEM",
    },
    "ricardo": {
        "senha": "RBC",
        "nome": "Ricardo",
        "setor": "MONTAGEM",
    },
    "marco": {
        "senha": "1963",
        "nome": "Marco",
        "setor": "MONTAGEM",
    },
}


def validar_login(usuario: str, senha: str):
    usuario = (usuario or "").strip().lower()
    senha = senha or ""

    if usuario not in USUARIOS:
        return None

    dados = USUARIOS[usuario]

    if senha != dados["senha"]:
        return None

    return {
        "usuario": usuario,
        "nome": dados["nome"],
        "setor": dados["setor"],
    }

PERMISSOES_MOVIMENTO = {
    "VENDAS": {
        "MONTADOS": ["FATURADO"],
    },
    "MONTAGEM": {
        "PEDIDO": ["EM_MONTAGEM"],
        "EM_MONTAGEM": ["PROGRAMADO", "IMPORTACAO", "MONTADOS"],
        "PROGRAMADO": ["MONTADOS"],
        "IMPORTACAO": ["MONTADOS"],
        "FATURADO": ["EMBALADO"],
        "EMBALADO": ["RETIRADO"],
    },


def pode_mover(setor_usuario: str, origem: str, destino: str) -> bool:
    destinos_permitidos = PERMISSOES_MOVIMENTO.get(setor_usuario, {}).get(origem, [])
    return destino in destinos_permitidos


def pode_criar_pedido(setor_usuario: str) -> bool:
    return setor_usuario == "VENDAS"


def pode_cancelar_pedido(setor_usuario: str) -> bool:
    return setor_usuario == "VENDAS"

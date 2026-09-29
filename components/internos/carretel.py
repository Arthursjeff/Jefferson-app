"""G4 - Conjunto carretel.

O G4 é formado por:
- carretel;
- cadeirinha;
- mola da cadeirinha.

Existem somente quatro variações validadas:
1. famílias 1330/2030 + NF;
2. famílias 1330/2030 + NA;
3. família 1325 + NF;
4. família 1325 + NA.

A identidade do G4 depende exclusivamente do grupo de família e do estado
NF/NA. Vedação, material/tipo de corpo, tamanho, conexão e demais
características não alteram o conjunto carretel.

Este módulo contém apenas regras de engenharia. Não consulta estoque,
Supabase, orçamento ou interface.
"""

FAMILIAS_CARRETEL_COMPARTILHADO = {"1330", "2030"}
FAMILIA_CARRETEL_1325 = "1325"


def _normalizar(valor):
    if valor is None:
        return None
    return str(valor).strip().upper()


def _normalizar_estado(estado):
    valor = _normalizar(estado)

    equivalencias = {
        "NF": "NF",
        "NORMALMENTE FECHADA": "NF",
        "NORMALMENTE FECHADO": "NF",
        "NA": "NA",
        "NORMALMENTE ABERTA": "NA",
        "NORMALMENTE ABERTO": "NA",
    }

    return equivalencias.get(valor, valor)


def identificar_grupo_carretel(familia):
    """Retorna o grupo de família que determina a identidade do G4."""
    familia = _normalizar(familia)

    if familia in FAMILIAS_CARRETEL_COMPARTILHADO:
        return "1330_2030"

    if familia == FAMILIA_CARRETEL_1325:
        return "1325"

    return None


def usa_carretel(familia):
    """Informa se a família possui uma das quatro variações validadas de G4."""
    return identificar_grupo_carretel(familia) is not None


def identificar_conjunto_carretel(familia, estado):
    """Retorna uma das quatro identidades lógicas possíveis do G4."""
    familia = _normalizar(familia)
    estado = _normalizar_estado(estado)
    grupo_familia = identificar_grupo_carretel(familia)

    if grupo_familia is None:
        return None

    if estado not in {"NF", "NA"}:
        return None

    identidade = {
        "grupo_familia": grupo_familia,
        "estado": estado,
    }

    return {
        "grupo_componente": "G4",
        "nome_grupo": "CONJUNTO_CARRETEL",
        "identidade": identidade,
        "componentes": {
            "carretel": identidade.copy(),
            "cadeirinha": identidade.copy(),
            "mola_cadeirinha": identidade.copy(),
        },
    }

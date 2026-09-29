"""G3 - Conjunto pistão.

O G3 é formado por pistão e mola, tratados como conjunto inseparável.

Regras validadas:
- 1342 e 1390: família + tamanho + vedação + material do corpo;
- 2094: toda a família utiliza o mesmo conjunto pistão;
- 2036: somente Teflon utiliza pistão. 3/8" e 1/2" compartilham o mesmo
  conjunto; os demais tamanhos são distintos. BSP/NPT não interfere;
- 1314: utiliza pistão. Família + tamanho + vedação + variante normal/anclada
  determinam o conjunto. O sufixo A identifica a variante anclada.

Este módulo contém apenas regras de engenharia.
"""

FAMILIAS_PISTAO_VARIAVEL = {"1342", "1390"}
FAMILIA_PISTAO_UNICO = "2094"
FAMILIA_2036 = "2036"
FAMILIA_1314 = "1314"


def _normalizar(valor):
    if valor is None:
        return None
    return str(valor).strip().upper()


def _normalizar_vedacao(vedacao):
    valor = _normalizar(vedacao)
    return {"PTFE": "TEFLON", "TEFLON": "TEFLON"}.get(valor, valor)


def _normalizar_tamanho(tamanho):
    valor = _normalizar(tamanho)
    equivalencias = {
        '3/8"': "3/8", "3/8": "3/8",
        '1/2"': "1/2", "1/2": "1/2",
        '3/4"': "3/4", "3/4": "3/4",
        '1"': "1", "1": "1",
        '1 1/2"': "1 1/2", "1 1/2": "1 1/2",
    }
    return equivalencias.get(valor, valor)


def _grupo_pistao_2036(tamanho):
    if tamanho in {"3/8", "1/2"}:
        return "3/8_1/2"
    return tamanho


def usa_pistao(familia, vedacao=None):
    """Informa se a configuração validada utiliza G3."""
    familia = _normalizar(familia)
    vedacao = _normalizar_vedacao(vedacao)

    if familia in FAMILIAS_PISTAO_VARIAVEL:
        return True
    if familia == FAMILIA_PISTAO_UNICO:
        return True
    if familia == FAMILIA_1314:
        return True
    if familia == FAMILIA_2036:
        return vedacao == "TEFLON"
    return False


def identificar_conjunto_pistao(
    familia,
    tamanho=None,
    vedacao=None,
    material_corpo=None,
    sufixos=None,
):
    """Retorna a identidade lógica conhecida do G3."""
    familia = _normalizar(familia)
    tamanho = _normalizar_tamanho(tamanho)
    vedacao = _normalizar_vedacao(vedacao)
    material_corpo = _normalizar(material_corpo)
    sufixos_normalizados = {
        _normalizar(item) for item in (sufixos or []) if _normalizar(item)
    }

    if not usa_pistao(familia=familia, vedacao=vedacao):
        return None

    if familia in FAMILIAS_PISTAO_VARIAVEL:
        identidade = {
            "regra": "FAMILIA_TAMANHO_VEDACAO_MATERIAL_CORPO",
            "familia": familia,
            "tamanho": tamanho,
            "vedacao": vedacao,
            "material_corpo": material_corpo,
        }

    elif familia == FAMILIA_PISTAO_UNICO:
        identidade = {
            "regra": "PISTAO_UNICO_FAMILIA",
            "familia": familia,
        }

    elif familia == FAMILIA_2036:
        identidade = {
            "regra": "2036_TEFLON_GRUPO_TAMANHO",
            "familia": familia,
            "vedacao": "TEFLON",
            "grupo_tamanho": _grupo_pistao_2036(tamanho),
        }

    elif familia == FAMILIA_1314:
        identidade = {
            "regra": "1314_TAMANHO_VEDACAO_VARIANTE",
            "familia": familia,
            "tamanho": tamanho,
            "vedacao": vedacao,
            "variante": "ANCLADO" if "A" in sufixos_normalizados else "NORMAL",
        }

    else:
        return None

    return {
        "grupo_componente": "G3",
        "nome_grupo": "CONJUNTO_PISTAO",
        "identidade": identidade,
        "componentes": {
            "pistao": identidade.copy(),
            "mola": identidade.copy(),
        },
    }

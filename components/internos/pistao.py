"""G3 - Conjunto pistão.

O G3 é formado por:
- pistão;
- mola.

Para o motor de componentes, pistão e mola são tratados como um conjunto:
a mola acompanha o pistão e não é procurada separadamente em outra fonte.

Regras validadas:
- 1342 e 1390: família + tamanho + vedação + material do corpo
  determinam a identidade do conjunto pistão;
- 2094: toda a família utiliza o mesmo conjunto pistão;
- 2036: somente configurações com vedação em Teflon utilizam pistão.
  Nesse caso, o tamanho determina o conjunto pistão. BSP/NPT e demais
  características não criam outra identidade de pistão;
- 2036 com outras vedações não utiliza G3: utiliza diafragma (G2).

Este módulo contém apenas regras de engenharia. Não consulta estoque,
Supabase, orçamento ou interface.
"""

FAMILIAS_PISTAO_VARIAVEL = {
    "1342",
    "1390",
}

FAMILIA_PISTAO_UNICO = "2094"
FAMILIA_2036 = "2036"


def _normalizar(valor):
    if valor is None:
        return None
    return str(valor).strip().upper()


def _normalizar_vedacao(vedacao):
    valor = _normalizar(vedacao)

    equivalencias = {
        "TEFLON": "TEFLON",
        "PTFE": "TEFLON",
    }

    return equivalencias.get(valor, valor)


def usa_pistao(familia, vedacao=None):
    """Informa se a configuração validada utiliza G3."""
    familia = _normalizar(familia)
    vedacao = _normalizar_vedacao(vedacao)

    if familia in FAMILIAS_PISTAO_VARIAVEL:
        return True

    if familia == FAMILIA_PISTAO_UNICO:
        return True

    if familia == FAMILIA_2036:
        return vedacao == "TEFLON"

    return False


def identificar_conjunto_pistao(
    familia,
    tamanho=None,
    vedacao=None,
    material_corpo=None,
):
    """Retorna a identidade lógica conhecida do G3.

    Retorna None quando a configuração não utiliza pistão segundo as
    regras atualmente validadas.
    """
    familia = _normalizar(familia)
    tamanho = _normalizar(tamanho)
    vedacao = _normalizar_vedacao(vedacao)
    material_corpo = _normalizar(material_corpo)

    if not usa_pistao(
        familia=familia,
        vedacao=vedacao,
    ):
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
            "regra": "2036_TEFLON_POR_TAMANHO",
            "familia": familia,
            "vedacao": "TEFLON",
            "tamanho": tamanho,
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

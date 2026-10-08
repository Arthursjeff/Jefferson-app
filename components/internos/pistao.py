"""G3 - Conjunto pistão.

O G3 representa o sistema físico do pistão.

Estrutura conceitual:
- pistão;
- mola do pistão;
- vedação associada ao pistão, que pode ser:
  - O-ring do pistão; ou
  - aro do pistão + mola interna da junta.

Regras de identidade:
- quando muda o pistão, muda também a vedação associada a ele;
- o O-ring do pistão é tratado em G5;
- aro e mola interna do aro permanecem associadas ao G3;
- o tipo de vedação do pistão (O-ring ou junta) será definido família a família.

Regras validadas:
- 1342 e 1390: família + tamanho + vedação + material do corpo;
- 2094: toda a família utiliza o mesmo conjunto pistão;
- 2036: somente Teflon utiliza pistão. 3/8" e 1/2" compartilham o mesmo
  conjunto; os demais tamanhos são distintos. BSP/NPT não interfere;
- 1314: família + tamanho + vedação + variante normal/anclada. Sufixo A
  identifica a variante anclada;
- 1335: somente configurações com sufixo D utilizam pistão. O agrupamento
  de tamanhos segue a mesma lógica do diafragma 1335 e a vedação diferencia
  o pistão;
- 1344 e 1397: utilizam pistão; tamanho e vedação diferenciam o conjunto.\n- 1351, 2050 e 2051: pistão exclusivo por família e tamanho; a vedação\n  do pistão corresponde à vedação da válvula.

Famílias explicitamente validadas sem G3:
1312, 1323, 1325, 1327, 1330, 1343, 1356, 1360, 1365, 1375,
1387, 1388, 1393.

Este módulo contém apenas regras de engenharia.
"""

FAMILIAS_PISTAO_VARIAVEL = {"1342", "1390"}
FAMILIAS_PISTAO_TAMANHO_VEDACAO = {"1344", "1397", "1351", "2050", "2051"}
FAMILIA_PISTAO_UNICO = "2094"
FAMILIA_2036 = "2036"
FAMILIA_1314 = "1314"
FAMILIA_1335 = "1335"

FAMILIAS_SEM_PISTAO = {
    "1312", "1323", "1325", "1327", "1330", "1343", "1356",
    "1360", "1365", "1375", "1387", "1388", "1393",
}


def _normalizar(valor):
    if valor is None:
        return None
    return str(valor).strip().upper()


def _normalizar_vedacao(vedacao):
    valor = _normalizar(vedacao)
    return {"PTFE": "TEFLON", "TEFLON": "TEFLON"}.get(valor, valor)


def _normalizar_material(material):
    valor = _normalizar(material)
    equivalencias = {
        "LATÃO": "LATAO", "LATAO": "LATAO", "INOX": "INOX",
        "AÇO INOX": "INOX", "ACO INOX": "INOX",
    }
    return equivalencias.get(valor, valor)


def _normalizar_tamanho(tamanho):
    valor = _normalizar(tamanho)
    equivalencias = {
        '3/8"': "3/8", "3/8": "3/8", '1/2"': "1/2", "1/2": "1/2",
        '3/4"': "3/4", "3/4": "3/4", '1"': "1", "1": "1",
        '1 1/2"': "1 1/2", "1 1/2": "1 1/2",
    }
    return equivalencias.get(valor, valor)


def _grupo_pistao_2036(tamanho):
    if tamanho in {"3/8", "1/2"}:
        return "3/8_1/2"
    return tamanho


def _grupo_pistao_1335(tamanho, material_corpo):
    if material_corpo == "LATAO":
        if tamanho in {"3/8", "1/2"}:
            return "3/8_1/2"
        if tamanho == "3/4":
            return "3/4"
    if material_corpo == "INOX" and tamanho in {"1/2", "3/4"}:
        return "1/2_3/4"
    return tamanho


def usa_pistao(familia, vedacao=None, sufixos=None):
    familia = _normalizar(familia)
    vedacao = _normalizar_vedacao(vedacao)
    sufixos_normalizados = {
        _normalizar(item) for item in (sufixos or []) if _normalizar(item)
    }
    if familia in FAMILIAS_SEM_PISTAO:
        return False
    if familia in FAMILIAS_PISTAO_VARIAVEL | FAMILIAS_PISTAO_TAMANHO_VEDACAO:
        return True
    if familia in {FAMILIA_PISTAO_UNICO, FAMILIA_1314}:
        return True
    if familia == FAMILIA_1335:
        return "D" in sufixos_normalizados
    if familia == FAMILIA_2036:
        return vedacao == "TEFLON"
    return False


def identificar_conjunto_pistao(familia, tamanho=None, vedacao=None, material_corpo=None, sufixos=None):
    familia = _normalizar(familia)
    tamanho = _normalizar_tamanho(tamanho)
    vedacao = _normalizar_vedacao(vedacao)
    material_corpo = _normalizar_material(material_corpo)
    sufixos_normalizados = {
        _normalizar(item) for item in (sufixos or []) if _normalizar(item)
    }

    if not usa_pistao(familia=familia, vedacao=vedacao, sufixos=sufixos):
        return None

    if familia in FAMILIAS_PISTAO_VARIAVEL:
        identidade = {"regra": "FAMILIA_TAMANHO_VEDACAO_MATERIAL_CORPO", "familia": familia,
                      "tamanho": tamanho, "vedacao": vedacao, "material_corpo": material_corpo}
    elif familia in FAMILIAS_PISTAO_TAMANHO_VEDACAO:
        identidade = {"regra": "FAMILIA_TAMANHO_VEDACAO", "familia": familia,
                      "tamanho": tamanho, "vedacao": vedacao}
    elif familia == FAMILIA_PISTAO_UNICO:
        identidade = {"regra": "PISTAO_UNICO_FAMILIA", "familia": familia}
    elif familia == FAMILIA_2036:
        identidade = {"regra": "2036_TEFLON_GRUPO_TAMANHO", "familia": familia,
                      "vedacao": "TEFLON", "grupo_tamanho": _grupo_pistao_2036(tamanho)}
    elif familia == FAMILIA_1314:
        identidade = {"regra": "1314_TAMANHO_VEDACAO_VARIANTE", "familia": familia,
                      "tamanho": tamanho, "vedacao": vedacao,
                      "variante": "ANCLADO" if "A" in sufixos_normalizados else "NORMAL"}
    elif familia == FAMILIA_1335:
        identidade = {"regra": "1335_D_GRUPO_TAMANHO_VEDACAO", "familia": familia,
                      "variante": "D", "grupo_tamanho": _grupo_pistao_1335(tamanho, material_corpo),
                      "vedacao": vedacao}
    else:
        return None

    # Ainda não definimos família a família se a vedação do pistão é O-ring
    # ou junta. Não inventar essa informação.
    return {
        "grupo_componente": "G3",
        "nome_grupo": "CONJUNTO_PISTAO",
        "identidade": identidade,
        "componentes": {
            "pistao": identidade.copy(),
            "mola_pistao": identidade.copy(),
            "aro_pistao": None,
            "mola_interna_aro": None,
        },
        "vedacao_pistao": vedacao if familia in {"1351", "2050", "2051"} else None,\n        "observacao_vedacao": "Vedação do pistão pode ser O-ring (G5) ou aro + mola interna (G3); tipo definido família a família. Na 1342, NBR/Buna-N usa O-ring; FKM, EPDM e PTFE usam aro.",
    }

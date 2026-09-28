"""G1 - Conjunto torre.

O G1 é formado por três componentes comparáveis separadamente:
- torre;
- núcleo móvel;
- mola.

Este módulo contém apenas regras de engenharia. Não consulta estoque,
Supabase, orçamento ou interface.

Princípio:
a identidade técnica é derivada das características que realmente
determinam o componente. Não são criados nomes/part numbers artificiais.
Part numbers de fabricação poderão ser acrescentados futuramente.
"""

FAMILIAS_SISTEMA_GENERICO = {
    "1342",
    "1327",
    "1335",
    "1390",
    "1365",
    "1325",
}

FAMILIAS_NUCLEO_ACHATADO = {
    "1330",
    "2030",
    "1325",
}

FAMILIAS_TORRE_COMPARTILHADA_2026_2036 = {
    "2026",
    "2036",
}


def _normalizar(valor):
    if valor is None:
        return None
    return str(valor).strip().upper()


def _normalizar_material(material):
    valor = _normalizar(material)

    equivalencias = {
        "LATÃO": "LATAO",
        "LATAO": "LATAO",
        "INOX": "INOX",
        "AÇO INOX": "INOX",
        "ACO INOX": "INOX",
        "AÇO INOXIDÁVEL": "INOX",
        "ACO INOXIDAVEL": "INOX",
    }

    return equivalencias.get(valor, valor)


def _normalizar_estado(estado):
    valor = _normalizar(estado)

    equivalencias = {
        "NORMALMENTE FECHADA": "NF",
        "NORMALMENTE FECHADO": "NF",
        "NF": "NF",
        "NORMALMENTE ABERTA": "NA",
        "NORMALMENTE ABERTO": "NA",
        "NA": "NA",
        "INA": "NA",
    }

    return equivalencias.get(valor, valor)


def _normalizar_construcao(construcao):
    valor = _normalizar(construcao)

    equivalencias = {
        "REGULAR": "REGULAR",
        "NORMAL": "REGULAR",
        "CAIXA Z": "Z",
        "Z": "Z",
        "À PROVA DE EXPLOSÃO": "Z",
        "A PROVA DE EXPLOSAO": "Z",
    }

    return equivalencias.get(valor, valor)


def _normalizar_vedacao(vedacao):
    valor = _normalizar(vedacao)

    equivalencias = {
        "BORRACHA": "BORRACHA",
        "TEFLON": "TEFLON",
        "PTFE": "TEFLON",
    }

    return equivalencias.get(valor, valor)


def identificar_sistema_torre(familia, material):
    """Classifica qual sistema de G1 deve ser usado.

    A ordem é intencional: exceções conhecidas são avaliadas antes da
    participação da família no sistema genérico.
    """
    familia = _normalizar(familia)
    material = _normalizar_material(material)

    if familia == "1323":
        return {
            "tipo": "EXCLUSIVO_FAMILIA",
            "grupo": "1323",
            "regra_detalhada": False,
        }

    if familia == "1335" and material == "INOX":
        return {
            "tipo": "EXCLUSIVO_FAMILIA",
            "grupo": "1335_INOX",
            "regra_detalhada": False,
        }

    if familia == "1390" and material == "INOX":
        return {
            "tipo": "EXCLUSIVO_FAMILIA",
            "grupo": "1390_INOX",
            "regra_detalhada": False,
        }

    if familia in FAMILIAS_TORRE_COMPARTILHADA_2026_2036:
        return {
            "tipo": "EXCLUSIVO_COMPARTILHADO",
            "grupo": "2026_2036",
            "regra_detalhada": False,
        }

    if familia in FAMILIAS_SISTEMA_GENERICO:
        return {
            "tipo": "GENERICO",
            "grupo": "GENERICO",
            "regra_detalhada": True,
        }

    return {
        "tipo": "EXCLUSIVO_FAMILIA",
        "grupo": familia,
        "regra_detalhada": False,
    }


def identificar_conjunto_torre(
    familia,
    material=None,
    estado=None,
    construcao=None,
    vedacao=None,
):
    """Retorna a representação lógica conhecida do G1 de uma válvula.

    Para o sistema genérico, as quatro dimensões são:
    material, estado, construção e vedação.

    Para sistemas exclusivos ainda não detalhados, o motor registra a
    classificação sem inventar combinações que ainda não foram validadas.
    """
    familia = _normalizar(familia)
    material = _normalizar_material(material)
    estado = _normalizar_estado(estado)
    construcao = _normalizar_construcao(construcao)
    vedacao = _normalizar_vedacao(vedacao)

    sistema = identificar_sistema_torre(
        familia=familia,
        material=material,
    )

    resultado = {
        "grupo_componente": "G1",
        "nome_grupo": "CONJUNTO_TORRE",
        "familia": familia,
        "sistema": sistema,
        "componentes": {
            "torre": None,
            "nucleo_movel": None,
            "mola": None,
        },
    }

    if sistema["tipo"] == "GENERICO":
        # A torre genérica muda com o material.
        resultado["componentes"]["torre"] = {
            "sistema": "GENERICO",
            "material": material,
            "estado": estado,
            "construcao": construcao,
            "vedacao": vedacao,
        }

        # No par equivalente latão/inox, núcleo móvel e mola permanecem
        # os mesmos. Por isso material não participa da identidade deles.
        resultado["componentes"]["nucleo_movel"] = {
            "sistema": "GENERICO",
            "estado": estado,
            "construcao": construcao,
            "vedacao": vedacao,
        }

        resultado["componentes"]["mola"] = {
            "sistema": "GENERICO",
            "estado": estado,
            "construcao": construcao,
            "vedacao": vedacao,
        }

    else:
        # Ainda não conhecemos todas as dimensões das famílias exclusivas.
        # Mantemos somente o que foi validado, sem fabricar regras.
        identidade_base = {
            "sistema": sistema["grupo"],
        }

        resultado["componentes"]["torre"] = identidade_base.copy()
        resultado["componentes"]["nucleo_movel"] = identidade_base.copy()
        resultado["componentes"]["mola"] = identidade_base.copy()

    if familia in FAMILIAS_NUCLEO_ACHATADO:
        resultado["componentes"]["nucleo_movel"]["formato"] = "ACHATADO"

    return resultado

"""G2 - Conjunto diafragma.

O G2 é formado por:
- diafragma;
- mola do diafragma;
- pulmão.

Regras estruturais validadas:
- família diferente implica diafragma diferente;
- vedação diferente implica diafragma diferente;
- diafragma e mola são inseparáveis: mudou o diafragma, mudou a mola;
- tamanho não é uma dimensão direta: cada família pode agrupar tamanhos que
  compartilham o mesmo diafragma;
- o pulmão pode variar independentemente do par diafragma + mola.

Regras atualmente conhecidas:
- 2036: somente configurações que não usam Teflon entram no G2.
  3/8" e 1/2" compartilham diafragma; 3/4", 1" e 1 1/2" são grupos distintos.
- 1330: no tamanho 08, presença/ausência da variante R altera o conjunto.
- 2030: nos tamanhos 12 e 16, presença/ausência de R altera o conjunto.
  No tamanho 10 existem três variantes: padrão, D e R.
  Os tamanhos grandes 10, 12 e 16 compartilham o mesmo tamanho-base de
  diafragma; a variante construtiva continua diferenciando o conjunto.
- 1335: em latão, 3/8" e 1/2" compartilham diafragma e 3/4" é outro grupo.
  Em inox, 1/2" e 3/4" compartilham diafragma.
  O pulmão tem quatro identidades: latão/inox × anclado/não anclado; R não o altera.
- 1332: possui diafragma; agrupamentos de tamanho pendentes.
- 2088: diafragma exclusivo, variando por vedação; agrupamentos pendentes.
- 3073: diafragma exclusivo, com grupos de 1, 1 1/2 e 2 polegadas.
- Mola do diafragma: aço inox 316L.

As demais famílias e agrupamentos serão acrescentados quando validados.
Este módulo contém apenas regras de engenharia.
"""

FAMILIA_2036 = "2036"
FAMILIA_1330 = "1330"
FAMILIA_2030 = "2030"
FAMILIA_1335 = "1335"
FAMILIAS_COM_DIAFRAGMA = frozenset({"1330", "1332", "1335", "2030", "2036", "2088", "3073"})


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


def _normalizar_material(material):
    valor = _normalizar(material)
    equivalencias = {
        "LATAO": "LATAO",
        "LATÃO": "LATAO",
        "INOX": "INOX",
        "ACO INOX": "INOX",
        "AÇO INOX": "INOX",
    }
    return equivalencias.get(valor, valor)


def _normalizar_tamanho(tamanho):
    valor = _normalizar(tamanho)
    equivalencias = {
        '3/8"': "3/8",
        "3/8": "3/8",
        '1/2"': "1/2",
        "1/2": "1/2",
        '3/4"': "3/4",
        "3/4": "3/4",
        '1"': "1",
        "1": "1",
        '1 1/4"': "1 1/4",
        "1 1/4": "1 1/4",
        '1-1/4"': "1 1/4",
        "1-1/4": "1 1/4",
        '1 1/2"': "1 1/2",
        "1 1/2": "1 1/2",
        '1-1/2"': "1 1/2",
        "1-1/2": "1 1/2",
        '2"': "2",
        "2": "2",
    }
    return equivalencias.get(valor, valor)


def _grupo_tamanho_2036(tamanho):
    if tamanho in {"3/8", "1/2"}:
        return "3/8_1/2"
    if tamanho in {"3/4", "1", "1 1/2"}:
        return tamanho
    return tamanho


def _grupo_tamanho_1335(tamanho, material_corpo):
    if material_corpo == "LATAO":
        if tamanho in {"3/8", "1/2"}:
            return "3/8_1/2"
        if tamanho == "3/4":
            return "3/4"

    if material_corpo == "INOX":
        if tamanho in {"1/2", "3/4"}:
            return "1/2_3/4"

    return tamanho


def _variante_construtiva(familia, tamanho_codigo, variante):
    """Resolve apenas as variantes R/D que alteram o G2."""
    tamanho_codigo = _normalizar(tamanho_codigo)
    variante = _normalizar(variante)

    if familia == FAMILIA_1330 and tamanho_codigo == "08":
        return "R" if variante == "R" else "PADRAO"

    if familia == FAMILIA_2030:
        if tamanho_codigo in {"12", "16"}:
            return "R" if variante == "R" else "PADRAO"

        if tamanho_codigo == "10":
            if variante in {"D", "R"}:
                return variante
            return "PADRAO"

    return None


def _grupo_tamanho(familia, tamanho, tamanho_codigo, material_corpo):
    if familia == FAMILIA_2036:
        return _grupo_tamanho_2036(tamanho)

    if familia == FAMILIA_1335:
        return _grupo_tamanho_1335(tamanho, material_corpo)

    if familia == FAMILIA_2030 and _normalizar(tamanho_codigo) in {"10", "12", "16"}:
        return "10_12_16"

    if familia == "1332" or familia == "2088":
        return None  # Grupos ainda não validados.

    if familia == "3073":
        return tamanho if tamanho in {"1", "1 1/2", "2"} else None

    return tamanho or _normalizar(tamanho_codigo)


def usa_diafragma(familia, vedacao=None):
    """Aplica apenas exclusões de G2 que já foram explicitamente validadas."""
    familia = _normalizar(familia)
    vedacao = _normalizar_vedacao(vedacao)

    if familia not in FAMILIAS_COM_DIAFRAGMA:
        return False

    if familia == FAMILIA_2036 and vedacao == "TEFLON":
        return False

    return True


def identificar_conjunto_diafragma(
    familia,
    tamanho=None,
    vedacao=None,
    material_corpo=None,
    tamanho_codigo=None,
    variante=None,
    sufixos=None,
):
    """Retorna a identidade lógica conhecida do G2.

    A função não cria códigos nominais de componentes. A identidade é derivada
    das características de engenharia já validadas.
    """
    familia = _normalizar(familia)
    tamanho = _normalizar_tamanho(tamanho)
    vedacao = _normalizar_vedacao(vedacao)
    material_corpo = _normalizar_material(material_corpo)
    tamanho_codigo = _normalizar(tamanho_codigo)

    if not usa_diafragma(familia=familia, vedacao=vedacao):
        return None

    grupo_tamanho = _grupo_tamanho(
        familia=familia,
        tamanho=tamanho,
        tamanho_codigo=tamanho_codigo,
        material_corpo=material_corpo,
    )

    variante_g2 = _variante_construtiva(
        familia=familia,
        tamanho_codigo=tamanho_codigo,
        variante=variante,
    )

    identidade_diafragma = {
        "familia": familia,
        "vedacao": vedacao,
        "grupo_tamanho": grupo_tamanho,
    }

    if variante_g2 is not None:
        identidade_diafragma["variante_construtiva"] = variante_g2

    # A mola acompanha obrigatoriamente o diafragma.
    identidade_mola = identidade_diafragma.copy()
    identidade_mola["material"] = "INOX 316L"
    identidade_diafragma["material"] = vedacao

    sufixos_normalizados = {
        _normalizar(item)
        for item in (sufixos or [])
        if _normalizar(item)
    }

    identidade_pulmao = {
        "familia": familia,
        "regra": "PADRAO",
    }

    if familia == FAMILIA_1335:
        identidade_pulmao = {
            "familia": familia,
            "material_corpo": material_corpo,
            "ancorada": "A" in sufixos_normalizados,
        }

    return {
        "grupo_componente": "G2",
        "nome_grupo": "CONJUNTO_DIAFRAGMA",
        "componentes": {
            "diafragma": identidade_diafragma,
            "mola": identidade_mola,
            "pulmao": identidade_pulmao,
        },
    }

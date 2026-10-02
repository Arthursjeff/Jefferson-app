"""Parser e identificação de kits de reparo Jefferson.

Este módulo trata a leitura estrutural do código do kit. A composição física
do kit (quais componentes G1-G5 ele contém) será acrescentada separadamente,
conforme as regras de engenharia forem validadas.

Estrutura-base conhecida:
    [prefixos] K [identificador da família] [vedação] [sequencial opcional] [sufixos]

Exemplos:
    K35A1
    K35A01
    K030A1
    ZK35A1
    K35A1Z
    K35A1A

Regras validadas:
- K identifica um kit de reparo;
- os dois dígitos-base identificam os dois últimos dígitos da família;
- um zero adicional pode ser usado para distinguir uma família 20xx quando
  houver famílias com os mesmos dois dígitos finais (ex.: K30 -> 1330,
  K030 -> 2030);
- o zero adicional não deve ser interpretado isoladamente sem considerar as
  famílias existentes;
- a letra após a identificação da família representa a vedação e reutiliza
  a mesma tabela de vedação do motor de descrição;
- o sequencial de tamanho é opcional e aceita zeros à esquerda: 1 == 01, 2 == 02 etc.;
- sem sequencial, existe um único grupo de kit para a família/vedação e ele atende todas as configurações aplicáveis;
- com sequencial, ele representa grupos físicos de tamanho, não a conexão diretamente;
- prefixos e sufixos podem modificar a aplicação do kit (ex.: Z);
- sufixos especiais como A podem distinguir uma variante construtiva do kit.
"""

import re

from motor_descricao import REGRAS_V01_TIPO_PRODUTO, REGRAS_V06_MATERIAL_VEDACAO


def _normalizar_codigo(codigo):
    if codigo is None:
        return ""
    return str(codigo).strip().upper().replace(" ", "")


def _familias_numericas_conhecidas():
    """Famílias numéricas cadastradas no motor de descrição."""
    return {
        familia
        for familia in REGRAS_V01_TIPO_PRODUTO
        if re.fullmatch(r"\d{4}", familia)
    }


def _familias_por_final(dois_digitos):
    return sorted(
        familia
        for familia in _familias_numericas_conhecidas()
        if familia.endswith(dois_digitos)
    )


def identificar_familia_kit(bloco_familia):
    """Resolve a família a partir do trecho numérico logo após o K.

    O bloco pode ter dois dígitos (ex.: 35) ou três começando em zero
    (ex.: 030). Quando existe conflito de finais, 0XX seleciona a família
    20XX. Sem o zero, prioriza a família não-20xx correspondente.

    Se a regra não permitir uma resolução segura, retorna None.
    """
    bloco = str(bloco_familia or "").strip()

    if not re.fullmatch(r"\d{2}|0\d{2}", bloco):
        return None

    tem_zero_distintivo = len(bloco) == 3
    final = bloco[-2:]
    candidatas = _familias_por_final(final)

    if not candidatas:
        return None

    if len(candidatas) == 1:
        return candidatas[0]

    if tem_zero_distintivo:
        candidatas_20 = [
            familia for familia in candidatas if familia.startswith("20")
        ]
        if len(candidatas_20) == 1:
            return candidatas_20[0]
        return None

    candidatas_nao_20 = [
        familia for familia in candidatas if not familia.startswith("20")
    ]
    if len(candidatas_nao_20) == 1:
        return candidatas_nao_20[0]

    return None


def interpretar_codigo_kit(codigo):
    """Interpreta somente a estrutura conhecida do código do kit.

    A função deliberadamente não determina ainda os componentes contidos
    no kit. O campo grupo_tamanho também fica como sequencial lógico até
    que o motor de componentes forneça o agrupamento técnico da família.
    """
    codigo_normalizado = _normalizar_codigo(codigo)

    if "K" not in codigo_normalizado:
        return {
            "sucesso": False,
            "erro": "Código não identificado como kit de reparo.",
            "codigo_original": codigo_normalizado,
        }

    posicao_k = codigo_normalizado.find("K")
    prefixos = codigo_normalizado[:posicao_k]
    restante = codigo_normalizado[posicao_k + 1:]

    # Tenta primeiro o formato com zero distintivo (0XX), depois XX.
    match_familia = re.match(r"(0\d{2}|\d{2})", restante)
    if not match_familia:
        return {
            "sucesso": False,
            "erro": "Identificador numérico da família não encontrado após K.",
            "codigo_original": codigo_normalizado,
        }

    bloco_familia = match_familia.group(1)
    familia = identificar_familia_kit(bloco_familia)

    if familia is None:
        return {
            "sucesso": False,
            "erro": "Não foi possível determinar com segurança a família do kit.",
            "codigo_original": codigo_normalizado,
            "bloco_familia": bloco_familia,
        }

    restante = restante[match_familia.end():]

    if not restante or not restante[0].isalpha():
        return {
            "sucesso": False,
            "erro": "Código de vedação não encontrado no kit.",
            "codigo_original": codigo_normalizado,
            "familia": familia,
        }

    codigo_vedacao = restante[0]
    vedacao = REGRAS_V06_MATERIAL_VEDACAO.get(codigo_vedacao)
    restante = restante[1:]

    match_sequencial = re.match(r"\d+", restante)

    if match_sequencial:
        sequencial_original = match_sequencial.group()
        sequencial_tamanho = int(sequencial_original)
        sufixos = restante[match_sequencial.end():]
    else:
        # Sem número = kit único para a família/vedação.
        sequencial_original = None
        sequencial_tamanho = None
        sufixos = restante

    return {
        "sucesso": True,
        "erro": None,
        "classe_produto": "KIT_REPARO",
        "codigo_original": codigo_normalizado,
        "prefixos": list(prefixos),
        "bloco_familia": bloco_familia,
        "familia": familia,
        "codigo_vedacao": codigo_vedacao,
        "vedacao": vedacao,
        "sequencial_original": sequencial_original,
        "sequencial_tamanho": sequencial_tamanho,
        "sufixos": list(sufixos),
        "grupo_tamanho": None,
        "aplicacoes": None,
        "componentes": None,
    }


def codigo_parece_kit(codigo):
    """Reconhece K no início ou após prefixos, como ZK..."""
    codigo_normalizado = _normalizar_codigo(codigo)
    return bool(re.match(r"^[A-Z]*K", codigo_normalizado))



def _nome_material_vedacao(vedacao):
    """Nome curto do material para compor nomes legíveis de componentes."""
    mapa = {
        "Buna-N (NBR)": "Buna-N",
        "Viton (FKM)": "Viton",
        "Etileno (EPDM)": "EPDM",
        "Teflon (PTFE)": "Teflon",
        "Neoprene": "Neoprene",
        "Delryin": "Delryin",
        "Inox": "Inox",
    }
    return mapa.get(vedacao, vedacao or "vedação não identificada")


def identificar_componentes_por_familia(resultado):
    """Cruza família + vedação + variante com os grupos já validados.

    Retorna somente componentes que sabemos que pertencem ao kit.
    Não exibe componentes condicionais como se estivessem presentes.
    """
    familia = resultado.get("familia")
    vedacao = resultado.get("vedacao")
    material = _nome_material_vedacao(vedacao)
    sufixos = set(resultado.get("sufixos") or [])

    componentes = {
        "G1": [
            "Núcleo móvel",
            f"Assento em {material}",
            "Mola do núcleo móvel",
        ],
        "G2": [],
        "G3": [],
        "G4": [],
        "G5": [],
    }

    # G2 - famílias cujo conjunto diafragma já foi validado.
    if familia in {"1330", "2030", "1335"}:
        componentes["G2"] = [
            f"Diafragma em {material}",
            "Mola do diafragma",
            "Pulmão",
        ]

    if familia == "2036" and resultado.get("codigo_vedacao") != "T":
        componentes["G2"] = [
            f"Diafragma em {material}",
            "Mola do diafragma",
            "Pulmão",
        ]

    # G3 - o pistão físico nunca entra no kit.
    if familia == "1342":
        componentes["G3"] = ["Mola do pistão"]

    if familia == "2036" and resultado.get("codigo_vedacao") == "T":
        componentes["G3"] = ["Mola do pistão"]

    # 1335 só possui G3 na variante D. Um K35A2 comum, por exemplo, não tem G3.
    if familia == "1335" and "D" in sufixos:
        componentes["G3"] = ["Mola do pistão"]

    # G4 - somente famílias de carretel já validadas.
    if familia in {"1330", "2030", "1325"}:
        componentes["G4"] = ["Carretel"]

    # G5 - somente O-rings cuja presença já foi confirmada.
    if familia == "1342":
        componentes["G5"] = [
            f"O-ring da tampa em {material}",
            f"O-ring da torre em {material}",
        ]

    if familia == "2036":
        componentes["G5"] = [
            f"O-ring da tampa em {material}",
        ]
        if resultado.get("codigo_vedacao") == "T":
            componentes["G5"].append(
                f"O-ring da torre em {material}"
            )
            componentes["G5"].append(
                "Disco de Teflon da tampa"
            )

    return componentes


def regra_geral_componentes_kit():
    """Mantém documentada a regra-base sem usá-la como presença automática."""
    return {
        "G1": "núcleo móvel + assento + mola do núcleo móvel",
        "G2": "diafragma + mola do diafragma + pulmão, se a família possuir G2",
        "G3": "mola do pistão e sua vedação, se a configuração possuir G3; pistão físico não entra",
        "G4": "carretel, se a família possuir G4",
        "G5": "O-rings aplicáveis já validados para a família",
    }


def identificar_componentes_kit(codigo):
    """Entrada pública inicial do motor de kits.

    Por enquanto retorna a interpretação do código. A composição G1-G5 será
    preenchida quando as regras de conteúdo dos kits forem consolidadas.
    """
    return interpretar_codigo_kit(codigo)


# =============================================================
# APLICAÇÕES INICIAIS DOS KITS - PARA VALIDAÇÃO NO ORÇAMENTO
# =============================================================
#
# O sequencial representa GRUPOS físicos de tamanho.
# Só entram aqui agrupamentos já conhecidos. Lacunas permanecem pendentes.
#

GRUPOS_TAMANHO_KIT = {
    "1335": {
        # Regra atualmente validada para corpo em latão.
        1: ["3/8\"", "1/2\""],
        2: ["3/4\""],
    },
    "2036": {
        1: ["3/8\"", "1/2\""],
        2: ["3/4\""],
        3: ["1\""],
        4: ["1 1/2\""],
    },
}


def _aplicacoes_por_sequencial(familia, sequencial):
    if sequencial is None:
        return "TODAS_AS_CONFIGURACOES_APLICAVEIS"
    return GRUPOS_TAMANHO_KIT.get(familia, {}).get(sequencial)


def _descricao_tamanhos(tamanhos):
    if tamanhos == "TODAS_AS_CONFIGURACOES_APLICAVEIS":
        return "todos os tamanhos/configurações aplicáveis"
    if not tamanhos:
        return None
    if len(tamanhos) == 1:
        return tamanhos[0]
    return " e ".join(tamanhos)


def gerar_variaveis_kit(resultado):
    """Converte o parser do kit em variáveis V para inspeção no orçamento."""
    familia = resultado.get("familia")
    sequencial = resultado.get("sequencial_tamanho")
    tamanhos = _aplicacoes_por_sequencial(familia, sequencial)
    componentes = identificar_componentes_por_familia(resultado)

    return {
        "V01": "Kit de reparo",
        "V06": resultado.get("vedacao"),
        "V07": _descricao_tamanhos(tamanhos),
        "V18": {
            "familia": familia,
            "sequencial_tamanho": sequencial,
            "tamanhos_aplicaveis": tamanhos,
            "prefixos": resultado.get("prefixos") or [],
            "sufixos": resultado.get("sufixos") or [],
        },
        # Componentes separados por grupo para facilitar a validação visual.
        "V20": componentes["G1"],
        "V21": componentes["G2"],
        "V22": componentes["G3"],
        "V23": componentes["G4"],
        "V24": componentes["G5"],
    }


def gerar_descricao_kit(resultado):
    familia = resultado.get("familia")
    vedacao = resultado.get("vedacao")
    tamanhos = _aplicacoes_por_sequencial(
        familia,
        resultado.get("sequencial_tamanho"),
    )

    partes = [f"Kit de reparo para válvula família {familia}"]

    if tamanhos:
        partes.append(f"tamanho {_descricao_tamanhos(tamanhos)}")
    elif resultado.get("sequencial_tamanho") is not None:
        partes.append(
            f"grupo de tamanho {resultado.get('sequencial_tamanho')} "
            "(tamanho ainda não mapeado)"
        )

    if vedacao:
        partes.append(f"vedação {vedacao}")

    return ", ".join(partes)


def processar_kit(codigo):
    """Processa kit para uso pela interface de orçamento."""
    resultado = interpretar_codigo_kit(codigo)

    if not resultado.get("sucesso"):
        return {
            "sucesso": False,
            "erro": resultado.get("erro"),
            "parser": resultado,
            "variaveis": None,
            "descricao": None,
        }

    resultado["aplicacoes"] = _aplicacoes_por_sequencial(
        resultado.get("familia"),
        resultado.get("sequencial_tamanho"),
    )
    resultado["componentes"] = identificar_componentes_por_familia(resultado)

    return {
        "sucesso": True,
        "erro": None,
        "parser": resultado,
        "variaveis": gerar_variaveis_kit(resultado),
        "descricao": gerar_descricao_kit(resultado),
    }

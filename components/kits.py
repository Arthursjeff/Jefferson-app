"""Parser e identificação de kits de reparo Jefferson.

Este módulo trata a leitura estrutural do código do kit. A composição física
do kit (quais componentes G1-G5 ele contém) será acrescentada separadamente,
conforme as regras de engenharia forem validadas.

Estrutura-base conhecida:
    [prefixos] K [identificador da família] [vedação] [sequencial] [sufixos]

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
- o sequencial de tamanho aceita zeros à esquerda: 1 == 01, 2 == 02 etc.;
- o sequencial representa grupos físicos de tamanho, não a conexão diretamente;
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
    if not match_sequencial:
        return {
            "sucesso": False,
            "erro": "Sequencial de tamanho do kit não encontrado.",
            "codigo_original": codigo_normalizado,
            "familia": familia,
            "codigo_vedacao": codigo_vedacao,
            "vedacao": vedacao,
        }

    sequencial_original = match_sequencial.group()
    sequencial_tamanho = int(sequencial_original)
    sufixos = restante[match_sequencial.end():]

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
    return GRUPOS_TAMANHO_KIT.get(familia, {}).get(sequencial)


def _descricao_tamanhos(tamanhos):
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
    regra = regra_geral_componentes_kit()

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
        "V20": regra["G1"],
        "V21": regra["G2"],
        "V22": regra["G3"],
        "V23": regra["G4"],
        "V24": regra["G5"],
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
    else:
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
    resultado["componentes"] = regra_geral_componentes_kit()

    return {
        "sucesso": True,
        "erro": None,
        "parser": resultado,
        "variaveis": gerar_variaveis_kit(resultado),
        "descricao": gerar_descricao_kit(resultado),
    }

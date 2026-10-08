"""Consulta técnica de componentes sem alterar o orçamento."""
from motor_descricao import processar_produto
from components.kits import codigo_parece_kit, processar_kit, GRUPOS_TAMANHO_KIT, identificar_familia_kit, _familias_por_final, REGRAS_V06_MATERIAL_VEDACAO
from components.internos.torre import identificar_conjunto_torre
from components.internos.diafragma import identificar_conjunto_diafragma
from components.internos.pistao import identificar_conjunto_pistao
from components.internos.carretel import identificar_conjunto_carretel
from components.internos.orings import identificar_orings


def sugerir_kit_reparo(parser, variaveis):
    """Retorna somente códigos que podem ser justificados pelas regras atuais."""
    familia = str(parser.get("familia") or "")
    vedacao_codigo = parser.get("codigo_vedacao")
    tamanho = variaveis.get("V07")
    material = str(variaveis.get("V05") or "").upper()
    if not (len(familia) == 4 and familia.isdigit() and vedacao_codigo in REGRAS_V06_MATERIAL_VEDACAO):
        return {"status": "não determinado", "motivo": "Família ou código de vedação não identificado."}
    final = familia[-2:]
    candidatas = _familias_por_final(final)
    if familia.startswith("20") and len(candidatas) > 1:
        bloco = "0" + final
    elif len(candidatas) == 1 or (not familia.startswith("20") and len([x for x in candidatas if not x.startswith("20")]) == 1):
        bloco = final
    else:
        return {"status": "não determinado", "motivo": "A identificação da família no código do kit é ambígua."}
    if identificar_familia_kit(bloco) != familia:
        return {"status": "não determinado", "motivo": "Não há identificação inequívoca da família no motor de kits."}

    base = "K" + bloco + vedacao_codigo
    grupos = GRUPOS_TAMANHO_KIT.get(familia)
    if not grupos:
        return {"status": "provável — conferir", "codigo": base,
                "motivo": "Família e vedação identificadas, mas o sequencial de tamanho não está mapeado. Código-base apenas; não é um kit confirmado."}
    if not tamanho:
        return {"status": "não determinado", "motivo": "Tamanho da conexão não identificado."}
    encontrados = [seq for seq, tamanhos in grupos.items() if tamanho in tamanhos]
    if len(encontrados) != 1:
        return {"status": "não determinado", "motivo": "O tamanho não corresponde a um único grupo cadastrado."}
    sequencial = encontrados[0]
    codigo = base + str(sequencial)
    observacoes = []
    prefixos = parser.get("prefixos") or []
    sufixos = parser.get("sufixos") or []
    if prefixos or sufixos or parser.get("letra_especial"):
        observacoes.append("Verificar prefixos, sufixos e variantes construtivas.")
    if familia == "1335" and "LAT" not in material:
        observacoes.append("O agrupamento da família 1335 foi validado somente para corpo em latão.")
    if familia == "2036" and vedacao_codigo == "T":
        observacoes.append("Confirmar a variante PTFE da família 2036.")
    if observacoes:
        return {"status": "provável — conferir", "codigo": codigo,
                "motivo": " ".join(observacoes), "tamanho": tamanho}
    return {"status": "identificado pelo mapeamento atual", "codigo": codigo,
            "motivo": "Família, vedação e grupo de tamanho correspondem ao cadastro atual.",
            "tamanho": tamanho}


def consultar_codigo(codigo, tensao=""):
    kit = codigo_parece_kit(codigo)
    resultado = processar_kit(codigo) if kit else processar_produto(codigo, tensao)
    if kit or not resultado.get("sucesso"):
        return {"kit": kit, "resultado": resultado, "grupos": {}, "pendencias": [], "kit_correspondente": None}
    parser = resultado.get("parser") or {}
    v = resultado.get("variaveis") or {}
    familia = parser.get("familia")
    material = v.get("V05")
    vedacao = v.get("V06")
    tamanho = v.get("V07")
    estado = v.get("V04")
    sufixos = parser.get("sufixos") or []
    letra = parser.get("letra_especial")
    variante = letra if letra in {"D", "R"} else next((x for x in sufixos if x in {"D", "R"}), None)
    pendencias = []
    grupos = {}
    regras = {
        "G1 — Torre e núcleo": lambda: identificar_conjunto_torre(familia, material=material, estado=estado, vedacao=vedacao, final=letra, bitola=tamanho, construcao="Z" if "Z" in (parser.get("prefixos") or []) else None),
        "G2 — Diafragma": lambda: identificar_conjunto_diafragma(familia, tamanho=tamanho, vedacao=vedacao, material_corpo=material, tamanho_codigo=parser.get("codigo_conexao"), variante=variante, sufixos=sufixos),
        "G3 — Pistão": lambda: identificar_conjunto_pistao(familia, tamanho=tamanho, vedacao=vedacao, material_corpo=material, sufixos=list(sufixos) + ([letra] if letra else [])),
        "G4 — Carretel": lambda: identificar_conjunto_carretel(familia, estado=estado, material_corpo=material),
        "G5 — O-rings": lambda: identificar_orings(familia, vedacao=parser.get("codigo_vedacao"), tamanho=tamanho),
    }
    for nome, funcao in regras.items():
        try:
            grupos[nome] = funcao()
        except Exception as exc:
            grupos[nome] = None
            pendencias.append(f"{nome}: não foi possível executar a identificação ({exc.__class__.__name__}).")
    for nome, valor in (("material do corpo", material), ("vedação", vedacao), ("tamanho", tamanho), ("funcionamento", estado)):
        if not valor:
            pendencias.append(f"Não foi possível determinar {nome}.")
    return {"kit": False, "resultado": resultado, "grupos": grupos, "pendencias": pendencias, "kit_correspondente": sugerir_kit_reparo(parser, v)}

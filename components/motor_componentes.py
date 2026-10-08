"""Consulta técnica de componentes sem alterar o orçamento."""
from motor_descricao import processar_produto
from components.kits import codigo_parece_kit, processar_kit, GRUPOS_TAMANHO_KIT, FAMILIAS_KIT_SEM_GRUPO, GRUPOS_CODIGO_CONEXAO_1342, KIT_ESPECIAL_2094, identificar_familia_kit, _familias_por_final, REGRAS_V06_MATERIAL_VEDACAO
from components.internos.torre import identificar_conjunto_torre
from components.internos.diafragma import identificar_conjunto_diafragma
from components.internos.pistao import identificar_conjunto_pistao
from components.internos.carretel import identificar_conjunto_carretel
from components.internos.orings import identificar_orings


def sugerir_kit_reparo(parser, variaveis, grupos_componentes=None):
    """Sugere apenas referências sustentadas pelo cadastro e engenharia.

    O motor G2/G3/G5 informa identidades físicas; o sequencial comercial
    só é emitido quando há uma equivalência validada.
    """
    familia = str(parser.get("familia") or "")
    vedacao_codigo = parser.get("codigo_vedacao")
    tamanho = variaveis.get("V07")
    material = str(variaveis.get("V05") or "").upper()
    prefixos = parser.get("prefixos") or []
    sufixos = parser.get("sufixos") or []
    letra = parser.get("letra_especial")
    especiais = bool(prefixos or sufixos or letra)

    def pendente(motivo, codigo=None):
        resposta = {"status": "provável — conferir" if codigo else "não determinado",
                    "motivo": motivo}
        if codigo:
            resposta["codigo"] = codigo
        return resposta

    if familia == "2094":
        return pendente(
            "A família utiliza conjunto único; K094RBD2Z é referência conhecida "
            "para a variante Z. Confirmar aplicação exata da construção consultada.",
            KIT_ESPECIAL_2094,
        )
    if not (len(familia) == 4 and familia.isdigit()
            and vedacao_codigo in REGRAS_V06_MATERIAL_VEDACAO):
        return pendente("Família ou código de vedação não identificado.")

    final = familia[-2:]
    candidatas = _familias_por_final(final)
    if familia.startswith("20") and len(candidatas) > 1:
        bloco = "0" + final
    elif len(candidatas) == 1 or (
        not familia.startswith("20")
        and len([x for x in candidatas if not x.startswith("20")]) == 1
    ):
        bloco = final
    else:
        return pendente("Identificação da família no código do kit é ambígua.")
    if identificar_familia_kit(bloco) != familia:
        return pendente("Família não resolvida inequivocamente no motor de kits.")

    base = "K" + bloco + vedacao_codigo
    grupo = None
    if familia in FAMILIAS_KIT_SEM_GRUPO:
        # A lista de kits comprova os materiais disponíveis por família.
        materiais = {"1327": {"A", "E", "T", "V"}, "2026": {"A", "E", "V"}}
        if vedacao_codigo not in materiais[familia]:
            return pendente("Não há código de kit conhecido para esta vedação.")
        codigo = base
    elif familia == "1342":
        codigo_conexao = str(parser.get("codigo_conexao") or "").zfill(2)
        grupo = GRUPOS_CODIGO_CONEXAO_1342.get(codigo_conexao)
        if grupo is None:
            return pendente("Código de conexão sem grupo comercial confirmado na 1342.")
        if vedacao_codigo not in {"A", "E", "T", "V"}:
            return pendente("Vedação não consta da lista de kits 1342.")
        codigo = base + str(grupo)
    else:
        grupos = GRUPOS_TAMANHO_KIT.get(familia)
        if not grupos:
            return pendente(
                "Há regras de componentes internos, mas falta a equivalência "
                "entre grupo físico e número comercial do kit.", base,
            )
        if not tamanho:
            return pendente("Tamanho da conexão não identificado.")
        encontrados = [seq for seq, tamanhos in grupos.items() if tamanho in tamanhos]
        if len(encontrados) != 1:
            return pendente("Tamanho não corresponde a um grupo comercial validado.")
        grupo = encontrados[0]
        codigo = base + str(grupo)

    observacoes = []
    if especiais:
        observacoes.append("Verificar prefixos, sufixos e variantes construtivas.")
    if familia == "1335" and "LAT" not in material:
        observacoes.append("Grupos comerciais da 1335 validados apenas para latão.")
    if familia == "2036":
        if grupo == 4:
            observacoes.append("Confirmar referência comercial do quarto grupo 2036.")
        if vedacao_codigo == "T":
            observacoes.append("Confirmar aplicação do kit PTFE da 2036.")
    if familia in {"1330", "2030"}:
        observacoes.append(
            "Confirmar reforço da membrana (R), variantes e construção do kit."
        )
    if familia == "1342" and grupos_componentes is not None:
        # O G3 fornece evidência física adicional; não altera o número comercial.
        pistao = grupos_componentes.get("G3 — Pistão")
        if pistao is None:
            observacoes.append("Conjunto de pistão não identificado para conferência.")
    if observacoes:
        return pendente(" ".join(observacoes), codigo)
    return {"status": "identificado pelo mapeamento atual",
            "codigo": codigo,
            "motivo": "Família, vedação e grupo comercial compatíveis com o cadastro.",
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
    return {"kit": False, "resultado": resultado, "grupos": grupos, "pendencias": pendencias, "kit_correspondente": sugerir_kit_reparo(parser, v, grupos)}

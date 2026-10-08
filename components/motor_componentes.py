"""Consulta técnica de componentes sem alterar o orçamento."""
from motor_descricao import processar_produto
from components.kits import codigo_parece_kit, processar_kit
from components.internos.torre import identificar_conjunto_torre
from components.internos.diafragma import identificar_conjunto_diafragma
from components.internos.pistao import identificar_conjunto_pistao
from components.internos.carretel import identificar_conjunto_carretel
from components.internos.orings import identificar_orings


def consultar_codigo(codigo, tensao=""):
    kit = codigo_parece_kit(codigo)
    resultado = processar_kit(codigo) if kit else processar_produto(codigo, tensao)
    if kit or not resultado.get("sucesso"):
        return {"kit": kit, "resultado": resultado, "grupos": {}, "pendencias": []}
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
    if familia == "2088":
        pendencias.append("G5: O-ring da tampa da família 2088 ainda não cadastrado no motor.")
    return {"kit": False, "resultado": resultado, "grupos": grupos, "pendencias": pendencias}

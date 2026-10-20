"""Laboratório: transformação por kit (2030 grande), sem movimentar estoque."""
import re
from components.internos.carretel import identificar_conjunto_carretel
from components.internos.diafragma import identificar_conjunto_diafragma

OPCOES = {"NA_NF": "NA – NF", "VEDACAO": "Troca de vedação", "REFORCO": "Troca de reforço"}
# NA é o estado aberto 2030, sem NA é NF. NPT pode ser representado por T.
_P = re.compile(r"^2030L(?P<vedacao>[AV])(?P<variante>[RD]?)(?P<tamanho>10|12|16)(?P<resto>(?:NA)?T?|TNA)$")
_K = re.compile(r"^K030(?P<vedacao>[AV])(?P<reforco>R?)2$")


def parse(codigo):
    m = _P.fullmatch(re.sub(r"\s+", "", str(codigo or "").upper()))
    if not m:
        return None
    p = m.groupdict()
    if (p["tamanho"] == "10" and p["variante"] not in ("R", "D")) or (
            p["tamanho"] in ("12", "16") and p["variante"] == "D"):
        return None
    resto = p.pop("resto")
    p.update(codigo=m.group(), familia="2030", corpo="L", na="NA" in resto,
             rosca="NPT" if "T" in resto else "BSP",
             reforco=p["variante"] == "R")
    return p


def montar(p, vedacao=None, variante=None, na=None):
    c = "2030L" + (p["vedacao"] if vedacao is None else vedacao)
    c += p["variante"] if variante is None else variante
    c += p["tamanho"] + ("NA" if (p["na"] if na is None else na) else "")
    c += "T" if p["rosca"] == "NPT" else ""
    return c if parse(c) else None


def mesmo_corpo(a, b):
    return bool(a and b and all(a[k] == b[k] for k in ("familia", "corpo", "tamanho", "rosca")))


def identidade_g2(p):
    tamanho = {"10": '1 1/4"', "12": '1 1/2"', "16": '2"'}[p["tamanho"]]
    vedacao = {"A": "BUNA-N", "V": "VITON"}[p["vedacao"]]
    g2 = identificar_conjunto_diafragma(
        "2030", tamanho=tamanho, vedacao=vedacao, material_corpo="LATAO",
        tamanho_codigo=p["tamanho"], variante=p["variante"])
    return g2["componentes"]["diafragma"] if g2 else None


def conjunto_igual(a, b):
    """Compara construção, vedação, NA/NF e identidade G2; tamanho pode variar."""
    if not a or not b or a["na"] != b["na"]:
        return False
    g4a = identificar_conjunto_carretel("2030", "NA" if a["na"] else "NF")
    g4b = identificar_conjunto_carretel("2030", "NA" if b["na"] else "NF")
    return (identidade_g2(a) is not None and identidade_g2(a) == identidade_g2(b)
            and g4a["identidade"] == g4b["identidade"])


def _oposto_na(p):
    return montar(p, na=not p["na"])


def _oposto_reforco(p):
    return None if p["variante"] == "D" else montar(
        p, variante="" if p["reforco"] else "R")


def avaliar(destino, operacao, estoque, carreteis=None):
    """Carretéis avulsos são códigos ERP identificados pelo operador, não inferidos."""
    destino = re.sub(r"\s+", "", str(destino or "").upper())
    p = parse(destino)
    r = {"tipo": "KIT", "destino": destino, "familia": "2030",
         "operacao": operacao, "base": [], "doadores": [], "pendencias": [],
         "status": "EM ESTUDO", "estoque_exato": estoque.get(destino, 0),
         "metodo": ""}
    if not p:
        r["pendencias"].append("A regra atende 2030L, vedação A/V, tamanho 12/16 ou 10 com R/D.")
        return r
    if operacao not in OPCOES:
        r["pendencias"].append("Escolha uma operação disponível para a família.")
        return r
    r["configuracao"] = dict(vedacao=p["vedacao"], funcionamento="NA" if p["na"] else "NF",
                            variante=p["variante"] or "PADRAO", rosca=p["rosca"])
    valvulas = [(codigo, qtd, parse(codigo)) for codigo, qtd in estoque.items()
               if qtd > 0 and parse(codigo)]
    if operacao == "NA_NF":
        base = _oposto_na(p)
        r["codigo_base_esperado"] = base
        r["metodo"] = "VALVULA_CARRETEL" if p["vedacao"] == "A" else "VALVULA_VALVULA"
        if estoque.get(base, 0) > 0:
            r["base"].append(dict(codigo=base, quantidade=estoque[base]))
        if p["vedacao"] == "A":
            estado = "NA" if p["na"] else "NF"
            sku = (carreteis or {}).get(estado, "").strip().upper()
            if sku and estoque.get(sku, 0) > 0:
                r["doadores"].append(dict(codigo=sku, quantidade=estoque[sku],
                                          origem="CARRETEL", estado=estado))
            else:
                r["pendencias"].append("Código e saldo ERP do carretel %s não localizados." % estado)
        else:
            for codigo, qtd, item in valvulas:
                if codigo != destino and item["vedacao"] == "V" and item["na"] == p["na"]:
                    r["doadores"].append(dict(codigo=codigo, quantidade=qtd,
                                              origem="VALVULA"))
    elif operacao == "VEDACAO":
        r["metodo"] = "VALVULA_VALVULA"
        for codigo, qtd, item in valvulas:
            if codigo != destino and mesmo_corpo(p, item):
                r["base"].append(dict(codigo=codigo, quantidade=qtd))
            if codigo != destino and conjunto_igual(p, item):
                r["doadores"].append(dict(codigo=codigo, quantidade=qtd,
                                          origem="VALVULA"))
    else:
        r["metodo"] = "VALVULA_KIT"
        base = _oposto_reforco(p)
        if base is None:
            r["pendencias"].append("A variante D não possui regra de troca de reforço.")
            return r
        r["codigo_base_esperado"] = base
        if estoque.get(base, 0) > 0:
            r["base"].append(dict(codigo=base, quantidade=estoque[base]))
        kit = "K030" + p["vedacao"] + ("R" if p["reforco"] else "") + "2"
        r["codigo_kit_esperado"] = kit
        if _K.fullmatch(kit) and estoque.get(kit, 0) > 0:
            r["doadores"].append(dict(codigo=kit, quantidade=estoque[kit], origem="KIT"))

    r["base"].sort(key=lambda x: (-x["quantidade"], x["codigo"]))
    r["doadores"].sort(key=lambda x: (-x["quantidade"], x["codigo"]))
    if not r["base"]:
        r["pendencias"].append("Nenhuma válvula base compatível em estoque.")
    if not r["doadores"]:
        r["pendencias"].append("Nenhuma doadora/kit/carretel compatível em estoque.")
    if r["base"] and r["doadores"]:
        r["status"] = "SIMULACAO_POSSIVEL"
    elif r["base"]:
        r["status"] = "BASE_LOCALIZADA"
    elif r["doadores"]:
        r["status"] = "DOADORES_LOCALIZADOS"
    return r


def calcular_residual(resultado, base, doadora, carreteis=None):
    if resultado.get("status") != "SIMULACAO_POSSIVEL":
        raise ValueError("Necessária base e doadora disponíveis.")
    if base not in [x["codigo"] for x in resultado["base"]]:
        raise ValueError("Base não disponível.")
    if doadora not in [x["codigo"] for x in resultado["doadores"]]:
        raise ValueError("Doadora não disponível.")
    destino = parse(resultado["destino"])
    b = parse(base)
    op = resultado["operacao"]
    if op == "NA_NF":
        if base != _oposto_na(destino):
            raise ValueError("Base deve ter NA/NF oposto.")
        if destino["vedacao"] == "A":
            estado = "NF" if destino["na"] else "NA"
            residual = (carreteis or {}).get(estado, "").strip().upper()
            if not residual or residual == doadora:
                raise ValueError("Informe código ERP distinto do carretel residual %s." % estado)
            tipo_residual = "CARRETEL"
        else:
            d = parse(doadora)
            if not d or d["vedacao"] != "V" or d["na"] != destino["na"]:
                raise ValueError("Doadora Viton inadequada.")
            residual, tipo_residual = _oposto_na(d), "VALVULA"
    elif op == "VEDACAO":
        d = parse(doadora)
        if not (mesmo_corpo(destino, b) and conjunto_igual(destino, d)):
            raise ValueError("Corpo ou conjunto de vedação doadora incompatível.")
        residual = montar(d, vedacao=b["vedacao"], variante=b["variante"], na=b["na"])
        tipo_residual = "VALVULA"
        if not residual:
            raise ValueError("Residual da doadora inválido (variante R/D incompatível com o tamanho).")
    elif op == "REFORCO":
        if base != _oposto_reforco(destino) or doadora != resultado.get("codigo_kit_esperado"):
            raise ValueError("Base ou kit não corresponde à variante desejada.")
        residual = "K030" + destino["vedacao"] + ("" if destino["reforco"] else "R") + "2"
        tipo_residual = "KIT"
        if not _K.fullmatch(residual):
            raise ValueError("Kit residual não reconhecido.")
    else:
        raise ValueError("Operação não reconhecida.")
    if not residual:
        raise ValueError("Código residual não reconhecido.")
    return dict(produto_final=resultado["destino"], valvula_base=base, origem=doadora,
                produto_residual=residual, tipo_residual=tipo_residual,
                quantidade=1, simulacao=True)

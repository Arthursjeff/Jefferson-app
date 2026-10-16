"""Motor de inferência ERP -> Jefferson V0.6.

Regras derivadas da amostra histórica de 5.623 equivalências.
NÃO certifica equivalência, material, tensão, acessórios ou aplicação.
"""
import re

FAMILIAS = {
    "024": "2024", "026": "2026", "030": "2030", "035": "2035",
    "036": "2036", "038": "2038", "050": "2050", "051": "2051",
    "073": "3073", "088": "2088", "094": "2094", "095": "2095",
    "099": "2099", "14": "1314", "23": "1323", "25": "1325",
    "27": "1327", "30": "1330", "35": "1335", "36": "2036",
    "42": "1342", "51": "1351", "60": "1360", "65": "1365",
    "73": "3073", "90": "1390", "97": "1397", "3014": "3014",
}
# Os prefixos mais específicos precisam vir primeiro.
PREFIXOS = tuple(sorted((
    "EZC", "ZCL", "ZCP", "ZRC", "ZC", "YC", "PA", "PE",
    "LP", "RC", "SI", "EZ", "Z", "E", "Y", "C",
), key=len, reverse=True))
VALVULA_COMPLETA = re.compile(r"^(?:[A-Z]{0,4}|V\d{2,4}-?)(?:13|20|30)\d{2}[A-Z][A-Z0-9/.-]+$")
KIT_COMPLETO = re.compile(r"^(?:Z?E?K|KZ)[A-Z0-9/.-]+$")
TAMANHO = re.compile(r"^([A-Z]{1,5})(\d{1,3})([A-Z0-9/.-]*)$")


def normal(valor):
    return re.sub(r"\s+", "", str(valor or "").strip().upper())


def categoria(codigo, descricao=""):
    c, d = normal(codigo), normal(descricao)
    if (re.match(r"^(?:ZK|EK|KZ|K\d)", c)
            or re.match(r"^(102|202)[-/]", c)
            or any(p in d for p in ("KITREPARO", "KITDEREPARO", "KITDEREPARACAO"))):
        return "KIT"
    if "BOBINA" in d or re.match(r"^(?:MH|GF|M\d|S\d)", c):
        return "BOBINA"
    if ("PISTAO" in d or "TERMOPAR" in d or "CUERPO" in d
            or re.match(r"^(?:SUD-|785\d+)", c)):
        return "PECA"
    if "VALVULA" in d or "VÁLVULA" in d:
        return "VALVULA"
    if (re.match(r"^(110|210|108|208|206)[-/]", c)
            or any(x in d for x in ("TORRE", "CONECTOR", "RETIFICADOR",
                                      "CONTROLADOR", "DIAFRAGMA"))):
        return "PECA"
    return "OUTRO"


def inferir_valvula(codigo):
    """Inferência estrutural; sem tentar converter família 12, tensão ou sufixo de lote."""
    c = normal(codigo)
    externo = re.match(r"^(\d{2,4})-(?=[A-Z])", c)
    familia_externa = externo.group(1) if externo else ""
    c = re.sub(r"^\d{2,4}-(?=[A-Z])", "", c)
    prefixo = ""
    for p in PREFIXOS:
        if c.startswith(p):
            prefixo, c = p, c[len(p):]
            break
    if familia_externa.startswith("0") and familia_externa in FAMILIAS:
        curto = familia_externa.lstrip("0")
        if curto and re.match("^" + re.escape(curto) + r"(?=[A-Z])", c):
            c = familia_externa + c[len(curto):]
    m = re.fullmatch(r"((?:13|20|30)\d{2})([A-Z]{1,5})(\d{1,3})([A-Z0-9/.-]*)", c)
    if m:
        fam, meio, num, fim = m.groups()
        if re.search(r"/\d|\d{1,3}V(?:CC|DC|CA|AC)", fim):
            return ""
        return prefixo + fam + meio + (num.zfill(2) if len(num) == 1 else num) + fim
    for fam in sorted(FAMILIAS, key=len, reverse=True):
        if not c.startswith(fam):
            continue
        m = TAMANHO.fullmatch(c[len(fam):])
        if not m:
            continue
        meio, num, fim = m.groups()
        if re.search(r"/\d|\d{1,3}V(?:CC|DC|CA|AC)", fim):
            return ""
        return prefixo + FAMILIAS[fam] + meio + (num.zfill(2) if len(num) == 1 else num) + fim
    return ""


def codigo_na_descricao(descricao):
    d = normal(descricao)
    if "VALVULA" not in d:
        return ""
    d = d.split("VALVULA", 1)[0]
    d = re.sub(r"^[^-]{0,16}-", "", d)
    return d if VALVULA_COMPLETA.fullmatch(d) else ""

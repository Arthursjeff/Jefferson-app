"""Conversor compartilhado de códigos ERP -> códigos técnicos Jefferson.

Recupera o conversor histórico de outubro/2026 e utiliza tabela de equivalências
como referência, nunca como autorização técnica automática. Não grava estoque.
"""
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import csv
import re

FAMILIAS = {
    "023": "1323", "23": "1323", "024": "2024", "026": "2026",
    "030": "2030", "035": "2035", "036": "2036", "038": "2038",
    "050": "2050", "051": "2051", "073": "3073", "088": "2088",
    "093": "2093", "094": "2094", "095": "2095", "099": "2099",
    "10": "1310", "11": "1311", "14": "1314", "25": "1325",
    "27": "1327", "30": "1330", "35": "1335", "36": "2036",
    "42": "1342", "65": "1365", "97": "1397",
    "12": "", "26": "", "56": "",
    "3014": "3014", "1330": "1330", "1327": "1327",
    "1342": "1342", "2030": "2030", "1335": "1335", "2036": "2036",
}
PREF = ("EZC", "ZCP", "ZRC", "ZC", "YC", "PA", "PE", "LP", "RC", "SI", "EK", "Z", "E", "Y", "C")
ESP = re.compile(r"^(?P<grupo>\d{2,4})-(?P<prefixo>[A-Z]+)(?P<resto>.+)$")
BASE = re.compile(r"^(?P<familia>\d{2,4})(?P<miolo>[A-Z]+)(?P<tamanho>\d{1,3})(?P<sufixo>[A-Z0-9/\-]*)$")
TECNICO = re.compile(r"^(?:[A-Z]{0,5}-?)?(?:13|20|30)\d{2}[A-Z][A-Z0-9/\-]*$")
DESCRICAO_TECNICA = re.compile(
    r"(?<![A-Z0-9])((?:(?:ZC|Z|YC|RC|LP|E|PA))?(?:13|20|30)\d{2})"
    r"[\s-]*([A-Z]{1,5})\s*(\d{1,3})([A-Z0-9/\-]*)"
)
KITS_LAB = frozenset((
    "K030A2", "K030AR2", "K030V2", "K030VR2",
    "K30A2", "K30AR2", "K30V2", "K30VR2",
))
MAPA = Path(__file__).resolve().parent / "data" / "equivalencias_erp_historicas.tsv"


@dataclass(frozen=True)
class Resultado:
    codigo_erp: str
    codigo_tecnico: str | None
    status: str
    metodo: str
    motivo: str


def normalizar(valor):
    return re.sub(r"\s+", "", str(valor or "").strip().upper())


@lru_cache(maxsize=1)
def carregar_equivalencias():
    """Equivalências de outubro de 2026; nunca carregar senhas ou chamar serviços."""
    mapa = {}
    with MAPA.open("r", encoding="utf-8-sig", newline="") as f:
        for linha in csv.reader(f, delimiter="\t"):
            if len(linha) < 2 or linha[0].startswith("#"):
                continue
            codigo, tecnico = normalizar(linha[0]), normalizar(linha[1])
            if not codigo or not TECNICO.fullmatch(tecnico):
                continue
            if codigo in mapa and mapa[codigo] != tecnico:
                # Uma contradição histórica não pode determinar identidade técnica.
                mapa.pop(codigo, None)
                continue
            mapa[codigo] = tecnico
    return mapa


def inferir_valvula(codigo):
    """Regra histórica de grupos/prefixos/bitolas; retorna hipótese, não homologação."""
    s = normalizar(codigo)
    prefixo = ""
    especial = ESP.fullmatch(s)
    if especial:
        grupo = especial["grupo"]
        texto = especial["prefixo"] + especial["resto"]
        prefixo = next((p for p in PREF if texto.startswith(p)), "")
        if not prefixo:
            return None, "Prefixo especial não conhecido"
        s = texto[len(prefixo):]
        if s.startswith(grupo):
            s = s[len(grupo):]
        elif s.startswith("20" + grupo) or s.startswith("13" + grupo):
            pass
        else:
            s = grupo + s
    m = BASE.fullmatch(s)
    if not m:
        return None, "Estrutura não reconhecida"
    familia = FAMILIAS.get(m["familia"])
    if not familia:
        return None, "Família ambígua ou ainda não mapeada"
    tamanho = m["tamanho"].zfill(2) if len(m["tamanho"]) == 1 else m["tamanho"]
    sufixo = m["sufixo"]
    if re.search(r"(?:12|24|110|220)V(?:CC|DC|CA|AC)$", sufixo):
        return None, "Tensão concatenada exige análise separada"
    candidato = prefixo + familia + m["miolo"] + tamanho + sufixo
    return (candidato, "Inferência sintática") if TECNICO.fullmatch(candidato) else (None, "Formato inválido")


def extrair_tecnico_descricao(descricao):
    """Obtém uma referência explícita na descrição; não interpreta peças genéricas."""
    texto = str(descricao or "").upper()
    achados = []
    for m in DESCRICAO_TECNICA.finditer(texto):
        codigo = "".join(m.groups())
        if TECNICO.fullmatch(codigo):
            achados.append(codigo)
    # Quando várias referências aparecem numa descrição, não escolher uma.
    unicos = list(dict.fromkeys(achados))
    return unicos[0] if len(unicos) == 1 else None


def converter(codigo_erp, descricao="", mapa=None):
    """CONFIRMADO exige confronto com descrição. INFERIDO não entra no saldo do Lab."""
    origem = normalizar(codigo_erp)
    if not origem:
        return Resultado(origem, None, "PENDENTE", "entrada", "Código vazio")
    desc = str(descricao or "").upper()
    if origem.startswith("EXP") or "EM CORTE" in desc:
        return Resultado(origem, None, "PENDENTE", "nao_operacional",
                         "Código de exposição/peça em corte; não usar como estoque de transformação")
    if origem in KITS_LAB:
        # Identificadores de kit são próprios e não são expandidos como válvula.
        if "KIT" in desc:
            return Resultado(origem, origem, "CONFIRMADO", "kit_identificado",
                             "Kit de reparo reconhecido para o Laboratório")
        return Resultado(origem, None, "PENDENTE", "kit", "Identidade de kit não confirmada")
    if "KIT" in desc or "BOBINA" in desc:
        return Resultado(origem, None, "PENDENTE", "tipo_produto",
                         "Kit/peça/bobina fora da interpretação de válvula")
    if origem.startswith(("101-", "101/", "102-", "102/", "202-", "202/", "210-")):
        return Resultado(origem, None, "PENDENTE", "codigo_interno",
                         "Código interno de peça/valvula requer correspondência específica")
    referencia = (mapa if mapa is not None else carregar_equivalencias()).get(origem)
    inferido, motivo = inferir_valvula(origem)
    if TECNICO.fullmatch(origem):
        inferido = origem
        motivo = "Código técnico já completo"
    candidato = referencia or inferido
    citado = extrair_tecnico_descricao(desc)
    if referencia and inferido and referencia != inferido:
        # Diferenças do mapa histórico são possíveis; confrontar com descrição.
        if citado and citado == referencia:
            return Resultado(origem, referencia, "CONFIRMADO", "mapa_descricao",
                             "Equivalência histórica confirmada pela descrição")
        if citado and citado == inferido:
            return Resultado(origem, inferido, "CONFIRMADO", "regra_descricao",
                             "A descrição confirma a regra sintática; mapa histórico diverge")
        return Resultado(origem, None, "DIVERGENTE", "mapa_regra",
                         "Equivalência histórica e inferência não coincidem")
    if candidato and citado:
        if citado == candidato:
            return Resultado(origem, candidato, "CONFIRMADO",
                             "mapa_descricao" if referencia else "regra_descricao",
                             "Código confirmado pela descrição do ERP")
        return Resultado(origem, None, "DIVERGENTE", "descricao",
                         f"Descrição aponta {citado}; regra/mapa aponta {candidato}")
    if referencia:
        return Resultado(origem, referencia, "REFERENCIA_TABELA", "mapa_historico",
                         "Correspondência antiga sem confirmação independente na descrição")
    if inferido:
        return Resultado(origem, inferido, "INFERIDO", "regra_familia", motivo)
    return Resultado(origem, None, "PENDENTE", "sem_regra", motivo)

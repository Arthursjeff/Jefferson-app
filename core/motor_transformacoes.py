"""Motor de simulação de transformações, sem movimentação de estoque.

Compatibilidades exigem regras explícitas por família. Não é seguro inferir
intercambiabilidade apenas de semelhanças entre códigos.
"""
from collections import defaultdict
import re

def normalizar(codigo):
    texto = re.sub(r"\s+", "", str(codigo or "").upper())
    # Hífens internos e sufixos técnicos (-I4, -72 etc.) são significativos.
    # Somente a separação gráfica entre prefixo e família é removida.
    return re.sub(r"^([A-Z]{1,4})-(?=(?:13|20|30)\d{2})", r"\1", texto)

def consolidar_estoque(registros):
    """Admite linhas ERP {codigo, quantidade, numero_serie?}; serial opcional."""
    agregado = defaultdict(float)
    series = defaultdict(list)
    rejeitados = []
    for i, item in enumerate(registros, 1):
        codigo = normalizar(item.get("codigo"))
        try:
            quantidade = float(str(item.get("quantidade", "0")).replace(",", "."))
        except (ValueError, TypeError):
            quantidade = -1
        if not codigo or quantidade < 0:
            rejeitados.append(i)
            continue
        agregado[codigo] += quantidade
        serie = str(item.get("numero_serie") or "").strip()
        if serie:
            series[codigo].append({"serie": serie, "quantidade": quantidade})
    return dict(agregado), dict(series), rejeitados


def familia(codigo):
    achado = re.search(r"(13\d{2}|20\d{2}|30\d{2})", normalizar(codigo))
    return achado.group(1) if achado else ""


def base_sem_z(codigo):
    codigo = normalizar(codigo)
    if codigo.startswith("Z") and familia(codigo):
        return codigo[1:]
    return ""


# Registro incremental de regras por família / construção.
# Nenhuma equivalência de torre é assumida entre famílias.
REGRAS = {
    "1335": {
        "torre": {
            "base_sem_z": True,
            "observacao": "Apenas a base sem Z é identificada automaticamente. "
                          "A válvula doadora da torre exige compatibilidade cadastrada.",
            "doadores_confirmados": [],
        },
    },
}

def avaliar(codigo_destino, tipo, metodo, estoque, regras=None):
    """Retorna possibilidades e bloqueios; não baixa nem reserva produtos."""
    codigo = normalizar(codigo_destino)
    tipo = str(tipo or "").upper()
    metodo = str(metodo or "").upper()
    regras = regras if regras is not None else REGRAS
    resultado = {
        "destino": codigo, "tipo": tipo, "metodo": metodo,
        "familia": familia(codigo), "estoque_exato": estoque.get(codigo, 0),
        "base": [], "doadores": [], "pendencias": [], "status": "EM ESTUDO"
    }
    if not codigo or not resultado["familia"]:
        resultado["pendencias"].append("Código sem família técnica reconhecida.")
        return resultado
    if tipo not in ("TORRE", "CORPO", "VEDACAO"):
        resultado["pendencias"].append("Selecione Corpo, Torre ou Vedação.")
        return resultado
    if metodo not in ("VALVULA_VALVULA", "VALVULA_KIT"):
        resultado["pendencias"].append("Selecione Válvula–Válvula ou Válvula–Kit.")
        return resultado
    regra = regras.get(resultado["familia"], {}).get(tipo.lower(), {})
    if not regra:
        resultado["pendencias"].append(
            "Compatibilidade de %s da família %s ainda não cadastrada." %
            (tipo.lower(), resultado["familia"]))
        return resultado
    if tipo == "TORRE" and regra.get("base_sem_z"):
        candidato = base_sem_z(codigo)
        if candidato:
            qtd = estoque.get(candidato, 0)
            if qtd > 0:
                resultado["base"].append({"codigo": candidato, "quantidade": qtd})
            else:
                resultado["pendencias"].append(
                    "Base sem Z (%s) não está disponível no estoque informado." % candidato)
        else:
            resultado["pendencias"].append("Esta regra se aplica a códigos com prefixo Z.")
    for doador in regra.get("doadores_confirmados", []):
        chave = normalizar(doador)
        if estoque.get(chave, 0) > 0:
            resultado["doadores"].append(
                {"codigo": chave, "quantidade": estoque[chave]})
    resultado["doadores"].sort(key=lambda x: (-x["quantidade"], x["codigo"]))
    if not resultado["doadores"]:
        resultado["pendencias"].append(
            "Ainda não há doadores de componente homologados para este cenário.")
    if resultado["base"] and resultado["doadores"]:
        resultado["status"] = "SIMULACAO_POSSIVEL"
    elif resultado["base"]:
        resultado["status"] = "BASE_LOCALIZADA"
    return resultado

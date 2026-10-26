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



# Estrutura técnica reconhecida para troca de corpo:
#   [construção] [família] [material do corpo] [configuração] [tamanho]
#   [final A, quando presente] [T=NPT, ausência=BSP] [INA] [-elétrico]
# O primeiro caractere após a família identifica a construção/material do
# corpo. Usamos a letra exata como chave, sem presumir equivalências.
# Construções especiais não reconhecidas não entram automaticamente na troca.
_PADRAO_CORPO_ROSCADO = re.compile(
    r"^(?P<prefixo>[A-Z]{0,4})(?P<familia>(?:13|20|30)\d{2})"
    r"(?P<material>[A-Z])(?P<configuracao>[A-Z]{0,5})"
    r"(?P<tamanho>\d{2})(?P<final>A?)(?P<npt>T?)"
    r"(?P<indicador>INA)?(?P<eletrico>-[A-Z0-9]+)?$"
)


def _partes_corpo(codigo):
    """Interpreta rosca e material sem confundir A final com BSP/NPT."""
    encontrado = _PADRAO_CORPO_ROSCADO.fullmatch(normalizar(codigo))
    return encontrado.groupdict() if encontrado else None


def chave_corpo(codigo):
    """Retorna (familia, tamanho, material, rosca)."""
    partes = _partes_corpo(codigo)
    if partes is None:
        return None
    return (
        partes["familia"],
        partes["tamanho"],
        partes["material"],
        "NPT" if partes["npt"] == "T" else "BSP",
    )


def localizar_doadores_corpo(codigo_destino, estoque):
    """Lista válvulas com família, tamanho, MATERIAL e rosca correspondentes."""
    procurada = chave_corpo(codigo_destino)
    if procurada is None:
        return []
    candidatos = []
    for codigo, quantidade in estoque.items():
        if quantidade > 0 and normalizar(codigo) != normalizar(codigo_destino):
            if chave_corpo(codigo) == procurada:
                candidatos.append({"codigo": codigo, "quantidade": quantidade})
    return sorted(candidatos, key=lambda item: (-item["quantidade"], item["codigo"]))


def corpo_oposto(codigo):
    """Obtém (rosca_destino, rosca_oposta, código com rosca invertida)."""
    partes = _partes_corpo(codigo)
    if partes is None:
        return None
    comum = (
        partes["prefixo"] + partes["familia"] + partes["material"]
        + partes["configuracao"] + partes["tamanho"] + partes["final"]
    )
    restante = (partes["indicador"] or "") + (partes["eletrico"] or "")
    if partes["npt"] == "T":
        return "NPT", "BSP", comum + restante
    return "BSP", "NPT", comum + "T" + restante



def calcular_residual_corpo(resultado, codigo_doadora):
    """Simula saída de produto vendido + residual após permuta dos corpos.

    A válvula base fornece os componentes não corporais do produto vendido;
    a doadora fornece o corpo requerido e conserva os seus demais componentes
    com o corpo retirado da base. Não efetua nenhuma movimentação.
    """
    if resultado.get("tipo") != "CORPO":
        raise ValueError("Cálculo residual disponível somente para troca de corpo.")
    if resultado.get("status") != "SIMULACAO_POSSIVEL":
        raise ValueError("A transformação requer base e doadora disponíveis.")
    if not resultado.get("base"):
        raise ValueError("Nenhuma válvula base disponível.")
    doadora = normalizar(codigo_doadora)
    opcoes = {normalizar(x["codigo"]) for x in resultado.get("doadores", [])}
    if doadora not in opcoes:
        raise ValueError("Doadora não está entre as opções disponíveis.")
    destino = resultado["destino"]
    base = normalizar(resultado["base"][0]["codigo"])
    chave_destino = chave_corpo(destino)
    chave_base = chave_corpo(base)
    chave_doadora = chave_corpo(doadora)
    if not all([chave_destino, chave_base, chave_doadora]):
        raise ValueError("Código de válvula não reconhecido para permuta.")
    if chave_doadora != chave_destino:
        raise ValueError("A doadora não fornece o corpo requerido.")
    if (chave_base[:3] != chave_destino[:3]
            or chave_base[3] == chave_destino[3]):
        raise ValueError("O corpo da base não corresponde à rosca oposta.")
    oposto = corpo_oposto(doadora)
    if oposto is None or oposto[0] != chave_doadora[3] or oposto[1] != chave_base[3]:
        raise ValueError("Não foi possível reconstruir o código residual.")
    residual = oposto[2]
    if chave_corpo(residual) != chave_base:
        raise ValueError("O código residual não manteve família, tamanho, material e rosca.")
    return {
        "valvula_base": base,
        "valvula_doadora": doadora,
        "produto_final": destino,
        "produto_residual": residual,
        "corpo_origem": chave_base[3],
        "corpo_destino": chave_destino[3],
        "quantidade": 1,
        "simulacao": True,
    }



# O conjunto G1 distingue torre EXTERNA de internos (assento, mola, núcleo).
# A permuta transfere sempre o conjunto G1 completo entre as válvulas.
from components.internos.torre import identificar_sistema_torre
from components.internos.regras_g1 import resolver_g1

_PADRAO_TORRE = re.compile(
    r"^(?P<z>Z?)(?P<familia>(?:13|20|30)\d{2})"
    r"(?P<material>[BI])(?P<vedacao>[A-Z])(?P<tamanho>\d{2})"
    r"(?P<final>A?)(?P<npt>T?)(?P<ina>INA)?(?P<eletrico>-[A-Z0-9]+)?$"
)

def _torre_partes(codigo):
    m = _PADRAO_TORRE.fullmatch(normalizar(codigo))
    return m.groupdict() if m else None

def _torre_construcao(p):
    return ("Z_INA" if p["z"] and p["ina"] else
            "Z" if p["z"] else "INA" if p["ina"] else "REGULAR")

def _torre_grupo(p):
    material = "LATAO" if p["material"] == "B" else "INOX"
    return identificar_sistema_torre(p["familia"], material)["grupo"]

def _torre_compatibilidade(destino, candidata):
    """Pré-filtro da torre externa; o conjunto completo é validado depois."""
    if not destino or not candidata:
        return False
    return (_torre_grupo(destino) == _torre_grupo(candidata)
            and destino["material"] == candidata["material"]
            and _torre_construcao(destino) == _torre_construcao(candidata))

def _torre_montar(p, z, ina):
    return (( "Z" if z else "") + p["familia"] + p["material"]
            + p["vedacao"] + p["tamanho"] + p["final"] + p["npt"]
            + ("INA" if ina else "") + (p["eletrico"] or ""))

def _avaliar_torre(codigo, estoque, resultado):
    p = _torre_partes(codigo)
    if not p or _torre_construcao(p) == "REGULAR":
        resultado["pendencias"].append(
            "A transformação exige código reconhecido com torre Z, INA ou Z+INA.")
        return resultado
    grupo = _torre_grupo(p)
    resultado["grupo_torre"] = grupo
    resultado["construcao_torre"] = _torre_construcao(p)
    base = _torre_montar(p, False, False)
    resultado["codigo_base_esperado"] = base
    if estoque.get(base, 0) > 0:
        resultado["base"].append({"codigo": base, "quantidade": estoque[base]})
    else:
        resultado["pendencias"].append("Válvula base sem torre especial %s sem saldo." % base)
    doadoras = []
    combinadas = []
    for codigo_estoque, quantidade in estoque.items():
        if quantidade <= 0 or normalizar(codigo_estoque) == codigo:
            continue
        item = _torre_partes(codigo_estoque)
        if not _torre_compatibilidade(p, item):
            continue
        # Nunca oferecer item de outra família para a 1335 (nem vice-versa).
        if p["familia"] == "1335" and item["familia"] != "1335":
            continue
        mesma_vedacao = item["vedacao"] == p["vedacao"]
        if mesma_vedacao and item["familia"] == p["familia"]:
            prioridade = 1
        elif (mesma_vedacao and item["familia"] == "1327"
              and p["familia"] != "1335"):
            prioridade = 2
        elif item["familia"] == p["familia"] and not mesma_vedacao:
            prioridade = 3
        else:
            continue
        candidato = {"codigo": normalizar(codigo_estoque),
                     "quantidade": quantidade, "prioridade": prioridade,
                     "vedacao_compativel": mesma_vedacao}
        if prioridade == 3:
            combinadas.append(candidato)
        else:
            doadoras.append(candidato)
    resultado["doadores"] = sorted(
        doadoras, key=lambda x: (x["prioridade"], -x["quantidade"], x["codigo"]))
    resultado["doadores_combinadas"] = sorted(
        combinadas, key=lambda x: (-x["quantidade"], x["codigo"]))
    if combinadas:
        resultado["pendencias"].append(
            "Há doadoras com vedação diferente (prioridade 3), mas a transformação "
            "Torre + Vedação está bloqueada até a definição do assento e demais componentes.")
    if not doadoras:
        resultado["pendencias"].append(
            "Não há doadora com a mesma vedação e torre G1 compatível em estoque.")
    if resultado["base"] and doadoras:
        resultado["status"] = "SIMULACAO_POSSIVEL"
    elif resultado["base"]:
        resultado["status"] = "BASE_LOCALIZADA"
    elif doadoras:
        resultado["status"] = "DOADORES_LOCALIZADOS"
    return resultado

def calcular_residual_torre(resultado, codigo_doadora):
    """Permuta construção da torre mantendo a identidade da doadora.

    Somente simulação de torre com vedação igual, com doadora homologada.
    """
    if resultado.get("tipo") != "TORRE" or resultado.get("status") != "SIMULACAO_POSSIVEL":
        raise ValueError("É necessária uma base e uma doadora compatível.")
    doadora = normalizar(codigo_doadora)
    opcao = next((d for d in resultado["doadores"] if d["codigo"] == doadora), None)
    if not opcao or not opcao["vedacao_compativel"]:
        raise ValueError("A doadora não está liberada para torre simples.")
    p = _torre_partes(doadora)
    destino = _torre_partes(resultado["destino"])
    base = _torre_partes(resultado["base"][0]["codigo"])
    if not _torre_compatibilidade(destino, p) or _torre_construcao(base) != "REGULAR":
        raise ValueError("Conjunto G1 incompatível.")
    residual = _torre_montar(p, False, False)
    return {"valvula_base": resultado["base"][0]["codigo"],
            "valvula_doadora": doadora,
            "produto_final": resultado["destino"],
            "produto_residual": residual,
            "quantidade": 1, "simulacao": True,
            "observacao": "Código residual previsto, ainda não homologado: a identidade "
                          "da torre externa não garante a compatibilidade dos componentes "
                          "internos G1. Conferir a composição antes da execução real.",
             "residual_sujeito_a_conferencia_g1": True}



def diagnosticar_componentes_torre(resultado, codigo_doadora):
    """Valida a permuta de dois conjuntos G1 INTEIROS, sem desmontar internos.

    A única exceção de identidade admitida é mola inox 303 versus 304.
    Falhas ou identidades G1 desconhecidas bloqueiam a homologação automática.
    """
    simulacao = calcular_residual_torre(resultado, codigo_doadora)

    def identificar(codigo):
        partes = _torre_partes(codigo)
        if not partes:
            raise ValueError("Código G1 não reconhecido: %s." % codigo)
        material = "LATAO" if partes["material"] == "B" else "INOX"
        g1 = resolver_g1(
            familia=partes["familia"], material=material,
            construcao=_torre_construcao(partes), vedacao=partes["vedacao"],
            final=partes["final"] or None, bitola=partes["tamanho"])
        return partes, g1

    partes_destino, destino = identificar(simulacao["produto_final"])
    _, base = identificar(simulacao["valvula_base"])
    _, doadora = identificar(simulacao["valvula_doadora"])
    _, residual = identificar(simulacao["produto_residual"])

    def normalizar_mola(componente, identidade):
        identidade = dict(identidade)
        if componente in ("mola_nucleo", "mola_cadeirinha") and identidade.get("material") in ("INOX 303", "INOX 304"):
            identidade["material"] = "INOX 303/304"
        return identidade

    divergencias = []
    comparacoes = (("doadora_destino", doadora, destino),
                   ("base_residual", base, residual))
    for nome, origem, esperado in comparacoes:
        if origem["validacao_pendente"] or esperado["validacao_pendente"]:
            divergencias.append(nome + ": identidade técnica G1 pendente")
        if origem["torre_externa"] != esperado["torre_externa"]:
            divergencias.append(nome + ": torre externa incompatível")
        nomes = set(origem["componentes_internos"]) | set(esperado["componentes_internos"])
        for componente in sorted(nomes):
            x = origem["componentes_internos"].get(componente)
            y = esperado["componentes_internos"].get(componente)
            if x is None or y is None or normalizar_mola(componente, x) != normalizar_mola(componente, y):
                divergencias.append(nome + ": " + componente + " incompatível")

    return {
        "status_engenharia": "COMPATIVEL_G1" if not divergencias else "BLOQUEADO_G1",
        "produto_residual_previsto": simulacao["produto_residual"],
        "construcao_destino": _torre_construcao(partes_destino),
        "envolve_ina": bool(partes_destino["ina"]),
        "tipo_troca": "CONJUNTO_G1_COMPLETO",
        "excecao_mola": "Somente inox 303 e inox 304",
        "divergencias": divergencias,
        "observacao": ("Permuta integral dos conjuntos G1, sem substituições individuais. "
                       "Validação baseada nas identidades técnicas G1 cadastradas; "
                       "não substitui a conferência física."),
    }


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
    if tipo == "CORPO":
        if metodo != "VALVULA_VALVULA":
            resultado["pendencias"].append("Troca de corpo só admite Válvula–Válvula.")
            return resultado
        oposto = corpo_oposto(codigo)
        if oposto is None:
            resultado["pendencias"].append(
                "Formato de código não reconhecido para troca BSP/NPT. "
                "Não foi gerada uma sugestão automática."
            )
            return resultado
        destino_rosca, origem_rosca, candidato = oposto
        resultado["conexao_destino"] = destino_rosca
        resultado["conexao_base"] = origem_rosca
        resultado["codigo_base_esperado"] = candidato
        qtd = estoque.get(candidato, 0)
        if qtd > 0:
            resultado["base"].append({"codigo": candidato, "quantidade": qtd})
        else:
            resultado["pendencias"].append(
                "Válvula base %s (%s) sem saldo no estoque carregado." %
                (candidato, origem_rosca)
            )
        resultado["doadores"] = localizar_doadores_corpo(codigo, estoque)
        if not resultado["doadores"]:
            resultado["pendencias"].append(
                "Nenhuma válvula com corpo %s da família, tamanho e material solicitados "
                "foi encontrada no estoque informado." % destino_rosca
            )
        if resultado["base"] and resultado["doadores"]:
            resultado["status"] = "SIMULACAO_POSSIVEL"
            resultado["pendencias"].append(
                "Base e doadoras encontradas. Selecione a doadora para simular "
                "o código residual e validar a transformação."
            )
        elif resultado["base"]:
            resultado["status"] = "BASE_LOCALIZADA"
        elif resultado["doadores"]:
            resultado["status"] = "DOADORES_LOCALIZADOS"
        return resultado
    if tipo == "TORRE":
        if metodo != "VALVULA_VALVULA":
            resultado["pendencias"].append("Transformação de torre exige Válvula–Válvula.")
            return resultado
        return _avaliar_torre(codigo, estoque, resultado)
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

import re


# =============================================================
# INTERPRETADOR DE CÓDIGOS JEFFERSON
# =============================================================
#
# ESTRUTURA:
#
# PREFIXOS | FAMÍLIA | BLOCO LETRAS | BLOCO NÚMEROS | SUFIXOS
#
# =============================================================


# =============================================================
# 1. PREFIXOS VÁLIDOS
# =============================================================

PREFIXOS_VALIDOS = [
    "ZC",
    "YC",
    "PA",
    "PE",
    "Z",
    "E",
    "Y",
]


# =============================================================
# 2. SUFIXOS VÁLIDOS
# =============================================================

SUFIXOS_FIXOS = [
    "INA",
    "-69A",
    "-69B",
    "-48",
    "NA",
    "UC",
    "VB",
    "LB",
    "AR",
    "-M",
    "T",
    "A",
    "D",
    "U",
    "C",
    "F",
    "B",
    "G",
    "H",
    "I",
    "K",
    "N",
    "M",
    "J",
]


# Sufixos variáveis:
# -I1
# -I2
# -I3
# -I4
# etc.

PADROES_SUFIXOS = [
    re.compile(r"^-I\d+"),
]


# =============================================================
# 3. REGRAS DOS BLOCOS DE 3 LETRAS
# =============================================================
#
# Posições:
#
# 0 = primeira letra
# 1 = segunda letra
# 2 = terceira letra
#
# A posição indicada é a LETRA ESPECIAL.
#
# Depois de remover a letra especial:
#
# primeira restante = CORPO
# segunda restante  = VEDAÇÃO
#
# =============================================================

REGRAS_3_LETRAS = {

    "1314": {
        "BST": 1,
    },

    "1390": {
        "BBT": 1,
    },

    "1351": {
        "BTV": 1,
    },

    "1350": {
        "BTV": 1,
    },

    "2050": {
        "BTV": 1,
    },

    "2051": {
        "BTV": 1,
    },

    "2094": {
        "RBD": 0,
    },

    "1397": {
        "FDA": 1,
    },

    "2030": {
        "LAR": 2,
        "LAD": 2,
	"LVR": 2,	
    },

    "1330": {
        "LAR": 2,
	"LVR": 2,
    },
}


# =============================================================
# 4. SEPARAR PREFIXOS
# =============================================================

def separar_prefixos(texto):

    if not texto:
        return [], ""

    restante = texto
    encontrados = []

    prefixos_ordenados = sorted(
        PREFIXOS_VALIDOS,
        key=len,
        reverse=True
    )

    while restante:

        encontrou = False

        for prefixo in prefixos_ordenados:

            if restante.startswith(prefixo):

                encontrados.append(prefixo)
                restante = restante[len(prefixo):]

                encontrou = True
                break

        if not encontrou:
            break

    return encontrados, restante


# =============================================================
# 5. SEPARAR SUFIXOS
# =============================================================

def separar_sufixos(texto):

    if not texto:
        return [], ""

    restante = texto
    encontrados = []

    sufixos_ordenados = sorted(
        SUFIXOS_FIXOS,
        key=len,
        reverse=True
    )

    while restante:

        encontrou = False

        # -----------------------------------------------------
        # SUFIXOS VARIÁVEIS
        # -----------------------------------------------------

        for padrao in PADROES_SUFIXOS:

            match = padrao.match(restante)

            if match:

                sufixo = match.group()

                encontrados.append(sufixo)
                restante = restante[len(sufixo):]

                encontrou = True
                break

        if encontrou:
            continue

        # -----------------------------------------------------
        # SUFIXOS FIXOS
        # -----------------------------------------------------

        for sufixo in sufixos_ordenados:

            if restante.startswith(sufixo):

                encontrados.append(sufixo)
                restante = restante[len(sufixo):]

                encontrou = True
                break

        if not encontrou:
            break

    return encontrados, restante


# =============================================================
# 6. INTERPRETAR BLOCO DE LETRAS
# =============================================================

def interpretar_bloco_letras(bloco, familia):

    quantidade = len(bloco)

    # =========================================================
    # 2 LETRAS - STANDARD
    # =========================================================
    #
    # Primeira = corpo
    # Segunda  = vedação
    # =========================================================

    if quantidade == 2:

        return {
            "status": "STANDARD",
            "quantidade": 2,
            "codigo_corpo": bloco[0],
            "codigo_vedacao": bloco[1],
            "letra_especial": None,
            "posicao_especial": None,
            "regra_encontrada": True,
            "mensagem": None,
        }

    # =========================================================
    # 3 LETRAS
    # =========================================================

    if quantidade == 3:

        regras_familia = REGRAS_3_LETRAS.get(
            familia
        )

        # -----------------------------------------------------
        # FAMÍLIA NÃO CADASTRADA
        # -----------------------------------------------------

        if regras_familia is None:

            return {
                "status": "REGRA NÃO ENCONTRADA",
                "quantidade": 3,
                "codigo_corpo": None,
                "codigo_vedacao": None,
                "letra_especial": None,
                "posicao_especial": None,
                "regra_encontrada": False,
                "mensagem": (
                    f"A família {familia} possui "
                    f"bloco de 3 letras '{bloco}', "
                    f"mas não existe regra cadastrada."
                ),
            }

        # -----------------------------------------------------
        # PROCURAR A COMBINAÇÃO
        # -----------------------------------------------------

        posicao_especial = regras_familia.get(
            bloco
        )

        if posicao_especial is None:

            return {
                "status": "COMBINAÇÃO NÃO CADASTRADA",
                "quantidade": 3,
                "codigo_corpo": None,
                "codigo_vedacao": None,
                "letra_especial": None,
                "posicao_especial": None,
                "regra_encontrada": False,
                "mensagem": (
                    f"A família {familia} está cadastrada, "
                    f"mas a combinação '{bloco}' "
                    f"não possui regra."
                ),
            }

        # -----------------------------------------------------
        # IDENTIFICAR LETRA ESPECIAL
        # -----------------------------------------------------

        letra_especial = bloco[
            posicao_especial
        ]

        # -----------------------------------------------------
        # RETIRAR LETRA ESPECIAL
        # -----------------------------------------------------

        letras_principais = [
            letra

            for indice, letra in enumerate(bloco)

            if indice != posicao_especial
        ]

        # -----------------------------------------------------
        # INTERPRETAR AS DUAS RESTANTES
        # -----------------------------------------------------

        codigo_corpo = letras_principais[0]
        codigo_vedacao = letras_principais[1]

        return {
            "status": "3 LETRAS INTERPRETADO",
            "quantidade": 3,
            "codigo_corpo": codigo_corpo,
            "codigo_vedacao": codigo_vedacao,
            "letra_especial": letra_especial,

            # Mantido internamente.
            "posicao_especial": posicao_especial + 1,

            "regra_encontrada": True,
            "mensagem": None,
        }

    # =========================================================
    # OUTRA QUANTIDADE
    # =========================================================

    return {
        "status": "FORA DO PADRÃO",
        "quantidade": quantidade,
        "codigo_corpo": None,
        "codigo_vedacao": None,
        "letra_especial": None,
        "posicao_especial": None,
        "regra_encontrada": False,
        "mensagem": (
            f"Bloco de letras '{bloco}' possui "
            f"{quantidade} caracteres. "
            f"O parser aceita atualmente 2 ou 3."
        ),
    }


# =============================================================
# 7. INTERPRETAR BLOCO NUMÉRICO
# =============================================================

def interpretar_bloco_numeros(bloco):

    quantidade = len(bloco)

    # =========================================================
    # 2 NÚMEROS - STANDARD
    # =========================================================
    #
    # Exemplo:
    # 02 = código da conexão
    # =========================================================

    if quantidade == 2:

        return {
            "status": "STANDARD",
            "quantidade": 2,
            "codigo_orificio": None,
            "codigo_conexao": bloco,
            "regra_encontrada": True,
            "mensagem": None,
        }

    # =========================================================
    # 3 NÚMEROS
    # =========================================================
    #
    # Exemplo:
    # 172
    #
    # 17 = código do orifício
    # 2  = código da conexão
    # =========================================================

    if quantidade == 3:

        return {
            "status": "3 NÚMEROS INTERPRETADO",
            "quantidade": 3,
            "codigo_orificio": bloco[:2],
            "codigo_conexao": bloco[2],
            "regra_encontrada": True,
            "mensagem": None,
        }

    # =========================================================
    # OUTRA QUANTIDADE
    # =========================================================

    return {
        "status": "FORA DO PADRÃO",
        "quantidade": quantidade,
        "codigo_orificio": None,
        "codigo_conexao": None,
        "regra_encontrada": False,
        "mensagem": (
            f"Bloco numérico '{bloco}' possui "
            f"{quantidade} caracteres. "
            f"O parser aceita atualmente 2 ou 3."
        ),
    }


# =============================================================
# 8. INTERPRETADOR PRINCIPAL
# =============================================================

def interpretar_codigo(codigo):

    codigo = codigo.strip().upper()

    alertas = []

    # =========================================================
    # 8.1 LOCALIZAR FAMÍLIA
    # =========================================================

    match_familia = re.search(
        r"(?<!\d)\d{4}(?!\d)",
        codigo
    )

    if not match_familia:

        return {
            "codigo_original": codigo,
            "sucesso": False,
            "erro": (
                "Família não encontrada. "
                "Era esperada uma sequência de 4 números."
            ),
        }

    familia = match_familia.group()

    inicio_familia = match_familia.start()
    fim_familia = match_familia.end()

    # =========================================================
    # 8.2 PREFIXOS
    # =========================================================

    area_prefixos = codigo[
        :inicio_familia
    ]

    prefixos, prefixo_nao_reconhecido = (
        separar_prefixos(
            area_prefixos
        )
    )

    if prefixo_nao_reconhecido:

        alertas.append(
            "Prefixo não reconhecido: "
            + prefixo_nao_reconhecido
        )

    # =========================================================
    # 8.3 RESTANTE APÓS FAMÍLIA
    # =========================================================

    restante = codigo[
        fim_familia:
    ]

    # =========================================================
    # 8.4 BLOCO DE LETRAS
    # =========================================================

    match_letras = re.match(
        r"[A-Z]+",
        restante
    )

    if match_letras:

        bloco_letras = match_letras.group()

        restante = restante[
            match_letras.end():
        ]

    else:

        bloco_letras = ""

    # =========================================================
    # 8.5 BLOCO NUMÉRICO
    # =========================================================

    match_numeros = re.match(
        r"\d+",
        restante
    )

    if match_numeros:

        bloco_numeros = match_numeros.group()

        restante = restante[
            match_numeros.end():
        ]

    else:

        bloco_numeros = ""

    # =========================================================
    # 8.6 INTERPRETAR LETRAS
    # =========================================================

    interpretacao_letras = (
        interpretar_bloco_letras(
            bloco_letras,
            familia
        )
    )

    if interpretacao_letras["mensagem"]:

        alertas.append(
            interpretacao_letras["mensagem"]
        )

    # =========================================================
    # 8.7 INTERPRETAR NÚMEROS
    # =========================================================

    interpretacao_numeros = (
        interpretar_bloco_numeros(
            bloco_numeros
        )
    )

    if interpretacao_numeros["mensagem"]:

        alertas.append(
            interpretacao_numeros["mensagem"]
        )

    # =========================================================
    # 8.8 SUFIXOS
    # =========================================================

    area_sufixos = restante

    sufixos, sufixo_nao_reconhecido = (
        separar_sufixos(
            area_sufixos
        )
    )

    if sufixo_nao_reconhecido:

        alertas.append(
            "Sufixo não reconhecido: "
            + sufixo_nao_reconhecido
        )

    # =========================================================
    # 8.9 VALIDAR RESULTADO
    # =========================================================

    letras_ok = interpretacao_letras[
        "regra_encontrada"
    ]

    numeros_ok = interpretacao_numeros[
        "regra_encontrada"
    ]

    prefixos_ok = (
        prefixo_nao_reconhecido == ""
    )

    sufixos_ok = (
        sufixo_nao_reconhecido == ""
    )

    sucesso = (
        letras_ok
        and numeros_ok
        and prefixos_ok
        and sufixos_ok
    )

    if sucesso:

        status_estrutura = (
            "CÓDIGO INTERPRETADO"
        )

    else:

        status_estrutura = (
            "VERIFICAR CÓDIGO"
        )

    # =========================================================
    # 8.10 RESULTADO FINAL
    # =========================================================

    return {

        # GERAL
        "codigo_original": codigo,
        "sucesso": sucesso,
        "status": status_estrutura,

        # PREFIXOS
        "area_prefixos": area_prefixos,
        "prefixos": prefixos,
        "prefixo_nao_reconhecido":
            prefixo_nao_reconhecido,

        # FAMÍLIA
        "familia": familia,

        # LETRAS
        "bloco_letras": bloco_letras,
        "quantidade_letras":
            interpretacao_letras["quantidade"],
        "status_letras":
            interpretacao_letras["status"],
        "codigo_corpo":
            interpretacao_letras["codigo_corpo"],
        "codigo_vedacao":
            interpretacao_letras["codigo_vedacao"],
        "letra_especial":
            interpretacao_letras["letra_especial"],
        "posicao_especial":
            interpretacao_letras["posicao_especial"],

        # NÚMEROS
        "bloco_numeros": bloco_numeros,
        "quantidade_numeros":
            interpretacao_numeros["quantidade"],
        "status_numeros":
            interpretacao_numeros["status"],
        "codigo_orificio":
            interpretacao_numeros["codigo_orificio"],
        "codigo_conexao":
            interpretacao_numeros["codigo_conexao"],

        # SUFIXOS
        "area_sufixos": area_sufixos,
        "sufixos": sufixos,
        "sufixo_nao_reconhecido":
            sufixo_nao_reconhecido,

        # ALERTAS
        "alertas": alertas,
    }


# =============================================================
# 9. MOTOR DE DESCRIÇÃO
# =============================================================


# =============================================================
# V01 - TIPO PRINCIPAL DO PRODUTO
# =============================================================
#
# ORIGEM:
# família identificada pelo parser
#
# =============================================================

REGRAS_V01_TIPO_PRODUTO = {

    "1342": "Válvula solenoide",
    "1335": "Válvula solenoide",
    "1327": "Válvula solenoide",
    "1330": "Válvula solenoide",
    "2030": "Válvula solenoide",
    "1323": "Válvula solenoide",
    "1365": "Válvula solenoide",
    "1393": "Válvula solenoide",
    "2026": "Válvula solenoide",
    "2036": "Válvula solenoide",
    "2094": "Válvula solenoide",
    "2012": "Válvula solenoide",
    "1312": "Válvula solenoide",
    "1343": "Válvula solenoide",
    "1344": "Válvula solenoide",
    "1325": "Válvula solenoide",
    "1390": "Válvula solenoide",
    "1360": "Válvula solenoide",
    "2051": "Válvula solenoide",
    "3073": "Válvula solenoide",
    "3014": "Válvula solenoide",
    "1356": "Válvula solenoide",
    "1388": "Válvula solenoide",
    "2088": "Válvula solenoide",
    "1339": "Válvula solenoide",
    "1351": "Válvula solenoide",
    "1375": "Válvula solenoide",
    "2050": "Válvula solenoide",
    "2095": "Válvula solenoide",
    "2024": "Válvula solenoide",
    "1387": "Válvula solenoide",
    "2073": "Válvula solenoide",
    "1314": "Válvula solenoide",
    "2041": "Válvula solenoide",

    "V171": "Válvula de segurança",

    "3010": "Válvula angular",

    "1317": "Controle de nível",
    "2017": "Controle de nível",
    "2049": "Controle de nível",
    "1340": "Controle de nível",
    "1376": "Controle de nível",
    "1380": "Controle de nível",
}


def definir_v01(familia):
    """
    Define a V01 usando exclusivamente
    a família identificada pelo parser.
    """

    return REGRAS_V01_TIPO_PRODUTO.get(
        familia
    )



# =============================================================
# V02 - TIPO DE ATUAÇÃO
# =============================================================
#
# ORIGENS POSSÍVEIS:
# - família
# - letra especial
# - sufixos
# - código da conexão
#
# PRIORIDADE:
# 1. Regras específicas
# 2. Regra padrão da família
#
# =============================================================


def definir_v02(
    familia,
    letra_especial,
    sufixos,
    codigo_conexao
):

    # =========================================================
    # 1335
    # =========================================================

    if familia == "1335":

        if "D" in sufixos:
            return "Ação direta"

        if "VB" in sufixos:
            return "Ação direta"

        if "A" in sufixos:
            return "Ação combinada"

        return "Servo operada"


    # =========================================================
    # 1330
    # =========================================================

    if familia == "1330":

        if codigo_conexao in ["04", "06"]:
            return "Ação direta"

        if codigo_conexao == "08":
            return "Servo operada"

        return None


    # =========================================================
    # 2030
    # =========================================================

    if familia == "2030":

        # Regra mais específica primeiro
        if letra_especial == "D" and codigo_conexao == "10":
            return "Servo operada"

        if codigo_conexao in ["08", "10"]:
            return "Ação direta"

        return "Servo operada"


    # =========================================================
    # 1314
    # =========================================================

    if familia == "1314":

        if "A" in sufixos:
            return "Ação combinada"

        return "Servo operada"


    # =========================================================
    # REGRAS FIXAS POR FAMÍLIA
    # =========================================================

    REGRAS_FIXAS_V02 = {

        "1342": "Servo operada",
        "1327": "Ação direta",
        "1323": "Ação direta",
        "1365": "Ação direta",
        "1393": "Ação direta",
        "2026": "Ação direta",
        "2036": "Servo operada",
        "2094": "Servo operada",
        "2012": "Ação direta",
        "1312": "Ação direta",
        "1343": "Servo operada",
        "1344": "Servo operada",
        "1325": "Servo operada",
        "1390": "Servo operada",
        "1360": "Ação direta",
        "2051": "Ação direta",
        "3073": "Servo operada",
        "3014": "Ação combinada",
        "1356": "Ação direta",
        "1388": "Ação direta",
        "2088": "Ação direta",
        "1351": "Servo operada",
        "2050": "Servo operada",
        "2073": "Servo operada",
        "2041": "Servo operada",
    }

    return REGRAS_FIXAS_V02.get(
        familia
    )




# =============================================================
# V03 - NÚMERO DE VIAS
# =============================================================
#
# ORIGEM:
# família identificada pelo parser
#
# =============================================================

REGRAS_V03_NUMERO_VIAS = {

    "1323": "3 vias",
    "1325": "3 vias",
    "1339": "4/3 vias",
    "1350": "5 vias",
    "1351": "3 vias",
    "1365": "3 vias",
    "1375": "5 vias",
    "1387": "3 vias",
    "2050": "5/2 vias",
    "2051": "3/2 vias",
    "2024": "5 vias",

    "1342": "2 vias",
    "1335": "2 vias",
    "1327": "2 vias",
    "1330": "2 vias",
    "2030": "2 vias",
    "1393": "2 vias",
    "2026": "2 vias",
    "2036": "2 vias",
    "2094": "2 vias",
    "2012": "2 vias",
    "1312": "2 vias",
    "1343": "2 vias",
    "1344": "2 vias",
    "1390": "2 vias",
    "1360": "2 vias",
    "3073": "2 vias",
    "3014": "2 vias",
    "1356": "2 vias",
    "1388": "2 vias",
    "2088": "2 vias",
    "1314": "2 vias",
    "2041": "2 vias",
    "3010": "2 vias",
}

def definir_v03(familia, sufixos):
    """
    Define a V03 - número de vias.

    Regra especial:
    Família 1335 + sufixo VB = 3 vias

    Caso contrário:
    utiliza a regra padrão da família.
    """

    # =========================================================
    # EXCEÇÕES
    # =========================================================

    if familia == "1335" and "VB" in sufixos:
        return "3 vias"

    # =========================================================
    # REGRA STANDARD
    # =========================================================

    return REGRAS_V03_NUMERO_VIAS.get(
        familia
    )


# =============================================================
# V04 - POSIÇÃO / ESTADO DA VÁLVULA
# =============================================================
#
# ORIGEM:
# - V03 = número de vias
# - sufixos identificados pelo parser
#
# =============================================================


def definir_v04(numero_vias, sufixos):
    """
    Define a V04 - posição/estado da válvula.

    REGRAS:

    2 vias:
        NA ou INA -> Normalmente aberta
        sem NA/INA -> Normalmente fechada

    Demais configurações:
        C -> Normalmente fechada
        A -> Normalmente aberta
        U -> Universal
    """

    # =========================================================
    # REGRA PARA 2 VIAS
    # =========================================================

    if numero_vias == "2 vias":

        if "NA" in sufixos or "INA" in sufixos:
            return "normalmente aberta"

        return "normalmente fechada"


    # =========================================================
    # REGRA PARA 3/5 VIAS E OUTRAS NÃO-2-VIAS
    # =========================================================

    if "C" in sufixos:
        return "normalmente fechada"

    if "A" in sufixos:
        return "normalmente aberta"

    if "U" in sufixos:
        return "universal"


    # =========================================================
    # SEM REGRA ENCONTRADA
    # =========================================================

    return None


# =============================================================
# V05 - MATERIAL DO CORPO
# =============================================================
#
# ORIGEM:
# codigo_corpo identificado pelo parser
#
# =============================================================

REGRAS_V05_MATERIAL_CORPO = {
    "B": "Latão",
    "S": "Inox 304",
    "I": "Inox 316",
    "L": "Alumínio",
    "P": "PVC",
    "T": "Teflon",
    "A": "Aço 1020",
    "F": "Ferro fundido",
}


def definir_v05(codigo_corpo):
    """
    Define a V05 - material do corpo
    usando o código do corpo identificado pelo parser.
    """

    return REGRAS_V05_MATERIAL_CORPO.get(
        codigo_corpo
    )


# =============================================================
# V06 - MATERIAL DA VEDAÇÃO
# =============================================================
#
# ORIGEM:
# codigo_vedacao identificado pelo parser
#
# =============================================================

REGRAS_V06_MATERIAL_VEDACAO = {
    "A": "Buna-N (NBR)",
    "V": "Viton (FKM)",
    "E": "Etileno (EPDM)",
    "T": "Teflon (PTFE)",
    "N": "Neoprene",
    "D": "Delryin",
    "S": "Inox",
}


def definir_v06(codigo_vedacao):
    """
    Define a V06 - material da vedação
    usando o código da vedação identificado pelo parser.
    """

    return REGRAS_V06_MATERIAL_VEDACAO.get(
        codigo_vedacao
    )

# =============================================================
# V07 - TAMANHO DA CONEXÃO
# =============================================================
#
# ORIGEM:
# codigo_conexao identificado pelo parser
#
# IMPORTANTE:
# Em blocos numéricos de 3 dígitos,
# a conexão pode vir como "1", "2", "3"...
# Nesse caso normalizamos para "01", "02", "03"...
#
# =============================================================

REGRAS_V07_TAMANHO_CONEXAO = {
    "01": '1/8"',
    "02": '1/4"',
    "03": '3/8"',
    "04": '1/2"',
    "06": '3/4"',
    "08": '1"',
    "10": '1 1/4"',
    "12": '1 1/2"',
    "16": '2"',
    "20": '2 1/2"',
    "24": '3"',
}


def definir_v07(codigo_conexao):
    """
    Define a V07 - tamanho da conexão.

    Exemplos:
    "02" -> 1/4"
    "2"  -> normaliza para "02" -> 1/4"
    "10" -> 1 1/4"
    """

    if codigo_conexao is None:
        return None

    codigo_normalizado = codigo_conexao.zfill(2)

    return REGRAS_V07_TAMANHO_CONEXAO.get(
        codigo_normalizado
    )

# =============================================================
# V08 - TIPO DE ROSCA / CONEXÃO
# =============================================================
#
# ORIGEM:
# sufixos identificados pelo parser
#
# REGRAS:
# B -> FLANGE
# T -> NPT
# Sem B e sem T -> BSP
#
# =============================================================

def definir_v08(sufixos):

    # FLANGE
    if "B" in sufixos:
        return "FLANGE"

    # NPT
    if "T" in sufixos:
        return "NPT"

    # STANDARD
    return "BSP"


# =============================================================
# V09 - ORIFÍCIO INTERNO
# =============================================================
#
# ORIGENS:
# - família
# - bloco numérico COMPLETO
# - letra especial, quando aplicável
#
# IMPORTANTE:
#
# Aqui usamos:
#
# resultado["bloco_numeros"]
#
# e NÃO resultado["codigo_conexao"]
#
# Exemplo:
#
# 1327IT172T
#
# bloco_numeros = "172"
#
# Portanto:
# 1327 + 172 = 1,75 mm
#
#
# PRIORIDADE:
#
# 1. Família + números + letra especial
# 2. Regra somente pela família
# 3. Família + números
#
# =============================================================


# =============================================================
# V09 - REGRAS PRINCIPAIS
# =============================================================

REGRAS_V09_ORIFICIO = {

    # ---------------------------------------------------------
    # 1314
    # ---------------------------------------------------------

    "1314": {
        "06": "19 mm",
        "08": "26 mm",
        "12": "32 mm",
        "16": "38 mm",
    },


    # ---------------------------------------------------------
    # 1327
    # ---------------------------------------------------------

    "1327": {
        "122": "1,25 mm",
        "172": "1,75 mm",
        "222": "2,25 mm",
        "302": "3,00 mm",
        "402": "4,00 mm",
        "502": "5,00 mm",
        "522": "5,25 mm",
    },


    # ---------------------------------------------------------
    # 1335
    # ---------------------------------------------------------

    "1335": {
        "03": "14 mm",
        "04": "14 mm",
        "06": "18 mm",
        "83": "8 mm",
        "84": "8 mm",
        "86": "8 mm",
    },


    # ---------------------------------------------------------
    # 1342
    # ---------------------------------------------------------

    "1342": {
        "06": "20 mm",
        "08": "26 mm",
        "12": "38 mm",
        "16": "50 mm",
        "20": "76 mm",
        "24": "76 mm",
    },


    # ---------------------------------------------------------
    # 1390
    # ---------------------------------------------------------

    "1390": {
        "02": "6 mm",
        "03": "9 mm",
        "04": "12 mm",
    },


    # ---------------------------------------------------------
    # 2026
    # ---------------------------------------------------------

    "2026": {
        "121": "1,25 mm",
        "171": "1,75 mm",
        "221": "2,25 mm",
        "301": "3,00 mm",

        "122": "1,25 mm",
        "172": "1,75 mm",
        "222": "2,25 mm",
        "302": "3,00 mm",
        "402": "4,00 mm",
    },


    # ---------------------------------------------------------
    # 2036
    # ---------------------------------------------------------

    "2036": {
        "03": "13 mm",
        "04": "13 mm",
        "06": "16 mm",
        "08": "25 mm",
        "12": "32 mm",
    },


    # ---------------------------------------------------------
    # 2012
    # ---------------------------------------------------------

    "2012": {
        "504": "5 mm",
        "506": "8 mm",
        "806": "11 mm",
        "404": "4 mm",
        "406": "4 mm",
        "408": "4 mm",
        "508": "5 mm",
    },


    # ---------------------------------------------------------
    # 1312
    # Mesma regra da 2012
    # ---------------------------------------------------------

    "1312": {
        "504": "5 mm",
        "506": "8 mm",
        "806": "11 mm",
        "404": "4 mm",
        "406": "4 mm",
        "408": "4 mm",
        "508": "5 mm",
    },


    # ---------------------------------------------------------
    # 1330
    # ---------------------------------------------------------

    "1330": {
        "0": "8 mm",
        "04": "18 mm",
        "06": "18 mm",
        "08": "26 mm",
    },


    # ---------------------------------------------------------
    # 2030
    # REGRAS STANDARD
    # ---------------------------------------------------------

    "2030": {
        "08": "32 mm",
        "10": "32 mm",
        "12": "48 mm",
        "16": "51 mm",
    },


    # ---------------------------------------------------------
    # 1332
    # ---------------------------------------------------------

    "1332": {
        "8": "26 mm",
        "10": "32 mm",
        "12": "48 mm",
        "16": "51 mm",
        "20": "76 mm",
        "24": "76 mm",
    },


    # ---------------------------------------------------------
    # 1356
    # ---------------------------------------------------------

    "1356": {
        "03": "2,25 mm",
        "04": "2,25 mm",
    },


    # ---------------------------------------------------------
    # 1388
    # ---------------------------------------------------------

    "1388": {
        "06": "24 mm",
        "08": "24 mm",
        "12": "51 mm",
        "16": "51 mm",
        "20": "76 mm",
        "24": "76 mm",
    },


    # ---------------------------------------------------------
    # 2088
    # ---------------------------------------------------------

    "2088": {
        "8": "32 mm",
        "10": "32 mm",
        "12": "48 mm",
        "16": "51 mm",
    },


    # ---------------------------------------------------------
    # 1323
    # ---------------------------------------------------------

    "1323": {
        "17": "1,75 mm",
        "20": "2,00 mm",
        "25": "2,50 mm",
    },


    # ---------------------------------------------------------
    # 1339
    # ---------------------------------------------------------

    "1339": {
        "01": "6 mm",
        "02": "8 mm",
        "03": "10 mm",
    },


    # ---------------------------------------------------------
    # 1365
    # ---------------------------------------------------------

    "1365": {
        "17": "1,75 mm",
        "22": "2,25 mm",
        "30": "3,00 mm",
        "40": "4,00 mm",
    },


    # ---------------------------------------------------------
    # 1350
    # ---------------------------------------------------------

    "1350": {
        "01": "7 mm",
        "02": "7 mm",
        "03": "10 mm",
    },


    # ---------------------------------------------------------
    # 1351
    # ---------------------------------------------------------

    "1351": {
        "01": "7 mm",
        "02": "7 mm",
        "03": "10 mm",
    },


    # ---------------------------------------------------------
    # 1375
    # ---------------------------------------------------------

    "1375": {
        "02": "5,5 mm",
    },


    # ---------------------------------------------------------
    # 1387
    # ---------------------------------------------------------

    "1387": {
        "01": "1,75 mm",
        "02": "5,50 mm",
    },


    # ---------------------------------------------------------
    # 2050
    # ---------------------------------------------------------

    "2050": {
        "02": "7 mm",
        "03": "7 mm",
        "04": "10 mm",
    },


    # ---------------------------------------------------------
    # 2051
    # ---------------------------------------------------------

    "2051": {
        "02": "7 mm",
        "03": "7 mm",
        "04": "10 mm",
    },


    # ---------------------------------------------------------
    # 2095
    #
    # Na tabela apareceu quatro vezes 02 = 3.
    # Uma regra é suficiente.
    # ---------------------------------------------------------

    "2095": {
        "02": "3 mm",
    },


    # ---------------------------------------------------------
    # 2024
    # ---------------------------------------------------------

    "2024": {
        "02": "1,75 mm",
    },


    # ---------------------------------------------------------
    # 1310
    # ---------------------------------------------------------

    "1310": {
        "06": "19 mm",
        "08": "26 mm",
        "12": "32 mm",
        "16": "38 mm",
        "20": "76 mm",
        "24": "76 mm",
        "32": "100 mm",
        "48": "150 mm",
        "64": "200 mm",
    },


    # ---------------------------------------------------------
    # 1360
    # ---------------------------------------------------------

    "1360": {
        "02": "2,25 mm",
        "03": "7 mm",
        "04": "7 mm",
    },


    # ---------------------------------------------------------
    # 2073
    # ---------------------------------------------------------

    "2073": {
        "06": "29 mm",
        "08": "29 mm",
        "12": "40 mm",
    },


    # ---------------------------------------------------------
    # 2094
    #
    # Conforme sua tabela:
    # números 2, 3 ou 4 = orifício 8 mm
    #
    # Coloquei as duas formas para segurança:
    # 2 / 02
    # 3 / 03
    # 4 / 04
    # ---------------------------------------------------------

    "2094": {
        "2": "8 mm",
        "02": "8 mm",

        "3": "8 mm",
        "03": "8 mm",

        "4": "8 mm",
        "04": "8 mm",
    },
}


# =============================================================
# V09 - REGRAS ESPECIAIS
# =============================================================
#
# Família + bloco numérico + letra especial
#
# Estas regras têm prioridade sobre a regra normal.
#
# =============================================================

REGRAS_V09_ESPECIAIS = {

    # ---------------------------------------------------------
    # 2030 + D
    # ---------------------------------------------------------

    ("2030", "10", "D"): "48 mm",


    # ---------------------------------------------------------
    # 2030 + R
    # ---------------------------------------------------------

    ("2030", "10", "R"): "45 mm",
    ("2030", "12", "R"): "45 mm",
    ("2030", "16", "R"): "45 mm",
}


# =============================================================
# V09 - REGRAS SOMENTE POR FAMÍLIA
# =============================================================
#
# Nestes casos não é necessário olhar
# o bloco numérico.
#
# =============================================================

REGRAS_V09_FAMILIA = {

    "1393": "8 mm",

    "1325": "16 mm",
}


# =============================================================
# FUNÇÃO AUXILIAR
# =============================================================

def buscar_numero_v09(
    regras_familia,
    bloco_numeros
):
    """
    Procura o bloco numérico preservando primeiro
    exatamente aquilo que veio do parser.

    Também protege os casos em que a tabela foi
    cadastrada com ou sem zero à esquerda.

    Exemplos:

    8  <-> 08
    2  <-> 02

    Blocos com 3 dígitos não são alterados.
    """

    if bloco_numeros is None:
        return None


    # ---------------------------------------------------------
    # 1. TESTE EXATO
    # ---------------------------------------------------------

    if bloco_numeros in regras_familia:

        return regras_familia[
            bloco_numeros
        ]


    # ---------------------------------------------------------
    # 2. BLOCO COM 1 DÍGITO
    #
    # Exemplo:
    # 8 -> 08
    # ---------------------------------------------------------

    if len(bloco_numeros) == 1:

        com_zero = bloco_numeros.zfill(2)

        if com_zero in regras_familia:

            return regras_familia[
                com_zero
            ]


    # ---------------------------------------------------------
    # 3. BLOCO COM 2 DÍGITOS COMEÇANDO COM ZERO
    #
    # Exemplo:
    # 08 -> 8
    # ---------------------------------------------------------

    if (
        len(bloco_numeros) == 2
        and bloco_numeros.startswith("0")
    ):

        sem_zero = bloco_numeros[1:]

        if sem_zero in regras_familia:

            return regras_familia[
                sem_zero
            ]


    return None


# =============================================================
# V09 - FUNÇÃO PRINCIPAL
# =============================================================

def definir_v09(
    familia,
    bloco_numeros,
    letra_especial
):
    """
    Define a V09 - orifício interno.

    PRIORIDADE:

    1. Regra especial:
       família + bloco numérico + letra especial

    2. Regra fixa:
       somente família

    3. Regra normal:
       família + bloco numérico
    """


    # =========================================================
    # 1. REGRA ESPECIAL
    # =========================================================

    chave_especial = (
        familia,
        bloco_numeros,
        letra_especial
    )


    if chave_especial in REGRAS_V09_ESPECIAIS:

        return REGRAS_V09_ESPECIAIS[
            chave_especial
        ]


    # =========================================================
    # 2. REGRA SOMENTE POR FAMÍLIA
    # =========================================================

    if familia in REGRAS_V09_FAMILIA:

        return REGRAS_V09_FAMILIA[
            familia
        ]


    # =========================================================
    # 3. LOCALIZAR FAMÍLIA
    # =========================================================

    regras_familia = REGRAS_V09_ORIFICIO.get(
        familia
    )


    if regras_familia is None:

        return None


    # =========================================================
    # 4. LOCALIZAR BLOCO NUMÉRICO
    # =========================================================

    return buscar_numero_v09(
        regras_familia,
        bloco_numeros
    )


# =============================================================
# V10 - PRESSÃO MÍNIMA DE TRABALHO
# =============================================================
#
# ORIGENS POSSÍVEIS:
# - família
# - sufixos
# - código da conexão
# - letra especial
# - código da vedação
#
# PRIORIDADE:
# 1. Regras com mais condições
# 2. Regras por sufixo
# 3. Regras por tamanho
# 4. Regras por vedação
# 5. Regra padrão da família
#
# =============================================================


def definir_v10(
    familia,
    sufixos,
    codigo_conexao,
    letra_especial,
    codigo_vedacao
):

    # ---------------------------------------------------------
    # NORMALIZAR TAMANHO
    #
    # Permite:
    # 8  = 08
    # 4  = 04
    # 2  = 02
    # ---------------------------------------------------------

    tamanho = codigo_conexao

    if tamanho is not None and len(tamanho) == 1:
        tamanho_2 = tamanho.zfill(2)
    else:
        tamanho_2 = tamanho


    # =========================================================
    # 1327
    # =========================================================

    if familia == "1327":
        return "0 bar"


    # =========================================================
    # 1314
    # =========================================================

    if familia == "1314":

        if "A" in sufixos:
            return "0 bar"

        return "0,1 bar"


    # =========================================================
    # 1335
    # =========================================================

    if familia == "1335":

        if "D" in sufixos:
            return "0 bar"

        if "A" in sufixos:
            return "0 bar"

        return "0,1 bar"


    # =========================================================
    # 1342
    # =========================================================

    if familia == "1342":

        if codigo_vedacao in ["T", "E", "V"]:
            return "0,5 bar"

        if codigo_vedacao == "A":
            return "0,2 bar"

        return None


    # =========================================================
    # 1390
    # =========================================================

    if familia == "1390":
        return "0,1 bar"


    # =========================================================
    # 1393
    # =========================================================

    if familia == "1393":
        return "0 bar"


    # =========================================================
    # 2026
    # =========================================================

    if familia == "2026":
        return "0 bar"


    # =========================================================
    # 2036
    # =========================================================

    if familia == "2036":

        if tamanho_2 in ["03", "04", "06"]:
            return "0,2 bar"

        if tamanho_2 == "08":
            return "0,3 bar"

        if tamanho_2 == "12":
            return "0,1 bar"

        return None


    # =========================================================
    # 1312 / 2012
    # =========================================================

    if familia in ["1312", "2012"]:
        return "0 bar"


    # =========================================================
    # 1330
    # =========================================================

    if familia == "1330":

        # Exceção mais específica primeiro
        if (
            tamanho_2 == "08"
            and letra_especial == "R"
        ):
            return "0,01 bar"

        if tamanho_2 == "08":
            return "0,001 bar"

        if tamanho_2 in ["00", "04", "06"]:
            return "0 bar"

        # Proteção caso o parser entregue "0"
        if tamanho == "0":
            return "0 bar"

        return None


    # =========================================================
    # 2030
    # =========================================================

    if familia == "2030":

        # -----------------------------------------
        # letra especial R
        # -----------------------------------------

        if (
            letra_especial == "R"
            and tamanho_2 in ["10", "12", "16"]
        ):
            return "0,01 bar"

        # -----------------------------------------
        # letra especial D
        # -----------------------------------------

        if (
            letra_especial == "D"
            and tamanho_2 == "10"
        ):
            return "0,001 bar"

        # -----------------------------------------
        # 12 / 16 standard
        # -----------------------------------------

        if tamanho_2 in ["12", "16"]:
            return "0,001 bar"

        # -----------------------------------------
        # 08 / 10 standard
        # -----------------------------------------

        if tamanho_2 in ["08", "10"]:
            return "0 bar"

        return None


    # =========================================================
    # 1332
    # =========================================================

    if familia == "1332":
        return "0 bar"


    # =========================================================
    # 1356
    # =========================================================

    if familia == "1356":
        return "0 bar"


    # =========================================================
    # 1388
    # =========================================================

    if familia == "1388":

        if "A" in sufixos:
            return "0 bar"

        if (
            "D" in sufixos
            and tamanho_2 in ["20", "24"]
        ):
            return "0 bar"

        return None


    # =========================================================
    # 2088
    # =========================================================

    if familia == "2088":

        if tamanho_2 in ["08", "10", "12", "16"]:
            return "0 bar"

        return None


    # =========================================================
    # V171
    # =========================================================

    if familia == "V171":
        return "0 bar"


    # =========================================================
    # 1323
    # =========================================================

    if familia == "1323":
        return "0 bar"


    # =========================================================
    # 1325
    # =========================================================

    if familia == "1325":
        return "0 bar"


    # =========================================================
    # 1339
    # =========================================================

    if familia == "1339":

        if tamanho_2 in ["01", "02", "03"]:
            return "0,5 bar"

        return None


    # =========================================================
    # 1350
    # =========================================================

    if familia == "1350":

        if "A" in sufixos:
            return "1 bar"

        if "B" in sufixos:
            return "0,5 bar"

        if "C" in sufixos:
            return "0,5 bar"

        if any(
            s in sufixos
            for s in ["G", "I", "D", "F"]
        ):
            return "0 bar"

        return None


    # =========================================================
    # 1351
    # =========================================================

    if familia == "1351":

        if "A" in sufixos:
            return "1 bar"

        if "B" in sufixos:
            return "0,5 bar"

        if "C" in sufixos:
            return "0,5 bar"

        if "G" in sufixos:
            return "1 bar"

        if "H" in sufixos:
            return "0,5 bar"

        if any(
            s in sufixos
            for s in ["K", "N", "M", "D", "J", "F"]
        ):
            return "0 bar"

        return None


    # =========================================================
    # 1365
    # =========================================================

    if familia == "1365":
        return "0 bar"


    # =========================================================
    # 1375
    # =========================================================

    if familia == "1375":
        return "0,5 bar"


    # =========================================================
    # 1387
    # =========================================================

    if familia == "1387":

        if "N" in sufixos:

            if tamanho_2 == "01":
                return "0 bar"

            if tamanho_2 == "02":
                return "0,5 bar"

        return None


    # =========================================================
    # 2050
    # =========================================================

    if familia == "2050":

        if "A" in sufixos:
            return "1 bar"

        if "B" in sufixos:
            return "0,5 bar"

        if "C" in sufixos:
            return "0,5 bar"

        if any(
            s in sufixos
            for s in ["G", "I"]
        ):
            return "0 bar"

        return None


    # =========================================================
    # 2051
    # =========================================================

    if familia == "2051":

        if "A" in sufixos:
            return "1 bar"

        if "B" in sufixos:
            return "0,5 bar"

        if "C" in sufixos:
            return "0,5 bar"

        if "G" in sufixos:
            return "1 bar"

        if "H" in sufixos:
            return "0,5 bar"

        if any(
            s in sufixos
            for s in ["K", "N", "M"]
        ):
            return "0 bar"

        return None


    # =========================================================
    # 2024
    # =========================================================

    if familia == "2024":

        if tamanho_2 == "02":
            return "0,8 bar"

        return None


    # =========================================================
    # 1310 / 1311
    # =========================================================

    if familia in ["1310", "1311"]:
        return "1,5 bar"


    # =========================================================
    # 1360
    # =========================================================

    if familia == "1360":
        return "0 bar"


    # =========================================================
    # 2073
    # =========================================================

    if familia == "2073":
        return "0,5 bar"


    # =========================================================
    # 2094
    # =========================================================

    if familia == "2094":
        return "1 bar"


    # =========================================================
    # SEM REGRA
    # =========================================================

    return None


# =============================================================
# V11 - PRESSÃO MÁXIMA DE TRABALHO - CA
# =============================================================

def definir_v11(
    familia,
    sufixos,
    bloco_numeros,
    codigo_conexao,
    letra_especial,
    codigo_vedacao
):

    # =========================================================
    # NORMALIZAÇÕES
    # =========================================================

    tamanho = codigo_conexao

    if tamanho is not None and len(tamanho) == 1:
        tamanho_2 = tamanho.zfill(2)
    else:
        tamanho_2 = tamanho

    # Quando temos 3 números:
    # 122 -> orifício 12
    # 172 -> orifício 17
    #
    # Quando temos 2:
    # 17 -> 17
    if bloco_numeros:

        if len(bloco_numeros) == 3:
            orificio = bloco_numeros[:2]
        else:
            orificio = bloco_numeros

    else:
        orificio = None


    # =========================================================
    # 1314
    # =========================================================

    if familia == "1314":

        if "A" in sufixos:
            return "7 bar"

        return "15 bar"


    # =========================================================
    # 1327
    # =========================================================

    if familia == "1327":

        # INA
        if "INA" in sufixos:

            regras_ina = {
                "12": "50 bar",
                "17": "20 bar",
                "22": "12 bar",
                "30": "10 bar",
                "40": "5 bar",
            }

            return regras_ina.get(orificio)

        # Orifício 12 + vedação T
        if orificio == "12" and codigo_vedacao == "T":
            return "100 bar"

        regras = {
            "12": "70 bar",
            "17": "35 bar",
            "22": "20 bar",
            "30": "10 bar",
            "40": "5 bar",
            "50": "3 bar",
            "52": "2,2 bar",
        }

        return regras.get(orificio)


    # =========================================================
    # 1335
    # =========================================================

    if familia == "1335":

        if "D" in sufixos:

            # Tabela informa orifício 08 = 1 bar.
            # Nos códigos 83/84/86 o orifício é 8.
            if bloco_numeros in ["83", "84", "86"]:
                return "1 bar"

            return "0,2 bar"

        if "A" in sufixos:
            return "7 bar"

        return "10 bar"


    # =========================================================
    # 1342
    # =========================================================

    if familia == "1342":

        if "INA" in sufixos and codigo_vedacao == "T":
            return "10 bar"

        if codigo_vedacao == "T":
            return "17 bar"

        return "10 bar"


    # =========================================================
    # 1390
    # =========================================================

    if familia == "1390":

        if "INA" in sufixos:
            return "10 bar"

        return "15 bar"


    # =========================================================
    # 1393
    # =========================================================

    if familia == "1393":
        return "4 bar"


    # =========================================================
    # 2026
    # =========================================================

    if familia == "2026":

        regras = {
            "12": "37 bar",
            "17": "15 bar",
            "22": "7,5 bar",
            "30": "3 bar",
            "40": "3 bar",
        }

        return regras.get(orificio)


    # =========================================================
    # 2036
    # =========================================================

    if familia == "2036":

        if codigo_vedacao == "T":
            return "10 bar"

        if tamanho_2 in ["08", "12"]:
            return "10 bar"

        return "15 bar"


    # =========================================================
    # 1359
    # =========================================================

    if familia == "1359":
        return "10 bar"


    # =========================================================
    # 2012 / 1312
    # =========================================================

    if familia in ["2012", "1312"]:

        # NA
        if "NA" in sufixos:

            if bloco_numeros in ["404", "406", "408"]:
                return "15 bar"

            if bloco_numeros in ["506", "508"]:
                return "12 bar"

        # Orifício 8 + conexão 06/08
        if bloco_numeros in ["806", "808"]:
            return "12 bar"

        # Conexão 08
        if tamanho_2 == "08":
            return "6 bar"

        # Conexão 04 / 06
        if tamanho_2 in ["04", "06"]:
            return "21 bar"

        return None


    # =========================================================
    # 1330
    # =========================================================

    if familia == "1330":

        if tamanho_2 == "08" and letra_especial == "R":
            return "2 bar"

        if tamanho == "0" or tamanho_2 == "00":
            return "1 bar"

        if tamanho_2 in ["04", "06", "08"]:
            return "0,2 bar"

        return None


    # =========================================================
    # 2030
    # =========================================================

    if familia == "2030":

        if (
            letra_especial == "R"
            and tamanho_2 in ["10", "12", "16"]
        ):
            return "2 bar"

        if letra_especial == "D" and tamanho_2 == "10":
            return "0,2 bar"

        if tamanho_2 in ["08", "10"]:
            return "0,05 bar"

        if tamanho_2 in ["12", "16"]:
            return "0,2 bar"

        return None


    # =========================================================
    # 1332
    # =========================================================

    if familia == "1332":

        if tamanho_2 in ["08", "10"]:
            return "3 bar"

        if tamanho_2 in ["12", "16"]:
            return "2 bar"

        if tamanho_2 in ["20", "24"]:
            return "1 bar"

        return None


    # =========================================================
    # 1356
    # =========================================================

    if familia == "1356":

        if "-48" in sufixos and tamanho_2 == "04":
            return "10 bar"

        if (
            tamanho_2 in ["03", "04"]
            and codigo_vedacao == "T"
        ):
            return "20 bar"

        return None


    # =========================================================
    # 1388
    # =========================================================

    if familia == "1388":

        if "D" in sufixos:
            return "0,1 bar"

        if "AR" in sufixos:
            return "5 bar"

        if "A" in sufixos:
            return "5 bar"

        return None


    # =========================================================
    # 2088
    # =========================================================

    if familia == "2088":
        return "3 bar"


    # =========================================================
    # V171
    # =========================================================
    #
    # IMPORTANTE:
    # Seu parser atual ainda precisa ser adaptado
    # para reconhecer a família alfanumérica V171.
    # =========================================================

    if familia == "V171":

        if tamanho == "P06":
            return "0,2 bar"

        if tamanho in ["2", "3", "02", "03"]:
            return "1,5 bar"

        return None


    # =========================================================
    # 1323
    # =========================================================

    if familia == "1323":

        if "U" in sufixos:

            regras_u = {
                "17": "9 bar",
                "20": "7 bar",
                "25": "3 bar",
            }

            return regras_u.get(orificio)

        regras = {
            "17": "12 bar",
            "20": "8 bar",
            "25": "3 bar",
        }

        return regras.get(orificio)


    # =========================================================
    # REGRAS FIXAS
    # =========================================================

    if familia == "1325":
        return "10 bar"

    if familia == "1339":
        return "10 bar"

    if familia == "1350":
        return "10 bar"

    if familia == "1351":
        return "10 bar"


    # =========================================================
    # 1365
    # =========================================================

    if familia == "1365":

        if "C" in sufixos:

            return {
                "17": "15 bar",
                "22": "11 bar",
                "30": "6 bar",
                "40": "3 bar",
            }.get(orificio)

        if "A" in sufixos:

            return {
                "17": "14 bar",
                "22": "10,5 bar",
                "30": "5 bar",
                "40": "3 bar",
            }.get(orificio)

        if "U" in sufixos:

            return {
                "17": "9 bar",
                "22": "7 bar",
                "30": "4 bar",
                "40": "1,5 bar",
            }.get(orificio)

        return None


    # =========================================================
    # OUTRAS REGRAS FIXAS
    # =========================================================

    if familia == "1375":
        return "10 bar"

    if familia == "1387":
        return "10 bar"

    if familia == "2050":
        return "8 bar"

    if familia == "2051":
        return "10 bar"

    if familia == "2095":
        return "8 bar"

    if familia == "2024":
        return "10 bar"


    # =========================================================
    # 1360
    # =========================================================

    if familia == "1360":

        if tamanho_2 == "02":
            return "1 bar"

        if tamanho_2 in ["03", "04"]:
            return "4 bar"

        return None


    # =========================================================
    # 2073
    # =========================================================

    if familia == "2073":
        return "10 bar"


    # =========================================================
    # 2094
    # =========================================================

    if familia == "2094":
        return "250 bar"


    # =========================================================
    # 1397
    # =========================================================

    if familia == "1397":

        if tamanho_2 == "16":
            return "25 bar"

        if tamanho_2 == "24":
            return "10 bar"

        return None


    # =========================================================
    # 3073
    # =========================================================

    if familia == "3073":
        return "8 bar"


    # =========================================================
    # 3014
    # =========================================================

    if familia == "3014":

        if tamanho_2 in ["12", "16"]:
            return "6 bar"

        return "7 bar"


    # =========================================================
    # SEM REGRA
    # =========================================================

    return None


# =============================================================
# V12 - TEMPERATURA DO FLUIDO
# =============================================================
#
# ORIGENS:
# - código da vedação
# - família
# - sufixos
#
# PRIORIDADE:
# 1. Sufixo especial
# 2. Regra específica da família
# 3. Regra standard da vedação
#
# =============================================================


REGRAS_V12_VEDACAO = {
    "A": "80°C",
    "V": "150°C",
    "E": "145°C",
    "T": "180°C",
}


REGRAS_V12_FAMILIA = {
    "3014": "60°C",
    "1397": "80°C",
    "2094": "80°C",
    "3073": "60°C",	


}


def definir_v12(
    familia,
    codigo_vedacao,
    sufixos
):

    # =========================================================
    # 1. SUFIXO UC
    # =========================================================

    if "UC" in sufixos:

        return (
            "nitrogênio líquido -200°C / 50°C, "
            "CO2 -60°C / 50°C, "
            "(para CO2 líquido, o diâmetro interno do tubo "
            "deve ser menor que o orifício interno da válvula)"
        )


    # =========================================================
    # 2. EXCEÇÕES POR FAMÍLIA
    # =========================================================

    if familia in REGRAS_V12_FAMILIA:

        return REGRAS_V12_FAMILIA[
            familia
        ]


    # =========================================================
    # 3. STANDARD POR VEDAÇÃO
    # =========================================================

    return REGRAS_V12_VEDACAO.get(
        codigo_vedacao
    )

# =============================================================
# V13 - DADOS DA BOBINA
# =============================================================
#
# CARACTERÍSTICAS:
# - tipo de bobina
# - classe térmica
# - proteção
# - conexão elétrica
# - certificação
#
# ORIGENS:
# - prefixos
# - família
#
# =============================================================


FAMILIAS_BOBINA_PEQUENA = [
    "2026",
    "2036",
]


FAMILIAS_CAIXA_ABRIGADA = [
    "1312",
    "2012",
    "1314",
    "1388",
    "2088",
]


def definir_v13(
    familia,
    prefixos
):

    # =========================================================
    # DADO COMUM A TODAS
    # =========================================================

    classe_termica = (
        "Classe H - suporta até 180°C"
    )


    # =========================================================
    # PREFIXO ZC
    # =========================================================

    if "ZC" in prefixos:

        return {
            "tipo_bobina":
                "Bobina encapsulada ZC",

            "classe_termica":
                classe_termica,

            "protecao":
                (
                    "À prova de explosão, intempéries "
                    "e corrosão salina NEMA 4X IEC 79-18m"
                ),

            "conexao_eletrica":
                '1/2" NPT',

            "certificacao":
                (
                    "Tipos 3, 3s, 4, 4x, 6, 7 e 9, "
                    "Classe I Divisão 1 Grupo A, B, C e D, "
                    "Classe II Divisão 1 Grupo E"
                ),
        }


    # =========================================================
    # PREFIXO YC
    # =========================================================

    if "YC" in prefixos:

        return {
            "tipo_bobina":
                "Bobina encapsulada YC",

            "classe_termica":
                classe_termica,

            "protecao":
                (
                    "À prova de intempéries e corrosão "
                    "salina NEMA 4X IEC 79-18m"
                ),

            "conexao_eletrica":
                '1/2" NPT',

            "certificacao":
                None,
        }


    # =========================================================
    # PREFIXO Z
    # =========================================================

    if "Z" in prefixos:

        return {
            "tipo_bobina":
                "Bobina carretel com caixa Z",

            "classe_termica":
                classe_termica,

            "protecao":
                (
                    'À prova de explosão e intempéries '
                    'IEC 79-1 "d"'
                ),

            "conexao_eletrica":
                '1/2" NPT',

            "certificacao":
                (
                    "ATEX - Diretiva 94 / 9 CE - "
                    "II 2G Ex d IIB T3 – "
                    "INMETRO NCC 15.0235 X"
                ),
        }


    # =========================================================
    # PREFIXO Y
    # =========================================================

    if "Y" in prefixos:

        return {
            "tipo_bobina":
                "Bobina carretel com caixa Y",

            "classe_termica":
                classe_termica,

            "protecao":
                (
                    'À prova de intempéries '
                    'IEC 79-1 "d"'
                ),

            "conexao_eletrica":
                '1/2" NPT',

            "certificacao":
                None,
        }


    # =========================================================
    # CAIXA DE USO GERAL ABRIGADO
    # =========================================================

    if familia in FAMILIAS_CAIXA_ABRIGADA:

        return {
            "tipo_bobina":
                (
                    "Bobina carretel com caixa "
                    "de uso geral abrigado"
                ),

            "classe_termica":
                classe_termica,

            "protecao":
                "IP65",

            "conexao_eletrica":
                '1/2" NPT',

            "certificacao":
                None,
        }


    # =========================================================
    # BOBINA STANDARD PEQUENA
    # =========================================================

    if familia in FAMILIAS_BOBINA_PEQUENA:

        return {
            "tipo_bobina":
                "Bobina standard pequena encapsulada",

            "classe_termica":
                classe_termica,

            "protecao":
                "IP65",

            "conexao_eletrica":
                "PG9",

            "certificacao":
                None,
        }


    # =========================================================
    # BOBINA STANDARD GRANDE
    # =========================================================

    return {
        "tipo_bobina":
            "Bobina standard grande encapsulada",

        "classe_termica":
            classe_termica,

        "protecao":
            "IP65",

        "conexao_eletrica":
            "PG9",

        "certificacao":
            None,
    }
# =============================================================
# V14 - POTÊNCIA DA BOBINA
# =============================================================
#
# ORIGENS:
# - família
# - prefixos
# - código da conexão
# - tipo de alimentação informado externamente
#
# tipo_alimentacao:
# "HZ"  = corrente alternada
# "VCC" = corrente contínua
#
# =============================================================

def definir_v14(
    familia,
    prefixos,
    codigo_conexao,
    tipo_alimentacao
):

    if not tipo_alimentacao:
        return None

    tipo_alimentacao = tipo_alimentacao.strip().upper()

    tem_z = "Z" in prefixos
    tem_zc = "ZC" in prefixos

    # Normaliza a conexão:
    # 8 -> 08
    # 6 -> 06
    conexao = codigo_conexao

    if conexao is not None and len(conexao) == 1:
        conexao = conexao.zfill(2)


    # =========================================================
    # 1314
    # =========================================================

    if familia == "1314":

        if tipo_alimentacao == "HZ":
            return "30 W"

        if tipo_alimentacao == "VCC":
            return "48 W"


    # =========================================================
    # 1388
    # =========================================================

    if familia == "1388":

        if (
            tem_z
            and conexao in [
                "06",
                "08",
                "12",
                "16",
                "20",
                "24",
            ]
        ):

            if tipo_alimentacao == "HZ":
                return "70 W"

            if tipo_alimentacao == "VCC":
                return "113 W"


    # =========================================================
    # 2088
    # =========================================================

    if familia == "2088":
        return "50 W"


    # =========================================================
    # 1312 / 2012
    # =========================================================

    if familia in ["1312", "2012"]:

        if tem_z:
            return "48 W"

        if tipo_alimentacao == "HZ":
            return "46 W"

        if tipo_alimentacao == "VCC":
            return "48 W"


    # =========================================================
    # 1344
    # =========================================================

    if familia == "1344":

        if tipo_alimentacao == "HZ":
            return "46 W"

        if tipo_alimentacao == "VCC":
            return "48 W"


    # =========================================================
    # 3073
    # =========================================================

    if familia == "3073":

        if tem_zc:

            if tipo_alimentacao == "HZ":
                return "13 W"

            if tipo_alimentacao == "VCC":
                return "19 W"

        else:

            if tipo_alimentacao == "HZ":
                return "13 W"

            if tipo_alimentacao == "VCC":
                return "21 W"


    # =========================================================
    # 2026 / 2036
    # =========================================================

    if familia in ["2026", "2036"]:
        return "6 W"


    # =========================================================
    # REGRA GERAL
    # =========================================================

    if tipo_alimentacao == "HZ":
        return "13 W"

    if tipo_alimentacao == "VCC":
        return "19 W"


    return None



# =============================================================
# V15 - PREFIXOS E SUFIXOS EXTRAS
# =============================================================
#
# OBJETIVO:
#
# Preservar individualmente cada prefixo e cada sufixo
# identificado pelo parser.
#
# A V15 NÃO junta tudo em uma única frase.
#
# Isso permite que futuramente o app decida:
#
# - texto que entra na linha da bobina
# - texto que entra nas observações
# - texto que entra como acessório
# - texto que não precisa aparecer
#
# =============================================================


# =============================================================
# V15 - REGRAS DOS PREFIXOS
# =============================================================

REGRAS_V15_PREFIXOS = {

    "ZC": (
        "bobina encapsulada à prova de explosão, intempéries "
        "e corrosão salina NEMA 4X IEC 79-18m, "
        "potência {potencia}, tipos 3, 3s, 4, 4x, 6, 7 e 9 "
        "Classe I Divisão 1 Grupo A, B, C e D. "
        "Classe II Divisão 1 Grupo E"
    ),

    "YC": (
        "bobina encapsulada à prova de intempéries "
        "e corrosão salina NEMA 4X IEC 79-18m, "
        "potência {potencia}"
    ),

    "PA": (
        "com temporizador analógico"
    ),

    "PE": (
        "com temporizador eletrônico"
    ),

    "Z": (
        'bobina com caixa à prova de explosão e intempéries '
        'IEC 79-1 "d" '
        '(ATEX - Diretiva 94 / 9 CE - II 2G Ex d IIB T3 – '
        'INMETRO NCC 15.0235 X)'
    ),

    "E": (
        "com limpeza para oxigênio"
    ),

    "Y": (
        'bobina com caixa à prova de intempéries IEC 79-1 "d"'
    ),
}


# =============================================================
# V15 - REGRAS DOS SUFIXOS
# =============================================================
#
# None significa:
#
# O sufixo é reconhecido e preservado,
# porém NÃO gera texto extra na V15.
#
# Ele pode continuar sendo usado normalmente por V02,
# V03, V04, V08, V10, V11 etc.
#
# =============================================================

REGRAS_V15_SUFIXOS = {

    # ---------------------------------------------------------
    # NÃO GERAM TEXTO EXTRA
    # ---------------------------------------------------------

    "INA": None,
    "NA": None,
    "VB": None,
    "LB": None,
    "T": None,
    "A": None,
    "D": None,
    "U": None,
    "C": None,
    "B": None,
    "G": None,
    "H": None,
    "I": None,
    "K": None,
    "N": None,
    "M": None,
    "J": None,
    "AR": None,
    "-48": None,


    # ---------------------------------------------------------
    # GERAM TEXTO EXTRA
    # ---------------------------------------------------------

    "-69A": (
        'com rearme manual de segurança "free-handle" '
        "com sinal elétrico"
    ),

    "-69B": (
        'com rearme manual de segurança "free-handle" '
        "sem sinal elétrico"
    ),

    "UC": (
        "USO PARA CRIOGENIA"
    ),

    "-M": (
        "com operador manual sob o orifício principal"
    ),

    "F": (
        "com filtro"
    ),
}


# =============================================================
# V15 - FUNÇÃO PRINCIPAL
# =============================================================

def definir_v15(
    familia,
    prefixos,
    sufixos,
    v14
):

    """
    Retorna os prefixos e sufixos de forma estruturada.

    Exemplo:

    {
        "prefixos": [
            {
                "codigo": "Z",
                "texto": "bobina com caixa..."
            }
        ],

        "sufixos": [
            {
                "codigo": "-M",
                "texto": "com operador manual..."
            }
        ],

        "extras": [
            ...
        ]
    }

    A lista "extras" contém somente os elementos
    que realmente geram algum texto.
    """

    prefixos_processados = []
    sufixos_processados = []
    extras = []


    # =========================================================
    # 1. PROCESSAR PREFIXOS
    # =========================================================

    for prefixo in prefixos:

        texto = REGRAS_V15_PREFIXOS.get(
            prefixo
        )


        # -----------------------------------------------------
        # SUBSTITUIR POTÊNCIA NOS PREFIXOS ZC / YC
        # -----------------------------------------------------

        if texto and "{potencia}" in texto:

            if v14:
                texto = texto.format(
                    potencia=v14
                )

            else:
                texto = texto.format(
                    potencia="potência não identificada"
                )


        item = {
            "tipo": "prefixo",
            "codigo": prefixo,
            "texto": texto,
        }


        prefixos_processados.append(
            item
        )


        # Só entra em extras se tiver texto.
        if texto:

            extras.append(
                item.copy()
            )


    # =========================================================
    # 2. PROCESSAR SUFIXOS
    # =========================================================

    for sufixo in sufixos:

        # -----------------------------------------------------
        # SUFIXO VARIÁVEL -I*
        # -----------------------------------------------------
        #
        # Exemplos:
        #
        # -I1
        # -I2
        # -I4
        # -I10
        #
        # -----------------------------------------------------

        if sufixo.startswith("-I"):

            texto = (
                "com indicador de posição "
                "de contato simples"
            )

        else:

            texto = REGRAS_V15_SUFIXOS.get(
                sufixo
            )


        item = {
            "tipo": "sufixo",
            "codigo": sufixo,
            "texto": texto,
        }


        sufixos_processados.append(
            item
        )


        # Só entra em extras se realmente
        # houver alguma informação textual.
        if texto:

            extras.append(
                item.copy()
            )


    # =========================================================
    # 3. RESULTADO DA V15
    # =========================================================

    return {

        "prefixos": prefixos_processados,

        "sufixos": sufixos_processados,

        "extras": extras,
    }


# =============================================================
# V16 - KV
# =============================================================
#
# ORIGENS:
# - família
# - bloco numérico COMPLETO
# - letra especial, quando aplicável
#
# PRIORIDADE:
# 1. Família + números + letra especial
# 2. Família + números
#
# =============================================================


# =============================================================
# REGRAS PRINCIPAIS
# =============================================================

REGRAS_V16_KV = {

    "1314": {
        "06": "6",
        "08": "10",
        "12": "15",
        "16": "23",
    },

    "1327": {
        "122": "0,05",
        "172": "0,09",
        "222": "0,13",
        "302": "0,26",
        "402": "0,43",
        "502": "0,60",
        "522": "0,65",
    },

    "1335": {
        "03": "2,35",
        "04": "2,65",
        "06": "4,3",
        "83": "1,7",
        "84": "1,7",
        "86": "1,7",
    },

    "1342": {
        "06": "5",
        "08": "11",
        "12": "25",
        "16": "40",
        "20": "66",
        "24": "87",
    },

    "1390": {
        "02": "0,80",
        "03": "1,60",
        "04": "2,35",
    },

    "1393": {
        "082": "1,80",
        "083": "2,80",
        "084": "2,80",
    },

    "2026": {
        "121": "0,05",
        "171": "0,09",
        "221": "0,13",
        "301": "0,26",
        "122": "0,05",
        "172": "0,09",
        "222": "0,13",
        "302": "0,26",
        "402": "0,35",
    },

    "2036": {
        "03": "2,60",
        "04": "4,20",
        "06": "5,50",
        "08": "10,50",
        "12": "22",
    },

    "2012": {
        "504": "0,60",
        "506": "0,60",
        "806": "1,40",
        "808": "1,40",
        "08": "2,50",
        "404": "0,39",
        "406": "0,60",
        "408": "0,39",
        "508": "0,60",
    },

    "1312": {
        "504": "0,60",
        "506": "0,60",
        "806": "1,40",
        "808": "1,40",
        "08": "2,50",
        "404": "0,39",
        "406": "0,60",
        "408": "0,39",
        "508": "0,60",
    },

    "1330": {
        "0": "1,7",
        "04": "3,4",
        "06": "4,2",
        "08": "12",
    },

    "2030": {
        "08": "10",
        "10": "12",
        "12": "35",
        "16": "43",
    },

    "1332": {
        "8": "13",
        "10": "22",
        "12": "30",
        "16": "55",
        "20": "60",
        "24": "79",
    },

    "1356": {
        "03": "0,13",
        "04": "0,13",
        "4-48": "0,60",
    },

    "1388": {
        "06": "6",
        "08": "12",
        "12": "36",
        "16": "49",
        "20": "65",
        "24": "80",
    },

    "2088": {
        "8": "12",
        "10": "15",
        "12": "36",
        "16": "49",
    },

    "1323": {
        "17": "0,09",
        "20": "0,10",
        "25": "0,14",
    },

    "1325": {
        "3": "2,7",
        "4": "3,4",
        "6": "4,7",
    },

    "1339": {
        "01": "0,34",
        "02": "0,68",
        "03": "1,27",
    },

    "1365": {
        "17": "0,08",
        "22": "0,12",
        "30": "0,21",
        "40": "0,16",
    },

    "1350": {
        "01": "0,80",
        "02": "0,96",
        "03": "1,90",
    },

    "1351": {
        "01": "0,80",
        "02": "0,96",
        "03": "1,90",
    },

    "1375": {
        "02": "0,59",
    },

    "1387": {
        "01": "0,09",
        "02": "0,59",
    },

    "2050": {
        "02": "0,80",
        "03": "0,96",
        "04": "1,90",
    },

    "2051": {
        "02": "0,80",
        "03": "0,96",
        "04": "1,90",
    },

    "2095": {
        "02": "0,18",
    },

    "2024": {
        "02": "0,08",
    },

    "1310": {
        "06": "6",
        "08": "11",
        "12": "15",
        "16": "23",
        "20": "66",
        "24": "86",
        "32": "150",
        "48": "320",
        "64": "600",
    },

    "1360": {
        "02": "0,15",
        "03": "1",
        "04": "1",
    },

    "2073": {
        "06": "8,7",
        "08": "16",
        "12": "29",
    },

    "2094": {
        "2": "1,1",
        "02": "1,1",
        "3": "1,5",
        "03": "1,5",
        "4": "1,5",
        "04": "1,5",
    },

    "3014": {
        "04": "2,65",
        "06": "4,3",
        "08": "11",
        "12": "26",
        "16": "41,5",
    },

    "3073": {
        "06": "8,7",
        "08": "16",
        "12": "49",
        "16": "60",
    },

    "1397": {
        "16": "36",
        "24": "85",
    },
}


# =============================================================
# REGRAS ESPECIAIS
# =============================================================
#
# Família + bloco numérico + letra especial
#
# =============================================================

REGRAS_V16_ESPECIAIS = {

    ("2030", "10", "D"): "24",

    ("2030", "10", "R"): "24",
    ("2030", "12", "R"): "35",
    ("2030", "16", "R"): "43",
}


# =============================================================
# FUNÇÃO AUXILIAR
# =============================================================

def buscar_numero_v16(
    regras_familia,
    bloco_numeros
):

    if bloco_numeros is None:
        return None

    # Busca exata
    if bloco_numeros in regras_familia:
        return regras_familia[
            bloco_numeros
        ]

    # 8 -> 08
    if len(bloco_numeros) == 1:

        com_zero = bloco_numeros.zfill(2)

        if com_zero in regras_familia:
            return regras_familia[
                com_zero
            ]

    # 08 -> 8
    if (
        len(bloco_numeros) == 2
        and bloco_numeros.startswith("0")
    ):

        sem_zero = bloco_numeros[1:]

        if sem_zero in regras_familia:
            return regras_familia[
                sem_zero
            ]

    return None


# =============================================================
# FUNÇÃO PRINCIPAL V16
# =============================================================

def definir_v16(
    familia,
    bloco_numeros,
    letra_especial
):

    # =========================================================
    # 1. REGRA ESPECIAL
    # =========================================================

    chave_especial = (
        familia,
        bloco_numeros,
        letra_especial
    )

    if chave_especial in REGRAS_V16_ESPECIAIS:

        return REGRAS_V16_ESPECIAIS[
            chave_especial
        ]


    # =========================================================
    # 2. REGRA NORMAL
    # =========================================================

    regras_familia = REGRAS_V16_KV.get(
        familia
    )

    if regras_familia is None:
        return None

    return buscar_numero_v16(
        regras_familia,
        bloco_numeros
    )


# =============================================================
# V17 - IMAGEM DO PRODUTO
# =============================================================
#
# OBJETIVO:
#
# Identificar qual imagem corresponde ao código do produto.
#
# A V17 NÃO busca a imagem no Supabase.
# Ela retorna apenas o nome do arquivo.
#
# Exemplo:
#
# V17 = "1342_Z.png"
#
# Depois o app utilizará esse nome para buscar o arquivo
# no Supabase Storage.
#
# =============================================================


def definir_v17(
    familia,
    prefixos,
    sufixos,
    letra_especial,
    codigo_corpo,
    codigo_vedacao,
    codigo_conexao,
):

    # =========================================================
    # NORMALIZAÇÕES
    # =========================================================

    prefixos = prefixos or []
    sufixos = sufixos or []

    familia = str(
        familia or ""
    ).upper()

    letra_especial = str(
        letra_especial or ""
    ).upper()

    codigo_corpo = str(
        codigo_corpo or ""
    ).upper()

    codigo_vedacao = str(
        codigo_vedacao or ""
    ).upper()

    tamanho = str(
        codigo_conexao or ""
    ).upper()


    # ---------------------------------------------------------
    # Normalização do tamanho
    #
    # 8 -> 08
    # 4 -> 04
    # ---------------------------------------------------------

    if tamanho.isdigit() and len(tamanho) == 1:
        tamanho_2 = tamanho.zfill(2)
    else:
        tamanho_2 = tamanho


    # =========================================================
    # FUNÇÕES AUXILIARES
    # =========================================================

    def tem_prefixo(*opcoes):

        return any(
            opcao in prefixos
            for opcao in opcoes
        )


    def tem_sufixo(*opcoes):

        return any(
            opcao in sufixos
            for opcao in opcoes
        )


    def tem_sufixo_69():

        return any(
            str(sufixo).startswith("-69")
            for sufixo in sufixos
        )


    def tem_sufixo_indicador():

        return any(
            str(sufixo).startswith("-I")
            for sufixo in sufixos
        )


    def corpo_inox():

        # S = Inox 304
        # I = Inox 316

        return codigo_corpo in [
            "S",
            "I",
        ]


    # =========================================================
    # 2012 / 1312
    # =========================================================

    if familia in [
        "2012",
        "1312",
    ]:

        return "1312_2012.png"


    # =========================================================
    # 1314
    # =========================================================

    if familia == "1314":

        if tamanho_2 == "24":
            return "1314_24.png"

        return "1314.png"


    # =========================================================
    # CONTROLE DE NÍVEL
    # =========================================================

    if familia in [
        "1317",
        "2017",
        "2049",
        "1340",
        "1376",
        "1380",
    ]:

        return "1317.png"


    # =========================================================
    # 1323
    # =========================================================

    if familia == "1323":

        if tem_prefixo("ZC"):
            return "1323_ZC.png"

        if tem_prefixo("Z"):
            return "1323_Z.png"

        return "1323.png"


    # =========================================================
    # 1325
    # =========================================================

    if familia == "1325":

        if tem_prefixo("ZC"):
            return "1325_ZC.png"

        if tem_prefixo("Z"):
            return "1325_Z.png"

        return "1325.png"


    # =========================================================
    # 1327
    # =========================================================

    if familia == "1327":

        if tem_prefixo("ZC"):
            return "1327_ZC.png"

        if tem_prefixo("Z"):
            return "1327_Z.png"

        if corpo_inox():
            return "1327_INOX.png"

        return "1327.png"


    # =========================================================
    # 1330
    # =========================================================

    if familia == "1330":

        if (
            tem_prefixo("ZC")
            and tamanho_2 == "08"
        ):
            return "1330_ZC_08.png"

        if (
            tem_prefixo("ZC")
            and tamanho_2 in [
                "04",
                "06",
            ]
        ):
            return "1330-ZC-LA04.png"

        if (
            tem_prefixo("Z")
            and tamanho_2 == "08"
        ):
            return "1330_Z_08.png"

        if tamanho_2 == "08":
            return "1330_08.png"

        if tamanho_2 in [
            "04",
            "06",
        ]:
            return "1330_04_06.png"

        return None


    # =========================================================
    # 1332
    # =========================================================

    if familia == "1332":

        return "1332.png"


    # =========================================================
    # 1335
    # =========================================================

    if familia == "1335":

        if tem_prefixo("ZC"):
            return "1335-ZC.png"

        if tem_prefixo("Z"):
            return "1335_Z.png"

        if tem_sufixo_69():
            return "1335_69.png"

        if corpo_inox():
            return "1335_INOX.png"

        return "1335.png"


    # =========================================================
    # 1342
    # =========================================================

    if familia == "1342":

        if tem_prefixo("ZC"):
            return "1342_ZC.png"

        if tem_prefixo("Z"):
            return "1342_Z.png"

        if tem_prefixo(
            "PA",
            "PE",
        ):
            return "1342_PA_PE.png"

        if tem_sufixo_indicador():
            return "1342_I.png"

        if tem_sufixo("-M"):
            return "1342_M.png"

        if corpo_inox():
            return "1342 INOX.png"

        if tamanho_2 in [
            "20",
            "24",
        ]:
            return "1342_20_24.png"

        if tamanho_2 in [
            "06",
            "08",
            "12",
            "16",
        ]:
            return "1342_06_08_12_16.png"

        return None


    # =========================================================
    # 1343
    # =========================================================

    if familia == "1343":

        if tem_sufixo("F"):
            return "1343_F.png"

        return "1343.png"


    # =========================================================
    # 1344
    # =========================================================

    if familia == "1344":

        return "1344.png"


    # =========================================================
    # 1349
    # =========================================================

    if familia == "1349":

        return "1349.png"


    # =========================================================
    # 1356
    # =========================================================

    if familia == "1356":

        return "1356.png"


    # =========================================================
    # 1360
    # =========================================================

    if familia == "1360":

        if codigo_corpo == "A":
            return "1360_A.png"

        if codigo_corpo == "P":
            return "1360_P.png"

        if (
            codigo_corpo == "T"
            and tamanho_2 == "02"
        ):
            return "1360_T_02.png"

        if (
            codigo_corpo == "T"
            and tamanho_2 == "04"
        ):
            return "1360_T_04.png"

        return None


    # =========================================================
    # 1365
    # =========================================================

    if familia == "1365":

        if tem_prefixo("ZC"):
            return "1365_ZC.png"

        if tem_prefixo("Z"):
            return "1365_Z.png"

        if tem_sufixo_69():
            return "1365_69.png"

        if corpo_inox():
            return "1365_INOX.png"

        return "1365.png"


    # =========================================================
    # 1388
    # =========================================================

    if familia == "1388":

        return "1388.png"


    # =========================================================
    # 1390
    # =========================================================

    if familia == "1390":

        if tem_prefixo("ZC"):
            return "1390_ZC.png"

        if tem_prefixo("Z"):
            return "1390_Z.png"

        if corpo_inox():
            return "1390_INOX.png"

        if tamanho_2 == "04":
            return "1390_04.png"

        if tamanho_2 in [
            "02",
            "03",
        ]:
            return "1390_02_03.png"

        return None


    # =========================================================
    # 1397
    # =========================================================

    if familia == "1397":

        if (
            tem_prefixo("Z")
            and tamanho_2 == "16"
        ):
            return "1397_Z_16.png"

        if (
            tem_prefixo("Z")
            and tamanho_2 == "24"
        ):
            return "1397_Z_24.png"

        return None


    # =========================================================
    # 2026
    # =========================================================

    if familia == "2026":

        return "2026.png"


    # =========================================================
    # 2030
    # =========================================================

    if familia == "2030":

        if (
            tem_prefixo("ZC")
            and tamanho_2 in [
                "12",
                "16",
            ]
        ):
            return "2030_ZC_12_16.png"

        if tem_prefixo("Z"):
            return "2030_Z.png"

        if (
            letra_especial in [
                "D",
                "R",
            ]
            and tamanho_2 == "10"
        ):
            return "2030_DR_10.png"

        if tamanho_2 in [
            "12",
            "16",
        ]:
            return "2030_12_16.png"

        if tamanho_2 in [
            "08",
            "10",
        ]:
            return "2030_08_10.png"

        return None


    # =========================================================
    # 2036
    # =========================================================

    if familia == "2036":

        if codigo_vedacao == "T":
            return "2036_T.png"

        if tamanho_2 == "12":
            return "2036_12.png"

        return "2036.png"


    # =========================================================
    # 2041
    # =========================================================

    if familia == "2041":

        if tem_prefixo("S"):
            return "2041_S.png"

        return "2041.png"


    # =========================================================
    # 2054
    # =========================================================

    if familia == "2054":

        return "2054.png"


    # =========================================================
    # 2088
    # =========================================================

    if familia == "2088":

        return "2088.png"


    # =========================================================
    # 2094
    # =========================================================

    if familia == "2094":

        return "2094.png"


    # =========================================================
    # 3010
    # =========================================================

    if familia == "3010":

        return "3010.png"


    # =========================================================
    # 3123
    # =========================================================

    if familia == "3123":

        return "3123.png"


    # =========================================================
    # 3014
    # =========================================================

    if familia == "3014":

        if tamanho_2 == "12":
            return "3014_12.png"

        if tamanho_2 == "08":
            return "3014_08.png"

        if tamanho_2 in [
            "04",
            "06",
        ]:
            return "3014_04_06.png"

        return None


    # =========================================================
    # 3073
    # =========================================================

    if familia == "3073":

        if tem_prefixo("ZC"):
            return "3073_ZC.png"

        if (
            tem_sufixo("CI")
            or (
                "C" in sufixos
                and "I" in sufixos
            )
        ):
            return "3073_CI.png"

        if tamanho_2 == "16":
            return "3073_16.png"

        if tamanho_2 == "08":
            return "3073_08.png"

        return None


    # =========================================================
    # V171
    # =========================================================

    if familia == "V171":

        return "V171.png"


    # =========================================================
    # TERMOPAR
    # =========================================================

    if familia == "TERMOPAR":

        return "TERMOPAR.png"


    # =========================================================
    # SEM IMAGEM CADASTRADA
    # =========================================================

    return None


# =============================================================
# 10. GERAR VARIÁVEIS DA DESCRIÇÃO
# =============================================================

def gerar_variaveis_descricao(
    resultado,
    tipo_alimentacao
):

    familia = resultado["familia"]
    sufixos = resultado["sufixos"]
    codigo_corpo = resultado["codigo_corpo"]
    codigo_conexao = resultado["codigo_conexao"]
    letra_especial = resultado["letra_especial"]
    codigo_vedacao = resultado["codigo_vedacao"]
    bloco_numeros = resultado["bloco_numeros"]


    # V01 - Tipo de produto
    v01 = definir_v01(
        familia
    )


    # V02 - Tipo de atuação
    v02 = definir_v02(
        familia,
        letra_especial,
        sufixos,
        codigo_conexao
    )


    # V03 - Número de vias
    v03 = definir_v03(
        familia,
        sufixos
    )


    # V04 - Estado / posição
    v04 = definir_v04(
        v03,
        sufixos
    )


    # V05 - Material do corpo
    v05 = definir_v05(
        codigo_corpo
    )


    # V06 - Material da vedação
    v06 = definir_v06(
        codigo_vedacao
    )


    # V07 - Tamanho da conexão
    v07 = definir_v07(
        codigo_conexao
    )


    # V08 - Tipo de rosca
    v08 = definir_v08(
        sufixos
    )


    # V09 - Orifício interno
    v09 = definir_v09(
        familia,
        bloco_numeros,
        letra_especial
    )


    # V10 - Pressão mínima
    v10 = definir_v10(
        familia,
        sufixos,
        codigo_conexao,
        letra_especial,
        codigo_vedacao
    )


    # V11 - Pressão máxima
    v11 = definir_v11(
        familia,
        sufixos,
        bloco_numeros,
        codigo_conexao,
        letra_especial,
        codigo_vedacao
    )


    # V12 - Temperatura
    v12 = definir_v12(
        familia,
        codigo_vedacao,
        sufixos
    )


    # V13 - Dados da bobina
    v13 = definir_v13(
        familia,
        resultado["prefixos"]
    )


    # V14 - Potência da bobina
    v14 = definir_v14(
        familia,
        resultado["prefixos"],
        codigo_conexao,
        tipo_alimentacao
    )


    # V15 - Prefixos e sufixos extras
    v15 = definir_v15(
        familia,
        resultado["prefixos"],
        sufixos,
        v14
    )


    # V16 - Kv
    v16 = definir_v16(
        familia,
        bloco_numeros,
        letra_especial
    )


    # V17 - Imagem
    v17 = definir_v17(
        familia,
        resultado["prefixos"],
        sufixos,
        letra_especial,
        codigo_corpo,
        codigo_vedacao,
        codigo_conexao
    )


    return {
        "V01": v01,
        "V02": v02,
        "V03": v03,
        "V04": v04,
        "V05": v05,
        "V06": v06,
        "V07": v07,
        "V08": v08,
        "V09": v09,
        "V10": v10,
        "V11": v11,
        "V12": v12,
        "V13": v13,
        "V14": v14,
        "V15": v15,
        "V16": v16,
        "V17": v17,
    }
# =============================================================
# IDENTIFICAR TIPO DE ALIMENTAÇÃO
# =============================================================

def identificar_tipo_alimentacao(tensao):

    if not tensao:
        return None

    tensao = str(tensao).strip().upper()

    if "VCC" in tensao:
        return "VCC"

    if "HZ" in tensao:
        return "HZ"

    return None



# =============================================================
# FUNÇÃO FINAL PARA USO NO APP
# =============================================================

def processar_produto(
    codigo,
    tensao
):

    # ---------------------------------------------------------
    # 1. INTERPRETAR CÓDIGO
    # ---------------------------------------------------------

    resultado = interpretar_codigo(
        codigo
    )


    # ---------------------------------------------------------
    # 2. ERRO GRAVE DO PARSER
    # ---------------------------------------------------------

    if resultado.get("erro"):

        return {
            "sucesso": False,
            "erro": resultado["erro"],
            "parser": resultado,
            "variaveis": None,
        }


    # ---------------------------------------------------------
    # 3. CÓDIGO NÃO INTERPRETADO COMPLETAMENTE
    # ---------------------------------------------------------

    if not resultado.get("sucesso"):

        return {
            "sucesso": False,
            "erro": "Código não interpretado completamente.",
            "parser": resultado,
            "variaveis": None,
        }


    # ---------------------------------------------------------
    # 4. IDENTIFICAR HZ / VCC PELA TENSÃO
    # ---------------------------------------------------------

    tipo_alimentacao = identificar_tipo_alimentacao(
        tensao
    )


    # ---------------------------------------------------------
    # 5. GERAR V01 ATÉ V16
    # ---------------------------------------------------------

    variaveis = gerar_variaveis_descricao(
        resultado,
        tipo_alimentacao
    )


    # ---------------------------------------------------------
    # 6. RESULTADO FINAL
    # ---------------------------------------------------------

    return {
        "sucesso": True,
        "erro": None,
        "parser": resultado,
        "variaveis": variaveis,
    }

from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


# ============================================================
# CONFIGURAÇÃO VISUAL
# ============================================================

COR_PRINCIPAL = colors.HexColor("#146B3A")
COR_PRINCIPAL_ESCURA = colors.HexColor("#0D512B")
COR_PRINCIPAL_CLARA = colors.HexColor("#E8F2EC")

CINZA_ESCURO = colors.HexColor("#3C4145")
CINZA_MEDIO = colors.HexColor("#70777C")
CINZA_LINHA = colors.HexColor("#D9DDDF")
CINZA_FUNDO = colors.HexColor("#F3F5F4")
CINZA_ALTERNADO = colors.HexColor("#F8F9F8")

BRANCO = colors.white
PRETO = colors.HexColor("#202326")


# ============================================================
# DADOS FIXOS - PROTÓTIPO VISUAL
# ============================================================

EMPRESA_NOME = "JEFFERSON SOLENOIDBRAS LIMITADA"
EMPRESA_CNPJ = "CNPJ: 56.541.642/0001-52"
EMPRESA_IE = "IE: 635.344.003.112"
EMPRESA_ENDERECO = "São Bernardo do Campo - SP"
EMPRESA_CONTATO = "+55 11 4336.7033 | WhatsApp +55 11 94761.9089"

PROPOSTA_NUMERO = "3288/26"
PROPOSTA_DATA = "24/08/2026"

CLIENTE = "METROVAL"
CLIENTE_CNPJ = "58.762.956/0001-00"
CLIENTE_CODIGO = "106"
RESPONSAVEL = "ARTHUR"


# ============================================================
# FUNÇÕES DE TEXTO
# ============================================================

def texto(
    c,
    x,
    y,
    valor,
    tamanho=8,
    fonte="Helvetica",
    cor=PRETO,
):
    c.setFillColor(cor)
    c.setFont(fonte, tamanho)
    c.drawString(x, y, str(valor))


def texto_direita(
    c,
    x,
    y,
    valor,
    tamanho=8,
    fonte="Helvetica",
    cor=PRETO,
):
    c.setFillColor(cor)
    c.setFont(fonte, tamanho)
    c.drawRightString(x, y, str(valor))


def texto_centro(
    c,
    x,
    y,
    valor,
    tamanho=8,
    fonte="Helvetica",
    cor=PRETO,
):
    c.setFillColor(cor)
    c.setFont(fonte, tamanho)
    c.drawCentredString(x, y, str(valor))


def texto_quebrado(
    c,
    conteudo,
    x,
    y,
    largura,
    tamanho=7,
    entrelinha=9,
    fonte="Helvetica",
    cor=PRETO,
    max_linhas=4,
):
    palavras = str(conteudo).split()

    linhas = []
    linha = ""

    c.setFont(fonte, tamanho)

    for palavra in palavras:

        tentativa = palavra if not linha else f"{linha} {palavra}"

        if c.stringWidth(
            tentativa,
            fonte,
            tamanho,
        ) <= largura:

            linha = tentativa

        else:

            if linha:
                linhas.append(linha)

            linha = palavra

    if linha:
        linhas.append(linha)

    linhas = linhas[:max_linhas]

    c.setFillColor(cor)
    c.setFont(fonte, tamanho)

    y_atual = y

    for linha in linhas:

        c.drawString(
            x,
            y_atual,
            linha,
        )

        y_atual -= entrelinha


# ============================================================
# CABEÇALHO - PÁGINA 1
# ============================================================

def desenhar_cabecalho(
    c,
    largura_pagina,
    altura_pagina,
):
    margem = 14 * mm

    y_topo = altura_pagina - 12 * mm

    # ========================================================
    # LOGO - ESQUERDA
    # ========================================================

    caminho_logo = Path(
        "assets/Logo_Jefferson.png"
    )

    if caminho_logo.exists():

        c.drawImage(
            str(caminho_logo),

            # joga um pouco para a esquerda para compensar
            # o espaço transparente da imagem
            margem - 8 * mm,

            # deixa a logo mais alta
            y_topo - 25 * mm,

            width=82 * mm,
            height=27 * mm,

            preserveAspectRatio=True,
            mask="auto",
        )

    # ========================================================
    # TÍTULO CENTRAL
    # ========================================================

    centro_pagina = largura_pagina / 2

    texto_centro(
        c,
        centro_pagina,
        y_topo - 4 * mm,
        "PROPOSTA COMERCIAL",
        tamanho=13,
        fonte="Helvetica-Bold",
        cor=COR_PRINCIPAL_ESCURA,
    )

    texto_centro(
        c,
        centro_pagina,
        y_topo - 11 * mm,
        "Válvulas e soluções para",
        tamanho=9,
        fonte="Helvetica",
        cor=CINZA_ESCURO,
    )

    texto_centro(
        c,
        centro_pagina,
        y_topo - 15.5 * mm,
        "controle de fluidos",
        tamanho=9,
        fonte="Helvetica",
        cor=CINZA_ESCURO,
    )
    # ========================================================
    # DADOS DA EMPRESA - DIREITA
    # ========================================================

    direita = largura_pagina - margem

    texto_direita(
        c,
        direita,
        y_topo - 3 * mm,
        EMPRESA_NOME,
        tamanho=8.5,
        fonte="Helvetica-Bold",
        cor=COR_PRINCIPAL_ESCURA,
    )

    texto_direita(
        c,
        direita,
        y_topo - 8 * mm,
        EMPRESA_CNPJ,
        tamanho=7.2,
        fonte="Helvetica",
        cor=CINZA_ESCURO,
    )

    texto_direita(
        c,
        direita,
        y_topo - 12.5 * mm,
        EMPRESA_IE,
        tamanho=7.2,
        fonte="Helvetica",
        cor=CINZA_ESCURO,
    )

    texto_direita(
        c,
        direita,
        y_topo - 17 * mm,
        EMPRESA_ENDERECO,
        tamanho=7.2,
        fonte="Helvetica",
        cor=CINZA_ESCURO,
    )

    texto_direita(
        c,
        direita,
        y_topo - 21.5 * mm,
        EMPRESA_CONTATO,
        tamanho=7.2,
        fonte="Helvetica",
        cor=CINZA_ESCURO,
    )

    # ========================================================
    # LINHA VERDE
    # ========================================================

    y_linha = y_topo - 31.5 * mm

    c.setStrokeColor(COR_PRINCIPAL_ESCURA)
    c.setLineWidth(1.2)

    c.line(
        margem,
        y_linha,
        largura_pagina - margem,
        y_linha,
    )

    return y_linha
# ============================================================
# PROPOSTA E DATA
# ============================================================

def desenhar_proposta_data(
    c,
    largura_pagina,
    y_topo,
):
    margem = 14 * mm

    largura_util = largura_pagina - 2 * margem
    meio = margem + largura_util / 2

    altura = 10 * mm

    y = y_topo - altura - 3 * mm

    c.setFillColor(CINZA_FUNDO)

    c.roundRect(
        margem,
        y,
        largura_util,
        altura,
        2 * mm,
        fill=1,
        stroke=0,
    )

    c.setStrokeColor(CINZA_LINHA)
    c.setLineWidth(0.5)

    c.line(
        meio,
        y + 1.5 * mm,
        meio,
        y + altura - 1.5 * mm,
    )

    # PROPOSTA

    texto(
        c,
        margem + 6 * mm,
        y + 6.2 * mm,
        "PROPOSTA Nº",
        tamanho=6.4,
        fonte="Helvetica-Bold",
        cor=CINZA_MEDIO,
    )

    texto(
        c,
        margem + 6 * mm,
        y + 1.7 * mm,
        PROPOSTA_NUMERO,
        tamanho=10.5,
        fonte="Helvetica-Bold",
        cor=COR_PRINCIPAL_ESCURA,
    )

    # DATA

    texto(
        c,
        meio + 6 * mm,
        y + 6.2 * mm,
        "DATA",
        tamanho=6.4,
        fonte="Helvetica-Bold",
        cor=CINZA_MEDIO,
    )

    texto(
        c,
        meio + 6 * mm,
        y + 1.7 * mm,
        PROPOSTA_DATA,
        tamanho=10.5,
        fonte="Helvetica-Bold",
        cor=COR_PRINCIPAL_ESCURA,
    )

    return y


# ============================================================
# CLIENTE
# ============================================================

def desenhar_cliente(
    c,
    largura_pagina,
    y_topo,
):
    margem = 14 * mm

    altura = 12 * mm
    y = y_topo - altura

    larguras = [
        57 * mm,
        57 * mm,
        30 * mm,
        38 * mm,
    ]

    titulos = [
        "CLIENTE",
        "CNPJ",
        "CÓD. CLIENTE",
        "RESPONSÁVEL",
    ]

    valores = [
        CLIENTE,
        CLIENTE_CNPJ,
        CLIENTE_CODIGO,
        RESPONSAVEL,
    ]

    x = margem

    for indice, largura in enumerate(larguras):

        c.setFillColor(
            CINZA_FUNDO
            if indice % 2 == 0
            else colors.HexColor("#FAFBFA")
        )

        c.rect(
            x,
            y,
            largura,
            altura,
            fill=1,
            stroke=0,
        )

        texto(
            c,
            x + 3 * mm,
            y + 7.3 * mm,
            titulos[indice],
            tamanho=6.3,
            fonte="Helvetica-Bold",
            cor=CINZA_MEDIO,
        )

        texto(
            c,
            x + 3 * mm,
            y + 1.8 * mm,
            valores[indice],
            tamanho=8.5,
            fonte="Helvetica-Bold",
        )

        x += largura

    c.setStrokeColor(CINZA_LINHA)
    c.setLineWidth(0.6)

    c.rect(
        margem,
        y,
        182 * mm,
        altura,
        fill=0,
        stroke=1,
    )

    return y


# ============================================================
# TÍTULO DE SEÇÃO
# ============================================================

def titulo_secao(
    c,
    y,
    titulo,
    largura_pagina,
):
    margem = 14 * mm

    # Título principal
    texto(
        c,
        margem,
        y,
        titulo,
        tamanho=10.5,
        fonte="Helvetica-Bold",
        cor=COR_PRINCIPAL_ESCURA,
    )

    # Aviso menor no lado direito
    texto_direita(
        c,
        largura_pagina - margem,
        y + 0.3 * mm,
        "Dados técnicos nas próximas páginas",
        tamanho=6.8,
        fonte="Helvetica-Oblique",
        cor=CINZA_MEDIO,
    )

    return y - 4.5 * mm

# ============================================================
# TABELA RESUMO
# ============================================================

def desenhar_resumo(
    c,
    y_topo,
):
    margem = 14 * mm

    colunas = [
        ("ITEM", 11 * mm),
        ("CÓDIGO DO PRODUTO", 48 * mm),
        ("TENSÃO", 27 * mm),
        ("QTD.", 14 * mm),
        ("VALOR UNIT.", 28 * mm),
        ("VALOR TOTAL", 29 * mm),
        ("PRAZO", 25 * mm),
    ]

    largura_total = sum(
        largura
        for _, largura in colunas
    )

    altura_cabecalho = 7 * mm
    altura_item = 11.5 * mm

    # ======================================================
    # CABEÇALHO
    # ======================================================

    y = y_topo - altura_cabecalho
    x = margem

    for titulo, largura in colunas:

        c.setFillColor(COR_PRINCIPAL_ESCURA)

        c.rect(
            x,
            y,
            largura,
            altura_cabecalho,
            fill=1,
            stroke=0,
        )

        texto_centro(
            c,
            x + largura / 2,
            y + 2.2 * mm,
            titulo,
            tamanho=6.2,
            fonte="Helvetica-Bold",
            cor=BRANCO,
        )

        x += largura

    # ======================================================
    # ITENS DE TESTE
    # ======================================================

    itens = [
        {
            "item": "01",
            "codigo": "Z1335BA04T",
            "tensao": "110 V / 60 Hz",
            "qtd": "4",
            "unitario": "R$ 1.500,00",
            "total": "R$ 6.000,00",
            "prazo": "IMEDIATO",
        },
        {
            "item": "02",
            "codigo": "2088LA12LT",
            "tensao": "110 V / 60 Hz",
            "qtd": "8",
            "unitario": "R$ 8.200,00",
            "total": "R$ 65.600,00",
            "prazo": "30 A 45 DIAS",
        },
        {
            "item": "03",
            "codigo": "2088LA16RT",
            "tensao": "110 V / 60 Hz",
            "qtd": "2",
            "unitario": "R$ 7.790,00",
            "total": "R$ 15.580,00",
            "prazo": "30 A 45 DIAS",
        },
        {
            "item": "04",
            "codigo": "2036BV04",
            "tensao": "220 V / 60 Hz",
            "qtd": "3",
            "unitario": "R$ 980,00",
            "total": "R$ 2.940,00",
            "prazo": "15 DIAS",
        },
        {
            "item": "05",
            "codigo": "1323BA20C",
            "tensao": "24 VCC",
            "qtd": "5",
            "unitario": "R$ 720,00",
            "total": "R$ 3.600,00",
            "prazo": "IMEDIATO",
        },
        {
            "item": "06",
            "codigo": "1342BA08T",
            "tensao": "220 V / 60 Hz",
            "qtd": "1",
            "unitario": "R$ 1.450,00",
            "total": "R$ 1.450,00",
            "prazo": "20 DIAS",
        },
        {
            "item": "07",
            "codigo": "1335BA06",
            "tensao": "110 V / 60 Hz",
            "qtd": "6",
            "unitario": "R$ 850,00",
            "total": "R$ 5.100,00",
            "prazo": "10 DIAS",
        },
        {
            "item": "08",
            "codigo": "2036BE06",
            "tensao": "24 VCC",
            "qtd": "2",
            "unitario": "R$ 1.180,00",
            "total": "R$ 2.360,00",
            "prazo": "30 DIAS",
        },
    ]

    # ======================================================
    # LINHAS DOS ITENS
    # ======================================================

    for indice, item in enumerate(itens):

        y -= altura_item

        c.setFillColor(
            BRANCO
            if indice % 2 == 0
            else CINZA_ALTERNADO
        )

        c.rect(
            margem,
            y,
            largura_total,
            altura_item,
            fill=1,
            stroke=0,
        )

        x = margem

        # ITEM
        largura = colunas[0][1]

        texto_centro(
            c,
            x + largura / 2,
            y + 4.0 * mm,
            item["item"],
            tamanho=7.5,
            fonte="Helvetica-Bold",
        )

        x += largura

        # CÓDIGO DO PRODUTO
        largura = colunas[1][1]

        texto_centro(
            c,
            x + largura / 2,
            y + 3.9 * mm,
            item["codigo"],
            tamanho=8.0,
            fonte="Helvetica-Bold",
        )

        x += largura

        # TENSÃO
        largura = colunas[2][1]

        texto_centro(
            c,
            x + largura / 2,
            y + 4.0 * mm,
            item["tensao"],
            tamanho=7.2,
        )

        x += largura

        # QUANTIDADE
        largura = colunas[3][1]

        texto_centro(
            c,
            x + largura / 2,
            y + 4.0 * mm,
            item["qtd"],
            tamanho=7.5,
            fonte="Helvetica-Bold",
        )

        x += largura

        # VALOR UNITÁRIO
        largura = colunas[4][1]

        texto_centro(
            c,
            x + largura / 2,
            y + 4.0 * mm,
            item["unitario"],
            tamanho=7.0,
        )

        x += largura

        # VALOR TOTAL
        largura = colunas[5][1]

        texto_centro(
            c,
            x + largura / 2,
            y + 4.0 * mm,
            item["total"],
            tamanho=7.0,
            fonte="Helvetica-Bold",
        )

        x += largura

        # PRAZO
        largura = colunas[6][1]

        texto_centro(
            c,
            x + largura / 2,
            y + 4.0 * mm,
            item["prazo"],
            tamanho=6.8,
            fonte="Helvetica-Bold",
        )

        c.setStrokeColor(CINZA_LINHA)
        c.setLineWidth(0.35)

        c.line(
            margem,
            y,
            margem + largura_total,
            y,
        )

    # ======================================================
    # BORDA GERAL
    # ======================================================

    c.setStrokeColor(CINZA_LINHA)
    c.setLineWidth(0.6)

    c.rect(
        margem,
        y,
        largura_total,
        y_topo - y,
        fill=0,
        stroke=1,
    )

    return y


# ============================================================
# OBSERVAÇÕES
# ============================================================

def desenhar_observacoes(
    c,
    y_topo,
):
    margem = 14 * mm

    altura = 24 * mm
    y = y_topo - altura

    c.setFillColor(COR_PRINCIPAL_CLARA)

    c.roundRect(
        margem,
        y,
        182 * mm,
        altura,
        2 * mm,
        fill=1,
        stroke=0,
    )

    texto(
        c,
        margem + 5 * mm,
        y + 17 * mm,
        "OBSERVAÇÕES / DESTAQUES DA PROPOSTA",
        tamanho=8.5,
        fonte="Helvetica-Bold",
        cor=COR_PRINCIPAL_ESCURA,
    )

    observacao = (
        "Os modelos ofertados foram selecionados conforme as condições "
        "informadas pelo cliente. Confirmar tensão, pressão de trabalho "
        "e conexão antes da emissão do pedido. Este espaço será utilizado "
        "para observações técnicas ou comerciais específicas."
    )

    texto_quebrado(
        c,
        observacao,
        margem + 5 * mm,
        y + 10.5 * mm,
        172 * mm,
        tamanho=7.3,
        entrelinha=8,
        max_linhas=3,
    )

    return y


# ============================================================
# TOTAL
# ============================================================

def desenhar_total(
    c,
    largura_pagina,
    y_topo,
):
    margem = 14 * mm

    largura = 64 * mm
    altura = 15 * mm

    x = largura_pagina - margem - largura
    y = y_topo - altura

    c.setFillColor(COR_PRINCIPAL_ESCURA)

    c.roundRect(
        x,
        y,
        largura,
        altura,
        2 * mm,
        fill=1,
        stroke=0,
    )

    texto(
        c,
        x + 5 * mm,
        y + 9.5 * mm,
        "TOTAL DA PROPOSTA",
        tamanho=7.5,
        fonte="Helvetica-Bold",
        cor=BRANCO,
    )

    texto_direita(
        c,
        x + largura - 5 * mm,
        y + 3 * mm,
        "R$ 87.180,00",
        tamanho=12,
        fonte="Helvetica-Bold",
        cor=BRANCO,
    )

    return y


# ============================================================
# CONDIÇÕES COMERCIAIS
# ============================================================

def desenhar_condicoes(
    c,
    y_topo,
):
    margem = 14 * mm

    # Título maior
    texto(
        c,
        margem,
        y_topo,
        "CONDIÇÕES COMERCIAIS",
        tamanho=11,
        fonte="Helvetica-Bold",
        cor=COR_PRINCIPAL_ESCURA,
    )

    # Mantemos a caixa compacta
    altura = 25 * mm
    y = y_topo - altura - 4 * mm

    c.setFillColor(CINZA_FUNDO)

    c.roundRect(
        margem,
        y,
        182 * mm,
        altura,
        1.5 * mm,
        fill=1,
        stroke=0,
    )

    condicoes = [
        (
            "Validade da proposta",
            "15 dias",
        ),
        (
            "Condição de pagamento",
            "28 dias",
        ),
        (
            "Frete",
            "FOB",
        ),
        (
            "Impostos",
            "Inclusos conforme legislação vigente",
        ),
    ]

    # Começa mais perto do topo
    y_linha = y + 18.5 * mm

    for titulo, valor in condicoes:

        # Nome da condição
        texto(
            c,
            margem + 6 * mm,
            y_linha,
            titulo,
            tamanho=8.8,
            fonte="Helvetica-Bold",
            cor=PRETO,
        )

        # Valor
        texto(
            c,
            margem + 65 * mm,
            y_linha,
            valor,
            tamanho=8.8,
            fonte="Helvetica",
            cor=PRETO,
        )

        # Espaçamento entre linhas
        y_linha -= 5.2 * mm

    return y


# ============================================================
# RODAPÉ
# ============================================================

def desenhar_rodape(
    c,
    largura_pagina,
):
    margem = 14 * mm
    y = 11 * mm

    c.setStrokeColor(CINZA_LINHA)
    c.setLineWidth(0.5)

    c.line(
        margem,
        y + 8 * mm,
        largura_pagina - margem,
        y + 8 * mm,
    )

    texto(
        c,
        margem,
        y + 3.5 * mm,
        "RESPONSÁVEL PELA PROPOSTA",
        tamanho=6.4,
        fonte="Helvetica-Bold",
        cor=CINZA_MEDIO,
    )

    texto(
        c,
        margem,
        y - 0.5 * mm,
        "Arthur - Comercial / Técnico",
        tamanho=7.2,
    )

    texto_direita(
        c,
        largura_pagina - margem,
        y + 3.5 * mm,
        EMPRESA_NOME,
        tamanho=6.4,
        fonte="Helvetica-Bold",
        cor=CINZA_MEDIO,
    )

    texto_direita(
        c,
        largura_pagina - margem,
        y - 0.5 * mm,
        EMPRESA_CONTATO,
        tamanho=7.0,
    )



# ============================================================
# PÁGINA 2 - FOLHA DE DADOS TÉCNICOS
# 3 ITENS VERTICAIS LADO A LADO
# ============================================================

def desenhar_cabecalho_tecnico(
    c,
    largura_pagina,
    altura_pagina,
    numero_pagina=2,
):
    margem = 14 * mm
    y_topo = altura_pagina - 12 * mm

    # --------------------------------------------------------
    # LOGO
    # --------------------------------------------------------

    caminho_logo = Path(
        "assets/Logo_Jefferson.png"
    )

    if caminho_logo.exists():

        c.drawImage(
            str(caminho_logo),
            margem,
            y_topo - 18 * mm,
            width=60 * mm,
            height=18 * mm,
            preserveAspectRatio=True,
            mask="auto",
        )

    # --------------------------------------------------------
    # TÍTULO
    # --------------------------------------------------------

    texto_direita(
        c,
        largura_pagina - margem,
        y_topo - 5 * mm,
        "DADOS TÉCNICOS",
        tamanho=13,
        fonte="Helvetica-Bold",
        cor=COR_PRINCIPAL_ESCURA,
    )

    texto_direita(
        c,
        largura_pagina - margem,
        y_topo - 11 * mm,
        f"Proposta {PROPOSTA_NUMERO}",
        tamanho=8,
        cor=CINZA_MEDIO,
    )

    texto_direita(
        c,
        largura_pagina - margem,
        y_topo - 16 * mm,
        f"Página {numero_pagina}",
        tamanho=7,
        cor=CINZA_MEDIO,
    )

    y_linha = y_topo - 23 * mm

    c.setStrokeColor(COR_PRINCIPAL)
    c.setLineWidth(1.2)

    c.line(
        margem,
        y_linha,
        largura_pagina - margem,
        y_linha,
    )

    return y_linha


# ============================================================
# CÉLULA DE UMA COLUNA TÉCNICA
# ============================================================

def desenhar_celula_tecnica(
    c,
    x,
    y,
    largura,
    altura,
    fundo=BRANCO,
):
    c.setFillColor(fundo)

    c.rect(
        x,
        y,
        largura,
        altura,
        fill=1,
        stroke=0,
    )

    c.setStrokeColor(CINZA_LINHA)
    c.setLineWidth(0.45)

    c.rect(
        x,
        y,
        largura,
        altura,
        fill=0,
        stroke=1,
    )


# ============================================================
# PÁGINA TÉCNICA COMPLETA
# ============================================================

def desenhar_pagina_tecnica_teste(
    c,
    largura_pagina,
    altura_pagina,
):
    margem = 14 * mm

    # --------------------------------------------------------
    # CABEÇALHO
    # --------------------------------------------------------

    y_topo = desenhar_cabecalho_tecnico(
        c,
        largura_pagina,
        altura_pagina,
        numero_pagina=2,
    )

    y_topo -= 5 * mm

    # ========================================================
    # DIMENSÕES GERAIS
    # ========================================================

    largura_util = largura_pagina - 2 * margem

    # 3 colunas iguais
    largura_coluna = largura_util / 3

    x1 = margem
    x2 = margem + largura_coluna
    x3 = margem + largura_coluna * 2

    colunas_x = [
        x1,
        x2,
        x3,
    ]

    itens = [
        {
            "item": "ITEM 01",
            "codigo": "Z1335BA04T",
        },
        {
            "item": "ITEM 02",
            "codigo": "2088LA12LT",
        },
        {
            "item": "ITEM 03",
            "codigo": "2036BV04",
        },
    ]

    # ========================================================
    # ALTURAS
    # ========================================================

    altura_item = 9 * mm
    altura_codigo = 11 * mm
    altura_imagem = 48 * mm

    # Altura padrão das linhas técnicas
    altura_linha = 6.8 * mm

    quantidade_linhas = 20

    y = y_topo
    
    # ========================================================
    # LINHA 1 - ITEM
    # ========================================================

    y -= altura_item

    for indice in range(3):

        x = colunas_x[indice]

        c.setFillColor(COR_PRINCIPAL_ESCURA)

        c.rect(
            x,
            y,
            largura_coluna,
            altura_item,
            fill=1,
            stroke=0,
        )

        c.setStrokeColor(BRANCO)
        c.setLineWidth(0.4)

        c.rect(
            x,
            y,
            largura_coluna,
            altura_item,
            fill=0,
            stroke=1,
        )

        texto_centro(
            c,
            x + largura_coluna / 2,
            y + 3.1 * mm,
            itens[indice]["item"],
            tamanho=8.5,
            fonte="Helvetica-Bold",
            cor=BRANCO,
        )

    # ========================================================
    # LINHA 2 - CÓDIGO
    # ========================================================

    y -= altura_codigo

    for indice in range(3):

        x = colunas_x[indice]

        desenhar_celula_tecnica(
            c,
            x,
            y,
            largura_coluna,
            altura_codigo,
            fundo=CINZA_FUNDO,
        )

        texto_centro(
            c,
            x + largura_coluna / 2,
            y + 4.1 * mm,
            itens[indice]["codigo"],
            tamanho=9,
            fonte="Helvetica-Bold",
            cor=PRETO,
        )

    # ========================================================
    # LINHA 3 - IMAGEM
    # ========================================================

    y -= altura_imagem

    for indice in range(3):

        x = colunas_x[indice]

        desenhar_celula_tecnica(
            c,
            x,
            y,
            largura_coluna,
            altura_imagem,
            fundo=BRANCO,
        )

        # Área interna da imagem
        margem_interna = 5 * mm

        c.setStrokeColor(CINZA_LINHA)
        c.setLineWidth(0.5)

        c.roundRect(
            x + margem_interna,
            y + 5 * mm,
            largura_coluna - 2 * margem_interna,
            altura_imagem - 10 * mm,
            2 * mm,
            fill=0,
            stroke=1,
        )

        texto_centro(
            c,
            x + largura_coluna / 2,
            y + altura_imagem / 2,
            "IMAGEM",
            tamanho=8,
            fonte="Helvetica-Bold",
            cor=CINZA_MEDIO,
        )

    # ========================================================
    # LINHAS TÉCNICAS
    # ========================================================

    dados_teste = [
        ("OPERAÇÃO", ["Ação direta", "Servo operada", "Ação combinada"]),
        ("VIAS", ["2 vias", "2 vias", "3 vias"]),
        ("POSIÇÃO", ["NF", "NF", "NA"]),
        ("CORPO", ["Latão", "Bronze", "Inox 316"]),
        ("VEDAÇÃO", ["Buna-N", "Viton", "EPDM"]),
        ("CONEXÃO", ['1/2" BSP', '1" NPT', '3/4" BSP']),
        ("ORIFÍCIO", ["18 mm", "26 mm", "12 mm"]),
        ("PRESSÃO MÍN.", ["0 bar", "0,2 bar", "0 bar"]),
        ("PRESSÃO MÁX.", ["7 bar", "15 bar", "10 bar"]),
        ("TEMPERATURA", ["80 °C", "150 °C", "145 °C"]),
        ("BOBINA", ["Encapsulada", "Carretel", "Encapsulada"]),
        ("CLASSE TÉRMICA", ["H - 180 °C", "H - 180 °C", "H - 180 °C"]),
        ("PROTEÇÃO", ["IP65", "IP65", "IP65"]),
        ("CONEXÃO ELÉTR.", ["Plug-in PG9", "Caixa geral", "Plug-in PG9"]),
        ("POTÊNCIA", ["13 W", "30 W", "19 W"]),
        ("TENSÃO", ["220 V / 60 Hz", "24 VCC", "110 V / 60 Hz"]),
        ("CERTIFICAÇÃO", ["—", "Área classificada", "—"]),
        ("PROTEÇÃO EX", ["—", "Ex db IIC T4 Gb", "—"]),
        ("ENTRADA ELÉTR.", ['PG9', '1/2" NPT', "PG9"]),
        ("OBSERVAÇÃO", ["Padrão", "Especial", "Padrão"]),
    ]

    # --------------------------------------------------------
    # LARGURAS
    # --------------------------------------------------------

    largura_util = largura_pagina - 2 * margem

    # Coluna única com o nome do parâmetro
    largura_campo = 38 * mm

    # O restante é dividido igualmente entre os 3 produtos
    largura_valores = largura_util - largura_campo
    largura_valor = largura_valores / 3

    for numero_linha in range(
        quantidade_linhas
    ):

        campo, valores = dados_teste[numero_linha]

        # ----------------------------------------------------
        # ALTURA DA LINHA
        # ----------------------------------------------------

        if campo == "OBSERVAÇÃO":
            altura_atual = altura_linha * 3
        else:
            altura_atual = altura_linha

        y -= altura_atual

        fundo = (
            CINZA_ALTERNADO
            if numero_linha % 2 == 1
            else BRANCO
        )

        # ====================================================
        # FUNDO DA LINHA INTEIRA
        # ====================================================

        c.setFillColor(fundo)

        c.rect(
            margem,
            y,
            largura_util,
            altura_atual,
            fill=1,
            stroke=0,
        )

        # ====================================================
        # NOME DO PARÂMETRO - APARECE UMA ÚNICA VEZ
        # ====================================================

        texto(
            c,
            margem + 3 * mm,
            y + (altura_atual / 2) - 1.2 * mm,
            campo,
            tamanho=6.4,
            fonte="Helvetica-Bold",
            cor=CINZA_ESCURO,
        )

        # Linha vertical depois do campo
        c.setStrokeColor(CINZA_LINHA)
        c.setLineWidth(0.4)

        x_inicio_valores = margem + largura_campo

        c.line(
            x_inicio_valores,
            y,
            x_inicio_valores,
            y + altura_atual,
        )

        # ====================================================
        # VALORES DOS 3 PRODUTOS
        # ====================================================

        for indice in range(3):

            x = (
                x_inicio_valores
                + indice * largura_valor
            )

            texto_centro(
                c,
                x + largura_valor / 2,
                y + (altura_atual / 2) - 1.2 * mm,
                valores[indice],
                tamanho=6.8,
                fonte="Helvetica",
                cor=PRETO,
            )

            # Separação vertical entre produtos
            if indice < 2:

                c.line(
                    x + largura_valor,
                    y,
                    x + largura_valor,
                    y + altura_atual,
                )

        # ====================================================
        # LINHA HORIZONTAL
        # ====================================================

        c.setStrokeColor(CINZA_LINHA)
        c.setLineWidth(0.35)

        c.line(
            margem,
            y,
            margem + largura_util,
            y,
        )

    # ========================================================
    # BORDA GERAL DAS LINHAS TÉCNICAS
    # ========================================================

    altura_total_dados = (
        (quantidade_linhas - 1) * altura_linha
        + (altura_linha * 3)
    )

    c.setStrokeColor(CINZA_LINHA)
    c.setLineWidth(0.6)

    c.rect(
        margem,
        y,
        largura_util,
        altura_total_dados,
        fill=0,
        stroke=1,
    )
            
    # ========================================================
    # RODAPÉ
    # ========================================================

    c.setStrokeColor(CINZA_LINHA)
    c.setLineWidth(0.5)

    c.line(
        margem,
        17 * mm,
        largura_pagina - margem,
        17 * mm,
    )

    texto(
        c,
        margem,
        11 * mm,
        "JEFFERSON SOLENOIDBRAS LIMITADA",
        tamanho=6.5,
        fonte="Helvetica-Bold",
        cor=CINZA_MEDIO,
    )

    texto_direita(
        c,
        largura_pagina - margem,
        11 * mm,
        "Dados técnicos da proposta",
        tamanho=6.5,
        cor=CINZA_MEDIO,
    )

    texto_centro(
        c,
        largura_pagina / 2,
        6 * mm,
        "2",
        tamanho=7,
        cor=CINZA_MEDIO,
    )

# ============================================================
# GERADOR PRINCIPAL
# ============================================================

def gerar_pdf_teste():

    buffer = BytesIO()

    largura_pagina, altura_pagina = A4

    c = canvas.Canvas(
        buffer,
        pagesize=A4,
    )

    c.setTitle(
        "Proposta Comercial Jefferson - Página 1"
    )

    # CABEÇALHO

    y = desenhar_cabecalho(
        c,
        largura_pagina,
        altura_pagina,
    )

    # PROPOSTA / DATA

    y = desenhar_proposta_data(
        c,
        largura_pagina,
        y,
    )

    # CLIENTE

    y = desenhar_cliente(
        c,
        largura_pagina,
        y - 3 * mm,
    )

    # RESUMO

    y = titulo_secao(
        c,
        y - 7 * mm,
        "RESUMO DA PROPOSTA",
        largura_pagina,
    )

    y = desenhar_resumo(
        c,
        y,
    )

    # OBSERVAÇÕES

    y = desenhar_observacoes(
        c,
        y - 5 * mm,
    )

    # TOTAL

    y = desenhar_total(
        c,
        largura_pagina,
        y - 4 * mm,
    )

    # CONDIÇÕES COMERCIAIS

    desenhar_condicoes(
        c,
        y - 6 * mm,
    )

    # RODAPÉ

    desenhar_rodape(
        c,
        largura_pagina,
    )

# ============================================================
# FINALIZA PÁGINA 1
# ============================================================

    c.showPage()


# ============================================================
# PÁGINA 2 - DADOS TÉCNICOS
# ============================================================

    desenhar_pagina_tecnica_teste(
        c,
        largura_pagina,
        altura_pagina,
    )

    c.showPage()


# ============================================================
# FINALIZA PDF
# ============================================================

    c.save()

    buffer.seek(0)

    return buffer.getvalue()

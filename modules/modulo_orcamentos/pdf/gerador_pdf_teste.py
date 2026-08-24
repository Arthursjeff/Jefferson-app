from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


# ============================================================
# CONFIGURAÇÃO VISUAL
# ============================================================

# COR TEMPORÁRIA.
# Quando você me passar o HEX oficial, vamos alterar só esta linha.
COR_PRINCIPAL = colors.HexColor("#146B3A")

COR_PRINCIPAL_ESCURA = colors.HexColor("#0E4D2A")
COR_PRINCIPAL_CLARA = colors.HexColor("#EAF3ED")

CINZA_ESCURO = colors.HexColor("#3F4448")
CINZA_MEDIO = colors.HexColor("#737A80")
CINZA_LINHA = colors.HexColor("#D7DBDE")
CINZA_FUNDO = colors.HexColor("#F4F5F5")

BRANCO = colors.white
PRETO = colors.HexColor("#202326")


# ============================================================
# DADOS FIXOS DO PROTÓTIPO
# Depois trocaremos pelos dados reais.
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
# FUNÇÕES AUXILIARES
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


def desenhar_texto_quebrado(
    c,
    texto_original,
    x,
    y,
    largura,
    tamanho=8,
    entrelinha=11,
    fonte="Helvetica",
    cor=PRETO,
    max_linhas=4,
):
    """
    Quebra texto simples para caber em uma largura fixa.
    """

    palavras = str(texto_original).split()

    linhas = []
    linha_atual = ""

    c.setFont(fonte, tamanho)

    for palavra in palavras:

        teste = (
            palavra
            if not linha_atual
            else linha_atual + " " + palavra
        )

        if c.stringWidth(
            teste,
            fonte,
            tamanho
        ) <= largura:

            linha_atual = teste

        else:

            if linha_atual:
                linhas.append(linha_atual)

            linha_atual = palavra

    if linha_atual:
        linhas.append(linha_atual)

    linhas = linhas[:max_linhas]

    c.setFillColor(cor)
    c.setFont(fonte, tamanho)

    y_atual = y

    for linha in linhas:

        c.drawString(
            x,
            y_atual,
            linha
        )

        y_atual -= entrelinha


# ============================================================
# IMAGEM TESTE DA VÁLVULA
# ============================================================

def desenhar_valvula_teste(
    c,
    x,
    y,
    largura,
    altura,
):
    """
    Desenho vetorial simples usado apenas como placeholder
    enquanto ainda não temos as imagens reais dos produtos.
    """

    centro_x = x + largura / 2
    centro_y = y + altura / 2

    c.saveState()

    c.setStrokeColor(CINZA_ESCURO)
    c.setFillColor(colors.white)
    c.setLineWidth(1)

    # corpo circular
    raio = min(
        largura,
        altura
    ) * 0.18

    c.circle(
        centro_x,
        centro_y - 2 * mm,
        raio,
        fill=0,
        stroke=1,
    )

    # conexão esquerda
    c.rect(
        x + 1 * mm,
        centro_y - 5 * mm,
        largura * 0.28,
        6 * mm,
        fill=0,
        stroke=1,
    )

    # conexão direita
    c.rect(
        centro_x + raio,
        centro_y - 5 * mm,
        largura * 0.27,
        6 * mm,
        fill=0,
        stroke=1,
    )

    # pescoço
    c.rect(
        centro_x - 5 * mm,
        centro_y + raio - 2 * mm,
        10 * mm,
        7 * mm,
        fill=0,
        stroke=1,
    )

    # bobina
    c.setFillColor(CINZA_ESCURO)

    c.rect(
        centro_x - 6 * mm,
        centro_y + raio + 5 * mm,
        12 * mm,
        8 * mm,
        fill=1,
        stroke=1,
    )

    c.restoreState()


# ============================================================
# CABEÇALHO
# ============================================================

def desenhar_cabecalho(c, largura_pagina, altura_pagina):

    margem = 14 * mm

    topo = altura_pagina - 15 * mm

    # --------------------------------------------------------
    # LOGO
    # --------------------------------------------------------

    caminho_logo = Path(
        "assets/icone_jefferson.png"
    )

    if caminho_logo.exists():

        c.drawImage(
            str(caminho_logo),
            margem,
            topo - 25 * mm,
            width=25 * mm,
            height=25 * mm,
            preserveAspectRatio=True,
            mask="auto",
        )

        texto(
            c,
            margem + 31 * mm,
            topo - 9 * mm,
            "JEFFERSON",
            tamanho=18,
            fonte="Helvetica-Bold",
            cor=COR_PRINCIPAL_ESCURA,
        )

        texto(
            c,
            margem + 31 * mm,
            topo - 15 * mm,
            "SOLENOID VALVES",
            tamanho=7,
            fonte="Helvetica",
            cor=CINZA_MEDIO,
        )

    else:

        texto(
            c,
            margem,
            topo - 10 * mm,
            "JEFFERSON",
            tamanho=22,
            fonte="Helvetica-Bold",
            cor=COR_PRINCIPAL,
        )

    # --------------------------------------------------------
    # DADOS DA EMPRESA - LADO DIREITO
    # --------------------------------------------------------

    x_direita = largura_pagina - margem

    texto_direita(
        c,
        x_direita,
        topo - 4 * mm,
        EMPRESA_NOME,
        tamanho=8.5,
        fonte="Helvetica-Bold",
        cor=PRETO,
    )

    texto_direita(
        c,
        x_direita,
        topo - 9 * mm,
        EMPRESA_CNPJ,
        tamanho=7.2,
        cor=CINZA_ESCURO,
    )

    texto_direita(
        c,
        x_direita,
        topo - 13 * mm,
        EMPRESA_IE,
        tamanho=7.2,
        cor=CINZA_ESCURO,
    )

    texto_direita(
        c,
        x_direita,
        topo - 17 * mm,
        EMPRESA_ENDERECO,
        tamanho=7.2,
        cor=CINZA_ESCURO,
    )

    texto_direita(
        c,
        x_direita,
        topo - 21 * mm,
        EMPRESA_CONTATO,
        tamanho=7.2,
        cor=CINZA_ESCURO,
    )

    # linha divisória
    y_linha = topo - 31 * mm

    c.setStrokeColor(COR_PRINCIPAL)
    c.setLineWidth(1.4)

    c.line(
        margem,
        y_linha,
        largura_pagina - margem,
        y_linha,
    )

    return y_linha


# ============================================================
# PROPOSTA + DATA
# ============================================================

def desenhar_proposta_data(
    c,
    largura_pagina,
    y_topo,
):

    margem = 14 * mm
    largura_util = largura_pagina - 2 * margem

    altura = 15 * mm
    meio = margem + largura_util / 2

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

    c.line(
        meio,
        y + 2.5 * mm,
        meio,
        y + altura - 2.5 * mm,
    )

    # PROPOSTA
    texto(
        c,
        margem + 6 * mm,
        y + 9.5 * mm,
        "PROPOSTA Nº",
        tamanho=6.3,
        fonte="Helvetica-Bold",
        cor=CINZA_MEDIO,
    )

    texto(
        c,
        margem + 6 * mm,
        y + 3.2 * mm,
        PROPOSTA_NUMERO,
        tamanho=12,
        fonte="Helvetica-Bold",
        cor=COR_PRINCIPAL_ESCURA,
    )

    # DATA
    texto(
        c,
        meio + 6 * mm,
        y + 9.5 * mm,
        "DATA",
        tamanho=6.3,
        fonte="Helvetica-Bold",
        cor=CINZA_MEDIO,
    )

    texto(
        c,
        meio + 6 * mm,
        y + 3.2 * mm,
        PROPOSTA_DATA,
        tamanho=12,
        fonte="Helvetica-Bold",
        cor=COR_PRINCIPAL_ESCURA,
    )

    return y


# ============================================================
# DADOS DO CLIENTE - FORMATO V2
# ============================================================

def desenhar_cliente(
    c,
    largura_pagina,
    y_topo,
):

    margem = 14 * mm
    largura_util = largura_pagina - 2 * margem

    altura = 17 * mm
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

    for indice in range(4):

        largura = larguras[indice]

        c.setFillColor(
            CINZA_FUNDO
            if indice % 2 == 0
            else colors.HexColor("#FAFAFA")
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
            y + 11 * mm,
            titulos[indice],
            tamanho=6,
            fonte="Helvetica-Bold",
            cor=CINZA_MEDIO,
        )

        texto(
            c,
            x + 3 * mm,
            y + 4 * mm,
            valores[indice],
            tamanho=8.3,
            fonte="Helvetica-Bold",
            cor=PRETO,
        )

        x += largura

    c.setStrokeColor(CINZA_LINHA)

    c.rect(
        margem,
        y,
        largura_util,
        altura,
        fill=0,
        stroke=1,
    )

    return y

# ============================================================
# RESUMO DA PROPOSTA
# ============================================================

def desenhar_titulo_secao(
    c,
    largura_pagina,
    y,
    titulo,
):

    margem = 14 * mm

    texto(
        c,
        margem,
        y,
        titulo,
        tamanho=10,
        fonte="Helvetica-Bold",
        cor=COR_PRINCIPAL_ESCURA,
    )

    return y - 5 * mm


def desenhar_resumo(
    c,
    largura_pagina,
    y_topo,
):

    margem = 14 * mm

    colunas = [
        ("ITEM", 12 * mm),
        ("IMAGEM", 27 * mm),
        ("MODELO / CONFIGURAÇÃO", 57 * mm),
        ("QTD.", 14 * mm),
        ("UNITÁRIO", 25 * mm),
        ("TOTAL", 27 * mm),
        ("PRAZO", 20 * mm),
    ]

    altura_cabecalho = 8 * mm
    altura_item = 23 * mm

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
            y + 2.7 * mm,
            titulo,
            tamanho=5.8,
            fonte="Helvetica-Bold",
            cor=BRANCO,
        )

        x += largura

    # ======================================================
    # DADOS TESTE
    # ======================================================

    itens = [
        {
            "item": "01",
            "codigo": ["Z1335BA04T"],
            "tensao": "110 V / 60 Hz",
            "qtd": "4",
            "unitario": "R$ 1.500,00",
            "total": "R$ 6.000,00",
            "prazo": "IMEDIATO",
        },
        {
            "item": "02",
            "codigo": ["V338-ZRC", "2088LA12LT"],
            "tensao": "110 V / 60 Hz",
            "qtd": "8",
            "unitario": "R$ 8.200,00",
            "total": "R$ 65.600,00",
            "prazo": "30 A 45 DIAS",
        },
        {
            "item": "03",
            "codigo": ["V338-ZRC", "2088LA16RT"],
            "tensao": "110 V / 60 Hz",
            "qtd": "2",
            "unitario": "R$ 7.790,00",
            "total": "R$ 15.580,00",
            "prazo": "30 A 45 DIAS",
        },
    ]

    largura_total = sum(
        largura
        for _, largura in colunas
    )

    for indice, item in enumerate(itens):

        y -= altura_item

        if indice % 2 == 0:
            fundo = colors.white
        else:
            fundo = colors.HexColor("#F7F8F7")

        c.setFillColor(fundo)

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
            y + 10 * mm,
            item["item"],
            tamanho=7.7,
        )

        x += largura

        # IMAGEM
        largura = colunas[1][1]

        desenhar_valvula_teste(
            c,
            x + 4 * mm,
            y + 3 * mm,
            largura - 8 * mm,
            altura_item - 6 * mm,
        )

        x += largura

        # MODELO / CONFIGURAÇÃO
        largura = colunas[2][1]

        y_codigo = y + 14.5 * mm

        for linha_codigo in item["codigo"]:

            texto(
                c,
                x + 3 * mm,
                y_codigo,
                linha_codigo,
                tamanho=7.2,
                fonte="Helvetica-Bold",
            )

            y_codigo -= 4 * mm

        texto(
            c,
            x + 3 * mm,
            y + 3.5 * mm,
            item["tensao"],
            tamanho=6.5,
            cor=CINZA_MEDIO,
        )

        x += largura

        # QTD
        largura = colunas[3][1]

        texto_centro(
            c,
            x + largura / 2,
            y + 10 * mm,
            item["qtd"],
            tamanho=8,
        )

        x += largura

        # UNITÁRIO
        largura = colunas[4][1]

        texto_centro(
            c,
            x + largura / 2,
            y + 10 * mm,
            item["unitario"],
            tamanho=6.6,
        )

        x += largura

        # TOTAL
        largura = colunas[5][1]

        texto_centro(
            c,
            x + largura / 2,
            y + 10 * mm,
            item["total"],
            tamanho=6.6,
            fonte="Helvetica-Bold",
        )

        x += largura

        # PRAZO
        largura = colunas[6][1]

        desenhar_texto_quebrado(
            c,
            item["prazo"],
            x + 2 * mm,
            y + 12 * mm,
            largura - 4 * mm,
            tamanho=6.3,
            entrelinha=7,
            fonte="Helvetica-Bold",
            max_linhas=2,
        )

        # LINHA DIVISÓRIA
        c.setStrokeColor(CINZA_LINHA)

        c.line(
            margem,
            y,
            margem + largura_total,
            y,
        )

    # BORDA COMPLETA
    c.setStrokeColor(CINZA_LINHA)

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
# OBSERVAÇÕES / DESTAQUES
# ============================================================

def desenhar_observacoes(
    c,
    largura_pagina,
    y_topo,
):

    margem = 14 * mm
    altura = 26 * mm

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
        y + 18.5 * mm,
        "OBSERVAÇÕES / DESTAQUES DA PROPOSTA",
        tamanho=7.7,
        fonte="Helvetica-Bold",
        cor=COR_PRINCIPAL_ESCURA,
    )

    conteudo = (
        "Os modelos ofertados foram selecionados conforme as condições "
        "informadas pelo cliente. Confirmar tensão, pressão de trabalho "
        "e conexão antes da emissão do pedido. Este campo será livre para "
        "observações técnicas e comerciais específicas."
    )

    desenhar_texto_quebrado(
        c,
        conteudo,
        margem + 5 * mm,
        y + 12.5 * mm,
        172 * mm,
        tamanho=6.8,
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

    largura = 67 * mm
    altura = 17 * mm

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
        y + 10.5 * mm,
        "TOTAL DA PROPOSTA",
        tamanho=7.5,
        fonte="Helvetica-Bold",
        cor=BRANCO,
    )

    texto_direita(
        c,
        x + largura - 5 * mm,
        y + 3.5 * mm,
        "R$ 87.180,00",
        tamanho=14,
        fonte="Helvetica-Bold",
        cor=BRANCO,
    )

    return y


# ============================================================
# CONDIÇÕES COMERCIAIS
# ============================================================

def desenhar_condicoes(
    c,
    largura_pagina,
    y_topo,
):

    margem = 14 * mm

    texto(
        c,
        margem,
        y_topo,
        "CONDIÇÕES COMERCIAIS",
        tamanho=8.8,
        fonte="Helvetica-Bold",
        cor=COR_PRINCIPAL_ESCURA,
    )

    altura = 25 * mm
    y = y_topo - altura - 3 * mm

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
        ("Validade da proposta", "15 dias"),
        ("Condição de pagamento", "28 dias"),
        ("Frete", "FOB"),
        ("Impostos", "Inclusos conforme legislação vigente"),
    ]

    y_linha = y + 18.5 * mm

    for titulo, valor in condicoes:

        texto(
            c,
            margem + 5 * mm,
            y_linha,
            titulo,
            tamanho=6.7,
            fonte="Helvetica-Bold",
        )

        texto(
            c,
            margem + 61 * mm,
            y_linha,
            valor,
            tamanho=6.7,
        )

        y_linha -= 5 * mm

    return y

# ============================================================
# RODAPÉ
# ============================================================

def desenhar_rodape(
    c,
    largura_pagina,
):

    margem = 14 * mm

    y = 13 * mm

    c.setStrokeColor(CINZA_LINHA)

    c.line(
        margem,
        y + 7 * mm,
        largura_pagina - margem,
        y + 7 * mm,
    )

    texto(
        c,
        margem,
        y + 2 * mm,
        "RESPONSÁVEL PELA PROPOSTA",
        tamanho=6.5,
        fonte="Helvetica-Bold",
        cor=CINZA_MEDIO,
    )

    texto(
        c,
        margem,
        y - 2 * mm,
        "Arthur - Comercial / Técnico",
        tamanho=7.2,
    )

    texto_direita(
        c,
        largura_pagina - margem,
        y + 2 * mm,
        EMPRESA_NOME,
        tamanho=6.5,
        fonte="Helvetica-Bold",
        cor=CINZA_MEDIO,
    )

    texto_direita(
        c,
        largura_pagina - margem,
        y - 2 * mm,
        EMPRESA_CONTATO,
        tamanho=7.2,
    )


# ============================================================
# GERADOR PRINCIPAL - SOMENTE PÁGINA 1
# ============================================================

def gerar_pdf_teste():

    buffer = BytesIO()

    largura_pagina, altura_pagina = A4

    c = canvas.Canvas(
        buffer,
        pagesize=A4,
    )

    c.setTitle(
        "Proposta Comercial Jefferson - Protótipo Página 1"
    )

    # ========================================================
    # CABEÇALHO
    # ========================================================

    y = desenhar_cabecalho(
        c,
        largura_pagina,
        altura_pagina,
    )

    # ========================================================
    # PROPOSTA + DATA
    # ========================================================

    y = desenhar_proposta_data(
        c,
        largura_pagina,
        y,
    )

    # ========================================================
    # CLIENTE
    # ========================================================

    y = desenhar_cliente(
        c,
        largura_pagina,
        y - 3 * mm,
    )

    # ========================================================
    # RESUMO
    # ========================================================

    y = desenhar_titulo_secao(
        c,
        largura_pagina,
        y - 7 * mm,
        "RESUMO DA PROPOSTA",
    )

    y = desenhar_resumo(
        c,
        largura_pagina,
        y,
    )

    # ========================================================
    # OBSERVAÇÕES
    # ========================================================

    y = desenhar_observacoes(
        c,
        largura_pagina,
        y - 5 * mm,
    )

    # ========================================================
    # TOTAL
    # ========================================================

    y = desenhar_total(
        c,
        largura_pagina,
        y - 4 * mm,
    )

    # ========================================================
    # CONDIÇÕES COMERCIAIS
    # ========================================================

    desenhar_condicoes(
        c,
        largura_pagina,
        y - 6 * mm,
    )

    # ========================================================
    # RODAPÉ
    # ========================================================

    desenhar_rodape(
        c,
        largura_pagina,
    )

    c.showPage()
    c.save()

    buffer.seek(0)

    return buffer.getvalue()

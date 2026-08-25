from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


# ============================================================
# CONFIGURAÇÃO VISUAL
# ============================================================

# COR TEMPORÁRIA
# Depois vamos substituir pelo verde oficial da Jefferson.
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
# IMAGEM TESTE DE PRODUTO
# ============================================================

def desenhar_valvula_teste(
    c,
    x,
    y,
    largura,
    altura,
):
    """
    Placeholder visual temporário.
    Depois será substituído pelas imagens reais.
    """

    centro_x = x + largura / 2
    centro_y = y + altura / 2

    c.saveState()

    c.setStrokeColor(CINZA_ESCURO)
    c.setLineWidth(0.9)

    raio = min(
        largura,
        altura
    ) * 0.20

    # Corpo
    c.setFillColor(BRANCO)

    c.circle(
        centro_x,
        centro_y - 1 * mm,
        raio,
        fill=1,
        stroke=1,
    )

    # Entrada esquerda
    c.rect(
        x + 1 * mm,
        centro_y - 4 * mm,
        largura * 0.28,
        6 * mm,
        fill=0,
        stroke=1,
    )

    # Saída direita
    c.rect(
        centro_x + raio,
        centro_y - 4 * mm,
        largura * 0.26,
        6 * mm,
        fill=0,
        stroke=1,
    )

    # Pescoço
    c.rect(
        centro_x - 4.5 * mm,
        centro_y + raio - 1 * mm,
        9 * mm,
        6 * mm,
        fill=0,
        stroke=1,
    )

    # Bobina
    c.setFillColor(CINZA_ESCURO)

    c.rect(
        centro_x - 6 * mm,
        centro_y + raio + 5 * mm,
        12 * mm,
        7 * mm,
        fill=1,
        stroke=1,
    )

    c.restoreState()


# ============================================================
# CABEÇALHO
# ============================================================

def desenhar_cabecalho(
    c,
    largura_pagina,
    altura_pagina,
):
    margem = 14 * mm

    y_topo = altura_pagina - 15 * mm

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
            y_topo - 22 * mm,
            width=75 * mm,
            height=24 * mm,
            preserveAspectRatio=True,
            mask="auto",
        )


    # --------------------------------------------------------
    # DADOS DA EMPRESA
    # --------------------------------------------------------

    direita = largura_pagina - margem

    texto_direita(
        c,
        direita,
        y_topo - 3 * mm,
        EMPRESA_NOME,
        tamanho=8,
        fonte="Helvetica-Bold",
    )

    texto_direita(
        c,
        direita,
        y_topo - 8 * mm,
        EMPRESA_CNPJ,
        tamanho=6.8,
        cor=CINZA_ESCURO,
    )

    texto_direita(
        c,
        direita,
        y_topo - 12 * mm,
        EMPRESA_IE,
        tamanho=6.8,
        cor=CINZA_ESCURO,
    )

    texto_direita(
        c,
        direita,
        y_topo - 16 * mm,
        EMPRESA_ENDERECO,
        tamanho=6.8,
        cor=CINZA_ESCURO,
    )

    texto_direita(
        c,
        direita,
        y_topo - 20 * mm,
        EMPRESA_CONTATO,
        tamanho=6.8,
        cor=CINZA_ESCURO,
    )

    y_linha = y_topo - 28 * mm

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

    # Caixa mais compacta
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

    # --------------------------------------------------------
    # PROPOSTA
    # --------------------------------------------------------

    texto(
        c,
        margem + 6 * mm,
        y + 6.2 * mm,
        "PROPOSTA Nº",
        tamanho=5.8,
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

    # --------------------------------------------------------
    # DATA
    # --------------------------------------------------------

    texto(
        c,
        meio + 6 * mm,
        y + 6.2 * mm,
        "DATA",
        tamanho=5.8,
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
# CLIENTE - FORMATO HORIZONTAL V2
# ============================================================

def desenhar_cliente(
    c,
    largura_pagina,
    y_topo,
):
    margem = 14 * mm

    # Caixa reduzida de 16 mm para 12 mm
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

        # Título da coluna
        texto(
            c,
            x + 3 * mm,
            y + 7.3 * mm,
            titulos[indice],
            tamanho=5.7,
            fonte="Helvetica-Bold",
            cor=CINZA_MEDIO,
        )

        # Valor
        texto(
            c,
            x + 3 * mm,
            y + 1.8 * mm,
            valores[indice],
            tamanho=8,
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
):
    margem = 14 * mm

    texto(
        c,
        margem,
        y,
        titulo,
        tamanho=9.5,
        fonte="Helvetica-Bold",
        cor=COR_PRINCIPAL_ESCURA,
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

    # Mais compacto para permitir vários itens
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
            y + 2.4 * mm,
            titulo,
            tamanho=5.2,
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
            y + 4.3 * mm,
            item["item"],
            tamanho=6.5,
        )

        x += largura

        # CÓDIGO DO PRODUTO
        largura = colunas[1][1]

        texto(
            c,
            x + 3 * mm,
            y + 4.2 * mm,
            item["codigo"],
            tamanho=6.7,
            fonte="Helvetica-Bold",
        )

        x += largura

        # TENSÃO
        largura = colunas[2][1]

        texto_centro(
            c,
            x + largura / 2,
            y + 4.2 * mm,
            item["tensao"],
            tamanho=6.2,
        )

        x += largura

        # QUANTIDADE
        largura = colunas[3][1]

        texto_centro(
            c,
            x + largura / 2,
            y + 4.2 * mm,
            item["qtd"],
            tamanho=6.5,
        )

        x += largura

        # VALOR UNITÁRIO
        largura = colunas[4][1]

        texto_centro(
            c,
            x + largura / 2,
            y + 4.2 * mm,
            item["unitario"],
            tamanho=6.1,
        )

        x += largura

        # VALOR TOTAL
        largura = colunas[5][1]

        texto_centro(
            c,
            x + largura / 2,
            y + 4.2 * mm,
            item["total"],
            tamanho=6.1,
            fonte="Helvetica-Bold",
        )

        x += largura

        # PRAZO
        largura = colunas[6][1]

        texto_centro(
            c,
            x + largura / 2,
            y + 4.2 * mm,
            item["prazo"],
            tamanho=5.9,
            fonte="Helvetica-Bold",
        )

        # Linha divisória
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
        tamanho=7.4,
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
        y + 11 * mm,
        172 * mm,
        tamanho=6.5,
        entrelinha=7.5,
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
        tamanho=6.5,
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

    texto(
        c,
        margem,
        y_topo,
        "CONDIÇÕES COMERCIAIS",
        tamanho=8.5,
        fonte="Helvetica-Bold",
        cor=COR_PRINCIPAL_ESCURA,
    )

    altura = 24 * mm
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

    y_linha = y + 17.5 * mm

    for titulo, valor in condicoes:

        texto(
            c,
            margem + 5 * mm,
            y_linha,
            titulo,
            tamanho=6.4,
            fonte="Helvetica-Bold",
        )

        texto(
            c,
            margem + 62 * mm,
            y_linha,
            valor,
            tamanho=6.4,
        )

        y_linha -= 4.8 * mm

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
        tamanho=5.7,
        fonte="Helvetica-Bold",
        cor=CINZA_MEDIO,
    )

    texto(
        c,
        margem,
        y - 0.5 * mm,
        "Arthur - Comercial / Técnico",
        tamanho=6.5,
    )

    texto_direita(
        c,
        largura_pagina - margem,
        y + 3.5 * mm,
        EMPRESA_NOME,
        tamanho=5.7,
        fonte="Helvetica-Bold",
        cor=CINZA_MEDIO,
    )

    texto_direita(
        c,
        largura_pagina - margem,
        y - 0.5 * mm,
        EMPRESA_CONTATO,
        tamanho=6.3,
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

    # ========================================================
    # CABEÇALHO
    # ========================================================

    y = desenhar_cabecalho(
        c,
        largura_pagina,
        altura_pagina,
    )

    # ========================================================
    # PROPOSTA / DATA
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

    y = titulo_secao(
        c,
        y - 7 * mm,
        "RESUMO DA PROPOSTA",
    )

    y = desenhar_resumo(
        c,
        y,
    )

    # ========================================================
    # OBSERVAÇÕES
    # ========================================================

    y = desenhar_observacoes(
        c,
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

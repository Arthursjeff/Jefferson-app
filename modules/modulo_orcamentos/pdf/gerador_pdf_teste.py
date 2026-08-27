from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

from reportlab.lib.utils import ImageReader

from modules.modulo_orcamentos.imagens_repository import (
    obter_url_imagem,
)

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
            margem - 12 * mm,

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
        tamanho=8,
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

    y_linha = y_topo - 27 * mm

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
    numero_orcamento,
    data_orcamento,
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
        numero_orcamento,
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
        data_orcamento,
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
    cliente,
    responsavel,
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
        (
            cliente.get("razao_social")
            or cliente.get("nome_fantasia")
            or "-"
        ),
        cliente.get("cnpj_cpf") or "-",
        cliente.get("codigo_cliente") or "-",
        responsavel or "-",
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
    itens,
    numero_item_inicial=1,
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
            f"{numero_item_inicial + indice:02d}",
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
            item["quantidade"],
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
            f"R$ {item['valor_unitario']:,.2f}",
            tamanho=7.0,
        )

        x += largura

        # VALOR TOTAL
        largura = colunas[5][1]

        texto_centro(
            c,
            x + largura / 2,
            y + 4.0 * mm,
            f"R$ {(item['quantidade'] * item['valor_unitario']):,.2f}",
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
    observacao_geral,
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
        observacao_geral
        or "Sem observações adicionais."
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
# VENDEDOR
# ============================================================

def desenhar_vendedor(
    c,
    y_topo,
    responsavel,
):
    margem = 14 * mm

    largura = 72 * mm
    altura = 15 * mm

    x = margem
    y = y_topo - altura

    # Fundo
    c.setFillColor(CINZA_FUNDO)

    c.roundRect(
        x,
        y,
        largura,
        altura,
        2 * mm,
        fill=1,
        stroke=0,
    )

    # Título
    texto(
        c,
        x + 5 * mm,
        y + 9.5 * mm,
        "VENDEDOR RESPONSÁVEL",
        tamanho=7.0,
        fonte="Helvetica-Bold",
        cor=CINZA_MEDIO,
    )

    # Nome do vendedor
    texto(
        c,
        x + 5 * mm,
        y + 3 * mm,
        responsavel,
        tamanho=10,
        fonte="Helvetica-Bold",
        cor=COR_PRINCIPAL_ESCURA,
    )

    return y
    
# ============================================================
# TOTAL
# ============================================================

def desenhar_total(
    c,
    largura_pagina,
    y_topo,
    itens,
    mostrar_total=True,
    pagina_total=None,
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

    total_orcamento = sum(
        item["quantidade"]
        * item["valor_unitario"]
        for item in itens
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
    
    if mostrar_total:

        valor_exibido = (
            f"R$ {total_orcamento:,.2f}"
        )

    else:

        valor_exibido = (
            f"Consultar página {pagina_total}"
        )
        
    texto_direita(
        c,
        x + largura - 5 * mm,
        y + 3 * mm,
        valor_exibido,
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
    numero_orcamento,
    numero_pagina=2,
):
    margem = 14 * mm
    y_topo = altura_pagina - 12 * mm

    # ========================================================
    # LOGO - ESQUERDA
    # ========================================================

    caminho_logo = Path(
        "assets/Logo_Jefferson.png"
    )

    centro_pagina = (
        largura_pagina / 2
    )

    if caminho_logo.exists():

        c.drawImage(
            str(caminho_logo),
            margem - 12 * mm,
            y_topo - 25 * mm,
            width=82 * mm,
            height=27 * mm,
            preserveAspectRatio=True,
            mask="auto",
        )

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
        f"Proposta {numero_orcamento}",
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
# AUXILIARES - PÁGINA TÉCNICA
# ============================================================

def valor_tecnico(valor):

    if valor is None:
        return "—"

    valor = str(valor).strip()

    if not valor:
        return "—"

    return valor


def texto_extras_v15(v15):

    if not isinstance(
        v15,
        dict,
    ):
        return "—"

    extras = (
        v15.get("extras")
        or []
    )

    if not extras:
        return "—"

    textos = []

    for extra in extras:

        texto_extra = (
            extra.get("texto")
            or ""
        ).strip()

        if texto_extra:
            textos.append(
                texto_extra
            )

    if not textos:
        return "—"

    return " | ".join(
        textos
    )


def carregar_imagem_produto(
    nome_imagem,
):

    if not nome_imagem:
        return None

    try:

        url = obter_url_imagem(
            nome_imagem
        )

        resposta = urlopen(
            url,
            timeout=10,
        )

        dados = resposta.read()

        return ImageReader(
            BytesIO(dados)
        )

    except Exception:

        return None

def desenhar_pagina_tecnica_teste(
    c,
    largura_pagina,
    altura_pagina,
    numero_orcamento,
    itens,
    numero_pagina,
    numero_item_inicial,
):

    margem = 14 * mm


    # ========================================================
    # CABEÇALHO
    # ========================================================

    y_topo = desenhar_cabecalho_tecnico(
        c,
        largura_pagina,
        altura_pagina,
        numero_orcamento,
        numero_pagina=numero_pagina,
    )

    y_topo -= 5 * mm


    # ========================================================
    # SOMENTE OS 3 PRIMEIROS ITENS
    # ========================================================
    #
    # A paginação para mais de 3 itens será feita depois.
    #
    # ========================================================

    itens_pagina = list(
        itens
    )


    # Completa as três posições com None.
    #
    # Assim:
    #
    # 1 produto -> 1 coluna preenchida
    # 2 produtos -> 2 colunas preenchidas
    # 3 produtos -> 3 colunas preenchidas

    while len(itens_pagina) < 3:

        itens_pagina.append(
            None
        )


    # ========================================================
    # DIMENSÕES
    # ========================================================

    largura_util = (
        largura_pagina
        - 2 * margem
    )

    largura_coluna = (
        largura_util / 3
    )

    colunas_x = [
        margem,
        margem + largura_coluna,
        margem + largura_coluna * 2,
    ]


    altura_item = 9 * mm
    altura_codigo = 11 * mm
    altura_imagem = 48 * mm
    altura_linha = 6.3 * mm

    y = y_topo


    # ========================================================
    # LINHA 1 - ITEM
    # ========================================================

    y -= altura_item


    for indice in range(3):

        x = colunas_x[indice]

        item = (
            itens_pagina[
                indice
            ]
        )


        c.setFillColor(
            COR_PRINCIPAL_ESCURA
        )

        c.rect(
            x,
            y,
            largura_coluna,
            altura_item,
            fill=1,
            stroke=0,
        )


        c.setStrokeColor(
            BRANCO
        )

        c.setLineWidth(
            0.4
        )

        c.rect(
            x,
            y,
            largura_coluna,
            altura_item,
            fill=0,
            stroke=1,
        )


        if item:

            titulo_item = (
                f"ITEM "
                f"{numero_item_inicial + indice:02d}"
            )

        else:

            titulo_item = ""


        texto_centro(
            c,
            x + largura_coluna / 2,
            y + 3.1 * mm,
            titulo_item,
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

        item = (
            itens_pagina[
                indice
            ]
        )


        desenhar_celula_tecnica(
            c,
            x,
            y,
            largura_coluna,
            altura_codigo,
            fundo=CINZA_FUNDO,
        )


        codigo = (
            item.get("codigo")
            if item
            else ""
        )


        texto_centro(
            c,
            x + largura_coluna / 2,
            y + 4.1 * mm,
            codigo,
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

        item = (
            itens_pagina[
                indice
            ]
        )


        desenhar_celula_tecnica(
            c,
            x,
            y,
            largura_coluna,
            altura_imagem,
            fundo=BRANCO,
        )


        if not item:
            continue


        variaveis = (
            item.get(
                "variaveis"
            )
            or {}
        )


        nome_imagem = (
            variaveis.get(
                "V17"
            )
        )


        imagem = (
            carregar_imagem_produto(
                nome_imagem
            )
        )


        margem_interna = (
            4 * mm
        )


        if imagem:

            c.drawImage(
                imagem,
                x + margem_interna,
                y + margem_interna,
                largura_coluna
                - 2 * margem_interna,
                altura_imagem
                - 2 * margem_interna,
                preserveAspectRatio=True,
                anchor="c",
                mask="auto",
            )


        else:

            texto_centro(
                c,
                x
                + largura_coluna / 2,
                y
                + altura_imagem / 2,
                "IMAGEM NÃO DISPONÍVEL",
                tamanho=6.5,
                fonte="Helvetica-Bold",
                cor=CINZA_MEDIO,
            )


    # ========================================================
    # PREPARAR DADOS REAIS
    # ========================================================

    dados_produtos = []


    for item in itens_pagina:

        if not item:

            dados_produtos.append(
                {}
            )

            continue


        variaveis = (
            item.get(
                "variaveis"
            )
            or {}
        )


        v13 = (
            variaveis.get(
                "V13"
            )
            or {}
        )


        v15 = (
            variaveis.get(
                "V15"
            )
            or {}
        )


        conexao = (
            f"{valor_tecnico(variaveis.get('V07'))} "
            f"{valor_tecnico(variaveis.get('V08'))}"
        ).strip()


        dados_produtos.append(
            {

                "TIPO":
                    valor_tecnico(
                        variaveis.get(
                            "V01"
                        )
                    ),

                "OPERAÇÃO":
                    valor_tecnico(
                        variaveis.get(
                            "V02"
                        )
                    ),

                "VIAS":
                    valor_tecnico(
                        variaveis.get(
                            "V03"
                        )
                    ),

                "POSIÇÃO":
                    valor_tecnico(
                        variaveis.get(
                            "V04"
                        )
                    ),

                "CORPO":
                    valor_tecnico(
                        variaveis.get(
                            "V05"
                        )
                    ),

                "VEDAÇÃO":
                    valor_tecnico(
                        variaveis.get(
                            "V06"
                        )
                    ),

                "CONEXÃO":
                    conexao,

                "ORIFÍCIO":
                    valor_tecnico(
                        variaveis.get(
                            "V09"
                        )
                    ),

                "PRESSÃO MÍN.":
                    valor_tecnico(
                        variaveis.get(
                            "V10"
                        )
                    ),

                "PRESSÃO MÁX.":
                    valor_tecnico(
                        variaveis.get(
                            "V11"
                        )
                    ),

                "TEMPERATURA":
                    valor_tecnico(
                        variaveis.get(
                            "V12"
                        )
                    ),

                "BOBINA":
                    valor_tecnico(
                        v13.get(
                            "tipo_bobina"
                        )
                    ),

                "CLASSE TÉRMICA":
                    valor_tecnico(
                        v13.get(
                            "classe_termica"
                        )
                    ),

                "PROTEÇÃO":
                    valor_tecnico(
                        v13.get(
                            "protecao"
                        )
                    ),

                "CONEXÃO ELÉTR.":
                    valor_tecnico(
                        v13.get(
                            "conexao_eletrica"
                        )
                    ),

                "CERTIFICAÇÃO":
                    valor_tecnico(
                        v13.get(
                            "certificacao"
                        )
                    ),

                "POTÊNCIA":
                    valor_tecnico(
                        variaveis.get(
                            "V14"
                        )
                    ),

                "TENSÃO":
                    valor_tecnico(
                        item.get(
                            "tensao"
                        )
                    ),

                "KV":
                    valor_tecnico(
                        variaveis.get(
                            "V16"
                        )
                    ),

                "OBSERVAÇÃO":
                    (
                        item.get(
                            "observacao"
                        )
                        or texto_extras_v15(
                            v15
                        )
                        or "—"
                    ),
            }
        )


    # ========================================================
    # CAMPOS DA TABELA
    # ========================================================

    campos = [
        "TIPO",
        "OPERAÇÃO",
        "VIAS",
        "POSIÇÃO",
        "CORPO",
        "VEDAÇÃO",
        "CONEXÃO",
        "ORIFÍCIO",
        "PRESSÃO MÍN.",
        "PRESSÃO MÁX.",
        "TEMPERATURA",
        "BOBINA",
        "CLASSE TÉRMICA",
        "PROTEÇÃO",
        "CONEXÃO ELÉTR.",
        "CERTIFICAÇÃO",
        "POTÊNCIA",
        "TENSÃO",
        "KV",
        "OBSERVAÇÃO",
    ]


    quantidade_linhas = len(
        campos
    )


    # ========================================================
    # LARGURAS DA TABELA
    # ========================================================

    largura_campo = (
        38 * mm
    )

    largura_valores = (
        largura_util
        - largura_campo
    )

    largura_valor = (
        largura_valores / 3
    )


    # ========================================================
    # DESENHAR DADOS
    # ========================================================

    for numero_linha, campo in enumerate(
        campos
    ):

        if campo == "OBSERVAÇÃO":

            altura_atual = (
                altura_linha * 2
            )

        else:

            altura_atual = (
                altura_linha
            )


        y -= altura_atual


        fundo = (
            CINZA_ALTERNADO
            if numero_linha % 2 == 1
            else BRANCO
        )


        c.setFillColor(
            fundo
        )


        c.rect(
            margem,
            y,
            largura_util,
            altura_atual,
            fill=1,
            stroke=0,
        )


        # ====================================================
        # NOME DO CAMPO
        # ====================================================

        texto(
            c,
            margem + 3 * mm,
            y
            + (
                altura_atual / 2
            )
            - 1.2 * mm,
            campo,
            tamanho=6.2,
            fonte="Helvetica-Bold",
            cor=CINZA_ESCURO,
        )


        x_inicio_valores = (
            margem
            + largura_campo
        )


        c.setStrokeColor(
            CINZA_LINHA
        )

        c.setLineWidth(
            0.4
        )


        c.line(
            x_inicio_valores,
            y,
            x_inicio_valores,
            y + altura_atual,
        )


        # ====================================================
        # VALORES
        # ====================================================

        for indice in range(3):

            x = (
                x_inicio_valores
                + indice
                * largura_valor
            )


            produto = (
                dados_produtos[
                    indice
                ]
            )


            valor = (
                produto.get(
                    campo,
                    ""
                )
                if produto
                else ""
            )


            if (
                campo
                == "OBSERVAÇÃO"
            ):

                texto_quebrado(
                    c,
                    valor,
                    x + 2 * mm,
                    y
                    + altura_atual
                    - 4 * mm,
                    largura_valor
                    - 4 * mm,
                    tamanho=5.8,
                    entrelinha=6.5,
                    max_linhas=2,
                )


            else:

                texto_centro(
                    c,
                    x
                    + largura_valor / 2,
                    y
                    + (
                        altura_atual / 2
                    )
                    - 1.2 * mm,
                    valor,
                    tamanho=6.2,
                    fonte="Helvetica",
                    cor=PRETO,
                )


            if indice < 2:

                c.line(
                    x
                    + largura_valor,
                    y,
                    x
                    + largura_valor,
                    y
                    + altura_atual,
                )


        c.line(
            margem,
            y,
            margem
            + largura_util,
            y,
        )


    # ========================================================
    # BORDA GERAL
    # ========================================================

    altura_total_dados = (
        (
            quantidade_linhas
            - 1
        )
        * altura_linha
        + altura_linha
        * 2
    )


    c.setStrokeColor(
        CINZA_LINHA
    )

    c.setLineWidth(
        0.6
    )


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

    c.setStrokeColor(
        CINZA_LINHA
    )

    c.setLineWidth(
        0.5
    )


    c.line(
        margem,
        17 * mm,
        largura_pagina
        - margem,
        17 * mm,
    )


    texto(
        c,
        margem,
        11 * mm,
        EMPRESA_NOME,
        tamanho=6.5,
        fonte="Helvetica-Bold",
        cor=CINZA_MEDIO,
    )


    texto_direita(
        c,
        largura_pagina
        - margem,
        11 * mm,
        "Dados técnicos da proposta",
        tamanho=6.5,
        cor=CINZA_MEDIO,
    )


    texto_centro(
        c,
        largura_pagina / 2,
        6 * mm,
        str(numero_pagina),
        tamanho=7,
        cor=CINZA_MEDIO,
    )

# ============================================================
# DIVIDIR LISTA EM BLOCOS
# ============================================================

def dividir_em_blocos(
    lista,
    tamanho,
):

    return [
        lista[indice:indice + tamanho]
        for indice in range(
            0,
            len(lista),
            tamanho,
        )
    ]

# ============================================================
# DESENHAR UMA PÁGINA COMERCIAL
# ============================================================

def desenhar_pagina_comercial(
    c,
    largura_pagina,
    altura_pagina,
    numero_orcamento,
    data_orcamento,
    cliente,
    itens_pagina,
    todos_itens,
    observacao_geral,
    responsavel,
    numero_item_inicial,
    eh_ultima_pagina,
    numero_ultima_pagina_comercial,
):

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
        numero_orcamento,
        data_orcamento,
    )


    # CLIENTE

    y = desenhar_cliente(
        c,
        largura_pagina,
        y - 3 * mm,
        cliente,
        responsavel,
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
        itens_pagina,
        numero_item_inicial,
    )


    # OBSERVAÇÕES

    y = desenhar_observacoes(
        c,
        y - 5 * mm,
        observacao_geral,
    )


    # VENDEDOR + TOTAL

    y_bloco = (
        y - 4 * mm
    )


    desenhar_vendedor(
        c,
        y_bloco,
        responsavel,
    )


    y = desenhar_total(
        c,
        largura_pagina,
        y_bloco,
        todos_itens,
        mostrar_total=eh_ultima_pagina,
        pagina_total=(
            numero_ultima_pagina_comercial
        ),
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
# GERADOR PRINCIPAL
# ============================================================

def gerar_pdf_orcamento(
    numero_orcamento,
    data_orcamento,
    cliente,
    itens,
    observacao_geral,
    responsavel,
):

    buffer = BytesIO()

    largura_pagina, altura_pagina = A4


    c = canvas.Canvas(
        buffer,
        pagesize=A4,
    )


    c.setTitle(
        "Proposta Comercial Jefferson"
    )


    # ========================================================
    # DIVIDIR ITENS
    # ========================================================

    paginas_comerciais = (
        dividir_em_blocos(
            itens,
            8,
        )
    )


    paginas_tecnicas = (
        dividir_em_blocos(
            itens,
            3,
        )
    )


    quantidade_paginas_comerciais = (
        len(
            paginas_comerciais
        )
    )


    # ========================================================
    # PÁGINAS COMERCIAIS
    # ========================================================

    numero_item_inicial = 1


    for indice_pagina, itens_pagina in enumerate(
        paginas_comerciais
    ):

        eh_ultima_pagina = (
            indice_pagina
            == quantidade_paginas_comerciais - 1
        )


        desenhar_pagina_comercial(
            c,
            largura_pagina,
            altura_pagina,
            numero_orcamento,
            data_orcamento,
            cliente,
            itens_pagina,
            itens,
            observacao_geral,
            responsavel,
            numero_item_inicial,
            eh_ultima_pagina,
            quantidade_paginas_comerciais,
        )


        c.showPage()


        numero_item_inicial += (
            len(
                itens_pagina
            )
        )


    # ========================================================
    # PÁGINAS TÉCNICAS
    # ========================================================

    numero_item_inicial = 1


    for indice_tecnico, itens_pagina in enumerate(
        paginas_tecnicas
    ):

        numero_pagina_pdf = (
            quantidade_paginas_comerciais
            + indice_tecnico
            + 1
        )


        desenhar_pagina_tecnica_teste(
            c,
            largura_pagina,
            altura_pagina,
            numero_orcamento,
            itens_pagina,
            numero_pagina_pdf,
            numero_item_inicial,
        )


        c.showPage()


        numero_item_inicial += (
            len(
                itens_pagina
            )
        )


    # ========================================================
    # FINALIZA PDF
    # ========================================================

    c.save()

    buffer.seek(
        0
    )

    return buffer.getvalue()

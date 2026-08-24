from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


# ======================================================
# CORES
# ======================================================

AZUL = colors.HexColor("#005B8F")
AZUL_ESCURO = colors.HexColor("#003B5C")
AZUL_CLARO = colors.HexColor("#EAF4F8")
CINZA_FUNDO = colors.HexColor("#F3F5F7")
CINZA_LINHA = colors.HexColor("#D7DEE3")
CINZA_TEXTO = colors.HexColor("#4B5563")
BRANCO = colors.white
PRETO = colors.HexColor("#1F2933")


# ======================================================
# ESTILOS
# ======================================================

ESTILO_TITULO = ParagraphStyle(
    "titulo",
    fontName="Helvetica-Bold",
    fontSize=18,
    textColor=AZUL_ESCURO,
    leading=21,
)

ESTILO_SUBTITULO = ParagraphStyle(
    "subtitulo",
    fontName="Helvetica-Bold",
    fontSize=10,
    textColor=AZUL_ESCURO,
    leading=13,
)

ESTILO_NORMAL = ParagraphStyle(
    "normal",
    fontName="Helvetica",
    fontSize=8.5,
    textColor=PRETO,
    leading=12,
)

ESTILO_PEQUENO = ParagraphStyle(
    "pequeno",
    fontName="Helvetica",
    fontSize=7.5,
    textColor=CINZA_TEXTO,
    leading=10,
)

ESTILO_TOTAL = ParagraphStyle(
    "total",
    fontName="Helvetica-Bold",
    fontSize=15,
    textColor=AZUL_ESCURO,
    alignment=TA_RIGHT,
)

ESTILO_DESTAQUE = ParagraphStyle(
    "destaque",
    fontName="Helvetica",
    fontSize=9,
    textColor=PRETO,
    leading=13,
)


# ======================================================
# CABEÇALHO / RODAPÉ
# ======================================================

def desenhar_cabecalho_rodape(canvas, doc):
    largura, altura = A4

    canvas.saveState()

    # Linha superior
    canvas.setFillColor(AZUL)
    canvas.rect(
        0,
        altura - 5 * mm,
        largura,
        5 * mm,
        fill=1,
        stroke=0,
    )

    # Rodapé
    canvas.setStrokeColor(CINZA_LINHA)
    canvas.line(
        15 * mm,
        13 * mm,
        largura - 15 * mm,
        13 * mm,
    )

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(CINZA_TEXTO)

    canvas.drawString(
        15 * mm,
        8 * mm,
        "Jefferson - Proposta Comercial",
    )

    canvas.drawRightString(
        largura - 15 * mm,
        8 * mm,
        f"Página {doc.page}",
    )

    canvas.restoreState()


# ======================================================
# COMPONENTES
# ======================================================

def bloco_titulo(texto):
    tabela = Table(
        [[Paragraph(texto, ESTILO_SUBTITULO)]],
        colWidths=[180 * mm],
    )

    tabela.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), AZUL_CLARO),
            ("BOX", (0, 0), (-1, -1), 0.6, CINZA_LINHA),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )

    return tabela


def tabela_dados_cliente():
    dados = [
        [
            Paragraph("<b>Cliente</b>", ESTILO_PEQUENO),
            Paragraph(
                "INDÚSTRIA EXEMPLO DE EQUIPAMENTOS LTDA.",
                ESTILO_NORMAL,
            ),
        ],
        [
            Paragraph("<b>CNPJ</b>", ESTILO_PEQUENO),
            Paragraph("12.345.678/0001-90", ESTILO_NORMAL),
        ],
        [
            Paragraph("<b>Cidade / UF</b>", ESTILO_PEQUENO),
            Paragraph("São Paulo / SP", ESTILO_NORMAL),
        ],
        [
            Paragraph("<b>Contato</b>", ESTILO_PEQUENO),
            Paragraph(
                "Departamento de Engenharia",
                ESTILO_NORMAL,
            ),
        ],
    ]

    tabela = Table(
        dados,
        colWidths=[35 * mm, 145 * mm],
    )

    tabela.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.6, CINZA_LINHA),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, CINZA_LINHA),
            ("BACKGROUND", (0, 0), (0, -1), CINZA_FUNDO),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )

    return tabela


def resumo_comercial():
    dados = [
        [
            Paragraph("<b>ITEM</b>", ESTILO_PEQUENO),
            Paragraph("<b>CÓDIGO</b>", ESTILO_PEQUENO),
            Paragraph("<b>PRODUTO</b>", ESTILO_PEQUENO),
            Paragraph("<b>QTD.</b>", ESTILO_PEQUENO),
            Paragraph("<b>PRAZO</b>", ESTILO_PEQUENO),
            Paragraph("<b>UNIT.</b>", ESTILO_PEQUENO),
            Paragraph("<b>TOTAL</b>", ESTILO_PEQUENO),
        ],
        [
            "01",
            "1335BA04T",
            Paragraph(
                "Válvula solenoide 2 vias NF",
                ESTILO_NORMAL,
            ),
            "2",
            "IMEDIATO",
            "R$ 850,00",
            "R$ 1.700,00",
        ],
        [
            "02",
            "1342BV08T",
            Paragraph(
                "Válvula solenoide servo operada",
                ESTILO_NORMAL,
            ),
            "1",
            "15 DIAS",
            "R$ 1.250,00",
            "R$ 1.250,00",
        ],
    ]

    tabela = Table(
        dados,
        colWidths=[
            12 * mm,
            28 * mm,
            55 * mm,
            12 * mm,
            22 * mm,
            25 * mm,
            26 * mm,
        ],
        repeatRows=1,
    )

    tabela.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AZUL_ESCURO),
            ("TEXTCOLOR", (0, 0), (-1, 0), BRANCO),
            ("ALIGN", (0, 0), (1, -1), "CENTER"),
            ("ALIGN", (3, 1), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOX", (0, 0), (-1, -1), 0.6, CINZA_LINHA),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, CINZA_LINHA),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                BRANCO,
                colors.HexColor("#FAFBFC"),
            ]),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
        ])
    )

    return tabela


def bloco_destaque():
    conteudo = Paragraph(
        "<b>Destaque da proposta</b><br/><br/>"
        "Fornecimento de válvulas solenoides Jefferson "
        "selecionadas para a aplicação informada. "
        "As condições técnicas apresentadas nesta proposta "
        "devem ser verificadas antes da instalação.",
        ESTILO_DESTAQUE,
    )

    tabela = Table(
        [[conteudo]],
        colWidths=[180 * mm],
    )

    tabela.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF9E8")),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#E7C766")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ])
    )

    return tabela


def ficha_tecnica_item(
    numero,
    codigo,
    tensao,
    descricao_curta,
):
    cabecalho = Table(
        [[
            Paragraph(
                f"ITEM {numero:02d}",
                ParagraphStyle(
                    "item",
                    fontName="Helvetica-Bold",
                    fontSize=9,
                    textColor=BRANCO,
                ),
            ),
            Paragraph(
                f"{codigo} - {tensao}",
                ParagraphStyle(
                    "cod",
                    fontName="Helvetica-Bold",
                    fontSize=11,
                    textColor=BRANCO,
                ),
            ),
        ]],
        colWidths=[28 * mm, 152 * mm],
    )

    cabecalho.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), AZUL_ESCURO),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )

    dados = [
        ["Tipo", "Válvula solenoide"],
        ["Operação", "Servo operada"],
        ["Vias", "2 vias"],
        ["Estado", "Normalmente fechada"],
        ["Corpo", "Latão"],
        ["Vedação", "Buna-N (NBR)"],
        ["Conexão", '1/2" NPT'],
        ["Orifício", "14 mm"],
        ["Pressão mínima", "0,1 bar"],
        ["Pressão máxima", "10 bar"],
        ["Temperatura máxima", "80 °C"],
        ["Proteção", "IP65"],
        ["Tensão", tensao],
        ["Potência", "13 W"],
    ]

    linhas = []

    for campo, valor in dados:
        linhas.append([
            Paragraph(f"<b>{campo}</b>", ESTILO_PEQUENO),
            Paragraph(valor, ESTILO_NORMAL),
        ])

    tabela = Table(
        linhas,
        colWidths=[55 * mm, 125 * mm],
    )

    tabela.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.6, CINZA_LINHA),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, CINZA_LINHA),
            ("BACKGROUND", (0, 0), (0, -1), CINZA_FUNDO),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ])
    )

    descricao = Table(
        [[
            Paragraph(
                "<b>DESCRIÇÃO TÉCNICA COMPLETA</b><br/><br/>"
                + descricao_curta,
                ESTILO_DESTAQUE,
            )
        ]],
        colWidths=[180 * mm],
    )

    descricao.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), AZUL_CLARO),
            ("BOX", (0, 0), (-1, -1), 0.6, CINZA_LINHA),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ])
    )

    return KeepTogether([
        cabecalho,
        Spacer(1, 3 * mm),
        tabela,
        Spacer(1, 4 * mm),
        descricao,
    ])


# ======================================================
# GERADOR
# ======================================================

def gerar_pdf_teste():
    buffer = BytesIO()

    doc = BaseDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=16 * mm,
        bottomMargin=18 * mm,
        title="Proposta Comercial Jefferson",
    )

    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="frame_principal",
    )

    template = PageTemplate(
        id="template_padrao",
        frames=[frame],
        onPage=desenhar_cabecalho_rodape,
    )

    doc.addPageTemplates([template])

    story = []

    # ==================================================
    # PÁGINA 1
    # ==================================================

    caminho_logo = Path("assets/icone_jefferson.png")

    if caminho_logo.exists():
        logo = Image(
            str(caminho_logo),
            width=24 * mm,
            height=24 * mm,
        )
    else:
        logo = Paragraph(
            "<b>JEFFERSON</b>",
            ESTILO_TITULO,
        )

    dados_cabecalho = [
        [
            logo,
            Paragraph(
                "<b>PROPOSTA COMERCIAL</b><br/>"
                "<font size='9'>Soluções em controle de fluidos</font>",
                ESTILO_TITULO,
            ),
            Paragraph(
                "<b>PROPOSTA Nº</b><br/>3288/26"
                "<br/><br/><b>DATA</b><br/>24/08/2026",
                ParagraphStyle(
                    "cab_direita",
                    fontName="Helvetica",
                    fontSize=9,
                    textColor=PRETO,
                    leading=12,
                    alignment=TA_RIGHT,
                ),
            ),
        ]
    ]

    cabecalho = Table(
        dados_cabecalho,
        colWidths=[
            28 * mm,
            98 * mm,
            54 * mm,
        ],
    )

    cabecalho.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )

    story.append(cabecalho)
    story.append(Spacer(1, 5 * mm))

    story.append(bloco_titulo("DADOS DO CLIENTE"))
    story.append(Spacer(1, 2 * mm))
    story.append(tabela_dados_cliente())
    story.append(Spacer(1, 6 * mm))

    story.append(bloco_titulo("RESUMO DA PROPOSTA"))
    story.append(Spacer(1, 2 * mm))
    story.append(resumo_comercial())
    story.append(Spacer(1, 6 * mm))

    story.append(bloco_destaque())
    story.append(Spacer(1, 7 * mm))

    total = Table(
        [[
            "",
            Paragraph(
                "TOTAL DA PROPOSTA",
                ESTILO_SUBTITULO,
            ),
            Paragraph(
                "R$ 2.950,00",
                ESTILO_TOTAL,
            ),
        ]],
        colWidths=[
            80 * mm,
            45 * mm,
            55 * mm,
        ],
    )

    total.setStyle(
        TableStyle([
            ("LINEABOVE", (1, 0), (-1, 0), 1.2, AZUL_ESCURO),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )

    story.append(total)
    story.append(Spacer(1, 5 * mm))

    story.append(bloco_titulo("CONDIÇÕES COMERCIAIS"))
    story.append(Spacer(1, 2 * mm))

    condicoes = Table(
        [
            ["Validade da proposta", "15 dias"],
            ["Condição de pagamento", "28 dias"],
            ["Frete", "FOB"],
            ["Impostos", "Inclusos conforme legislação vigente"],
        ],
        colWidths=[55 * mm, 125 * mm],
    )

    condicoes.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.6, CINZA_LINHA),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, CINZA_LINHA),
            ("BACKGROUND", (0, 0), (0, -1), CINZA_FUNDO),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )

    story.append(condicoes)

    # ==================================================
    # PÁGINA 2
    # ==================================================

    story.append(PageBreak())

    story.append(
        Paragraph(
            "ESPECIFICAÇÃO TÉCNICA",
            ESTILO_TITULO,
        )
    )

    story.append(
        Paragraph(
            "Detalhamento técnico dos itens ofertados",
            ESTILO_PEQUENO,
        )
    )

    story.append(Spacer(1, 6 * mm))

    descricao_1 = (
        "Válvula solenoide servo operada, 2 vias, normalmente fechada, "
        "corpo em latão, vedação em Buna-N (NBR), conexão de 1/2&quot; NPT, "
        "orifício interno de 14 mm, pressão de trabalho mínima de 0,1 bar "
        "e máxima de 10 bar, temperatura máxima do fluido de 80 °C, "
        "bobina encapsulada, classe H, grau de proteção IP65, "
        "potência de 13 W e tensão de acionamento 220 V / 60 Hz."
    )

    story.append(
        ficha_tecnica_item(
            1,
            "1335BA04T",
            "220/60HZ",
            descricao_1,
        )
    )

    story.append(Spacer(1, 8 * mm))

    descricao_2 = (
        "Válvula solenoide servo operada, 2 vias, normalmente fechada, "
        "construída para aplicações industriais, com especificação técnica "
        "conforme os parâmetros indicados nesta proposta."
    )

    story.append(
        ficha_tecnica_item(
            2,
            "1342BV08T",
            "24VCC",
            descricao_2,
        )
    )

    doc.build(story)

    buffer.seek(0)

    return buffer.getvalue()

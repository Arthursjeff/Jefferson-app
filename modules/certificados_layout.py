"""Layout fixo do certificado Jefferson baseado no PDF 40.686 fornecido.

Usa as coordenadas da página 612 x 792 e os elementos gráficos do modelo.
Todos os valores variáveis continuam vindo da Fila e do motor de descrição
(incluindo correções homologadas), sem consulta ao histórico ERP.
"""
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zoneinfo import ZoneInfo

from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

W, H = 612, 792
ASSETS = Path(__file__).resolve().parents[1] / "assets" / "certificados"
MESES = (
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
)


def _texto(valor):
    if valor is None:
        return ""
    if isinstance(valor, dict):
        return ", ".join(
            _texto(x) for x in valor.values() if x not in (None, "", [], {})
        )
    if isinstance(valor, (list, tuple)):
        return ", ".join(
            _texto(x) for x in valor if x not in (None, "", [], {})
        )
    return str(valor).strip()


def _qtd(valor):
    numero = Decimal(str(valor))
    if numero == numero.to_integral_value():
        return str(int(numero))
    return format(numero.normalize(), "f").replace(".", ",")


def _desenhar(c, x, topo, texto, negrito=False, tamanho=10, largura=None):
    nome_fonte = "Times-Bold" if negrito else "Times-Roman"
    texto = _texto(texto)
    if not texto:
        return
    if largura is not None:
        while stringWidth(texto, nome_fonte, tamanho) > largura and tamanho > 7:
            tamanho -= 0.25
        if stringWidth(texto, nome_fonte, tamanho) > largura:
            raise ValueError("Texto longo demais para o layout do certificado.")
    c.setFont(nome_fonte, tamanho)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(x, H - topo, texto)


def _centro(c, topo, texto, negrito=True, tamanho=11.5, sublinhar=False):
    fonte = "Times-Bold" if negrito else "Times-Roman"
    texto = _texto(texto)
    while stringWidth(texto, fonte, tamanho) > 440 and tamanho > 8:
        tamanho -= .25
    if stringWidth(texto, fonte, tamanho) > 440:
        raise ValueError("Nome do cliente excede o espaço disponível no certificado.")
    c.setFont(fonte, tamanho)
    c.drawCentredString(341, H - topo, texto)
    if sublinhar:
        metade = stringWidth(texto, fonte, tamanho) / 2
        c.setLineWidth(.7)
        c.line(341 - metade, H - topo - 1.8,
               341 + metade, H - topo - 1.8)


def _pontilhado(c, rotulo, valor, topo, x_valor=337.5,
                negrito=True, tamanho=10, largura_valor=222):
    fonte = "Times-Bold" if negrito else "Times-Roman"
    x = 124.1
    rotulo = _texto(rotulo)
    c.setFont(fonte, tamanho)
    c.drawString(x, H - topo, rotulo)
    passo = stringWidth(".", fonte, tamanho)
    pos = x + stringWidth(rotulo, fonte, tamanho) + 1
    while pos + passo < x_valor - 2:
        c.drawString(pos, H - topo, ".")
        pos += passo
    _desenhar(
        c, x_valor, topo, valor, negrito=negrito, tamanho=tamanho,
        largura=largura_valor,
    )


def _quebrar(c, x, topo, texto, largura, tamanho=9.3,
             distancia=11.2, max_linhas=3, negrito=False):
    fonte = "Times-Bold" if negrito else "Times-Roman"
    linhas = simpleSplit(_texto(texto), fonte, tamanho, largura)
    if len(linhas) > max_linhas:
        raise ValueError(
            "Descrição técnica longa demais para o espaço do certificado. "
            "Revise a característica antes de emitir."
        )
    for indice, linha in enumerate(linhas):
        _desenhar(
            c, x, topo + distancia * indice, linha,
            negrito=negrito, tamanho=tamanho,
        )


def _imagem(c, nome, x, topo, largura, altura):
    arquivo = ASSETS / nome
    if not arquivo.is_file():
        raise FileNotFoundError(f"Elemento gráfico do certificado ausente: {nome}")
    c.drawImage(
        ImageReader(str(arquivo)),
        x, H - topo - altura,
        width=largura, height=altura,
        preserveAspectRatio=False,
    )


def _marca(c, com_marca):
    if com_marca:
        _imagem(c, "logo.webp", 84, 0, 255.84, 74.52)
        _imagem(c, "cabecalho.webp", 369.6, 0, 214.2, 53.52)
        _imagem(c, "rodape.webp", 84, 713.64, 479.88, 69.84)
    else:
        # No modelo sem marca, os elementos comerciais são suprimidos.
        _desenhar(
            c, 124, 762, "Jefferson Solenoidbras Ltda.",
            negrito=True, tamanho=8,
        )
    _imagem(c, "assinatura.webp", 125.04, 644.76, 78.72, 28.32)


def _operacao(variaveis):
    valores = []
    for campo in ("V03", "V02", "V04"):
        texto = _texto(variaveis.get(campo))
        if texto and texto.casefold() not in [v.casefold() for v in valores]:
            valores.append(texto)
    return ", ".join(valores)


def _desenhar_pagina(c, pedido, item, com_marca):
    v = item.get("variaveis") or {}
    _marca(c, com_marca)

    hoje = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    data = (
        f"São Bernardo do Campo, {hoje.day} de "
        f"{MESES[hoje.month - 1]} de {hoje.year}"
    )
    _desenhar(c, 362.2, 76.2, data, tamanho=10, largura=226)
    _centro(c, 116.1, "CERTIFICADO DE QUALIDADE", sublinhar=True)
    _centro(c, 141.6, pedido.get("cliente") or "CLIENTE NÃO INFORMADO",
            sublinhar=True)
    _desenhar(
        c, 124.1, 167.5,
        "Estamos especificando os materiais e faixas de trabalho das válvulas "
        "solenoides de nossa fabricação,",
        largura=436,
    )
    _desenhar(
        c, 124.1, 181, "marca JEFFERSON, que se identificam como:",
    )
    _pontilhado(
        c, "CATÁLOGO Nº.:", item.get("codigo"), 218.1,
        x_valor=275.2, largura_valor=94,
    )
    conexao = " ".join(
        x for x in (_texto(v.get("V07")), _texto(v.get("V08"))) if x
    )
    _desenhar(c, 374.8, 218.1, conexao, negrito=True, largura=75)
    estado = _texto(v.get("V04")).casefold()
    abreviacao = (
        "NF" if "fechad" in estado
        else "NA" if "abert" in estado else ""
    )
    _desenhar(c, 463.5, 218.1, abreviacao, negrito=True, largura=29)
    _desenhar(
        c, 495.5, 218.1, pedido.get("nota_fiscal"),
        negrito=True, largura=80,
    )
    _pontilhado(
        c, "Quantidade:",
        f"{_qtd(item.get('quantidade'))} peça(s)", 232.2,
        x_valor=275.2, largura_valor=150,
    )
    series = ", ".join(_texto(x) for x in item.get("series") or [])
    _pontilhado(
        c, "Nº de série:", series, 245.6,
        x_valor=275.2, negrito=False, largura_valor=282,
    )

    _desenhar(c, 124.1, 284.5, "Material:", negrito=True)
    c.setLineWidth(.65)
    c.line(124, H - 285.3, 164.8, H - 285.3)
    _pontilhado(c, "Corpo:", _texto(v.get("V05")), 309.8)
    _pontilhado(c, "Torre:", "AISI 316", 321.3)
    _pontilhado(c, "Mola de Retorno:", "AISI 302", 332.3)
    _pontilhado(c, "Vedações:", _texto(v.get("V06")), 346.1)
    _pontilhado(c, "Bobina:", "", 357.7)
    bobina = _texto(v.get("V13"))
    potencia = _texto(v.get("V14"))
    if potencia and potencia.casefold() not in bobina.casefold():
        bobina += (", " if bobina else "") + f"potência {potencia}"
    _quebrar(c, 337.6, 358, bobina, largura=220, max_linhas=3)
    _pontilhado(
        c, "Tensão de acionamento:", item.get("tensao"),
        410, x_valor=337.5,
    )

    _desenhar(c, 124.1, 451, "Dados de processo:", negrito=True)
    c.line(124, H - 451.9, 206.5, H - 451.9)
    pressao_min = _texto(v.get("V10"))
    pressao_max = _texto(v.get("V11"))
    if pressao_min.lower().endswith(" bar") and pressao_max.lower().endswith(" bar"):
        pressao_min = pressao_min[:-4]
    _pontilhado(
        c, "Pressão de Trabalho:",
        f"{pressao_min} a {pressao_max}",
        478.7, x_valor=329,
    )
    _pontilhado(c, "Estanqueidade:", "100%", 492.4, x_valor=329)
    _pontilhado(c, "Temperatura:", _texto(v.get("V12")), 506.1, x_valor=329)
    _pontilhado(c, "Operação:", "", 519.8, x_valor=329)
    _quebrar(
        c, 329, 519.8, _operacao(v),
        largura=227, tamanho=9.5, max_linhas=2,
    )

    _desenhar(c, 124.1, 566.5, "* Garantia:", negrito=True)
    c.setLineWidth(.65)
    c.line(136, H - 568.2, 185, H - 568.2)
    _desenhar(
        c, 187, 566.5,
        "12 meses, exceto partes elétricas (bobinas).",
    )
    _quebrar(
        c, 124.1, 593,
        "Certificamos que os dados informados se cumprem em cada uma das "
        "unidades fabricadas que se tem cumprido todos os requisitos de prova "
        "em nosso manual de controle de qualidade.",
        largura=436, tamanho=10, distancia=13.7,
    )
    c.setLineWidth(.7)
    c.line(124, H - 674.4, 240, H - 674.4)
    _desenhar(c, 124.1, 685.2, "Jefferson Solenoidbras Ltda", True, 9)
    _desenhar(c, 124.1, 696.9, "Arthur Henrique Rosa", True, 9)
    _desenhar(c, 124.1, 708.7, "Área Técnica", True, 9)


def gerar_pdf_certificados_layout(pedido, data_faturamento, itens,
                                 com_marca=True):
    """Retorna PDF em memória; uma página por item, com layout do modelo."""
    if not itens or any(item.get("erros") for item in itens):
        raise ValueError("Há itens sem validação técnica ou rastreabilidade.")
    if data_faturamento is None:
        raise ValueError("Data de faturamento não encontrada na fila.")
    pdf = BytesIO()
    documento = canvas.Canvas(
        pdf, pagesize=(W, H), pageCompression=1,
    )
    documento.setTitle(
        "Certificado de Qualidade - NF " + str(pedido.get("nota_fiscal") or "")
    )
    documento.setAuthor("Jefferson Solenoidbras Ltda.")
    for item in itens:
        _desenhar_pagina(documento, pedido, item, com_marca)
        documento.showPage()
    documento.save()
    return pdf.getvalue()

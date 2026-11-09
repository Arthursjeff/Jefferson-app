"""Classificação das ocorrências de importação PRN, sem acessar o banco."""
from decimal import Decimal

AVISO_CODIGO_TECNICO = "Código técnico não reconhecido"
AVISO_DIFERENCA_TOTAL = "Diferença total cabeçalho x soma itens"
OCORRENCIAS_INFORMATIVAS = {AVISO_CODIGO_TECNICO, AVISO_DIFERENCA_TOTAL}
TOLERANCIA_ARREDONDAMENTO = Decimal("0.02")


def classificar_ocorrencias(ocorrencias, diferenca):
    """Separa erros estruturais de avisos sem impedir registros comerciais válidos.

    ``diferenca`` é total do cabeçalho menos soma dos itens. O PRN não informa
    a natureza do ajuste: não presumir frete, desconto ou imposto.
    """
    erros = [tipo for tipo in ocorrencias if tipo not in OCORRENCIAS_INFORMATIVAS]
    avisos = []
    if AVISO_CODIGO_TECNICO in ocorrencias:
        avisos.append("Código técnico não reconhecido (ERP preservado)")

    delta = Decimal(str(diferenca or "0"))
    if abs(delta) > TOLERANCIA_ARREDONDAMENTO:
        valor = f"{abs(delta):,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")
        relacao = "acima" if delta > 0 else "abaixo"
        avisos.append(
            f"Total do ERP {relacao} da soma dos itens em R$ {valor} "
            "(diferença financeira não discriminada no PRN; conferir origem)"
        )
    return erros, avisos

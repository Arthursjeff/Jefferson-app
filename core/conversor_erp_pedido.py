"""Sugestões não destrutivas de códigos técnicos para o módulo Criar Pedido.

A fonte original do PRN não é modificada. Não se infere um código quando
não há uma sugestão previamente cadastrada para aquele item.
"""
import re


def _limpar(valor):
    return str(valor or "").strip()


def _parece_codigo(valor):
    """Filtro conservador: exclui descrições e textos comerciais."""
    valor = _limpar(valor)
    return bool(
        valor and len(valor) <= 64
        and not re.search(r"\\s", valor)
        and re.fullmatch(r"[A-Za-z0-9./_-]+", valor)
    )


def sugerir_codigo(item):
    """Retorna dados de exibição; jamais confirma uma equivalência técnica."""
    original = _limpar(item.get("codigo_erp"))
    candidato = _limpar(item.get("codigo_tecnico_sugerido"))
    if candidato and _parece_codigo(candidato):
        return {
            "codigo_erp": original,
            "codigo_sugerido": candidato,
            "codigo_inicial": candidato,
            "situacao": "SUGESTÃO NÃO VALIDADA — conferir",
        }
    return {
        "codigo_erp": original,
        "codigo_sugerido": "",
        "codigo_inicial": original,
        "situacao": "SEM SUGESTÃO — conferir manualmente",
    }

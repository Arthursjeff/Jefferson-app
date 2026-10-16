"""Conciliação ERP -> Jefferson: cadastro, histórico e motor estrutural.

Sugestões são não auditadas: o comercial deve confirmar todos os itens.
Não altera itens importados nem a base de equivalências.
"""
import csv
import re
from functools import lru_cache
from pathlib import Path
from core.motor_erp_regras import (
    categoria, codigo_na_descricao, inferir_valvula,
    normal, VALVULA_COMPLETA, KIT_COMPLETO,
)

MAPA_455 = Path(__file__).parent / "data" / "erp_equivalencias_455.csv"
STATUS_HISTORICO = "REFERENCIA_CODIGO_NAO_AUDITADA"
STATUS_REGRA = "REGRA_CONFERIDA_COM_DESCRICAO"


def _parece_codigo(valor):
    v = normal(valor)
    return bool(v and len(v) <= 64 and
                re.fullmatch(r"[A-Z0-9./_-]+", v))


@lru_cache(maxsize=1)
def _mapa():
    resultado = {}
    try:
        with MAPA_455.open("r", encoding="utf-8-sig", newline="") as arquivo:
            for registro in csv.DictReader(arquivo, delimiter=";"):
                codigo = normal(registro.get("codigo_erp"))
                if codigo:
                    resultado[codigo] = registro
    except FileNotFoundError:
        return {}
    return resultado


def sugerir_codigo(item):
    """Produz sugestão e rastreio da origem da decisão, sem auto-homologação."""
    original = normal(item.get("codigo_erp"))
    individual = normal(item.get("codigo_tecnico_sugerido"))
    descricao = item.get("descricao_original") or ""
    info = _mapa().get(original, {})
    historico = normal(info.get("codigo_tecnico_proposto"))
    status = info.get("situacao", "")
    tipo = info.get("tipo_provavel", "") or categoria(original, descricao)
    pela_regra = inferir_valvula(original) if tipo == "VALVULA" else ""
    # Mesmo sem descrição textual, tentar estrutura; mas não presumir que
    # qualquer peça ou bobina com números seja válvula.
    if tipo == "OUTRO" and not info and not descricao:
        pela_regra = inferir_valvula(original)
    pela_descricao = codigo_na_descricao(descricao) if tipo == "VALVULA" else ""

    fontes = {}
    if _parece_codigo(individual):
        fontes["CADASTRO"] = individual
    if (status in (STATUS_HISTORICO, STATUS_REGRA)
            and tipo in ("VALVULA", "KIT") and _parece_codigo(historico)):
        fontes["HISTORICO"] = historico
    if pela_regra and VALVULA_COMPLETA.fullmatch(pela_regra):
        fontes["REGRA"] = pela_regra
    if pela_descricao:
        fontes["DESCRICAO"] = pela_descricao

    # Referência histórica exata pode divergir de regra geral V0.5.
    # Nesses casos, preservar o código do cadastro/histórico, mas exibir
    # conflito para revisão e NÃO preencher automaticamente.
    distintos = set(fontes.values())
    if len(distintos) > 1:
        detalhes = "; ".join(f"{origem}: {codigo}" for origem, codigo in fontes.items())
        return dict(codigo_erp=original, codigo_sugerido="",
                    codigo_inicial=original,
                    situacao="CONFLITO — preencher código após conferir",
                    origem_sugestao=detalhes,
                    tipo_provavel=tipo,
                    codigo_regra=pela_regra)
    if fontes:
        prioridade = next((chave for chave in
                           ("CADASTRO", "HISTORICO", "DESCRICAO", "REGRA")
                           if chave in fontes), "")
        codigo = fontes[prioridade]
        # Inferência isolada não possui validação documental.
        situacao = ("INFERÊNCIA POR REGRA — confirmar"
                    if set(fontes) == {"REGRA"}
                    else "SUGESTÃO HISTÓRICA/DOCUMENTAL — confirmar")
        return dict(codigo_erp=original, codigo_sugerido=codigo,
                    codigo_inicial=codigo, situacao=situacao,
                    origem_sugestao=" + ".join(fontes),
                    tipo_provavel=tipo, codigo_regra=pela_regra)
    return dict(codigo_erp=original, codigo_sugerido="",
                codigo_inicial=original,
                situacao="SEM EQUIVALÊNCIA SEGURA — conferir",
                origem_sugestao="NENHUMA",
                tipo_provavel=tipo, codigo_regra=pela_regra)

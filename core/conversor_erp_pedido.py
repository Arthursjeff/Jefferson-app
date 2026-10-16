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
MAPA_HISTORICO = Path(__file__).parent / "data" / "erp_equivalencias_historicas.tsv"
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



@lru_cache(maxsize=1)
def _historico_completo():
    """Retorna mapa dos pares e chaves conflitantes, sem assumir validade técnica."""
    mapa = {}
    conflitos = set()
    try:
        with MAPA_HISTORICO.open("r", encoding="utf-8-sig", newline="") as arquivo:
            for linha in csv.reader(arquivo, delimiter="\t"):
                if len(linha) < 2:
                    continue
                codigo, destino = normal(linha[0]), normal(linha[1])
                if not codigo or codigo in ("CODIGO", "CÓDIGO") or not destino:
                    continue
                if codigo in mapa and mapa[codigo] != destino:
                    conflitos.add(codigo)
                mapa[codigo] = destino
    except FileNotFoundError:
        pass
    return mapa, conflitos


def _codigo_historico_valido(codigo, tipo):
    """Somente formatos completos de válvula/kit; descrições NÃO são códigos."""
    return bool((tipo == "VALVULA" and VALVULA_COMPLETA.fullmatch(codigo))
                or (tipo == "KIT" and KIT_COMPLETO.fullmatch(codigo)))

def sugerir_codigo(item):
    """Produz sugestão e rastreio da origem da decisão, sem auto-homologação."""
    original = normal(item.get("codigo_erp"))
    individual = normal(item.get("codigo_tecnico_sugerido"))
    descricao = item.get("descricao_original") or ""
    info = _mapa().get(original, {})
    historico = normal(info.get("codigo_tecnico_proposto"))
    tabela_historica, conflitos_historicos = _historico_completo()
    historico_global = tabela_historica.get(original, "")
    status = info.get("situacao", "")
    tipo = info.get("tipo_provavel", "") or categoria(original, descricao)
    if tipo == "OUTRO" and VALVULA_COMPLETA.fullmatch(historico_global):
        tipo = "VALVULA"
    if tipo == "OUTRO" and KIT_COMPLETO.fullmatch(historico_global):
        tipo = "KIT"
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
    if (original in conflitos_historicos):
        return dict(codigo_erp=original, codigo_sugerido="",
                    codigo_inicial=original,
                    situacao="CONFLITO NA TABELA HISTÓRICA — conferir",
                    origem_sugestao="HISTORICO_CONFLITANTE", tipo_provavel=tipo,
                    codigo_regra=pela_regra)
    if _codigo_historico_valido(historico_global, tipo):
        fontes["HISTORICO_COMPLETO"] = historico_global
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
                           ("CADASTRO", "HISTORICO_COMPLETO", "HISTORICO", "DESCRICAO", "REGRA")
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

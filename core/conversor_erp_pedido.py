"""Conversor ERP -> código Jefferson (pré-validação humana).

Consulta somente referências históricas do diagnóstico de 455 códigos e a
sugestão específica da linha comercial. Nunca modifica o PRN ou Supabase.
A tabela histórica é não auditada: nenhuma sugestão é homologação técnica.
"""
import csv
import re
from functools import lru_cache
from pathlib import Path

MAPA_455 = Path(__file__).parent / "data" / "erp_equivalencias_455.csv"
STATUS_HISTORICO = "REFERENCIA_CODIGO_NAO_AUDITADA"
STATUS_REGRA = "REGRA_CONFERIDA_COM_DESCRICAO"


def _limpar(valor):
    return str(valor or "").strip().upper()


def _parece_codigo(valor):
    """Elimina textos descritivos sem tentar completar códigos incompletos."""
    valor = _limpar(valor)
    return bool(valor and len(valor) <= 64 and not re.search(r"\\s", valor)
                and re.fullmatch(r"[A-Z0-9./_-]+", valor))


@lru_cache(maxsize=1)
def _mapa():
    resultado = {}
    try:
        with MAPA_455.open("r", encoding="utf-8-sig", newline="") as arquivo:
            for registro in csv.DictReader(arquivo, delimiter=";"):
                codigo = _limpar(registro.get("codigo_erp"))
                if codigo:
                    resultado[codigo] = registro
    except FileNotFoundError:
        # Aplicativo permanece utilizável se o catálogo estiver ausente.
        return {}
    return resultado


def sugerir_codigo(item):
    """Retorna sugestão editável, jamais conversão confirmada automaticamente."""
    original = _limpar(item.get("codigo_erp"))
    individual = _limpar(item.get("codigo_tecnico_sugerido"))
    info = _mapa().get(original, {})
    candidato_mapa = _limpar(info.get("codigo_tecnico_proposto"))
    status = info.get("situacao", "")
    tipo = info.get("tipo_provavel", "")
    candidatos = []
    if _parece_codigo(individual):
        candidatos.append(("CADASTRO", individual))
    if (status in (STATUS_HISTORICO, STATUS_REGRA)
            and tipo in ("VALVULA", "KIT") and _parece_codigo(candidato_mapa)):
        candidatos.append(("HISTORICO", candidato_mapa))
    distintos = {codigo for _, codigo in candidatos}
    if len(distintos) > 1:
        return dict(codigo_erp=original, codigo_sugerido="",
                    codigo_inicial=original,
                    situacao="CONFLITO ENTRE FONTES — conferir",
                    origem_sugestao="CONFLITO")
    if candidatos:
        origem, codigo = candidatos[0]
        return dict(codigo_erp=original, codigo_sugerido=codigo,
                    codigo_inicial=codigo,
                    situacao="SUGESTÃO NÃO VALIDADA — conferir",
                    origem_sugestao=origem)
    return dict(codigo_erp=original, codigo_sugerido="",
                codigo_inicial=original,
                situacao="SEM SUGESTÃO SEGURA — conferir",
                origem_sugestao="NENHUMA")

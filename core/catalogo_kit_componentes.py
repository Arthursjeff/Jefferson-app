"""Receitas técnicas de kit por peças; cadastro pendente, sem operação de estoque.

Uma montagem de kit pode consumir várias peças e não produzir residual.
Peças sem código ERP recebem referência temporária (REFPEND-...), sempre
marcada para identificação e bloqueada para homologação.
"""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re

from components.kits import interpretar_codigo_kit
from core.motor_transformacoes import familia, normalizar

MODOS = {
    "MONTAR_KIT": "Montar kit de reparo a partir de componentes",
    "ALTERAR_VALVULA": "Transformar válvula usando kit/carretel/componentes",
}
GRUPOS = ("G2", "G3", "G4", "G5", "OUTRO")
TIPOS = ("COMPONENTE", "CARRETEL", "KIT", "OUTRO")
STATUS_RESIDUAL = ("NAO_HA_SOBRA", "DESCARTE", "RETORNO_IDENTIFICADO")
CODIGO_RE = re.compile(r"^[A-Z0-9][A-Z0-9./_-]{1,79}$")
PENDENTE_PREFIXO = "REFPEND-"


def codigo_provisorio(grupo, descricao):
    """Identidade provisória de cadastro, NUNCA SKU ou saldo ERP."""
    s = normalizar(descricao)
    digest = hashlib.sha256((grupo + "|" + s).encode("utf-8")).hexdigest()[:14].upper()
    return f"{PENDENTE_PREFIXO}{grupo}-{digest}"


def eh_referencia_pendente(codigo):
    return normalizar(codigo).startswith(PENDENTE_PREFIXO)


def _quantidade(valor):
    try:
        q = Decimal(str(valor).replace(",", "."))
    except (InvalidOperation, ValueError):
        raise ValueError("Quantidade de componente inválida.") from None
    if not q.is_finite() or q <= 0 or q > 1000 or q.as_tuple().exponent < -3:
        raise ValueError("Quantidade deve estar entre 0,001 e 1.000, com até três casas decimais.")
    return float(q)


def _codigo(codigo, campo):
    s = normalizar(codigo)
    if not CODIGO_RE.fullmatch(s) or eh_referencia_pendente(s):
        raise ValueError(f"{campo}: informe um código válido, sem espaços, ou deixe vazio se não existir.")
    return s


def preparar_proposta_componentes(modo, produto_final, base, componentes, usuario,
                                 justificativa, residual="", destino_residual="NAO_HA_SOBRA"):
    """Monta payload 100% compatível com transformacoes_possiveis.

    Apenas proposta PENDENTE. O motor do Laboratório não homologa a composição
    física de um kit sem conferência de engenharia.
    """
    if modo not in MODOS:
        raise ValueError("Escolha montagem de kit ou transformação de válvula.")
    operador = str(usuario or "").strip().lower()
    if not operador:
        raise ValueError("Identifique o operador responsável.")
    justificativa = str(justificativa or "").strip()
    if len(justificativa) < 10 or len(justificativa) > 2000:
        raise ValueError("Informe justificativa técnica de 10 a 2.000 caracteres.")
    final = _codigo(produto_final, "Produto final")
    if modo == "MONTAR_KIT":
        kit = interpretar_codigo_kit(final)
        if not kit.get("sucesso"):
            raise ValueError("Produto final deve ser um kit Jefferson reconhecido: "
                             + str(kit.get("erro") or "código não reconhecido"))
        if normalizar(base):
            raise ValueError("Montagem de kit não usa válvula base; cadastre as peças abaixo.")
        familia_produto = kit.get("familia")
    else:
        familia_produto = familia(final)
        if not familia_produto:
            raise ValueError("Produto final deve ser uma válvula com família identificada.")
    entradas = []
    if modo == "ALTERAR_VALVULA":
        entradas.append({"papel": "BASE", "codigo": _codigo(base, "Válvula base"), "quantidade": 1})
    if not isinstance(componentes, list) or not 1 <= len(componentes) <= 25:
        raise ValueError("Informe entre 1 e 25 peças/insumos na composição.")
    detalhes = []
    faltantes = []
    for indice, item in enumerate(componentes, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Linha {indice}: dados do componente inválidos.")
        grupo = str(item.get("grupo") or "").strip().upper()
        tipo = str(item.get("tipo") or "COMPONENTE").strip().upper()
        if grupo not in GRUPOS or tipo not in TIPOS:
            raise ValueError(f"Linha {indice}: grupo ou natureza de peça inválidos.")
        descricao = str(item.get("descricao") or "").strip()
        if len(descricao) > 160:
            raise ValueError(f"Linha {indice}: descrição excede 160 caracteres.")
        codigo_erp = normalizar(item.get("codigo"))
        qtd = _quantidade(item.get("quantidade", 1))
        if codigo_erp:
            codigo = _codigo(codigo_erp, f"Linha {indice}")
        else:
            if len(descricao) < 4:
                raise ValueError(f"Linha {indice}: sem código ERP, descreva a peça (mínimo 4 caracteres).")
            codigo = codigo_provisorio(grupo, descricao)
            faltantes.append(codigo)
        papel = "KIT" if tipo == "KIT" else "CARRETEL" if tipo == "CARRETEL" else "COMPONENTE"
        entradas.append({"papel": papel, "codigo": codigo, "quantidade": qtd})
        detalhes.append({
            "grupo": grupo, "tipo": tipo, "codigo": codigo, "descricao": descricao,
            "quantidade": qtd, "sem_codigo_erp": eh_referencia_pendente(codigo),
        })
    detalhes.sort(key=lambda x: (x["grupo"], x["codigo"], x["tipo"], x["descricao"]))
    saidas = [{"papel": "PRODUTO", "codigo": final, "quantidade": 1}]
    residual = normalizar(residual)
    if destino_residual not in STATUS_RESIDUAL:
        raise ValueError("Escolha o destino dos componentes remanescentes.")
    if destino_residual == "RETORNO_IDENTIFICADO":
        saidas.append({"papel": "RESIDUAL", "codigo": _codigo(residual, "Código residual"), "quantidade": 1})
    elif residual:
        raise ValueError("Código residual informado sem selecionar Retorno identificado.")
    if modo == "ALTERAR_VALVULA" and destino_residual == "NAO_HA_SOBRA":
        # Não presumir que a troca de kit deixa a peça antiga reutilizável.
        pass
    parametros = {
        "operacao": "MONTAGEM_COMPONENTES" if modo == "MONTAR_KIT" else "ADAPTACAO_COMPONENTES",
        "metodo": "CADASTRO_MANUAL_COMPONENTES",
        "componentes": detalhes,
        "codigos_sem_erp": sorted(set(faltantes)),
        "destino_residual": destino_residual,
        "validacao_tecnica": "PENDENTE_ENGENHARIA",
        "nao_movimenta_estoque": True,
    }
    agora = datetime.now(timezone.utc).isoformat()
    assinatura = hashlib.sha256(json.dumps({
        "grau": "KIT_REPARO", "subtipo": parametros["operacao"],
        "entradas": entradas, "saidas": saidas, "parametros_tecnicos": parametros,
    }, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return {
        "assinatura": assinatura,
        "grau": "KIT_REPARO",
        "subtipo": parametros["operacao"],
        "familia": familia_produto,
        "produto_final": final,
        "entradas": entradas,
        "saidas": saidas,
        "parametros_tecnicos": parametros,
        "versao_regra": "laboratorio-componentes-kit-2026-11-v1",
        "estado": "PENDENTE",
        "origem_cadastro": "LABORATORIO_COMPONENTES_KIT",
        "registrada_por": operador,
        "validada_por": None,
        "primeira_validacao_em": None,
        "ultima_validacao_em": None,
        "total_validacoes": 0,
        "observacao": justificativa,
    }


def pode_homologar_composicao(registro):
    """Nunca homologar enquanto houver identidades temporárias de estoque."""
    if registro.get("grau") != "KIT_REPARO":
        return True, ""
    parametros = registro.get("parametros_tecnicos") or {}
    if parametros.get("metodo") != "CADASTRO_MANUAL_COMPONENTES":
        return True, ""
    temporarias = [e.get("codigo") for e in registro.get("entradas") or []
                   if eh_referencia_pendente(e.get("codigo"))]
    if temporarias or parametros.get("codigos_sem_erp"):
        return False, "Existem peças sem código ERP. Corrija a identificação antes de homologar."
    return True, ""

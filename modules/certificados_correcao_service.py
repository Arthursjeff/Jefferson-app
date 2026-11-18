"""Camada de correções técnicas homologadas para o gerador de certificados.

Não edita o motor de descrição nem dados da fila. Cada aprovação ou revogação
é um evento imutável no Supabase. A regra vigente é o evento mais recente por
(código exato, campo, tensão quando aplicável, escopo).
"""
from datetime import datetime

from core.database import supabase


TABELA = "certificados_correcoes_tecnicas"
CAMPOS_EDITAVEIS = (
    "V01", "V02", "V03", "V04", "V05", "V06", "V07",
    "V08", "V09", "V10", "V11", "V12", "V13", "V14", "V16",
)
CAMPOS_POR_TENSAO = frozenset({"V13", "V14"})


def normalizar_codigo(codigo):
    """Mesma normalização usada por processar_produto: sem espaços."""
    return str(codigo or "").strip().upper().replace(" ", "")


def chave_tensao(campo, tensao):
    """Correção de bobina/potência não pode vazar para outra tensão."""
    if campo not in CAMPOS_POR_TENSAO:
        return ""
    return "".join(str(tensao or "").upper().split())


def _indice_eventos(eventos, criar_chave):
    """Ordenados por id desc. A revogação também prevalece sobre versões antigas."""
    indice = {}
    for evento in eventos:
        chave = criar_chave(evento)
        if chave not in indice:
            indice[chave] = evento
    return indice


def carregar_correcoes(pedido_id, itens):
    """Lê apenas correções dos códigos/itens selecionados, sem histórico do ERP."""
    codigos = sorted({
        normalizar_codigo(item.get("codigo")) for item in itens
        if normalizar_codigo(item.get("codigo"))
    })
    item_ids = [item["id"] for item in itens if item.get("id") is not None]
    if not codigos or not item_ids:
        return {"permanentes": {}, "pontuais": {}, "historico": []}

    permanentes = (
        supabase.table(TABELA)
        .select("*")
        .eq("escopo", "PERMANENTE")
        .in_("codigo", codigos)
        .order("id", desc=True)
        .limit(2000)
        .execute().data or []
    )
    pontuais = (
        supabase.table(TABELA)
        .select("*")
        .eq("escopo", "PONTUAL")
        .eq("pedido_id", pedido_id)
        .in_("pedido_item_id", item_ids)
        .order("id", desc=True)
        .limit(2000)
        .execute().data or []
    )

    return {
        "permanentes": _indice_eventos(
            permanentes,
            lambda e: (e["codigo"], e["campo"], e["tensao_referencia"]),
        ),
        "pontuais": _indice_eventos(
            pontuais,
            lambda e: (
                e["pedido_item_id"], e["codigo"], e["campo"],
                e["tensao_referencia"],
            ),
        ),
        "historico": sorted(
            permanentes + pontuais,
            key=lambda e: int(e["id"]), reverse=True,
        ),
    }


def aplicar_correcoes(variaveis, item, correcoes):
    """Aplica apenas na cópia usada pelo certificado, preservando o motor original.

    A correção pontual tem prioridade sobre a permanente no mesmo pedido/item.
    Quando o evento mais recente é REVOGAR, cai para a fonte anterior.
    """
    saida = dict(variaveis or {})
    origens = {}
    codigo = normalizar_codigo(item.get("codigo"))
    tensao = item.get("tensao")
    item_id = item.get("id")
    for campo in CAMPOS_EDITAVEIS:
        chave = chave_tensao(campo, tensao)
        pontual = correcoes.get("pontuais", {}).get((item_id, codigo, campo, chave))
        permanente = correcoes.get("permanentes", {}).get((codigo, campo, chave))
        escolhido = None
        if pontual and pontual["acao"] == "APROVAR":
            escolhido = pontual
        elif permanente and permanente["acao"] == "APROVAR":
            escolhido = permanente
        if escolhido:
            saida[campo] = escolhido["valor_corrigido"]
            origens[campo] = escolhido
    return saida, origens


def registrar_correcao(*, pedido_id, item_id, codigo, campo, tensao,
                       escopo, valor_anterior, valor_corrigido,
                       justificativa, usuario, acao="APROVAR"):
    """Grava somente um novo evento, sem UPDATE/DELETE em regras anteriores."""
    codigo = normalizar_codigo(codigo)
    campo = str(campo or "").upper().strip()
    escopo = str(escopo or "").upper().strip()
    acao = str(acao or "").upper().strip()
    justificativa = str(justificativa or "").strip()
    usuario = str(usuario or "").strip().lower()
    valor_corrigido = str(valor_corrigido or "").strip()
    if (not codigo or campo not in CAMPOS_EDITAVEIS
            or escopo not in {"PONTUAL", "PERMANENTE"}
            or acao not in {"APROVAR", "REVOGAR"}):
        raise ValueError("Parâmetros da correção não são válidos.")
    if not usuario or len(justificativa) < 5:
        raise ValueError("Informe o responsável e a justificativa técnica.")
    if acao == "APROVAR" and (not valor_corrigido or len(valor_corrigido) > 500):
        raise ValueError("Informe um valor técnico válido, de até 500 caracteres.")
    if escopo == "PONTUAL" and (pedido_id is None or item_id is None):
        raise ValueError("Correção pontual exige pedido e item existentes.")
    payload = {
        "escopo": escopo,
        "pedido_id": pedido_id,
        "pedido_item_id": item_id,
        "codigo": codigo,
        "campo": campo,
        "tensao_referencia": chave_tensao(campo, tensao),
        "acao": acao,
        "valor_anterior": str(valor_anterior or "")[:500],
        "valor_corrigido": valor_corrigido if acao == "APROVAR" else "",
        "justificativa": justificativa[:2000],
        "usuario": usuario,
    }
    resposta = supabase.table(TABELA).insert(payload).execute()
    if not resposta.data:
        raise RuntimeError("Não foi possível confirmar o registro da correção.")
    return resposta.data[0]

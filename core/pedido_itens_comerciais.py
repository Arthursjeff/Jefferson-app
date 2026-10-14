"""Integração comercial da fila. Nunca altera documentos ou itens importados."""
from datetime import date
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from core.database import supabase


def numero_erp(numero, ano=None):
    texto = str(numero or "").strip()
    if "/" in texto:
        parte, sufixo = texto.rsplit("/", 1)
        return f"{parte.strip()}/{sufixo.strip()}"
    ano = int(ano if ano is not None else date.today().year % 100)
    return f"{texto}/{ano:02d}"


def buscar_orcamento(numero, ano=None):
    chave = numero_erp(numero, ano)
    limite = (date.today() - relativedelta(months=6)).isoformat()
    docs = (supabase.table("documentos_comerciais")
            .select("id,numero_erp,cliente_nome_erp,data_documento,valor_total_cabecalho")
            .eq("numero_erp", chave).gte("data_documento", limite)
            .order("data_documento", desc=True).limit(10).execute().data or [])
    if not docs:
        return None
    documento = docs[0]
    itens = (supabase.table("itens_comerciais")
             .select("id,codigo_erp,codigo_tecnico_sugerido,tensao_original,quantidade,preco_unitario,valor_total_item,ordem_item")
             .eq("documento_id", documento["id"])
             .order("ordem_item").execute().data or [])
    return {"documento": documento, "itens": itens, "candidatos": len(docs)}


def listar_itens_pedido(pedido_id):
    return (supabase.table("fila_pedido_itens").select("*")
            .eq("pedido_id", pedido_id).order("ordem").execute().data or [])


def gravar_itens_confirmados(pedido_id, itens, usuario, documento_id=None):
    """Usar somente após confirmar e criar o pedido; lança exceção em falha."""
    registros = []
    for ordem, item in enumerate(itens, 1):
        codigo = str(item.get("codigo") or "").strip()
        qtd = Decimal(str(item.get("quantidade") or "0"))
        preco = Decimal(str(item.get("valor_unitario") or "0"))
        if not codigo or qtd <= 0 or preco < 0:
            raise ValueError("Código, quantidade e valor unitário inválidos.")
        registros.append({
            "pedido_id": pedido_id, "ordem": ordem, "codigo": codigo,
            "tensao": str(item.get("tensao") or ""),
            "quantidade": str(qtd), "valor_unitario": str(preco),
            "item_comercial_id": item.get("item_comercial_id") or None,
        })
    if not registros:
        raise ValueError("Informe pelo menos um item.")
    total = sum(Decimal(r["quantidade"]) * Decimal(r["valor_unitario"]) for r in registros)
    # Não modificar o orçamento de origem.
    supabase.table("fila_pedido_itens").insert(registros).execute()
    supabase.table("fila_pedidos").update({
        "documento_comercial_id": documento_id,
        "origem_dados": "IMPORTADO" if documento_id else "MANUAL",
        "valor_total_confirmado": str(total.quantize(Decimal("0.01"))),
        "confirmado_por": usuario,
        "confirmado_em": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    }).eq("id", pedido_id).execute()
    return total

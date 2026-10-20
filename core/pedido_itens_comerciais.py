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
             .select("id,codigo_erp,codigo_tecnico_sugerido,descricao_original,tensao_original,quantidade,preco_unitario,valor_total_item,ordem_item")
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


def editar_itens_administrador(pedido_id, linhas, series_por_item, usuario):
    """Edita somente os itens da fila; nunca modifica o orçamento ERP original."""
    from modules.modulo_01.rastreabilidade import listar_series
    atuais = {str(i["id"]): i for i in listar_itens_pedido(pedido_id)}
    preparados = []
    ids_recebidos = set()
    for ordem, linha in enumerate(linhas, 1):
        ident = str(linha.get("ID") or "").strip()
        if ident and ident not in atuais:
            raise ValueError("Item não pertence ao pedido.")
        if ident and ident in ids_recebidos:
            raise ValueError("Item repetido.")
        if ident:
            ids_recebidos.add(ident)
        codigo = str(linha.get("Código") or "").strip()
        try:
            quantidade = Decimal(str(linha.get("Quantidade")))
            preco = Decimal(str(linha.get("Preço unitário")))
        except Exception:
            raise ValueError(f"Quantidade ou preço inválido para {codigo}.")
        if not codigo or quantidade <= 0 or preco < 0:
            raise ValueError("Código obrigatório, quantidade positiva e preço não negativo.")
        preparados.append((ident, {"codigo": codigo, "tensao": str(linha.get("Tensão") or ""),
                           "quantidade": str(quantidade), "valor_unitario": str(preco), "ordem": ordem}))
    if not preparados:
        raise ValueError("O pedido deve conter pelo menos um item.")
    anteriores_series = listar_series(pedido_id)
    por_item = {}
    for serie in anteriores_series:
        por_item.setdefault(str(serie["pedido_item_id"]), []).append(serie)
    for ident, dados in preparados:
        if not ident:
            continue
        registros = series_por_item.get(ident, por_item.get(ident, []))
        if not registros:
            if por_item.get(ident):
                raise ValueError(f"Rastreabilidade vazia para {dados['codigo']}.")
            continue
        total = Decimal("0")
        for registro in registros:
            try:
                qtd = Decimal(str(registro.get("quantidade")))
            except Exception:
                raise ValueError("Quantidade de série inválida.")
            if qtd <= 0:
                raise ValueError("Quantidade de série deve ser positiva.")
            if not registro.get("sem_numero") and not str(registro.get("numero_serie") or "").strip():
                raise ValueError("Número de série obrigatório ou marque Sem número.")
            total += qtd
        if any(r.get("sem_numero") for r in registros) and len(registros) != 1:
            raise ValueError("Sem número de série não pode ser misturado com outras séries.")
        if total != Decimal(dados["quantidade"]):
            raise ValueError(f"As séries de {dados['codigo']} somam {total}, mas o item tem {dados['quantidade']}.")
    # Validação integral antes de qualquer escrita.
    for ident, dados in preparados:
        if ident:
            supabase.table("fila_pedido_itens").update(dados).eq("id", ident).eq("pedido_id", pedido_id).execute()
        else:
            supabase.table("fila_pedido_itens").insert({"pedido_id": pedido_id, **dados}).execute()
    for ident, dados in preparados:
        if not ident or ident not in series_por_item:
            continue
        supabase.table("fila_pedido_series").delete().eq("pedido_item_id", ident).execute()
        registros = series_por_item[ident]
        if registros:
            supabase.table("fila_pedido_series").insert([{
                "pedido_item_id": ident, "numero_serie": None if r.get("sem_numero") else str(r["numero_serie"]).strip(),
                "quantidade": str(r["quantidade"]), "sem_numero": bool(r.get("sem_numero")),
                "registrado_por": usuario,
            } for r in registros]).execute()
    for ident in set(atuais) - ids_recebidos:
        supabase.table("fila_pedido_series").delete().eq("pedido_item_id", ident).execute()
        supabase.table("fila_pedido_itens").delete().eq("id", ident).eq("pedido_id", pedido_id).execute()
    total = sum(Decimal(d["quantidade"]) * Decimal(d["valor_unitario"]) for _, d in preparados)
    supabase.table("fila_pedidos").update({"valor_total_confirmado": str(total.quantize(Decimal("0.01"))) }).eq("id", pedido_id).execute()
    return total

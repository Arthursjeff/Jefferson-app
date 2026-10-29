"""Rastreabilidade dos itens antes de entrar em Montados."""
from decimal import Decimal
from core.database import supabase
from core.pedido_itens_comerciais import listar_itens_pedido

def listar_series(pedido_id, itens=None):
    if itens is None:
        itens = listar_itens_pedido(pedido_id)
    if not itens:
        return []
    ids = [i["id"] for i in itens]
    return (supabase.table("fila_pedido_series").select("*")
            .in_("pedido_item_id", ids).order("id").execute().data or [])


def consultar_rastreabilidade_pedidos(pedido_ids):
    """Consulta em lote os itens e suas séries para o histórico de pedidos.

    Somente lê os dados já cadastrados, sem criar/alterar rastreabilidade.
    Cada série gera uma linha com sua própria quantidade; itens sem série
    registrada continuam visíveis como "Não registrado".
    """
    ids = list(dict.fromkeys(pedido_ids))
    if not ids:
        return {}

    itens = []
    for inicio in range(0, len(ids), 200):
        lote = ids[inicio:inicio + 200]
        itens.extend(
            supabase.table("fila_pedido_itens")
            .select("id,pedido_id,ordem,codigo,tensao,quantidade")
            .in_("pedido_id", lote)
            .order("ordem")
            .execute().data or []
        )

    series_por_item = {}
    ids_itens = [item["id"] for item in itens]
    for inicio in range(0, len(ids_itens), 200):
        lote = ids_itens[inicio:inicio + 200]
        registros = (
            supabase.table("fila_pedido_series")
            .select("pedido_item_id,numero_serie,quantidade,sem_numero")
            .in_("pedido_item_id", lote)
            .order("id")
            .execute().data or []
        )
        for registro in registros:
            series_por_item.setdefault(registro["pedido_item_id"], []).append(registro)

    resultado = {pedido_id: [] for pedido_id in ids}
    for item in itens:
        base = {
            "Código": item.get("codigo") or "-",
            "Tensão": item.get("tensao") or "-",
            "Qtd. item": item.get("quantidade"),
        }
        registros = series_por_item.get(item["id"], [])
        if not registros:
            resultado[item["pedido_id"]].append({
                **base, "Número de série": "Não registrado", "Qtd. série": "-",
            })
            continue
        for registro in registros:
            serie = ("Sem número de série" if registro.get("sem_numero")
                     else str(registro.get("numero_serie") or "").strip() or "Não registrado")
            resultado[item["pedido_id"]].append({
                **base, "Número de série": serie,
                "Qtd. série": registro.get("quantidade"),
            })
    return resultado


def validar_rastreabilidade(pedido_id, entradas=None):
    itens = listar_itens_pedido(pedido_id)
    if not itens:
        return True, "Pedido legado sem itens cadastrados."
    if entradas is None:
        series = listar_series(pedido_id)
        entradas = {}
        for registro in series:
            entradas.setdefault(registro["pedido_item_id"], []).append(registro)
    for item in itens:
        linhas = entradas.get(item["id"], [])
        if not linhas:
            return False, f"Informe a rastreabilidade do item {item['codigo']}."
        sem = [x for x in linhas if x.get("sem_numero")]
        if sem and (len(linhas) != 1 or not sem[0].get("sem_numero")):
            return False, f"Marcação sem série inconsistente: {item['codigo']}."
        total = Decimal("0")
        for linha in linhas:
            try:
                quantidade = Decimal(str(linha.get("quantidade") or 0))
            except Exception:
                return False, f"Quantidade inválida: {item['codigo']}."
            if quantidade <= 0:
                return False, f"Quantidade inválida: {item['codigo']}."
            if not linha.get("sem_numero") and not str(linha.get("numero_serie") or "").strip():
                return False, f"Número de série obrigatório: {item['codigo']}."
            total += quantidade
        if total != Decimal(str(item["quantidade"])):
            return False, f"A soma das quantidades de {item['codigo']} deve ser {item['quantidade']}."
    return True, "Rastreabilidade completa."

def salvar_rastreabilidade(pedido_id, entradas, usuario):
    valido, mensagem = validar_rastreabilidade(pedido_id, entradas)
    if not valido:
        return False, mensagem
    itens = listar_itens_pedido(pedido_id)
    if not itens:
        return True, "Pedido legado sem itens; nenhuma série exigida."
    ids = [i["id"] for i in itens]
    registros = []
    for item in itens:
        for linha in entradas[item["id"]]:
            sem = bool(linha.get("sem_numero"))
            registros.append({
                "pedido_item_id": item["id"],
                "numero_serie": None if sem else str(linha["numero_serie"]).strip(),
                "quantidade": str(linha["quantidade"]),
                "sem_numero": sem,
                "registrado_por": usuario,
            })
    # Substitui a rastreabilidade somente depois da validação integral.
    anterior = listar_series(pedido_id)
    supabase.table("fila_pedido_series").delete().in_("pedido_item_id", ids).execute()
    try:
        supabase.table("fila_pedido_series").insert(registros).execute()
    except Exception:
        if anterior:
            supabase.table("fila_pedido_series").insert([
                {k: v for k, v in x.items() if k not in ("id", "registrado_em")}
                for x in anterior]).execute()
        raise
    return True, "Rastreabilidade registrada."

def interface_rastreabilidade(pedido):
    import streamlit as st
    itens = listar_itens_pedido(pedido["id"])
    if not itens:
        st.info("Pedido anterior ao cadastro de itens: rastreabilidade dispensada.")
        return {}
    salvos = listar_series(pedido["id"])
    agrupados = {}
    for linha in salvos:
        agrupados.setdefault(linha["pedido_item_id"], []).append(linha)
    entradas = {}
    st.markdown("#### Números de série por item")
    for item in itens:
        ident = item["id"]
        st.markdown(f"**{item['codigo']}** — Quantidade: {item['quantidade']}")
        existentes = agrupados.get(ident, [])
        sem_inicial = bool(existentes and existentes[0]["sem_numero"])
        sem = st.checkbox("Sem número de série", value=sem_inicial, key=f"serie_sem_{pedido['id']}_{ident}")
        if sem:
            entradas[ident] = [{"sem_numero": True, "numero_serie": None, "quantidade": item["quantidade"]}]
        else:
            iniciais = [
                {"Número de série": x["numero_serie"] or "", "Quantidade": float(x["quantidade"])}
                for x in existentes if not x["sem_numero"]
            ] or [{"Número de série": "", "Quantidade": float(item["quantidade"])}]
            linhas = st.data_editor(iniciais, num_rows="dynamic", hide_index=True,
                                    use_container_width=True, key=f"serie_editor_{pedido['id']}_{ident}")
            entradas[ident] = [
                {"sem_numero": False, "numero_serie": x.get("Número de série"),
                 "quantidade": x.get("Quantidade")}
                for x in (linhas.to_dict("records") if hasattr(linhas, "to_dict") else linhas)]
    return entradas

def exibir_series_card(pedido, itens=None):
    import streamlit as st
    with st.expander("Rastreabilidade / números de série"):
        try:
            if itens is None:
                itens = listar_itens_pedido(pedido["id"])
            series = listar_series(pedido["id"], itens=itens)
            itens = {i["id"]: i for i in itens}
            if not series:
                st.caption("Nenhum número de série registrado.")
            else:
                st.dataframe([{
                    "Código": itens.get(s["pedido_item_id"], {}).get("codigo", ""),
                    "Número de série": "Sem número" if s["sem_numero"] else s["numero_serie"],
                    "Quantidade": s["quantidade"], "Registrado por": s["registrado_por"],
                    "Registrado em": s["registrado_em"],
                } for s in series], hide_index=True, use_container_width=True)
        except Exception as exc:
            st.warning(f"Erro ao consultar rastreabilidade: {exc}")

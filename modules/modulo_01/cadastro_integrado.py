import streamlit as st
from datetime import date
from decimal import Decimal
from core.database import supabase
from core.conversor_erp_pedido import sugerir_codigo
from core.pedido_itens_comerciais import numero_erp, buscar_orcamento, gravar_itens_confirmados, listar_itens_pedido
from core.permissions import pode_criar_pedido
from core.pedidos import criar_pedido
from core.notificacoes import criar_notificacao_para_setor

def pagina_cadastro_integrado():
    st.title("➕ Criar Pedido")
    if not pode_criar_pedido(st.session_state.setor):
        st.error("Sem permissão para criar pedidos.")
        return
    c1, c2 = st.columns([4, 1])
    with c1:
        numero = st.text_input("Número ERP", key="erp_numero")
    with c2:
        ano = st.number_input("Ano", min_value=0, max_value=99, value=date.today().year % 100, key="erp_ano")
    chave = numero_erp(numero, ano) if numero.strip() else ""
    st.caption("Número completo: " + (chave or "—"))
    if st.button("Buscar orçamento", disabled=not bool(chave)):
        try:
            achado = buscar_orcamento(numero, ano)
            st.session_state["erp_resultado"] = achado
            st.session_state["erp_chave"] = chave
            st.session_state["erp_cliente"] = achado["documento"].get("cliente_nome_erp") or "" if achado else ""
            st.session_state["erp_itens"] = [
                {"ID origem": str(i.get("id") or ""),
                 "Código ERP (original)": sugerir_codigo(i)["codigo_erp"],
                 "Código sugerido": sugerir_codigo(i)["codigo_sugerido"],
                 "Situação": sugerir_codigo(i)["situacao"],
                 "Código": sugerir_codigo(i)["codigo_inicial"],
                 "Tensão": i.get("tensao_original") or "",
                 "Quantidade": float(i.get("quantidade") or 0),
                 "Valor unitário": float(i.get("preco_unitario") or 0)}
                for i in (achado["itens"] if achado else [])]
            st.session_state["erp_versao"] = st.session_state.get("erp_versao", 0) + 1
        except Exception as exc:
            st.error(f"Erro ao consultar orçamento: {exc}")
    if not chave or st.session_state.get("erp_chave") != chave:
        st.info("Clique em Buscar orçamento para continuar.")
        return
    achado = st.session_state.get("erp_resultado")
    if achado:
        st.success("Orçamento localizado. Confira todos os dados.")
        if achado.get("candidatos", 0) > 1:
            st.warning("Mais de um documento localizado; foi selecionado o mais recente.")
    else:
        st.warning("Não localizado nos últimos seis meses. Cadastro manual disponível.")
    cliente = st.text_input("Cliente", key="erp_cliente")
    origem = st.session_state.get("erp_itens") or [{"Código": "", "Tensão": "", "Quantidade": 1.0, "Valor unitário": 0.0}]
    editados = st.data_editor(origem, num_rows="dynamic", hide_index=True, use_container_width=True,
                              disabled=["ID origem", "Código ERP (original)", "Código sugerido", "Situação"],
                              column_config={"ID origem": None},
                              key="erp_editor_" + str(st.session_state.get("erp_versao", 0)))
    linhas = editados.to_dict("records") if hasattr(editados, "to_dict") else editados
    itens = []
    ids_validos = {str(i.get("id")) for i in (achado["itens"] if achado else []) if i.get("id") is not None}
    for i, linha in enumerate(linhas):
        identificador = str(linha.get("ID origem") or "")
        referencia = identificador if identificador in ids_validos else None
        itens.append({"codigo": linha.get("Código"), "tensao": linha.get("Tensão"),
                      "quantidade": linha.get("Quantidade"), "valor_unitario": linha.get("Valor unitário"),
                      "item_comercial_id": referencia})
    try:
        total = sum(Decimal(str(x["quantidade"])) * Decimal(str(x["valor_unitario"])) for x in itens)
        st.metric("Total confirmado", "R$ " + f"{total:,.2f}")
    except Exception:
        st.warning("Revise as quantidades e valores.")
    tipo = st.selectbox("Tipo do pedido", ["NORMAL", "PROGRAMADO", "IMPORTACAO"])
    previsao = st.date_input("Data prevista de faturamento")
    st.caption("Os códigos técnicos são apenas sugestões não auditadas. Confira cada linha antes de confirmar.")
    confirmado = st.checkbox("Confirmei o cliente, os códigos, tensões, quantidades e valores.")
    if st.button("Criar pedido", type="primary", disabled=not confirmado):
        try:
            if not cliente.strip() or not itens:
                raise ValueError("Informe cliente e itens.")
            for item in itens:
                if not str(item["codigo"] or "").strip() or Decimal(str(item["quantidade"])) <= 0 or Decimal(str(item["valor_unitario"])) < 0:
                    raise ValueError("Código, quantidade ou valor inválido.")
            duplicado = (supabase.table("fila_pedidos").select("id")
                         .eq("numero_pedido", chave).neq("status", "CANCELADO").limit(1).execute().data)
            if duplicado:
                raise ValueError("Já existe um pedido não cancelado com esse número.")
            pedido = criar_pedido(chave, cliente, st.session_state.nome, tipo, str(previsao))
            if not pedido:
                raise RuntimeError("Não foi possível criar o card.")
            try:
                gravar_itens_confirmados(pedido["id"], itens, st.session_state.nome,
                                        achado["documento"]["id"] if achado else None)
            except Exception:
                supabase.table("fila_pedido_itens").delete().eq("pedido_id", pedido["id"]).execute()
                supabase.table("fila_movimentacoes").delete().eq("pedido_id", pedido["id"]).execute()
                supabase.table("fila_pedidos").delete().eq("id", pedido["id"]).execute()
                raise
            try:
                criar_notificacao_para_setor(pedido_id=pedido["id"], setor_destino="MONTAGEM",
                                            tipo="NOVO_PEDIDO", mensagem=f"Novo pedido criado: {chave} - {cliente}")
            except Exception:
                st.warning("Pedido criado, mas a notificação não foi enviada.")
            for k in ("erp_resultado", "erp_chave", "erp_cliente", "erp_itens", "erp_numero"):
                st.session_state.pop(k, None)
            st.success("Pedido criado com itens confirmados.")
            st.rerun()
        except Exception as exc:
            st.error(f"Não foi possível criar o pedido: {exc}")

def mostrar_itens_do_card(pedido):
    with st.expander("📦 Itens do pedido"):
        try:
            itens = listar_itens_pedido(pedido["id"])
            if not itens:
                st.caption("Pedido sem itens cadastrados.")
                return
            st.dataframe([{"Código": i["codigo"], "Tensão": i["tensao"], "Quantidade": i["quantidade"],
                           "Valor unitário": i["valor_unitario"], "Valor total": i["valor_total"]}
                          for i in itens], hide_index=True, use_container_width=True)
            st.caption("Valor total confirmado: R$ " + f"{float(pedido.get('valor_total_confirmado') or 0):,.2f}")
        except Exception as exc:
            st.warning(f"Não foi possível consultar os itens: {exc}")

"""Investigações aprofundadas do histórico ERP; somente leitura."""
from datetime import date
from io import BytesIO
import pandas as pd
import streamlit as st
import altair as alt


def brl(x):
    return "R$ " + f"{float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def excel(df, nome):
    b = BytesIO()
    with pd.ExcelWriter(b, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Estudo")
    st.download_button("Exportar estudo completo", b.getvalue(), file_name=nome,
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       key="adv_" + nome)


def pagina_aprofundada(docs, carregar_itens):
    st.subheader("Investigação aprofundada")
    st.caption("Investigue um cliente no histórico, sua frequência de compras e quais produtos explicam variações.")
    if docs.empty:
        st.info("Sem faturamentos no histórico.")
        return
    nomes = sorted(docs["cliente"].dropna().unique())
    cliente = st.selectbox("Cliente", nomes, key="adv_cliente")
    base = docs.loc[docs["cliente"] == cliente].copy()
    base["ano"] = base["data"].dt.year
    historico = base.groupby("ano").agg(
        Faturamento=("valor", "sum"), Documentos=("id", "nunique"),
        Ultima_compra=("data", "max")).reset_index()
    historico["Ticket médio"] = historico["Faturamento"] / historico["Documentos"].clip(lower=1)
    historico["Variação anual (%)"] = historico["Faturamento"].pct_change() * 100
    st.markdown("#### Histórico anual")
    st.dataframe(historico.style.format({"Faturamento": brl, "Ticket médio": brl,
        "Variação anual (%)": lambda v: "—" if pd.isna(v) else f"{v:+.1f}%"}),
        use_container_width=True, hide_index=True)
    chart = historico.copy()
    chart["Valor exibido"] = chart["Faturamento"].map(brl)
    st.altair_chart(alt.Chart(chart).mark_bar().encode(
        x=alt.X("ano:O", title="Ano"), y=alt.Y("Faturamento:Q", title="Faturamento (R$)"),
        tooltip=["ano:O", alt.Tooltip("Valor exibido:N", title="Faturamento")]).properties(height=280),
        use_container_width=True)
    compras = base.dropna(subset=["data"]).sort_values("data")["data"].drop_duplicates()
    intervalos = compras.diff().dt.days.dropna()
    c1,c2,c3 = st.columns(3)
    c1.metric("Último faturamento", compras.max().strftime("%d/%m/%Y") if len(compras) else "—")
    c2.metric("Intervalo médio entre dias com compra", f"{intervalos.mean():.0f} dias" if len(intervalos) else "—")
    c3.metric("Dias desde última compra", f"{(pd.Timestamp(date.today())-compras.max()).days}" if len(compras) else "—")
    st.caption("A frequência considera dias distintos com faturamento, não número de linhas ou pedidos.")
    excel(historico, "historico_cliente.xlsx")

    st.markdown("#### Investigar mudança por código ou família")
    anos = sorted(int(x) for x in base["ano"].dropna().unique())
    if len(anos) < 2:
        st.info("Este cliente precisa ter faturamentos em pelo menos dois anos para comparar produtos.")
        return
    a,b = st.columns(2)
    with a:
        ano_a = st.selectbox("Ano de referência", anos, index=max(0,len(anos)-2), key="adv_ano_a")
    with b:
        ano_b = st.selectbox("Ano de comparação", anos, index=len(anos)-1, key="adv_ano_b")
    if ano_a == ano_b:
        st.info("Selecione anos diferentes.")
        return
    recorte = base[base["ano"].isin([ano_a, ano_b])]
    ids = tuple(recorte["id"].dropna().astype(str).unique())
    st.caption(f"Consulta sob demanda de itens vinculados a {len(ids)} documentos. O valor dos itens pode diferir do faturamento do cabeçalho.")
    if st.button("Analisar produtos deste cliente", key="adv_rodar"):
        st.session_state["adv_consulta"] = (cliente,ano_a,ano_b)
    if st.session_state.get("adv_consulta") != (cliente,ano_a,ano_b):
        return
    with st.spinner("Carregando itens dos dois anos..."):
        itens = carregar_itens(ids)
    if itens.empty:
        st.info("Sem itens vinculados a esses documentos.")
        return
    mapa = recorte.set_index("id")["ano"]
    itens = itens.copy()
    itens["ano"] = itens["documento_id"].map(mapa)
    dimensao = st.radio("Detalhar por", ["Código ERP", "Família"], horizontal=True, key="adv_dim")
    campo = "codigo_erp" if dimensao == "Código ERP" else "familia_sugerida"
    medida = st.radio("Métrica", ["Valor dos itens", "Quantidade"], horizontal=True, key="adv_med")
    valor = "valor_total_item" if medida == "Valor dos itens" else "quantidade"
    p = itens.pivot_table(index=campo, columns="ano", values=valor, aggfunc="sum", fill_value=0)
    p = p.reindex(columns=[ano_a,ano_b], fill_value=0)
    p.columns = ["Referência", "Comparação"]
    p["Diferença"] = p["Comparação"]-p["Referência"]
    p["Variação (%)"] = 100*p["Diferença"]/p["Referência"].replace(0,float("nan"))
    p["Situação"] = "Continua"
    p.loc[(p["Referência"]>0)&(p["Comparação"]==0),"Situação"] = "Sem compra no ano B"
    p.loc[(p["Referência"]==0)&(p["Comparação"]>0),"Situação"] = "Novo no ano B"
    tabela = p.reset_index().sort_values("Diferença")
    ordem = st.radio("Ordenar", ["Maiores perdas", "Maiores ganhos"], horizontal=True, key="adv_ordem")
    tabela = tabela.sort_values("Diferença", ascending=ordem=="Maiores perdas")
    limite = st.selectbox("Exibir", [10,20,50,100,100000], key="adv_limite",
                          format_func=lambda n:"Todos" if n==100000 else f"Top {n}")
    mostrado = tabela.head(limite)
    if medida == "Valor dos itens":
        st.dataframe(mostrado.style.format({"Referência":brl,"Comparação":brl,"Diferença":brl,
            "Variação (%)":lambda x:"—" if pd.isna(x) else f"{x:+.1f}%"}), hide_index=True, use_container_width=True)
    else:
        st.dataframe(mostrado, hide_index=True, use_container_width=True)
    excel(tabela,"comparativo_produtos_cliente.xlsx")
    if ano_b == date.today().year:
        st.warning("O ano B ainda está em andamento. Compare também períodos equivalentes antes de concluir que houve perda.")

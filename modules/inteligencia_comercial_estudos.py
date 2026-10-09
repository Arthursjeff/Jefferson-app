"""Comparador de períodos e estudos comerciais. Não altera dados do ERP."""
from datetime import date, timedelta
import pandas as pd
import streamlit as st
import altair as alt


def _brl(v):
    return "R$ " + f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _base(docs, inicio, fim, clientes=None):
    x = docs.loc[docs["data"].between(pd.Timestamp(inicio), pd.Timestamp(fim))].copy()
    if clientes:
        x = x[x["cliente"].isin(clientes)]
    return x


def _metricas(df):
    return {"Faturamento": float(df["valor"].sum()), "Documentos": int(df["id"].nunique()),
            "Clientes ativos": int(df["cliente"].nunique()),
            "Ticket médio": float(df["valor"].sum() / max(df["id"].nunique(), 1))}


def _quadro_comparativo(a, b, dimensao, metrica):
    def agg(x):
        g = x.groupby(dimensao, dropna=False)
        if metrica == "Faturamento":
            return g["valor"].sum()
        if metrica == "Documentos":
            return g["id"].nunique()
        return g["cliente"].nunique()
    resultado = pd.concat([agg(a).rename("Período A"), agg(b).rename("Período B")], axis=1).fillna(0)
    resultado["Diferença"] = resultado["Período B"] - resultado["Período A"]
    resultado["Variação (%)"] = (resultado["Diferença"] / resultado["Período A"].replace(0, float("nan")) * 100).round(2)
    resultado["Situação"] = resultado.apply(lambda r: "Novo" if r["Período A"] == 0 and r["Período B"] > 0
                                           else ("Sem movimento" if r["Período A"] == 0 else
                                                 ("Perda total" if r["Período B"] == 0 else "Comparável")), axis=1)
    return resultado.reset_index().sort_values("Diferença")


def _grafico_linhas(a, b, metrica, nomes):
    def mensal(df, nome):
        if df.empty:
            return pd.DataFrame(columns=["Mês", "Valor", "Período"])
        x = df.copy()
        x["Mês"] = x["data"].dt.month
        if metrica == "Faturamento":
            s = x.groupby("Mês")["valor"].sum()
        elif metrica == "Documentos":
            s = x.groupby("Mês")["id"].nunique()
        else:
            s = x.groupby("Mês")["cliente"].nunique()
        out = s.rename("Valor").reset_index()
        out["Período"] = nome
        return out
    dados = pd.concat([mensal(a, nomes[0]), mensal(b, nomes[1])], ignore_index=True)
    if dados.empty:
        return
    dados["Exibição"] = dados["Valor"].map(_brl if metrica == "Faturamento" else lambda v: str(int(v)))
    grafico = alt.Chart(dados).mark_line(point=True).encode(
        x=alt.X("Mês:O", sort=list(range(1, 13))),
        y=alt.Y("Valor:Q", title="R$" if metrica == "Faturamento" else metrica),
        color="Período:N",
        tooltip=["Período:N", "Mês:O", alt.Tooltip("Exibição:N", title=metrica)])
    st.altair_chart(grafico.properties(height=360), use_container_width=True)


def _download(df, nome):
    from io import BytesIO
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Comparativo")
    st.download_button("Exportar análise em Excel", buffer.getvalue(), file_name=nome,
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       key="ic_export_" + nome)


def pagina_comparador(docs, carregar_itens=None):
    st.subheader("Comparador de períodos")
    st.caption("Compare dois intervalos independentes. Os valores são nominais e a SUDAMERICANA já foi excluída na origem.")
    hoje = date.today()
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Período A (referência)**")
        a_inicio = st.date_input("Início A", date(2024, 1, 1), key="cmp_ai")
        a_fim = st.date_input("Fim A", date(2024, 12, 31), key="cmp_af")
    with c2:
        st.markdown("**Período B (comparação)**")
        b_inicio = st.date_input("Início B", date(2025, 1, 1), key="cmp_bi")
        b_fim = st.date_input("Fim B", date(2025, 12, 31), key="cmp_bf")
    if a_inicio > a_fim or b_inicio > b_fim:
        st.error("Corrija as datas: o início não pode superar o fim.")
        return
    if max(a_fim, b_fim) > hoje:
        st.warning("Há datas futuras no comparativo; os resultados podem estar incompletos.")
    equivalente = st.checkbox("Igualar duração dos períodos para comparação justa", value=True, key="cmp_equivalente")
    if equivalente:
        dias = min((a_fim-a_inicio).days, (b_fim-b_inicio).days,
                   (hoje-a_inicio).days, (hoje-b_inicio).days)
        if dias < 0:
            st.warning("Um período ainda não começou. Ajuste as datas.")
            return
        a_fim_efetivo = a_inicio + timedelta(days=dias)
        b_fim_efetivo = b_inicio + timedelta(days=dias)
        st.caption(f"Períodos efetivos: {a_inicio:%d/%m/%Y} a {a_fim_efetivo:%d/%m/%Y} × {b_inicio:%d/%m/%Y} a {b_fim_efetivo:%d/%m/%Y} ({dias+1} dias cada).")
    else:
        a_fim_efetivo, b_fim_efetivo = a_fim, b_fim
        if (a_fim-a_inicio).days != (b_fim-b_inicio).days:
            st.warning("Comparação de durações diferentes: percentuais podem refletir a diferença de tempo, não desempenho.")

    clientes = st.multiselect("Clientes específicos (vazio = todos)", sorted(docs["cliente"].dropna().unique()), key="cmp_clientes")
    a = _base(docs, a_inicio, a_fim_efetivo, clientes)
    b = _base(docs, b_inicio, b_fim_efetivo, clientes)
    metrica = st.selectbox("Indicador", ["Faturamento", "Documentos", "Clientes ativos", "Ticket médio"], key="cmp_metrica")
    ma, mb = _metricas(a)[metrica], _metricas(b)[metrica]
    delta = mb - ma
    pct = delta / ma * 100 if ma else None
    cols = st.columns(3)
    fmt = _brl if metrica in ("Faturamento", "Ticket médio") else lambda v: f"{v:,.0f}".replace(",", ".")
    cols[0].metric("Período A", fmt(ma))
    cols[1].metric("Período B", fmt(mb))
    cols[2].metric("Diferença B − A", fmt(delta), delta=f"{pct:+.1f}%" if pct is not None else "Sem base percentual")
    if metrica != "Ticket médio":
        _grafico_linhas(a, b, metrica, (f"A: {a_inicio} a {a_fim_efetivo}", f"B: {b_inicio} a {b_fim_efetivo}"))
    else:
        st.caption("Ticket médio é calculado por valor de cabeçalho dividido por documentos distintos.")
    st.markdown("#### Quem explica a diferença?")
    dimensao = st.selectbox("Detalhar por", ["Cliente", "Mês", "Ano"], key="cmp_dimensao")
    detalhe_metrica = metrica if metrica not in ("Ticket médio",) else "Faturamento"
    aa, bb = a.copy(), b.copy()
    if dimensao == "Cliente":
        coluna = "cliente"
    elif dimensao == "Mês":
        coluna = "mes"
        aa[coluna], bb[coluna] = aa["data"].dt.month, bb["data"].dt.month
    else:
        coluna = "ano"
        aa[coluna], bb[coluna] = aa["data"].dt.year, bb["data"].dt.year
    tabela = _quadro_comparativo(aa, bb, coluna, detalhe_metrica)
    ordem = st.radio("Ordenar por", ["Maiores perdas", "Maiores ganhos"], horizontal=True, key="cmp_ordem")
    tabela = tabela.sort_values("Diferença", ascending=ordem == "Maiores perdas")
    limite = st.selectbox("Exibir", [10, 20, 50, 100, 100000], index=1, key="cmp_top",
                          format_func=lambda n: "Todos" if n == 100000 else f"Top {n}")
    exibida = tabela.head(limite)
    if detalhe_metrica == "Faturamento":
        st.dataframe(exibida.style.format({"Período A": _brl, "Período B": _brl, "Diferença": _brl,
                                           "Variação (%)": lambda v: "—" if pd.isna(v) else f"{v:+.1f}%"}),
                     hide_index=True, use_container_width=True)
    else:
        st.dataframe(exibida, hide_index=True, use_container_width=True)
    _download(tabela, "comparativo_comercial.xlsx")


def pagina_estudos(docs):
    st.subheader("Estudos investigativos")
    st.caption("Investigue mudanças de comportamento de compra por cliente, com referência temporal configurável.")
    c1, c2 = st.columns(2)
    with c1:
        referencia = st.date_input("Início do período de referência", date(2024, 1, 1), key="inv_ri")
        referencia_fim = st.date_input("Fim do período de referência", date(2024, 12, 31), key="inv_rf")
    with c2:
        atual = st.date_input("Início do período analisado", date(2025, 1, 1), key="inv_ai")
        atual_fim = st.date_input("Fim do período analisado", date(2025, 12, 31), key="inv_af")
    if referencia > referencia_fim or atual > atual_fim:
        st.warning("Corrija os intervalos.")
        return
    if (referencia_fim-referencia).days != (atual_fim-atual).days:
        st.warning("Os períodos de investigação têm durações diferentes. A classificação de perda ou queda pode ser enganosa.")
    if st.button("Executar investigação", type="primary", key="inv_executar"):
        a = _base(docs, referencia, referencia_fim)
        b = _base(docs, atual, atual_fim)
        t = _quadro_comparativo(a, b, "cliente", "Faturamento")
        st.session_state["inv_resultado"] = t
        st.session_state["inv_datas"] = (referencia, referencia_fim, atual, atual_fim)
    if st.session_state.get("inv_datas") != (referencia, referencia_fim, atual, atual_fim):
        st.info("Execute a investigação para os períodos selecionados.")
        return
    t = st.session_state.get("inv_resultado")
    if t is None:
        return
    perdidos = t[(t["Período A"] > 0) & (t["Período B"] == 0)]
    reduziram = t[(t["Período A"] > 0) & (t["Período B"] > 0) & (t["Diferença"] < 0)]
    novos = t[(t["Período A"] == 0) & (t["Período B"] > 0)]
    k = st.columns(4)
    k[0].metric("Clientes sem recompra", len(perdidos))
    k[1].metric("Clientes em queda", len(reduziram))
    k[2].metric("Clientes novos/reativados", len(novos))
    k[3].metric("Redução entre clientes em queda", _brl(-reduziram["Diferença"].sum()))
    categoria = st.selectbox("Estudo", ["Sem recompra", "Em queda", "Novos/reativados", "Todos"], key="inv_categoria")
    recorte = {"Sem recompra": perdidos, "Em queda": reduziram, "Novos/reativados": novos, "Todos": t}[categoria]
    st.dataframe(recorte.sort_values("Diferença").style.format({
        "Período A": _brl, "Período B": _brl, "Diferença": _brl,
        "Variação (%)": lambda v: "—" if pd.isna(v) else f"{v:+.1f}%"}),
        hide_index=True, use_container_width=True)
    st.caption("Sem recompra significa ausência de faturamento no período B, não necessariamente perda definitiva. Novos/reativados podem ter comprado antes do período A.")
    _download(recorte, "estudo_clientes.xlsx")

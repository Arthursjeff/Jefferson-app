"""Índice de faturamento sobre registros comerciais do ERP (P, E, F)."""
from datetime import date
import pandas as pd
import streamlit as st
import altair as alt
from core.database import supabase

@st.cache_data(ttl=600, show_spinner=False)
def carregar_movimentos(inicio, fim):
    registros = []
    offset = 0
    while True:
        lote = (supabase.table("documentos_comerciais")
                .select("id,situacao_erp,data_documento,cliente_nome_erp")
                .in_("situacao_erp", ["P", "E", "F"])
                .gte("data_documento", inicio).lte("data_documento", fim)
                .order("id").range(offset, offset + 999).execute().data or [])
        registros.extend(lote)
        if len(lote) < 1000:
            break
        offset += 1000
    df = pd.DataFrame(registros)
    if df.empty:
        return df
    from modules.inteligencia_comercial import _cliente_ficticio
    df["cliente"] = df["cliente_nome_erp"].fillna("Sem identificação").astype(str).str.strip()
    df = df.loc[~df["cliente"].map(_cliente_ficticio)].copy()
    df["data"] = pd.to_datetime(df["data_documento"], errors="coerce")
    return df

def _resumo(df, dimensao):
    t = (df.groupby([dimensao, "situacao_erp"])["id"].nunique().unstack(fill_value=0)
         .reindex(columns=["P", "E", "F"], fill_value=0))
    t = t.rename(columns={"P": "Orçamentos", "E": "Pedidos", "F": "Faturados"})
    t["Total de registros"] = t[["Orçamentos", "Pedidos", "Faturados"]].sum(axis=1)
    t["Índice (%)"] = (100 * t["Faturados"] / t["Total de registros"].replace(0, float("nan"))).round(2)
    return t.reset_index()

def pagina_conversao():
    st.subheader("Índice de faturamento comercial")
    st.caption("Participação dos documentos faturados entre orçamentos (P), pedidos (E) e faturamentos (F). Não é taxa de conversão de oportunidades: uma mesma negociação pode gerar registros em múltiplas etapas.")
    c1,c2 = st.columns(2)
    with c1:
        periodo = st.date_input("Período (data do documento)", (date(2024,1,1), date.today()), key="ic_conv_datas")
    with c2:
        dimensao = st.selectbox("Agrupar por", ["Mês", "Ano", "Cliente"], key="ic_conv_dim")
    if not isinstance(periodo, (list, tuple)) or len(periodo) != 2:
        st.info("Selecione as duas datas.")
        return
    inicio, fim = periodo
    if inicio > fim:
        st.warning("O início deve ser anterior ao fim.")
        return
    with st.spinner("Consultando orçamentos, pedidos e faturamentos..."):
        df = carregar_movimentos(inicio.isoformat(), fim.isoformat())
    if df.empty:
        st.info("Não há registros P, E ou F com data do documento no intervalo.")
        return
    clientes = st.multiselect("Filtrar clientes (vazio = todos)", sorted(df["cliente"].unique()), key="ic_conv_clientes")
    if clientes:
        df = df[df["cliente"].isin(clientes)]
    if df.empty:
        st.info("Nenhum registro nos filtros.")
        return
    n = df.groupby("situacao_erp")["id"].nunique()
    p, e, f = (int(n.get(x, 0)) for x in ("P", "E", "F"))
    total = p + e + f
    cols = st.columns(5)
    for col, titulo, valor in zip(cols, ["Orçamentos", "Pedidos", "Faturados", "Total de registros", "Índice de faturamento"], [p,e,f,total, f"{f/total*100:.2f}%".replace(".", ",") if total else "—"]):
        col.metric(titulo, valor)
    base = df.copy()
    if dimensao == "Mês":
        base["categoria"] = base["data"].dt.to_period("M").astype(str)
    elif dimensao == "Ano":
        base["categoria"] = base["data"].dt.year.astype("Int64").astype(str)
    else:
        base["categoria"] = base["cliente"]
    tabela = _resumo(base, "categoria")
    tabela = tabela.sort_values("Índice (%)", ascending=False) if dimensao == "Cliente" else tabela.sort_values("categoria")
    if dimensao == "Cliente":
        top = st.selectbox("Quantidade de clientes no gráfico", [10,20,50,100,100000], index=1, key="ic_conv_top", format_func=lambda v: "Todos" if v==100000 else f"Top {v}")
        grafico_df = tabela.head(top)
    else:
        grafico_df = tabela
    grafico = alt.Chart(grafico_df).mark_line(point=True) if dimensao != "Cliente" else alt.Chart(grafico_df).mark_bar()
    grafico = grafico.encode(x=alt.X("categoria:N", title=dimensao, sort=None),
                            y=alt.Y("Índice (%):Q", scale=alt.Scale(domain=[0,100]), title="Índice (%)"),
                            tooltip=["categoria:N", "Orçamentos:Q", "Pedidos:Q", "Faturados:Q", "Total de registros:Q", alt.Tooltip("Índice (%):Q", format=".2f")])
    st.altair_chart(grafico.properties(height=350), use_container_width=True)
    st.dataframe(tabela, hide_index=True, use_container_width=True)
    from io import BytesIO
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        tabela.to_excel(writer, index=False, sheet_name="Indice")
    st.download_button("Exportar índice em Excel", buffer.getvalue(), file_name="indice_faturamento_comercial.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="ic_conv_excel")
    st.caption("Base temporal: data_documento para P, E e F. Cancelados (C) não entram. O índice mede registros, não contatos únicos; períodos incompletos e etapas em datas distintas afetam a comparação.")

"""Inteligência Comercial v2 — estudos históricos, somente leitura."""
from datetime import date
from io import BytesIO
import unicodedata
import pandas as pd
import streamlit as st
import altair as alt
from core.database import supabase

PAGE = 1000
COLS = "id,situacao_erp,data_documento,data_faturamento,cliente_nome_erp,valor_total_cabecalho"
ITEM_COLS = "documento_id,codigo_erp,familia_sugerida,quantidade,valor_total_item"

def normalizar(s):
    s = unicodedata.normalize("NFKD", str(s or ""))
    return "".join(c for c in s if not unicodedata.combining(c)).upper().strip()

def brl(v):
    return "R$ " + f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

@st.cache_data(ttl=600, show_spinner=False)
def documentos():
    registros = []
    pos = 0
    while True:
        lote = (supabase.table("documentos_comerciais").select(COLS)
                .in_("situacao_erp", ["P", "E", "F"])
                .order("id").range(pos, pos + PAGE - 1).execute().data or [])
        registros.extend(lote)
        if len(lote) < PAGE:
            break
        pos += PAGE
    df = pd.DataFrame(registros)
    if df.empty:
        return df
    df["cliente"] = df["cliente_nome_erp"].fillna("Sem identificação").astype(str).str.strip()
    df = df[~df["cliente"].map(lambda x: "SUDAMERICANA" in normalizar(x) or "SUD AMERICANA" in normalizar(x))].copy()
    df["data"] = pd.to_datetime(df["data_documento"], errors="coerce")
    df["valor"] = pd.to_numeric(df["valor_total_cabecalho"], errors="coerce").fillna(0)
    df["tipo"] = df["situacao_erp"].map({"P": "Orçamento", "E": "Venda", "F": "Venda"})
    df = df.dropna(subset=["data"]).drop_duplicates(subset=["id"])
    df["ano"] = df["data"].dt.year
    df["mes"] = df["data"].dt.month
    return df

@st.cache_data(ttl=600, show_spinner=False)
def itens(ids):
    if not ids:
        return pd.DataFrame()
    registros = []
    for p in range(0, len(ids), 100):
        grupo = list(ids[p:p+100])
        offset = 0
        while True:
            lote = (supabase.table("itens_comerciais").select(ITEM_COLS)
                    .in_("documento_id", grupo).order("id")
                    .range(offset, offset+PAGE-1).execute().data or [])
            registros.extend(lote)
            if len(lote) < PAGE:
                break
            offset += PAGE
    x = pd.DataFrame(registros)
    if not x.empty:
        x["quantidade"] = pd.to_numeric(x["quantidade"], errors="coerce").fillna(0)
        x["valor_total_item"] = pd.to_numeric(x["valor_total_item"], errors="coerce").fillna(0)
        x["codigo_erp"] = x["codigo_erp"].fillna("Não identificado")
        x["familia_sugerida"] = x["familia_sugerida"].fillna("Não classificada")
    return x

def tabela_formatada(tabela):
    """Exibe unidades claras e formatação brasileira sem alterar dados exportados."""
    titulos = {
        "Cliente": "Cliente",
        "historico_compras": "Média histórica de compras (R$)",
        "atual_compras": "Média atual de compras (R$)",
        "historico_orcamentos": "Média histórica de orçamentos (R$)",
        "atual_orcamentos": "Média atual de orçamentos (R$)",
        "historico_pedidos": "Média histórica de pedidos (nº/ano)",
        "atual_pedidos": "Média atual de pedidos (nº/ano)",
        "historico_cotacoes": "Média histórica de cotações (nº/ano)",
        "atual_cotacoes": "Média atual de cotações (nº/ano)",
        "variacao_compras": "Diferença média de compras (R$)",
        "variacao_orcamentos": "Diferença média de orçamentos (R$)",
        "variacao_indicador": "Diferença média do indicador",
        "Anos com compras nos meses selecionados": "Anos com compras (nº)",
        "Última compra": "Última compra",
        "Último orçamento": "Último orçamento",
        "Meses desde última compra": "Meses sem compra",
        "Meses desde último orçamento": "Meses sem orçamento",
    }
    x = tabela.rename(columns=titulos)
    moeda = [v for v in x.columns if "(R$)" in v]
    contagem = [v for v in x.columns if "(nº/ano)" in v]
    inteiros = [v for v in x.columns if v.endswith("(nº)")]
    formatos = {v: brl for v in moeda}
    formatos.update({v: lambda n: "—" if pd.isna(n) else f"{n:.2f}".replace(".", ",") for v in contagem})
    formatos.update({v: lambda n: "—" if pd.isna(n) else f"{n:.0f}" for v in inteiros})
    for v in ["Meses sem compra", "Meses sem orçamento"]:
        if v in x.columns:
            formatos[v] = lambda n: "—" if pd.isna(n) else f"{n:.1f}".replace(".", ",")
    for v in ["Última compra", "Último orçamento"]:
        if v in x.columns:
            formatos[v] = lambda n: "—" if pd.isna(n) else n.strftime("%d/%m/%Y")
    st.dataframe(x.style.format(formatos, na_rep="—"), hide_index=True, use_container_width=True)


def exportar(tabela, nome):
    b = BytesIO()
    with pd.ExcelWriter(b, engine="openpyxl") as w:
        tabela.to_excel(w, index=False, sheet_name="Estudo")
    st.download_button("Exportar Excel", b.getvalue(), file_name=nome,
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def filtros_data(df, inicio, fim):
    return df[df["data"].between(pd.Timestamp(inicio), pd.Timestamp(fim))].copy()

def resumo(df, por="cliente"):
    if df.empty:
        return pd.DataFrame(columns=[por,"compras","orcamentos","pedidos","cotacoes"])
    x = df.pivot_table(index=por, columns="tipo", values="valor", aggfunc="sum", fill_value=0)
    x = x.reindex(columns=["Venda","Orçamento"], fill_value=0)
    n = df.pivot_table(index=por, columns="tipo", values="id", aggfunc="nunique", fill_value=0)
    n = n.reindex(columns=["Venda","Orçamento"], fill_value=0)
    return pd.DataFrame({por:x.index,"compras":x["Venda"].values,
        "orcamentos":x["Orçamento"].values,"pedidos":n["Venda"].values,
        "cotacoes":n["Orçamento"].values})

def classificacoes(historico, atual, metrica, referencia_anos, comparacao_anos):
    a = resumo(historico).set_index("cliente")
    b = resumo(atual).set_index("cliente")
    nomes = a.index.union(b.index)
    r = pd.DataFrame(index=nomes)
    for c in ["compras","orcamentos","pedidos","cotacoes"]:
        r["historico_"+c] = a[c].reindex(nomes, fill_value=0) / max(referencia_anos, 1)
        r["atual_"+c] = b[c].reindex(nomes, fill_value=0) / max(comparacao_anos, 1)
    r["variacao_compras"] = r["atual_compras"] - r["historico_compras"]
    r["variacao_orcamentos"] = r["atual_orcamentos"] - r["historico_orcamentos"]
    r["variacao_indicador"] = r["atual_"+metrica] - r["historico_"+metrica]
    r.index.name = "Cliente"
    return r.reset_index()

def aplicar_classe(t, classe, primeira, metrica):
    if classe == "Top 20":
        return t.sort_values("atual_"+metrica, ascending=False).head(20)
    if classe == "Principais perdas":
        return t[(t.historico_compras > 0) & (t.atual_compras < t.historico_compras)].sort_values("variacao_compras")
    if classe == "Novos entrantes":
        return t[t["Cliente"].isin(primeira[primeira >= pd.Timestamp("2024-01-01")].index)].sort_values("atual_"+metrica, ascending=False)
    if classe == "Potenciais players":
        return t[(t.historico_compras > 0) & (t.variacao_compras > 0)].sort_values("variacao_compras", ascending=False)
    if classe == "Oportunidades":
        return t[(t.historico_orcamentos > 0) & (t.variacao_orcamentos > 0)].sort_values("variacao_orcamentos", ascending=False)
    return t.sort_values("atual_"+metrica, ascending=False)

def seletor_classe(chave):
    return st.selectbox("Classificação comercial", ["Todos","Top 20","Principais perdas",
                        "Novos entrantes","Potenciais players","Oportunidades"], key=chave)

def tabela_classes(df, ref, atual, metrica, classe, primeira, nome):
    r = classificacoes(ref, atual, metrica, max(ref["ano"].nunique(),1), max(atual["ano"].nunique(),1))
    r = aplicar_classe(r, classe, primeira, metrica)
    tabela_formatada(r)
    exportar(r, nome)

def pagina_conversao(df):
    st.subheader("01 — Conversão comercial")
    st.caption("Participação de pedidos vendidos no total comercial. Quantidade de documentos e valor financeiro são indicadores independentes.")
    periodo = st.date_input("Período", (date(2024,1,1), date.today()), key="ic2_conv_datas")
    if len(periodo) != 2:
        return
    x = filtros_data(df, *periodo)
    n = x.groupby("tipo")["id"].nunique()
    v = x.groupby("tipo")["valor"].sum()
    pedidos, orc = int(n.get("Venda",0)), int(n.get("Orçamento",0))
    venda_val, orc_val = float(v.get("Venda",0)), float(v.get("Orçamento",0))
    a,b,c,d = st.columns(4)
    a.metric("Pedidos vendidos", pedidos)
    b.metric("Orçamentos", orc)
    c.metric("Conversão por quantidade", f"{100*pedidos/(pedidos+orc):.2f}%" if pedidos+orc else "—")
    d.metric("Conversão por valor", f"{100*venda_val/(venda_val+orc_val):.2f}%" if venda_val+orc_val else "—")
    st.caption(f"Valor vendido: {brl(venda_val)} | Valor orçado: {brl(orc_val)}")
    por = st.selectbox("Detalhar por", ["Ano","Mês","Cliente"], key="ic2_conv_por")
    x["grupo"] = x["ano"].astype(str) if por=="Ano" else (x["data"].dt.to_period("M").astype(str) if por=="Mês" else x["cliente"])
    t = resumo(x, "grupo")
    t["Conversão quantidade (%)"] = 100*t.pedidos/(t.pedidos+t.cotacoes).replace(0,float("nan"))
    t["Conversão valor (%)"] = 100*t.compras/(t.compras+t.orcamentos).replace(0,float("nan"))
    st.dataframe(t, hide_index=True, use_container_width=True)
    exportar(t, "conversao_comercial.xlsx")

def pagina_evolucao(df, primeira):
    st.subheader("02 — Evolução do desempenho")
    st.caption("Análise aprofundada de um único cliente, produto ou família por vez.")
    dim = st.radio("Investigar", ["Cliente","Produto","Família"], horizontal=True, key="ic2_evol_dim")
    base = df.copy()
    if dim != "Cliente":
        if not st.button("Carregar produtos e famílias", key="ic2_evol_carregar") and "ic2_evol_itens" not in st.session_state:
            st.info("Carregue os itens para selecionar um produto ou família.")
            return
        if "ic2_evol_itens" not in st.session_state:
            st.session_state["ic2_evol_itens"] = itens(tuple(df.id.astype(str)))
        it = st.session_state["ic2_evol_itens"]
        if it.empty:
            st.info("Não há itens associados.")
            return
        coluna = "codigo_erp" if dim=="Produto" else "familia_sugerida"
        opcoes = sorted(it[coluna].astype(str).unique())
        escolha = st.selectbox(dim, opcoes, key="ic2_evol_alvo")
        it = it[it[coluna].astype(str)==escolha]
        base = base.merge(it[["documento_id","valor_total_item","quantidade"]], left_on="id",right_on="documento_id")
        base["valor"] = base["valor_total_item"]
    else:
        escolha = st.selectbox("Cliente", sorted(df.cliente.unique()), key="ic2_evol_cliente")
        base = base[base.cliente==escolha]
    c1,c2 = st.columns(2)
    inicio = c1.date_input("Início", date(2020,1,1), key="ic2_evol_ini")
    fim = c2.date_input("Fim", date.today(), key="ic2_evol_fim")
    if inicio>fim:
        st.warning("Período inválido.")
        return
    base = filtros_data(base, inicio, fim)
    tempo = st.selectbox("Agrupamento", ["Mensal","Trimestral","Anual"], key="ic2_evol_tempo")
    medida = st.selectbox("Indicador", ["Valor (R$)","Documentos","Unidades"], key="ic2_evol_medida",
                         disabled=False)
    if medida=="Unidades" and dim=="Cliente":
        st.info("Unidades são disponíveis somente para produtos e famílias.")
        return
    freq = {"Mensal":"M","Trimestral":"Q","Anual":"Y"}[tempo]
    base["periodo"] = base.data.dt.to_period(freq).astype(str)
    if medida=="Valor (R$)":
        t = base.groupby(["periodo","tipo"])["valor"].sum().reset_index(name="resultado")
    elif medida=="Documentos":
        t = base.groupby(["periodo","tipo"])["id"].nunique().reset_index(name="resultado")
    else:
        t = base.groupby(["periodo","tipo"])["quantidade"].sum().reset_index(name="resultado")
    if t.empty:
        st.info("Sem dados para o período.")
        return
    st.altair_chart(alt.Chart(t).mark_line(point=True).encode(
        x=alt.X("periodo:N",sort=None), y="resultado:Q",color="tipo:N",
        tooltip=["periodo","tipo","resultado"]).properties(height=360),use_container_width=True)
    st.dataframe(t,hide_index=True,use_container_width=True)
    exportar(t,"evolucao_comercial.xlsx")
    st.caption("Valores de produtos/famílias são calculados pelos itens, não pelo cabeçalho do documento.")

def pagina_sazonalidade(df, primeira):
    st.subheader("03 — Sazonalidade comercial")
    st.caption("Compare os mesmos meses em anos diferentes e identifique clientes com histórico recorrente.")
    meses = st.multiselect("Meses analisados", list(range(1,13)), default=[7],
                           format_func=lambda x: ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"][x-1],
                           key="ic2_saz_meses")
    if not meses:
        st.info("Selecione ao menos um mês.")
        return
    base = df[df.mes.isin(meses)].copy()
    ano = st.selectbox("Ano de comparação", sorted(base.ano.unique(), reverse=True), key="ic2_saz_ano")
    referencia = base[base.ano < ano]
    atual = base[base.ano == ano]
    if referencia.empty:
        st.info("Sem histórico anterior para comparação.")
        return
    metrica = st.selectbox("Indicador", ["compras","orcamentos","pedidos","cotacoes"], key="ic2_saz_metrica",
                           format_func=lambda x: {"compras":"Valor vendido","orcamentos":"Valor orçado",
                           "pedidos":"Nº de pedidos","cotacoes":"Nº de orçamentos"}[x])
    classe = seletor_classe("ic2_saz_classe")
    frequencia = (referencia[referencia.tipo=="Venda"].groupby("cliente")["ano"].nunique()
                  .rename("Anos com compras nos meses selecionados"))
    r = classificacoes(referencia,atual,metrica,referencia.ano.nunique(),1)
    r = aplicar_classe(r,classe,primeira,metrica).merge(frequencia,how="left",left_on="Cliente",right_index=True)
    r["Anos com compras nos meses selecionados"] = r["Anos com compras nos meses selecionados"].fillna(0).astype(int)
    tabela_formatada(r)
    exportar(r,"sazonalidade_comercial.xlsx")
    st.caption("A média de referência considera os anos anteriores presentes na base; o ano atual pode estar incompleto.")

def pagina_recuperacao(df, primeira):
    st.subheader("04 — Recuperação de clientes")
    st.caption("Identifique quem comprava ou orçava regularmente e quando interrompeu a movimentação.")
    anos = sorted(df.ano.unique())
    if len(anos)<2:
        st.info("Histórico insuficiente.")
        return
    ano = st.selectbox("Ano de comparação", sorted(anos[1:],reverse=True), key="ic2_rec_ano")
    referencia = df[df.ano<ano]
    atual = df[df.ano==ano]
    metrica = st.selectbox("Indicador",["compras","orcamentos","pedidos","cotacoes"],
        format_func=lambda x: {"compras":"Valor vendido","orcamentos":"Valor orçado","pedidos":"Nº de pedidos","cotacoes":"Nº de orçamentos"}[x],
        key="ic2_rec_met")
    classe = seletor_classe("ic2_rec_classe")
    r = classificacoes(referencia,atual,metrica,referencia.ano.nunique(),1)
    r = aplicar_classe(r,classe,primeira,metrica)
    compras = df[df.tipo=="Venda"].groupby("cliente")["data"].max().rename("Última compra")
    orcs = df[df.tipo=="Orçamento"].groupby("cliente")["data"].max().rename("Último orçamento")
    r = r.merge(compras,left_on="Cliente",right_index=True,how="left").merge(orcs,left_on="Cliente",right_index=True,how="left")
    r["Meses desde última compra"] = ((pd.Timestamp.today()-r["Última compra"]).dt.days/30.44).round(1)
    r["Meses desde último orçamento"] = ((pd.Timestamp.today()-r["Último orçamento"]).dt.days/30.44).round(1)
    st.dataframe(r,hide_index=True,use_container_width=True)
    exportar(r,"recuperacao_clientes.xlsx")
    st.caption("Última movimentação considera todo o histórico. A data exata de início da queda exige análise temporal mais detalhada.")

def pagina_inteligencia_comercial():
    if not st.session_state.get("logado") or st.session_state.get("setor") != "ADMINISTRADOR":
        st.error("Acesso restrito ao administrador.")
        st.stop()
    st.title("Inteligência Comercial")
    st.caption("Estudos comerciais | orçamento e venda | histórico ERP | SUDAMERICANA excluída | somente leitura")
    try:
        with st.spinner("Carregando histórico comercial..."):
            df = documentos()
    except Exception as e:
        st.error("Falha ao carregar dados comerciais.")
        st.caption(str(e))
        return
    if df.empty:
        st.info("Não há registros comerciais disponíveis.")
        return
    primeira = df.groupby("cliente")["data"].min()
    tabs = st.tabs(["01 · Conversão","02 · Evolução","03 · Sazonalidade","04 · Recuperação"])
    with tabs[0]:
        pagina_conversao(df)
    with tabs[1]:
        pagina_evolucao(df,primeira)
    with tabs[2]:
        pagina_sazonalidade(df,primeira)
    with tabs[3]:
        pagina_recuperacao(df,primeira)
    st.caption("Classificações: Top 20, Principais perdas, Novos entrantes (sem movimentação antes de 2024), Potenciais players (compras em crescimento) e Oportunidades (orçamentos em crescimento).")

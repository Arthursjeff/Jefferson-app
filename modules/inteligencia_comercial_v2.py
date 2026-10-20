"""Inteligência Comercial v2 — estudos históricos, somente leitura."""
from datetime import date
from io import BytesIO
import unicodedata
import time
import pandas as pd
import streamlit as st
import altair as alt
from core.database import supabase
from core.permissoes import tem_acesso_modulo

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
    # Consultas menores e retentativas para desconexões transitórias HTTP/2.
    for p in range(0, len(ids), 40):
        grupo = list(ids[p:p+40])
        offset = 0
        while True:
            for tentativa in range(4):
                try:
                    lote = (supabase.table("itens_comerciais").select(ITEM_COLS)
                            .in_("documento_id", grupo).order("id")
                            .range(offset, offset+PAGE-1).execute().data or [])
                    break
                except (ConnectionError, TimeoutError) as exc:
                    if tentativa == 3:
                        raise RuntimeError("Falha de conexão ao carregar itens comerciais. Tente novamente.") from exc
                    time.sleep(0.5 * (2 ** tentativa))
                except Exception as exc:
                    # Erros transitórios do transporte httpx (inclui RemoteProtocolError).
                    import httpx
                    if not isinstance(exc, (httpx.TransportError, httpx.TimeoutException)) or tentativa == 3:
                        raise
                    time.sleep(0.5 * (2 ** tentativa))
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

def _conversao_resumo(base, grupo="grupo"):
    """P/E/F são propostas; E/F são propostas convertidas em vendas."""
    if base.empty:
        return pd.DataFrame(columns=[grupo, "Orçamentos (nº)", "Vendas (nº)",
            "Valor orçado (R$)", "Valor vendido (R$)",
            "Conversão quantidade (%)", "Conversão valor (%)"])
    base = base.copy()
    base["venda"] = base["situacao_erp"].isin(["E", "F"])
    # Um documento conta uma única vez por grupo; itens repetidos são somados antes.
    dados = base.groupby([grupo, "id"], as_index=False).agg(
        valor=("valor", "sum"), venda=("venda", "max"))
    dados["valor_vendido"] = dados["valor"].where(dados["venda"], 0)
    t = dados.groupby(grupo, as_index=False).agg(
        **{"Orçamentos (nº)": ("id", "nunique"),
           "Vendas (nº)": ("venda", "sum"),
           "Valor orçado (R$)": ("valor", "sum"),
           "Valor vendido (R$)": ("valor_vendido", "sum")})
    t["Conversão quantidade (%)"] = (100 * t["Vendas (nº)"] /
        t["Orçamentos (nº)"].replace(0, float("nan")))
    t["Conversão valor (%)"] = (100 * t["Valor vendido (R$)"] /
        t["Valor orçado (R$)"].replace(0, float("nan")))
    return t


def _conversao_exibir(t, nome):
    formatos = {"Orçamentos (nº)": lambda v: f"{v:,.0f}".replace(",", "."),
                "Vendas (nº)": lambda v: f"{v:,.0f}".replace(",", "."),
                "Valor orçado (R$)": brl, "Valor vendido (R$)": brl,
                "Conversão quantidade (%)": lambda v: "—" if pd.isna(v) else f"{v:.2f}%".replace(".", ","),
                "Conversão valor (%)": lambda v: "—" if pd.isna(v) else f"{v:.2f}%".replace(".", ",")}
    st.dataframe(t.style.format(formatos, na_rep="—"), hide_index=True, use_container_width=True)
    exportar(t, nome)


def pagina_conversao(df):
    st.subheader("01 — Conversão comercial")
    st.caption("Todo documento P, E ou F conta como orçamento emitido; apenas E e F contam como venda. "
               "A conversão é a proporção de documentos atualmente vendidos, não uma vinculação histórica entre propostas.")
    anos = sorted(df["ano"].dropna().astype(int).unique())
    if not anos:
        st.info("Não há documentos com data válida.")
        return
    escolha = st.selectbox("Período", ["Todo o histórico"] + [str(a) for a in reversed(anos)],
                           key="ic2_conv_periodo")
    x = df.copy() if escolha == "Todo o histórico" else df[df["ano"] == int(escolha)].copy()
    if x.empty:
        st.info("Nenhum documento nesse período.")
        return
    x["grupo"] = "Total"
    total = _conversao_resumo(x).iloc[0]
    a, b, c, d = st.columns(4)
    a.metric("Orçamentos emitidos (P+E+F)", f'{int(total["Orçamentos (nº)"]):,}'.replace(",", "."))
    b.metric("Vendas (E+F)", f'{int(total["Vendas (nº)"]):,}'.replace(",", "."))
    c.metric("Conversão numérica", f'{total["Conversão quantidade (%)"]:.2f}%'.replace(".", ","))
    d.metric("Conversão financeira", f'{total["Conversão valor (%)"]:.2f}%'.replace(".", ","))
    st.caption(f'Valor total orçado: {brl(total["Valor orçado (R$)"])} | '
               f'Valor vendido: {brl(total["Valor vendido (R$)"])}')

    st.markdown("#### Comparativo anual")
    anual = x.copy()
    anual["grupo"] = anual["ano"].astype(int)
    por_ano = _conversao_resumo(anual).rename(columns={"grupo": "Ano"}).sort_values("Ano")
    tipo_grafico = st.radio("Visualizar", ["Comparativo", "Vendas", "Orçamentos"],
                           horizontal=True, key="ic2_conv_grafico")
    unidade = st.radio("Medida", ["Quantidade", "Valor (R$)"],
                      horizontal=True, key="ic2_conv_unidade")
    col_orc = "Orçamentos (nº)" if unidade == "Quantidade" else "Valor orçado (R$)"
    col_venda = "Vendas (nº)" if unidade == "Quantidade" else "Valor vendido (R$)"
    colunas = ([col_orc, col_venda] if tipo_grafico == "Comparativo" else
               [col_venda] if tipo_grafico == "Vendas" else [col_orc])
    plot = por_ano.melt(id_vars=["Ano"], value_vars=colunas,
                        var_name="Indicador", value_name="Resultado")
    graf = alt.Chart(plot).mark_bar().encode(
        x=alt.X("Ano:O", title="Ano"),
        xOffset=alt.XOffset("Indicador:N"),
        y=alt.Y("Resultado:Q", title=unidade),
        color=alt.Color("Indicador:N", title=""),
        tooltip=["Ano:O", "Indicador:N", alt.Tooltip("Resultado:Q", format=",.2f")]
    ).properties(height=350)
    st.altair_chart(graf, use_container_width=True)
    # Conversão no gráfico é sempre por quantidade, inclusive na visualização financeira.
    taxa = por_ano[["Ano", "Conversão quantidade (%)"]].copy()
    taxa["Ano"] = taxa["Ano"].astype(str)
    st.caption("Conversão numérica por ano (E+F ÷ P+E+F): " + " | ".join(
        f'{r["Ano"]}: {r["Conversão quantidade (%)"]:.1f}%'.replace(".", ",")
        for _, r in taxa.iterrows()))
    _conversao_exibir(por_ano, "conversao_por_ano.xlsx")

    st.markdown("#### Detalhamento")
    dimensao = st.radio("Analisar por", ["Cliente", "Produto"],
                        horizontal=True, key="ic2_conv_dimensao")
    if dimensao == "Cliente":
        clientes = sorted(x["cliente"].unique())
        escolhido = st.selectbox("Cliente", ["Todos os clientes"] + clientes,
                                key="ic2_conv_cliente")
        base = x if escolhido == "Todos os clientes" else x[x["cliente"] == escolhido]
        base = base.copy()
        base["grupo"] = base["cliente"]
        t = _conversao_resumo(base).rename(columns={"grupo": "Cliente"})
        t = t.sort_values("Orçamentos (nº)", ascending=False)
        _conversao_exibir(t, "conversao_por_cliente.xlsx")
        if escolhido != "Todos os clientes":
            por_cliente_ano = base.copy()
            por_cliente_ano["grupo"] = por_cliente_ano["ano"].astype(int)
            st.markdown("**Histórico anual do cliente**")
            _conversao_exibir(_conversao_resumo(por_cliente_ano).rename(
                columns={"grupo": "Ano"}).sort_values("Ano"), "conversao_cliente_anos.xlsx")
    else:
        if not st.button("Carregar itens para análise de produtos", key="ic2_conv_carregar") and "ic2_conv_itens" not in st.session_state:
            st.info("Carregue os itens para estudar conversão por produto.")
            return
        if "ic2_conv_itens" not in st.session_state:
            st.session_state["ic2_conv_itens"] = itens(tuple(df["id"].astype(str)))
        it = st.session_state["ic2_conv_itens"]
        if it.empty:
            st.info("Nenhum item encontrado.")
            return
        it = it.copy()
        it["documento_id"] = it["documento_id"].astype(str)
        it["codigo_erp"] = it["codigo_erp"].astype(str)
        # Agrupar linhas do mesmo código dentro de um documento evita duplicar propostas.
        it = it.groupby(["documento_id", "codigo_erp"], as_index=False)["valor_total_item"].sum()
        base = x.copy()
        base["id"] = base["id"].astype(str)
        base = base.merge(it, left_on="id", right_on="documento_id", how="inner")
        base["valor"] = base["valor_total_item"]
        produtos = sorted(base["codigo_erp"].unique())
        selecionado = st.selectbox("Produto", ["Todos os produtos"] + produtos,
                                  key="ic2_conv_produto")
        if selecionado != "Todos os produtos":
            base = base[base["codigo_erp"] == selecionado]
        base["grupo"] = base["codigo_erp"]
        t = _conversao_resumo(base).rename(columns={"grupo": "Produto"})
        t = t.sort_values("Orçamentos (nº)", ascending=False)
        _conversao_exibir(t, "conversao_por_produto.xlsx")
        if selecionado != "Todos os produtos":
            base = base.copy()
            base["grupo"] = base["ano"].astype(int)
            st.markdown("**Histórico anual do produto**")
            _conversao_exibir(_conversao_resumo(base).rename(
                columns={"grupo": "Ano"}).sort_values("Ano"), "conversao_produto_anos.xlsx")
    st.caption("A conversão financeira considera os valores registrados no ERP. "
               "No detalhamento por produto, cada código usa o valor dos próprios itens.")

def pagina_produtos(df, primeira):
    """Portfólio: tendência, recorrência, alcance e concentração comercial."""
    st.subheader("02 — Produtos")
    st.caption("Identifique produtos e famílias em expansão ou queda, sua frequência de saída, "
               "quantidade de clientes atendidos e dependência comercial. Apenas vendas E/F.")
    inicio_mes = pd.Timestamp(date.today()).replace(day=1)
    inicio_atual = inicio_mes - pd.DateOffset(months=12)
    docs = df[(df["data"] < inicio_mes) & df["situacao_erp"].isin(["E", "F"])].copy()
    if docs.empty:
        st.info("Não há vendas em meses completos.")
        return
    inicio_hist = docs["data"].min().to_period("M").to_timestamp()
    meses_hist = (inicio_atual.year - inicio_hist.year) * 12 + inicio_atual.month - inicio_hist.month
    meses_total = (inicio_mes.year - inicio_hist.year) * 12 + inicio_mes.month - inicio_hist.month
    if meses_hist < 12:
        st.info("São necessários pelo menos 12 meses históricos anteriores ao período atual.")
        return
    if "ic2_prod_itens" not in st.session_state:
        if not st.button("Carregar análise do portfólio", key="ic2_prod_carregar"):
            st.info("Clique para carregar os itens vendidos. O carregamento pode levar algum tempo.")
            return
        try:
            with st.spinner("Consultando itens vendidos no Supabase..."):
                st.session_state["ic2_prod_itens"] = itens(tuple(docs["id"].astype(str)))
        except Exception as exc:
            st.warning("A conexão com o Supabase foi interrompida. Tente carregar novamente.")
            st.caption("Tipo de falha: " + type(exc).__name__)
            return
    it = st.session_state["ic2_prod_itens"]
    if it.empty:
        st.info("Não há itens comerciais vinculados às vendas.")
        return
    base = it.copy()
    base["documento_id"] = base["documento_id"].astype(str)
    docs["id"] = docs["id"].astype(str)
    base = base.merge(docs[["id", "cliente", "data"]], left_on="documento_id",
                      right_on="id", how="inner")
    if base.empty:
        st.info("Não há itens de venda correspondentes aos documentos.")
        return
    base["mes_ref"] = base["data"].dt.to_period("M")
    base["janela"] = base["data"].ge(inicio_atual).map({True: "Atual", False: "Histórico"})
    dimensao = st.radio("Analisar por", ["Produto", "Família"], horizontal=True, key="ic2_prod_dim")
    campo = "codigo_erp" if dimensao == "Produto" else "familia_sugerida"
    base[campo] = base[campo].fillna("Não identificado").astype(str).str.strip()
    base = base[base[campo].ne("")]
    if base.empty:
        st.info("Nenhum item identificado.")
        return
    base["valor"] = base["valor_total_item"]
    grupo = base.groupby([campo, "janela"])[["quantidade", "valor"]].sum().unstack(fill_value=0)
    nomes = grupo.index
    def col(metrica, periodo):
        chave = (metrica, periodo)
        return grupo[chave] if chave in grupo.columns else pd.Series(0., index=nomes)
    res = pd.DataFrame(index=nomes)
    for sigla, metrica in [("q", "quantidade"), ("r", "valor")]:
        res[f"h_{sigla}"] = col(metrica, "Histórico") * 12 / meses_hist
        res[f"a_{sigla}"] = col(metrica, "Atual")
    res["Clientes distintos"] = base.groupby(campo)["cliente"].nunique().reindex(nomes, fill_value=0)
    res["Clientes atuais"] = base[base["janela"] == "Atual"].groupby(campo)["cliente"].nunique().reindex(nomes, fill_value=0)
    res["Meses com vendas"] = base.groupby(campo)["mes_ref"].nunique().reindex(nomes, fill_value=0)
    res["Frequência (%)"] = res["Meses com vendas"] * 100 / meses_total
    res["Meses com vendas / total"] = res["Meses com vendas"].astype(int).astype(str) + "/" + str(meses_total)
    res["Última venda"] = base.groupby(campo)["data"].max().reindex(nomes)
    participacao = base.groupby([campo, "cliente"])["valor"].sum()
    total = participacao.groupby(level=0).sum()
    maior = participacao.groupby(level=0).max()
    lider = participacao.groupby(level=0).idxmax().map(lambda chave: chave[1])
    res["Principal cliente"] = lider.reindex(nomes).fillna("Não identificado")
    res["Maior cliente (%)"] = 100 * maior.reindex(nomes, fill_value=0) / total.reindex(nomes).replace(0, float("nan"))
    for sigla in ["q", "r"]:
        res[f"Variação {sigla} (%)"] = 100 * (res[f"a_{sigla}"] / res[f"h_{sigla}"].replace(0, float("nan")) - 1)
        res[f"Diferença {sigla}"] = res[f"a_{sigla}"] - res[f"h_{sigla}"]
    def classificar(linha):
        h, a = linha["h_q"], linha["a_q"]
        if h <= 0:
            return "Novo / sem histórico" if a > 0 else "Sem saída"
        variacao = 100 * (a / h - 1)
        if variacao < -15:
            return "Em queda"
        if variacao > 15:
            return "Em crescimento"
        return "Estável"
    res["Tendência"] = res.apply(classificar, axis=1)
    res["Perfil"] = res.apply(
        lambda x: "Concentrado" if x["Clientes distintos"] == 1 or
        (pd.notna(x["Maior cliente (%)"]) and x["Maior cliente (%)"] >= 70)
        else "Diversificado", axis=1)
    res["Importância"] = res.apply(
        lambda x: "Estratégico em queda" if x["Tendência"] == "Em queda" and
        (x["Frequência (%)"] >= 50 or x["Clientes distintos"] >= 10)
        else x["Tendência"], axis=1)
    st.caption(f"Histórico: {inicio_hist:%m/%Y} a {(inicio_atual - pd.Timedelta(days=1)):%m/%Y} "
               f"({meses_hist} meses). Atual: últimos 12 meses completos. "
               f"Frequência: meses com vendas de {meses_total} meses observados. "
               "Tendência: variação de unidades superior a ±15%; concentração: maior cliente ≥70%.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Itens com vendas", len(res))
    c2.metric("Em queda", int(res["Tendência"].eq("Em queda").sum()))
    c3.metric("Em crescimento", int(res["Tendência"].eq("Em crescimento").sum()))
    f1, f2, f3 = st.columns(3)
    tendencia = f1.selectbox("Filtrar tendência", ["Todos", "Em queda", "Em crescimento", "Estável", "Novo / sem histórico", "Estratégico em queda"], key="ic2_prod_tendencia")
    perfil = f2.selectbox("Perfil de clientes", ["Todos", "Concentrado", "Diversificado"], key="ic2_prod_perfil")
    indicador = f3.radio("Ordenar e comparar por", ["Unidades", "Faturamento"], key="ic2_prod_indicador")
    ranking = st.selectbox("Ranking", ["Maiores perdas", "Maiores ganhos", "Maior saída", "Mais clientes", "Mais frequentes", "Maior faturamento"], key="ic2_prod_ranking")
    filtrado = res.copy()
    if tendencia != "Todos":
        filtro_col = "Importância" if tendencia == "Estratégico em queda" else "Tendência"
        filtrado = filtrado[filtrado[filtro_col] == tendencia]
    if perfil != "Todos":
        filtrado = filtrado[filtrado["Perfil"] == perfil]
    sigla = "q" if indicador == "Unidades" else "r"
    ordenacoes = {
        "Maiores perdas": (f"Diferença {sigla}", True),
        "Maiores ganhos": (f"Diferença {sigla}", False),
        "Maior saída": ("a_q", False),
        "Mais clientes": ("Clientes distintos", False),
        "Mais frequentes": ("Frequência (%)", False),
        "Maior faturamento": ("a_r", False),
    }
    coluna_ordem, asc = ordenacoes[ranking]
    filtrado = filtrado.sort_values(coluna_ordem, ascending=asc)
    tabela = filtrado.reset_index().rename(columns={
        campo: dimensao, "h_q": "Unidades históricas (nº/ano)",
        "a_q": "Unidades atuais (nº/ano)",
        "h_r": "Faturamento histórico (R$)", "a_r": "Faturamento atual (R$)",
        "Meses com vendas": "Meses com vendas (nº)",
        "Clientes distintos": "Clientes históricos + atuais (nº)",
        "Clientes atuais": "Clientes atuais (nº)"})
    colunas = [dimensao, "Tendência", "Importância", "Perfil",
               "Unidades históricas (nº/ano)", "Unidades atuais (nº/ano)",
               "Faturamento histórico (R$)", "Faturamento atual (R$)",
               "Variação q (%)", "Variação r (%)",
               "Clientes históricos + atuais (nº)", "Clientes atuais (nº)",
               "Meses com vendas / total", "Principal cliente", "Maior cliente (%)", "Última venda"]
    st.markdown("#### Ranking do portfólio")
    if tabela.empty:
        st.info("Nenhum item corresponde aos filtros.")
        return
    _recuperacao_tabela(tabela[colunas])
    exportar(tabela[colunas], "analise_produtos.xlsx")
    escolha = st.selectbox(f"Detalhar {dimensao.lower()}", filtrado.index.tolist(), key="ic2_prod_escolha")
    linha = res.loc[escolha]
    st.markdown("#### Diagnóstico individual")
    st.write(f"**{escolha}** — {linha['Importância']}; perfil {linha['Perfil'].lower()}.")
    m1, m2, m3 = st.columns(3)
    m1.metric("Média histórica mensal (peças)", f"{linha['h_q']/12:.1f}".replace(".", ","))
    m2.metric("Média atual mensal (peças)", f"{linha['a_q']/12:.1f}".replace(".", ","))
    m3.metric("Frequência de saída", f"{int(linha['Meses com vendas'])} de {meses_total} meses")
    st.caption(f"Clientes distintos: {int(linha['Clientes distintos'])} | "
               f"Maior cliente representa {linha['Maior cliente (%)']:.1f}% do valor vendido no histórico completo.")
    detalhe = base[base[campo] == escolha].copy()
    clientes = detalhe.groupby("cliente").agg(
        **{"Unidades totais": ("quantidade", "sum"), "Faturamento total (R$)": ("valor", "sum"),
           "Última venda": ("data", "max")})
    recentes = detalhe[detalhe["data"] >= inicio_atual].groupby("cliente").agg(
        **{"Unidades últimos 12 meses": ("quantidade", "sum"),
           "Faturamento últimos 12 meses (R$)": ("valor", "sum")})
    clientes = clientes.join(recentes, how="left")
    clientes[["Unidades últimos 12 meses", "Faturamento últimos 12 meses (R$)"]] = (
        clientes[["Unidades últimos 12 meses", "Faturamento últimos 12 meses (R$)"]].fillna(0))
    clientes = clientes.sort_values("Faturamento total (R$)", ascending=False).reset_index().rename(columns={"cliente": "Cliente"})
    st.markdown("**Principais clientes compradores**")
    st.caption("Total = todo o histórico disponível; últimos 12 meses = meses completos anteriores ao mês atual. Clientes sem compras recentes aparecem com zero.")
    _recuperacao_tabela(clientes.head(20))
    detalhe["Ano"] = detalhe["data"].dt.year
    anos = list(range(inicio_hist.year, (inicio_mes - pd.Timedelta(days=1)).year + 1))
    anual = detalhe.groupby("Ano")[["quantidade", "valor"]].sum().reindex(anos, fill_value=0).reset_index().rename(
        columns={"quantidade": "Unidades vendidas", "valor": "Faturamento (R$)"})
    st.markdown("**Evolução anual**")
    serie = st.radio("Visualizar evolução", ["Unidades vendidas", "Faturamento (R$)"], horizontal=True, key="ic2_prod_graf")
    st.altair_chart(alt.Chart(anual).mark_line(point=True).encode(
        x=alt.X("Ano:O"), y=alt.Y(f"{serie}:Q"),
        tooltip=["Ano:O", alt.Tooltip(f"{serie}:Q", format=",.2f")]
    ).properties(height=310), use_container_width=True)
    st.caption("O ano atual contém apenas meses completos; compare o ritmo anualizado na tabela principal.")
    _recuperacao_tabela(anual)
    exportar(anual, "produto_evolucao_anual.xlsx")


def _sazonalidade_tabela(df, meses, indicador, hoje=None):
    """Média sazonal de períodos completos e média geral equivalente.
    Cada ano do período inclui zeros quando não houve movimentação.
    """
    import calendar
    hoje = hoje or date.today()
    base = df[df["data"].dt.date <= hoje].copy()
    if base.empty:
        return pd.DataFrame(), [], 0
    inicio = date(2020, 1, 1)
    ultimo_mes_completo = date(hoje.year, hoje.month, 1) - pd.Timedelta(days=1)
    ultimo_mes_completo = ultimo_mes_completo.date() if hasattr(ultimo_mes_completo, "date") else ultimo_mes_completo
    meses_completos = (ultimo_mes_completo.year - inicio.year) * 12 + ultimo_mes_completo.month - inicio.month + 1
    if meses_completos <= 0:
        return pd.DataFrame(), [], 0
    todos_anos = list(range(inicio.year, hoje.year + 1))
    # Só um conjunto de meses integralmente concluído pode integrar a média sazonal.
    anos_referencia = [ano for ano in todos_anos
                       if all(date(ano, mes, calendar.monthrange(ano, mes)[1]) <= ultimo_mes_completo
                              for mes in meses)]
    recorte = base[base["mes"].isin(meses)].copy()
    if indicador == "consultas":
        recorte["medida"] = 1
        base["medida"] = 1
    elif indicador == "pedidos":
        recorte["medida"] = (recorte["tipo"] == "Venda").astype(int)
        base["medida"] = (base["tipo"] == "Venda").astype(int)
    elif indicador == "cotacoes":
        recorte["medida"] = (recorte["tipo"] == "Orçamento").astype(int)
        base["medida"] = (base["tipo"] == "Orçamento").astype(int)
    elif indicador == "compras":
        recorte["medida"] = recorte["valor"].where(recorte["tipo"] == "Venda", 0)
        base["medida"] = base["valor"].where(base["tipo"] == "Venda", 0)
    else:
        recorte["medida"] = recorte["valor"].where(recorte["tipo"] == "Orçamento", 0)
        base["medida"] = base["valor"].where(base["tipo"] == "Orçamento", 0)
    clientes = sorted(base["cliente"].unique())
    tabela = pd.DataFrame({"Cliente": clientes}).set_index("Cliente")
    por_ano = recorte.groupby(["cliente", "ano"])["medida"].sum().unstack(fill_value=0)
    for ano in todos_anos:
        tabela[str(ano)] = por_ano[ano].reindex(clientes, fill_value=0) if ano in por_ano else 0
    colunas_media = [str(ano) for ano in anos_referencia]
    tabela["Média do período"] = tabela[colunas_media].sum(axis=1) / len(colunas_media) if colunas_media else 0.0
    # Geral considera todos os meses completos, mesmo os sem movimentação.
    completo = base[base["data"].dt.date <= ultimo_mes_completo]
    geral = completo.groupby("cliente")["medida"].sum().reindex(clientes, fill_value=0)
    tabela["Média geral equivalente"] = geral / meses_completos * len(meses)
    tabela["Índice sazonal (%)"] = (100 * tabela["Média do período"] /
        tabela["Média geral equivalente"].replace(0, float("nan")))
    tabela["Diferença sazonal (%)"] = tabela["Índice sazonal (%)"] - 100
    return tabela, anos_referencia, meses_completos


def pagina_sazonalidade(df, primeira):
    st.subheader("03 — Sazonalidade comercial")
    st.caption("Compare os mesmos meses em todos os anos disponíveis. Os resultados são ordenados pela média do período, do maior para o menor.")
    meses = st.multiselect("Meses analisados", list(range(1, 13)), default=[7],
        format_func=lambda x: ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"][x-1],
        key="ic2_saz_meses")
    if not meses:
        st.info("Selecione ao menos um mês.")
        return
    indicador = st.selectbox("Indicador", ["compras", "orcamentos", "pedidos", "cotacoes", "consultas"],
        format_func=lambda x: {"compras": "Valor vendido (R$)", "orcamentos": "Valor orçado (R$)",
            "pedidos": "Número de pedidos", "cotacoes": "Número de orçamentos",
            "consultas": "Número de consultas (pedidos + orçamentos)"}[x],
        key="ic2_saz_metrica")
    classe = seletor_classe("ic2_saz_classe")
    tabela, anos_referencia, n_meses = _sazonalidade_tabela(df, meses, indicador)
    if tabela.empty:
        st.info("Sem dados comerciais para o estudo.")
        return
    anos = [str(ano) for ano in range(2020, date.today().year + 1)]
    if not anos_referencia:
        st.info("Nenhum período selecionado está integralmente concluído.")
        return
    ano_mais_recente = anos_referencia[-1]
    anteriores = anos_referencia[:-1]
    if classe == "Top 20":
        tabela = tabela.nlargest(20, "Média do período")
    elif classe == "Novos entrantes":
        novos = primeira[primeira >= pd.Timestamp("2024-01-01")].index
        tabela = tabela[tabela.index.isin(novos)]
    elif classe in ("Principais perdas", "Potenciais players", "Oportunidades"):
        # Para classificar, usa-se o mesmo período em anos completos e não o ano em andamento.
        if not anteriores:
            st.info("É necessário ter pelo menos dois períodos anuais completos para essa classificação.")
            return
        referencia = df[df["ano"].isin(anteriores) & df["mes"].isin(meses)]
        atual = df[(df["ano"] == ano_mais_recente) & df["mes"].isin(meses)]
        historico = resumo(referencia).set_index("cliente")
        recente = resumo(atual).set_index("cliente")
        nomes = tabela.index
        media_compras = historico["compras"].reindex(nomes, fill_value=0) / len(anteriores)
        media_orc = historico["orcamentos"].reindex(nomes, fill_value=0) / len(anteriores)
        compras_recentes = recente["compras"].reindex(nomes, fill_value=0)
        orc_recentes = recente["orcamentos"].reindex(nomes, fill_value=0)
        if classe == "Principais perdas":
            tabela = tabela[(media_compras > 0) & (compras_recentes < media_compras)]
        elif classe == "Potenciais players":
            tabela = tabela[(media_compras > 0) & (compras_recentes > media_compras)]
        else:
            tabela = tabela[(media_orc > 0) & (orc_recentes > media_orc)]
    tabela = tabela.sort_values("Média do período", ascending=False)
    exibicao = tabela.reset_index()
    colunas = ["Cliente"] + anos + ["Média do período", "Média geral equivalente", "Índice sazonal (%)"]
    exibicao = exibicao[colunas]
    monetario = indicador in ("compras", "orcamentos")
    formatos = {ano: (brl if monetario else lambda v: f"{v:,.0f}".replace(",", ".")) for ano in anos}
    formatos["Média do período"] = brl if monetario else lambda v: f"{v:.2f}".replace(".", ",")
    formatos["Média geral equivalente"] = brl if monetario else lambda v: f"{v:.2f}".replace(".", ",")
    formatos["Índice sazonal (%)"] = lambda v: "—" if pd.isna(v) else f"{v:.1f}%".replace(".", ",")
    titulos = {"Média do período": "Média meses selecionados" + (" (R$)" if monetario else " (nº)"),
               "Média geral equivalente": "Média geral equivalente" + (" (R$)" if monetario else " (nº)")}
    st.caption(f"Média sazonal: anos {anos_referencia[0]} a {anos_referencia[-1]} com todos os meses selecionados concluídos. "
               f"Média geral: {n_meses} meses completos desde jan/2020, ajustada para {len(meses)} mês(es). "
               "O ano atual é exibido mesmo quando o período selecionado ainda não terminou, mas não entra na média sazonal nesse caso.")
    st.dataframe(exibicao.rename(columns=titulos).style.format(
        {titulos.get(k, k): v for k, v in formatos.items()}, na_rep="—"),
        hide_index=True, use_container_width=True)
    exportar(exibicao.rename(columns=titulos), "sazonalidade_comercial.xlsx")
    st.caption("Índice sazonal acima de 100%: período mais forte que a média geral; abaixo de 100%: período mais fraco. "
               "Meses sem movimentação contam como zero. Classificações de crescimento/perda usam somente períodos anuais completos.")

def _recuperacao_agrupar(base, campo, meses_historicos, meses_atuais, inicio_atual):
    """Histórico anterior à janela móvel; vendas E/F e consultas P/E/F."""
    x = base.copy()
    x["venda"] = x["situacao_erp"].isin(["E", "F"])
    x["mes_ref"] = x["data"].dt.to_period("M")
    # Um mesmo documento pode conter vários itens da família, mas só uma consulta.
    x = x.groupby([campo, "id", "mes_ref"], as_index=False).agg(
        data=("data", "max"), valor=("valor", "sum"),
        quantidade=("quantidade", "sum"), venda=("venda", "max"))
    x["valor_vendido"] = x["valor"].where(x["venda"], 0)
    x["unidades_vendidas"] = x["quantidade"].where(x["venda"], 0)
    x["pedidos"] = x["venda"].astype(int)
    x["consultas"] = 1
    antes = x[x["data"] < inicio_atual]
    atual = x[x["data"] >= inicio_atual]
    metricas = ["pedidos", "consultas", "valor_vendido", "valor", "unidades_vendidas"]
    h = antes.groupby(campo)[metricas].sum().div(meses_historicos / 12).add_prefix("historico_")
    t = atual.groupby(campo)[metricas].sum().div(meses_atuais / 12).add_prefix("atual_")
    nomes = h.index.union(t.index)
    r = h.reindex(nomes, fill_value=0).join(t.reindex(nomes, fill_value=0))
    anos = antes.assign(ano=antes["data"].dt.year).groupby(campo)["ano"].nunique()
    meses = antes.groupby(campo)["mes_ref"].nunique()
    # Anos civis observados, inclusive os parciais, para não superar 100%.
    primeiro_ano = (inicio_atual - pd.DateOffset(months=meses_historicos)).year
    ultimo_ano = (inicio_atual - pd.Timedelta(days=1)).year
    anos_calendario = max(1, ultimo_ano - primeiro_ano + 1)
    # Regularidade é calculada no intervalo de observação, incluindo meses sem compras.
    meses_com_compra = antes[antes["venda"]].groupby(campo)["mes_ref"].nunique()
    anos_com_compra = antes[antes["venda"]].assign(ano=lambda z: z["data"].dt.year).groupby(campo)["ano"].nunique()
    r["Meses com vendas"] = meses_com_compra.reindex(nomes, fill_value=0).astype(int)
    r["Meses observados"] = meses_historicos
    r["Anos com vendas"] = anos_com_compra.reindex(nomes, fill_value=0)
    r["Anos observados"] = anos_calendario
    r["Regularidade anual (%)"] = 100 * r["Anos com vendas"] / anos_calendario
    r["Perfil"] = pd.cut(r["Regularidade anual (%)"], bins=[-1, 30, 60, 101],
                        labels=["Pontual", "Intermitente", "Recorrente"], right=False).astype(str)
    r["Última venda"] = x[x["venda"]].groupby(campo)["data"].max().reindex(nomes)
    r["Última consulta"] = x.groupby(campo)["data"].max().reindex(nomes)
    for metrica in metricas:
        r["deficit_" + metrica] = (r["historico_" + metrica] - r["atual_" + metrica]).clip(lower=0)
    r["Queda de pedidos (%)"] = 100 * (1 - r["atual_pedidos"] /
        r["historico_pedidos"].replace(0, float("nan")))
    r["Queda de valor (%)"] = 100 * (1 - r["atual_valor_vendido"] /
        r["historico_valor_vendido"].replace(0, float("nan")))
    r["Conversão histórica (%)"] = 100 * r["historico_pedidos"] / r["historico_consultas"].replace(0, float("nan"))
    r["Conversão atual (%)"] = 100 * r["atual_pedidos"] / r["atual_consultas"].replace(0, float("nan"))
    r.index.name = campo
    return r.reset_index(), x


def _recuperacao_tabela(t):
    formatos = {}
    for col in t.columns:
        if col in ["Regularidade anual", "Frequência mensal"]:
            continue
        if "(R$)" in col:
            formatos[col] = lambda v: "—" if pd.isna(v) else brl(v)
        elif "(%)" in col:
            formatos[col] = lambda v: "—" if pd.isna(v) else f"{v:.1f}%".replace(".", ",")
        elif col in ["Última venda", "Última consulta"]:
            formatos[col] = lambda v: "—" if pd.isna(v) else v.strftime("%d/%m/%Y")
        elif col not in ["Cliente", "Produto", "Família", "Perfil"] and pd.api.types.is_numeric_dtype(t[col]):
            formatos[col] = lambda v: "—" if pd.isna(v) else f"{v:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
    st.dataframe(t.style.format(formatos, na_rep="—"), hide_index=True, use_container_width=True)


def _recuperacao_produtos_cliente(base_docs, cliente, inicio_atual, meses_historicos):
    """Compara o mix do cliente com os mesmos códigos vendidos aos demais clientes."""
    # Carregamento explícito: selecionar cliente não dispara milhares de consultas.
    ids = tuple(base_docs.loc[base_docs["situacao_erp"].isin(["E", "F"]), "id"].astype(str))
    chave = (len(ids), ids[0] if ids else None, ids[-1] if ids else None)
    if st.session_state.get("ic2_rec_mix_chave") != chave:
        st.session_state.pop("ic2_rec_mix_itens", None)
        st.session_state["ic2_rec_mix_chave"] = chave
    if "ic2_rec_mix_itens" not in st.session_state:
        if not st.button("Carregar comparação de produtos", key="ic2_rec_mix_carregar"):
            st.caption("A comparação consulta os itens vendidos do histórico. Clique para carregar quando necessário.")
            return
        try:
            with st.spinner("Carregando itens vendidos para comparação..."):
                st.session_state["ic2_rec_mix_itens"] = itens(ids)
        except Exception as exc:
            st.warning("Não foi possível carregar os itens agora. Tente novamente pelo botão.")
            st.caption(f"Detalhe técnico: {type(exc).__name__}")
            return
    it = st.session_state["ic2_rec_mix_itens"]
    if it.empty:
        st.info("Não há itens disponíveis para análise de produtos.")
        return
    dados = it[["documento_id", "codigo_erp", "familia_sugerida", "quantidade", "valor_total_item"]].copy()
    dados["documento_id"] = dados["documento_id"].astype(str)
    dados["codigo_erp"] = dados["codigo_erp"].astype(str).str.strip()
    dados["familia_sugerida"] = dados["familia_sugerida"].astype(str).str.strip()
    dados = dados.merge(base_docs[["id", "cliente", "data", "situacao_erp"]].assign(
        id=lambda z: z["id"].astype(str)), left_on="documento_id", right_on="id", how="inner")
    dados = dados[dados["situacao_erp"].isin(["E", "F"])].copy()
    if dados.empty:
        st.info("Não existem itens vendidos para comparação.")
        return
    dados["janela"] = dados["data"].ge(inicio_atual).map({True: "atual", False: "historico"})
    dados["outros"] = dados["cliente"].ne(cliente)
    fator = {"historico": 12 / meses_historicos, "atual": 1.0}
    nivel = st.radio("Analisar mix por", ["Produto (código exato)", "Família"],
                     horizontal=True, key="ic2_rec_mix_nivel")
    campo = "codigo_erp" if nivel.startswith("Produto") else "familia_sugerida"
    dados["unidades_ano"] = dados["quantidade"] * dados["janela"].map(fator)
    dados["valor_ano"] = dados["valor_total_item"] * dados["janela"].map(fator)
    agrupado = dados.groupby([campo, "outros", "janela"], as_index=False)[
        ["unidades_ano", "valor_ano"]].sum()
    metricas = ["unidades_ano", "valor_ano"]
    piv = agrupado.pivot_table(index=campo, columns=["outros", "janela"],
                               values=metricas, aggfunc="sum", fill_value=0)
    def serie(metrica, outros, janela):
        chave = (metrica, outros, janela)
        return piv[chave] if chave in piv.columns else pd.Series(0.0, index=piv.index)
    res = pd.DataFrame(index=piv.index)
    for metrica, titulo in [("unidades_ano", "q"), ("valor_ano", "r")]:
        for outros, prefixo in [(False, "cliente"), (True, "mercado")]:
            for janela, sufixo in [("historico", "h"), ("atual", "a")]:
                res[f"{prefixo}_{titulo}_{sufixo}"] = serie(metrica, outros, janela)
    # Ranking considera apenas produtos historicamente vendidos ao cliente.
    res = res[(res["cliente_q_h"] > 0) | (res["cliente_r_h"] > 0)].copy()
    if res.empty:
        st.info("Este cliente não tem produtos vendidos no período histórico.")
        return
    res["perda_q"] = res["cliente_q_h"] - res["cliente_q_a"]
    res["perda_r"] = res["cliente_r_h"] - res["cliente_r_a"]
    modo = st.radio("Comparar produtos por", ["Quantidade de peças", "Valor (R$)"],
                    horizontal=True, key="ic2_rec_mix_modo")
    sufixo = "q" if modo == "Quantidade de peças" else "r"
    def tendencia(h, a):
        if h <= 0:
            return "Sem base histórica" if a > 0 else "Sem movimento"
        variacao = (a / h - 1) * 100
        if variacao < -15:
            return "Em queda"
        if variacao > 15:
            return "Em crescimento"
        return "Estável"
    def leitura(l):
        c = tendencia(l[f"cliente_{sufixo}_h"], l[f"cliente_{sufixo}_a"])
        m = tendencia(l[f"mercado_{sufixo}_h"], l[f"mercado_{sufixo}_a"])
        if c == "Em queda" and m in ["Estável", "Em crescimento"]:
            return "Perda específica do cliente"
        if c == "Em queda" and m == "Em queda":
            return "Queda também nos demais clientes"
        if c == "Em crescimento":
            return "Cliente em crescimento"
        return "Investigar"
    res["Leitura"] = res.apply(leitura, axis=1)
    res["Tendência dos demais"] = res.apply(
        lambda l: tendencia(l[f"mercado_{sufixo}_h"], l[f"mercado_{sufixo}_a"]), axis=1)
    res = res.sort_values("perda_" + sufixo, ascending=False)
    colunas = [f"cliente_{sufixo}_h", f"cliente_{sufixo}_a",
               f"mercado_{sufixo}_h", f"mercado_{sufixo}_a"]
    titulo = "Produto" if campo == "codigo_erp" else "Família"
    rotulos = ["Cliente histórico", "Cliente atual", "Demais histórico", "Demais atual"]
    if sufixo == "r":
        rotulos = [x + " (R$)" for x in rotulos]
    tabela = res[colunas + ["Tendência dos demais", "Leitura"]].rename(
        columns=dict(zip(colunas, rotulos))).reset_index().rename(columns={campo: titulo})
    st.caption("Valores equivalentes anuais. 'Demais clientes' exclui o cliente selecionado. "
               "Queda/crescimento: variação superior a 15%; critérios indicativos, não causas comprovadas.")
    _recuperacao_tabela(tabela)
    exportar(tabela, "recuperacao_mix_cliente.xlsx")
    perdas = res[res["perda_" + sufixo] > 0].head(3)
    if not perdas.empty:
        nomes = ", ".join(str(v) for v in perdas.index)
        st.info(f"Principais itens associados à redução de compras: {nomes}. "
                "Consulte a coluna 'Leitura' para diferenciar perda específica de queda generalizada.")


def _recuperacao_indicadores(linha):
    st.markdown("#### Diagnóstico do desempenho")
    itens_indicadores = [
        ("Pedidos vendidos / ano", "historico_pedidos", "atual_pedidos", False, False),
        ("Consultas / ano", "historico_consultas", "atual_consultas", False, False),
        ("Valor vendido / ano", "historico_valor_vendido", "atual_valor_vendido", True, False),
        ("Conversão por quantidade", "Conversão histórica (%)", "Conversão atual (%)", False, True),
    ]
    for par in [itens_indicadores[:2], itens_indicadores[2:]]:
        colunas = st.columns(2)
        for coluna, (titulo, chave_h, chave_a, moeda, percentual) in zip(colunas, par):
            h, a = linha[chave_h], linha[chave_a]
            def fmt(v):
                if pd.isna(v):
                    return "—"
                if moeda:
                    return brl(v)
                return (f"{v:.1f}%" if percentual else f"{v:,.1f}").replace(",", "X").replace(".", ",").replace("X", ".")
            with coluna:
                st.markdown(f"**{titulo}**")
                st.caption(f"Histórico: {fmt(h)}  |  Atual: {fmt(a)}")
                if pd.notna(h) and pd.notna(a) and h > 0:
                    delta = a - h if percentual else 100 * (a / h - 1)
                    unidade = "p.p." if percentual else "%"
                    st.caption(f"Variação: {delta:+.1f} {unidade}".replace(".", ","))
    hist_c, atual_c = linha["historico_consultas"], linha["atual_consultas"]
    hist_v, atual_v = linha["historico_pedidos"], linha["atual_pedidos"]
    if hist_c > 0 and hist_v > 0:
        dc = atual_c / hist_c - 1
        dv = atual_v / hist_v - 1
        if dc < -0.15 and dv < -0.15:
            texto = "Consultas e vendas caíram: possível retração de demanda."
        elif dc >= -0.15 and dv < -0.15:
            texto = "Consultas relativamente estáveis, vendas em queda: possível perda de conversão."
        elif dv >= 0.15:
            texto = "Vendas acima do ritmo histórico."
        else:
            texto = "Sem queda expressiva de pedidos segundo o critério de 15%."
        st.info("Leitura inicial: " + texto + " Verifique o comportamento dos produtos abaixo.")


def pagina_recuperacao(df, primeira):
    st.subheader("04 — Recuperação comercial")
    st.caption("Detecte quedas de clientes, produtos e famílias. Compare a média histórica anual "
               "com os últimos 12 meses completos, distinguindo compras recorrentes de pontuais.")
    hoje = pd.Timestamp(date.today())
    inicio_mes = hoje.replace(day=1)
    inicio_atual = inicio_mes - pd.DateOffset(months=12)
    base_docs = df[df["data"] < inicio_mes].copy()
    inicio_historico = base_docs["data"].min().to_period("M").to_timestamp() if not base_docs.empty else inicio_atual
    meses_historicos = (inicio_atual.year - inicio_historico.year) * 12 + inicio_atual.month - inicio_historico.month
    if meses_historicos < 12:
        st.info("É necessário ao menos um ano de histórico antes dos últimos 12 meses completos.")
        return
    st.caption(f"Referência histórica: {inicio_historico:%m/%Y} a {(inicio_atual - pd.Timedelta(days=1)):%m/%Y} "
               f"({meses_historicos} meses). Atual: {inicio_atual:%m/%Y} a {(inicio_mes - pd.Timedelta(days=1)):%m/%Y}. "
               "Médias apresentadas em equivalentes anuais.")
    dimensao = st.radio("Investigar", ["Clientes", "Produtos", "Famílias"], horizontal=True,
                        key="ic2_rec_dim")
    if dimensao == "Clientes":
        base = base_docs.copy()
        base["quantidade"] = 0
        campo = "cliente"
    else:
        if not st.button("Carregar itens para recuperação", key="ic2_rec_carregar") and "ic2_rec_itens" not in st.session_state:
            st.info("Carregue os itens para estudar produtos e famílias.")
            return
        if "ic2_rec_itens" not in st.session_state:
            st.session_state["ic2_rec_itens"] = itens(tuple(df["id"].astype(str)))
        it = st.session_state["ic2_rec_itens"]
        if it.empty:
            st.info("Não há itens disponíveis.")
            return
        campo = "codigo_erp" if dimensao == "Produtos" else "familia_sugerida"
        it = it.copy()
        it["documento_id"] = it["documento_id"].astype(str)
        it[campo] = it[campo].astype(str)
        it = it.groupby(["documento_id", campo], as_index=False)[["quantidade", "valor_total_item"]].sum()
        base = base_docs.copy()
        base["id"] = base["id"].astype(str)
        base = base.merge(it, left_on="id", right_on="documento_id", how="inner")
        base["valor"] = base["valor_total_item"]
    if base.empty:
        st.info("Não há movimentações nessa dimensão.")
        return
    r, detalhamento = _recuperacao_agrupar(base, campo, meses_historicos, 12, inicio_atual)
    perfil = st.selectbox("Perfil de compra", ["Recorrente", "Intermitente", "Pontual", "Todos"],
                          key="ic2_rec_perfil")
    criterio = st.radio("Priorizar perdas por", ["Pedidos", "Valor (R$)"] +
                       (["Unidades vendidas"] if dimensao != "Clientes" else []),
                       horizontal=True, key="ic2_rec_prioridade")
    chave = {"Pedidos": "pedidos", "Valor (R$)": "valor_vendido",
             "Unidades vendidas": "unidades_vendidas"}[criterio]
    r = r[r["historico_" + chave] > 0].copy()
    if perfil != "Todos":
        r = r[r["Perfil"] == perfil]
    r = r[r["deficit_" + chave] > 0].sort_values("deficit_" + chave, ascending=False)
    nome = {"Clientes": "Cliente", "Produtos": "Produto", "Famílias": "Família"}[dimensao]
    r = r.rename(columns={campo: nome})
    visual = st.radio("Exibir médias em", ["Quantidade", "Financeiro (R$)"],
                      horizontal=True, key="ic2_rec_visual")
    if visual == "Quantidade":
        medidas = [("historico_pedidos", "Vendas históricas (nº/ano)"),
                   ("atual_pedidos", "Vendas atuais (nº/ano)"),
                   ("historico_consultas", "Consultas históricas (nº/ano)"),
                   ("atual_consultas", "Consultas atuais (nº/ano)")]
    else:
        medidas = [("historico_valor_vendido", "Vendas históricas (R$)"),
                   ("atual_valor_vendido", "Vendas atuais (R$)"),
                   ("historico_valor", "Consultas históricas (R$)"),
                   ("atual_valor", "Consultas atuais (R$)")]
    tabela = r[[nome, "Perfil"] + [col for col, _ in medidas] +
               ["Conversão histórica (%)", "Conversão atual (%)", "Última venda"]].copy()
    tabela = tabela.rename(columns=dict(medidas))
    tabela.insert(6, "Regularidade anual",
                  r["Anos com vendas"].astype(int).astype(str) + " de " +
                  r["Anos observados"].astype(int).astype(str))
    tabela.insert(7, "Frequência mensal",
                  r["Meses com vendas"].astype(int).astype(str) + " de " +
                  r["Meses observados"].astype(int).astype(str))
    st.markdown("#### Maiores déficits")
    st.caption("Ordenação pelo maior déficit absoluto. Regularidade anual = anos com compras / anos observados; "
               "frequência mensal = meses com compras / meses completos do histórico. "
               "Recorrente ≥60% dos anos, intermitente ≥30%, pontual abaixo de 30%.")
    if tabela.empty:
        st.info("Nenhuma queda identificada com os filtros escolhidos.")
        return
    _recuperacao_tabela(tabela)
    exportar(tabela, "recuperacao_comercial.xlsx")
    escolha = st.selectbox(f"Detalhar {nome.lower()}", r[nome].tolist(), key="ic2_rec_alvo")
    linha = r[r[nome] == escolha].iloc[0]
    _recuperacao_indicadores(linha)
    if dimensao == "Clientes":
        st.markdown("#### Produtos que explicam a mudança")
        _recuperacao_produtos_cliente(base_docs, escolha, inicio_atual, meses_historicos)
    st.caption(f'Última venda: {linha["Última venda"]:%d/%m/%Y}' if pd.notna(linha["Última venda"]) else "Nenhuma venda registrada.")
    detalhe = detalhamento[detalhamento[campo] == escolha].copy()
    detalhe["Ano"] = detalhe["data"].dt.year.astype(int)
    anos = list(range(int(base_docs["ano"].min()), int(base_docs["ano"].max()) + 1))
    agrupado = detalhe.groupby("Ano").agg(
        **{"Vendas": ("pedidos", "sum"), "Consultas (P+E+F)": ("consultas", "sum"),
           "Valor vendido (R$)": ("valor_vendido", "sum"),
           "Valor consultado (R$)": ("valor", "sum"),
           "Unidades vendidas": ("unidades_vendidas", "sum")})
    agrupado = agrupado.reindex(anos, fill_value=0).reset_index()
    agrupado["Conversão (%)"] = (100 * agrupado["Vendas"] /
                                 agrupado["Consultas (P+E+F)"].replace(0, float("nan")))
    st.markdown("#### Evolução anual")
    st.caption("O ano em andamento mostra apenas os meses completos transcorridos; "
               "compare-o com o ritmo atual anualizado da tabela acima.")
    modo = st.radio("Visualizar", ["Quantidade", "Valor (R$)"], horizontal=True, key="ic2_rec_graf_modo")
    series = (["Vendas", "Consultas (P+E+F)"] if modo == "Quantidade"
              else ["Valor vendido (R$)", "Valor consultado (R$)"])
    dados = agrupado.melt(id_vars="Ano", value_vars=series, var_name="Indicador", value_name="Total")
    st.altair_chart(alt.Chart(dados).mark_line(point=True).encode(
        x=alt.X("Ano:O", title="Ano"), y=alt.Y("Total:Q", title=modo),
        color="Indicador:N", tooltip=["Ano:O", "Indicador:N", alt.Tooltip("Total:Q", format=",.2f")]
    ).properties(height=350), use_container_width=True)
    st.markdown("**Conversão anual por quantidade**")
    st.altair_chart(alt.Chart(agrupado).mark_line(point=True).encode(
        x=alt.X("Ano:O"), y=alt.Y("Conversão (%):Q", scale=alt.Scale(domain=[0, 100])),
        tooltip=["Ano:O", alt.Tooltip("Conversão (%):Q", format=".1f")]
    ).properties(height=220), use_container_width=True)
    _recuperacao_tabela(agrupado)
    exportar(agrupado, "recuperacao_historico_detalhado.xlsx")
    st.caption("Consultas = P+E+F; vendas = E+F. A queda de conversão é um indício, "
               "não uma confirmação de problema de preço. Valores de produtos e famílias vêm dos itens.")

def pagina_inteligencia_comercial():
    if not st.session_state.get("logado") or not tem_acesso_modulo(
        st.session_state.get("usuario"), st.session_state.get("setor"), "Inteligência Comercial"
    ):
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
    # Manter as abas; executar somente os cálculos da aba ativa.
    tabs = st.tabs(
        ["01 · Conversão", "02 · Produtos", "03 · Sazonalidade", "04 · Recuperação"],
        on_change="rerun", key="ic2_aba_ativa",
    )
    with tabs[0]:
        if tabs[0].open:
            pagina_conversao(df)
    with tabs[1]:
        if tabs[1].open:
            pagina_produtos(df, primeira)
    with tabs[2]:
        if tabs[2].open:
            pagina_sazonalidade(df, primeira)
    with tabs[3]:
        if tabs[3].open:
            pagina_recuperacao(df, primeira)
    st.caption("Classificações: Top 20, Principais perdas, Novos entrantes (sem movimentação antes de 2024), Potenciais players (compras em crescimento) e Oportunidades (orçamentos em crescimento).")

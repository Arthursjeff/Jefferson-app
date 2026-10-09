"""Dashboard comercial histórico (somente leitura)."""
from datetime import date
from io import BytesIO
import unicodedata
import altair as alt
import pandas as pd
import streamlit as st
from core.database import supabase

DOC_COLS = "id,situacao_erp,data_faturamento,data_documento,cliente_nome_erp,valor_total_cabecalho"
ITEM_COLS = "documento_id,codigo_erp,familia_sugerida,quantidade,valor_total_item"
PAGE_SIZE = 1000

def _nome_normalizado(valor):
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    return "".join(c for c in texto if not unicodedata.combining(c)).upper().replace("-", " ").replace("_", " ")

def _cliente_ficticio(valor):
    # Inclui SUL-AMERICANO, SUL AMERICANO, SULAMERICANO e variantes femininas.
    nome = " ".join(_nome_normalizado(valor).split())
    return "SUL AMERICAN" in nome or "SULAMERICAN" in nome

def _reais(valor):
    return "R$ " + f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def _chart(serie, tipo="bar", monetario=False):
    """Eixo e tooltip em BRL, mantendo os valores numéricos para agregação."""
    dados = serie.rename("valor").reset_index()
    categoria = dados.columns[0]
    dados[categoria] = dados[categoria].astype(str)
    dados["exibicao"] = dados["valor"].map(_reais if monetario else lambda v: f"{v:,.0f}".replace(",", "."))
    eixo = alt.Axis(title="Valor (R$)" if monetario else "Quantidade",
                    labelExpr="'R$ ' + format(datum.value, '.2s')" if monetario else None)
    base = alt.Chart(dados).encode(
        x=alt.X(f"{categoria}:N", title=categoria, sort=None),
        y=alt.Y("valor:Q", title="Valor (R$)" if monetario else "Quantidade", axis=eixo),
        tooltip=[alt.Tooltip(f"{categoria}:N", title=categoria),
                 alt.Tooltip("exibicao:N", title="Valor (R$)" if monetario else "Quantidade")],
    )
    grafico = base.mark_line(point=True) if tipo == "line" else base.mark_bar()
    st.altair_chart(grafico.properties(height=350), use_container_width=True)


@st.cache_data(ttl=600, show_spinner=False)
def carregar_documentos(inicio, fim):
    registros = []
    offset = 0
    while True:
        consulta = (supabase.table("documentos_comerciais")
                    .select(DOC_COLS).eq("situacao_erp", "F")
                    .gte("data_faturamento", inicio).lte("data_faturamento", fim)
                    .order("id").range(offset, offset + PAGE_SIZE - 1))
        lote = consulta.execute().data or []
        registros.extend(lote)
        if len(lote) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    df = pd.DataFrame(registros)
    if not df.empty:
        df["data"] = pd.to_datetime(df["data_faturamento"], errors="coerce")
        df["valor"] = pd.to_numeric(df["valor_total_cabecalho"], errors="coerce").fillna(0)
        df["cliente"] = df["cliente_nome_erp"].fillna("Sem identificação").astype(str).str.strip()
        df = df.loc[~df["cliente"].map(_cliente_ficticio)].copy()
    return df

@st.cache_data(ttl=600, show_spinner=False)
def carregar_itens(documentos_ids):
    if not documentos_ids:
        return pd.DataFrame()
    registros = []
    # O filtro por documento impede varredura indiscriminada dos itens de outros períodos.
    for pos in range(0, len(documentos_ids), 100):
        grupo = list(documentos_ids[pos:pos + 100])
        offset = 0
        while True:
            lote = (supabase.table("itens_comerciais").select(ITEM_COLS)
                    .in_("documento_id", grupo).order("id")
                    .range(offset, offset + PAGE_SIZE - 1).execute().data or [])
            registros.extend(lote)
            if len(lote) < PAGE_SIZE:
                break
            offset += PAGE_SIZE
    df = pd.DataFrame(registros)
    if not df.empty:
        df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce").fillna(0)
        df["valor_total_item"] = pd.to_numeric(df["valor_total_item"], errors="coerce").fillna(0)
        df["codigo_erp"] = df["codigo_erp"].fillna("Não identificado")
        df["familia_sugerida"] = df["familia_sugerida"].fillna("Não classificada")
    return df

def _exportar(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Dados", index=False)
    return buffer.getvalue()

def _grafico(df, coluna, metrica, titulo, limite=20):
    st.subheader(titulo)
    if df.empty:
        st.info("Sem dados para os filtros selecionados.")
        return
    agrupado = df.groupby(coluna, dropna=False)[metrica].sum().sort_values(ascending=False).head(limite)
    _chart(agrupado, monetario=metrica in ("valor", "valor_total_item"))
    with st.expander("Ver tabela e exportar"):
        tabela = agrupado.rename(metrica).reset_index()
        if metrica in ("valor", "valor_total_item"):
            st.dataframe(tabela.style.format({metrica: _reais}), use_container_width=True, hide_index=True)
        else:
            st.dataframe(tabela, use_container_width=True, hide_index=True)
        st.download_button("Exportar Excel", _exportar(tabela), file_name="jefferson_analise.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           key=f"export_{titulo}")

def pagina_inteligencia_comercial():
    if not st.session_state.get("logado") or st.session_state.get("setor") != "ADMINISTRADOR":
        st.error("Acesso restrito ao administrador.")
        st.stop()

    st.title("Inteligência Comercial")
    st.caption("Dashboard histórico | documentos faturados (F) | cliente fictício Sul-Americano excluído das análises | dados originais preservados")
    with st.expander("Filtros gerais", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            intervalo = st.date_input("Período de faturamento", (date(2020, 1, 1), date.today()),
                                      min_value=date(2020, 1, 1), max_value=date.today(),
                                      key="ic_periodo")
        with c2:
            agrupamento = st.selectbox("Agrupamento temporal", ["Mensal", "Diário", "Anual"])
        if not isinstance(intervalo, (tuple, list)) or len(intervalo) != 2:
            st.info("Selecione as duas datas.")
            return
        inicio, fim = intervalo
        if inicio > fim:
            st.warning("Data inicial maior que a final.")
            return
    try:
        with st.spinner("Consultando faturamentos..."):
            docs = carregar_documentos(inicio.isoformat(), fim.isoformat())
    except Exception as exc:
        st.error("Não foi possível consultar os documentos comerciais. Verifique as permissões e as colunas do Supabase.")
        st.caption(type(exc).__name__)
        return
    if docs.empty:
        st.warning("Nenhum documento faturado com data de faturamento neste período.")
        return
    nomes = sorted(docs["cliente"].unique().tolist())
    clientes = st.multiselect("Clientes (vazio = todos)", nomes, key="ic_clientes")
    if clientes:
        docs = docs[docs["cliente"].isin(clientes)].copy()
    if docs.empty:
        st.info("Nenhum documento para os clientes escolhidos.")
        return

    k1,k2,k3,k4 = st.columns(4)
    total = float(docs["valor"].sum())
    k1.metric("Faturamento", f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    k2.metric("Clientes ativos", docs["cliente"].nunique())
    k3.metric("Documentos F", docs["id"].nunique())
    k4.metric("Ticket médio", f"R$ {total/max(docs['id'].nunique(),1):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    geral, aba_clientes, produtos, personalizado = st.tabs(["Geral", "Clientes", "Produtos", "Personalizado"])
    with geral:
        freq = {"Mensal":"MS", "Diário":"D", "Anual":"YS"}[agrupamento]
        evolucao = docs.dropna(subset=["data"]).set_index("data")["valor"].resample(freq).sum()
        st.subheader("Evolução do faturamento")
        _chart(evolucao, tipo="line", monetario=True)
        st.caption("Somente situação F; data_faturamento. Valores nominais, sem ajuste de inflação.")
        c1,c2 = st.columns(2)
        with c1:
            st.subheader("Documentos por período")
            contagem = docs.dropna(subset=["data"]).set_index("data")["id"].resample(freq).count()
            _chart(contagem)
        with c2:
            st.subheader("Ticket médio por período")
            ticket = evolucao.div(contagem.where(contagem.ne(0)))
            _chart(ticket.dropna(), tipo="line", monetario=True)
        st.download_button("Exportar documentos filtrados", _exportar(docs.drop(columns=["data"])),
                           file_name="documentos_faturados.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with aba_clientes:
        top = st.selectbox("Exibir ranking", [5,10,20,50,100,500,100000], index=2,
                           format_func=lambda x: "Todos" if x==100000 else f"Top {x}")
        _grafico(docs, "cliente", "valor", "Ranking de clientes por faturamento", top)
        ativos = docs.dropna(subset=["data"]).copy()
        ativos["periodo"] = ativos["data"].dt.to_period("M").astype(str)
        serie = ativos.groupby("periodo")["cliente"].nunique()
        st.subheader("Clientes ativos por mês")
        _chart(serie, tipo="line")
    with produtos:
        st.caption("Produtos e famílias usam valores dos itens; podem diferir do faturamento do cabeçalho.")
        if st.button("Carregar dados de produtos", key="ic_carregar_itens"):
            st.session_state["ic_itens_solicitados"] = True
        if st.session_state.get("ic_itens_solicitados"):
            try:
                with st.spinner("Consultando itens dos documentos selecionados..."):
                    itens = carregar_itens(tuple(docs["id"].dropna().astype(str).tolist()))
                if itens.empty:
                    st.info("Não foram encontrados itens vinculados aos documentos filtrados.")
                else:
                    indicador = st.selectbox("Métrica de produtos", ["Valor dos itens", "Quantidade"])
                    metrica = "valor_total_item" if indicador=="Valor dos itens" else "quantidade"
                    limite = st.selectbox("Top produtos/famílias", [10,20,50,100,100000], index=1,
                                          format_func=lambda x: "Todos" if x==100000 else f"Top {x}")
                    _grafico(itens, "familia_sugerida", metrica, "Ranking de famílias", limite)
                    _grafico(itens, "codigo_erp", metrica, "Ranking de códigos ERP", limite)
                    if metrica=="quantidade":
                        st.warning("Quantidades somadas podem incluir produtos ou unidades diferentes; use o filtro por código para comparações técnicas.")
            except Exception as exc:
                st.error("Não foi possível consultar os itens comerciais.")
                st.caption(type(exc).__name__)
    with personalizado:
        st.caption("Construtor inicial: escolha uma dimensão e uma métrica; os filtros gerais permanecem aplicados.")
        dimensao = st.selectbox("Dimensão", ["Cliente", "Mês", "Ano"])
        medida = st.selectbox("Métrica", ["Faturamento", "Documentos"])
        limite = st.selectbox("Limite de categorias", [10,20,50,100,100000], index=1,
                              format_func=lambda x: "Todas" if x==100000 else str(x))
        base = docs.copy()
        if dimensao=="Mês":
            base["categoria"] = base["data"].dt.to_period("M").astype(str)
        elif dimensao=="Ano":
            base["categoria"] = base["data"].dt.year.astype(str)
        else:
            base["categoria"] = base["cliente"]
        coluna = "valor" if medida=="Faturamento" else "id"
        agregado = (base.groupby("categoria")[coluna].sum() if medida=="Faturamento"
                    else base.groupby("categoria")["id"].nunique())
        agregado = agregado.sort_values(ascending=False).head(limite)
        tipo = st.radio("Visualização", ["Barras", "Linha", "Tabela"], horizontal=True)
        if tipo=="Barras":
            _chart(agregado, monetario=medida=="Faturamento")
        elif tipo=="Linha":
            _chart(agregado, tipo="line", monetario=medida=="Faturamento")
        else:
            tabela_personalizada = agregado.rename(medida).reset_index()
            if medida=="Faturamento":
                st.dataframe(tabela_personalizada.style.format({medida: _reais}), use_container_width=True)
            else:
                st.dataframe(tabela_personalizada, use_container_width=True)
        st.download_button("Exportar gráfico personalizado",
                           _exportar(agregado.rename(medida).reset_index()),
                           file_name="grafico_personalizado.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

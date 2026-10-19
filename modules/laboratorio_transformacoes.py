"""Laboratório administrativo/operacional para simular transformações."""
import io
import pandas as pd
import streamlit as st
from core.motor_transformacoes import avaliar, consolidar_estoque, normalizar


def _ler_estoque(arquivo):
    nome = arquivo.name.lower()
    if nome.endswith(".xlsx"):
        df = pd.read_excel(arquivo, dtype=str)
    else:
        dados = arquivo.getvalue()
        try:
            df = pd.read_csv(io.BytesIO(dados), sep=None, engine="python", dtype=str,
                             encoding="utf-8-sig")
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(dados), sep=None, engine="python", dtype=str,
                             encoding="latin1")
    return df.fillna("")


def pagina_laboratorio_transformacoes():
    st.title("Laboratório de Transformações")
    st.caption("Simulador de regras e estoque provisório. Sem movimentações, reservas ou gravações no Supabase.")
    with st.expander("Estoque de teste", expanded=True):
        arquivo = st.file_uploader(
            "Carregar relatório ERP (.csv ou .xlsx)", type=["csv", "xlsx"],
            key="transformacoes_arquivo")
        if arquivo is None:
            st.info("Para iniciar, carregue seu estoque provisório do ERP ou use o exemplo fictício abaixo.")
            usar_demo = st.checkbox("Usar estoque fictício de demonstração", value=False)
            if not usar_demo:
                st.stop()
            dados = pd.DataFrame([
                {"codigo": "1335BE04", "quantidade": 5, "numero_serie": ""},
                {"codigo": "Z1335BA04", "quantidade": 2, "numero_serie": ""},
            ])
        else:
            try:
                dados = _ler_estoque(arquivo)
            except Exception as exc:
                st.error(f"Não foi possível ler o relatório: {exc}")
                st.stop()
        st.caption(f"{len(dados)} linhas recebidas. Informe quais colunas representam código e quantidade.")
        colunas = list(dados.columns)
        c1, c2, c3 = st.columns(3)
        def sugestao(palavras, padrao=0):
            return next((i for i, c in enumerate(colunas)
                         if any(p in str(c).lower() for p in palavras)), padrao)
        with c1:
            col_codigo = st.selectbox("Coluna do código", colunas,
                                    index=sugestao(("cód", "cod", "item", "produto")))
        with c2:
            col_qtd = st.selectbox("Coluna da quantidade", colunas,
                                 index=sugestao(("quant", "qtd", "saldo")))
        with c3:
            opcoes_serie = ["(sem série)"] + colunas
            col_serie = st.selectbox("Coluna da série (opcional)", opcoes_serie,
                                    index=next((i+1 for i, c in enumerate(colunas)
                                                if "série" in str(c).lower() or "serie" in str(c).lower()), 0))
        registros = [{
            "codigo": linha[col_codigo],
            "quantidade": linha[col_qtd],
            "numero_serie": linha[col_serie] if col_serie != "(sem série)" else "",
        } for _, linha in dados.iterrows()]
        saldos, series, rejeitados = consolidar_estoque(registros)
        if rejeitados:
            st.warning(f"{len(rejeitados)} linhas ignoradas por código ou quantidade inválidos.")
        st.metric("Códigos distintos no teste", len(saldos))
        if col_serie != "(sem série)":
            st.caption("Séries são lidas para estrutura futura, mas ainda não são consumidas ou movimentadas.")

    st.subheader("Simular transformação")
    codigo = st.text_input("Código técnico vendido", value="Z1335BE04")
    tipo = st.radio("Tipo de transformação", ("Torre", "Vedação", "Corpo"),
                    horizontal=True)
    metodos = ("Válvula–Válvula", "Válvula–Kit") if tipo == "Vedação" else ("Válvula–Válvula",)
    metodo = st.radio("Origem do componente", metodos, horizontal=True)
    if st.button("Analisar possibilidades", type="primary"):
        st.session_state["laboratorio_transformacoes_resultado"] = avaliar(
            codigo, tipo.upper().replace("Ç", "C").replace("Ã", "A"),
            "VALVULA_KIT" if metodo == "Válvula–Kit" else "VALVULA_VALVULA",
            saldos)
    resultado = st.session_state.get("laboratorio_transformacoes_resultado")
    if not resultado:
        return
    if normalizar(codigo) != resultado["destino"]:
        st.info("O código mudou. Clique em Analisar possibilidades para atualizar a simulação.")
        return
    st.subheader("Resultado da análise")
    st.write("Destino:", resultado["destino"])
    st.write("Saldo exato informado:", resultado["estoque_exato"])
    if resultado["base"]:
        st.success("Base candidata localizada no estoque provisório.")
        st.dataframe(pd.DataFrame(resultado["base"]), hide_index=True, use_container_width=True)
    if resultado["doadores"]:
        st.write("Origens homologadas disponíveis para o componente:")
        opcoes = [x["codigo"] for x in resultado["doadores"]]
        st.selectbox("Selecione a origem utilizada", opcoes)
        st.caption("A escolha é apenas uma simulação e não será gravada.")
    if resultado["pendencias"]:
        for texto in resultado["pendencias"]:
            st.warning(texto)
    st.caption("Nenhuma peça é presumida compatível apenas por aparência do código. "
               "As regras de doadores, kits e produtos residuais serão cadastradas por família.")

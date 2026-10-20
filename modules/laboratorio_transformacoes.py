"""Laboratório administrativo/operacional para simular transformações."""
import io
import pandas as pd
import streamlit as st
from core.motor_transformacoes import avaliar, consolidar_estoque, normalizar, calcular_residual_corpo, calcular_residual_torre
from core.transformacoes_kit_2030 import OPCOES, parse as parse_kit_2030, avaliar as avaliar_kit_2030, calcular_residual as calcular_residual_kit_2030


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
    tipo = st.radio("Tipo de transformação", ("Torre", "Kit de Reparo", "Corpo"),
                    horizontal=True)
    op_kit = None
    carreteis = {}
    if tipo == "Kit de Reparo":
        if parse_kit_2030(codigo):
            op_kit = st.radio("Operação de Kit de Reparo", list(OPCOES),
                              format_func=lambda v: OPCOES[v], horizontal=True)
            if op_kit == "NA_NF" and parse_kit_2030(codigo)["vedacao"] == "A":
                st.caption("Buna-N: identifique os códigos reais ERP dos carretéis G4 NA e NF. "
                           "O laboratório não inventa referências de estoque.")
                col_na, col_nf = st.columns(2)
                with col_na:
                    carreteis["NA"] = normalizar(st.text_input("Código ERP do carretel NA", key="kit_carretel_na"))
                with col_nf:
                    carreteis["NF"] = normalizar(st.text_input("Código ERP do carretel NF", key="kit_carretel_nf"))
        else:
            st.info("Operações de Kit de Reparo disponíveis para 2030L grande "
                    "(12/16 e 10 R/D) ou 1330L de 1 polegada (10), em A/V.")
        metodo = "Válvula–Válvula"
    else:
        metodo = "Válvula–Válvula"
    if st.button("Analisar possibilidades", type="primary"):
        if tipo == "Kit de Reparo":
            st.session_state["laboratorio_transformacoes_resultado"] = avaliar_kit_2030(
                codigo, op_kit, saldos, carreteis)
        else:
            st.session_state["laboratorio_transformacoes_resultado"] = avaliar(
                codigo, tipo.upper(), "VALVULA_VALVULA", saldos)
    resultado = st.session_state.get("laboratorio_transformacoes_resultado")
    if not resultado:
        return
    tipo_atual = "KIT" if tipo == "Kit de Reparo" else tipo.upper()
    if (normalizar(codigo) != resultado["destino"]
            or tipo_atual != resultado["tipo"]
            or (tipo_atual == "KIT" and op_kit != resultado.get("operacao"))):
        st.info("A seleção mudou. Clique em Analisar possibilidades para atualizar a simulação.")
        return
    st.subheader("Resultado da análise")
    st.write("Destino:", resultado["destino"])
    st.write("Saldo exato informado:", resultado["estoque_exato"])
    if resultado["tipo"] == "KIT":
        st.caption("Operação: " + OPCOES.get(resultado.get("operacao"), "não cadastrada"))
        st.write("Configuração vendida:", resultado.get("configuracao", "não reconhecida"))
        if resultado.get("codigo_base_esperado"):
            st.write("Base esperada:")
            st.code(resultado["codigo_base_esperado"])
        if resultado.get("codigo_kit_esperado"):
            st.write("Kit esperado:")
            st.code(resultado["codigo_kit_esperado"])
        if resultado["base"]:
            st.success("Bases disponíveis encontradas no estoque provisório.")
            st.dataframe(pd.DataFrame(resultado["base"]), hide_index=True, use_container_width=True)
        if resultado["doadores"]:
            st.success("Origens disponíveis encontradas no estoque provisório.")
            st.dataframe(pd.DataFrame(resultado["doadores"]), hide_index=True, use_container_width=True)
        if resultado["base"] and resultado["doadores"]:
            base = st.selectbox("Escolha a válvula base", [x["codigo"] for x in resultado["base"]],
                                key="kit_base", format_func=lambda v: v)
            doadora = st.selectbox("Escolha a doadora / kit / carretel",
                                   [x["codigo"] for x in resultado["doadores"]],
                                   key="kit_doadora")
            try:
                simu = calcular_residual_kit_2030(resultado, base, doadora, carreteis)
            except ValueError as exc:
                st.warning("Combinação ainda não validada: " + str(exc))
            else:
                st.subheader("Resultado da transformação por kit")
                col_saida, col_retorno = st.columns(2)
                with col_saida:
                    st.markdown("**Válvula vendida**")
                    st.code(simu["produto_final"])
                with col_retorno:
                    st.markdown("**Residual previsto (" + simu["tipo_residual"] + ")**")
                    st.code(simu["produto_residual"])
                assinatura = (simu["produto_final"], simu["valvula_base"],
                              simu["origem"], simu["produto_residual"])
                if st.button("Validar os dois códigos", key="validar_residual_kit"):
                    st.session_state["residual_kit_validado"] = assinatura
                if st.session_state.get("residual_kit_validado") == assinatura:
                    st.success("Códigos validados pelo operador nesta simulação.")
                else:
                    st.info("Confirme produto final e residual antes de validar.")
        for pendencia in resultado["pendencias"]:
            st.warning(pendencia)
        st.caption("Simulação técnica; não baixa nem reserva válvulas, carretéis ou kits. "
                   "A execução real requer conferência dos conjuntos G2/G4 e seus componentes.")
        return
    if resultado["tipo"] == "CORPO" and resultado.get("codigo_base_esperado"):
        st.write(
            f"Corpo solicitado: **{resultado['conexao_destino']}**. "
            f"Buscar válvula base com corpo **{resultado['conexao_base']}**:"
        )
        st.code(resultado["codigo_base_esperado"])
        st.caption("Todos os demais atributos técnicos permanecem no código.")
    if resultado["tipo"] == "TORRE":
        st.write("Conjunto solicitado:", resultado.get("construcao_torre", "não identificado"))
        if resultado.get("codigo_base_esperado"):
            st.write("Base esperada:")
            st.code(resultado["codigo_base_esperado"])
        if resultado.get("grupo_torre"):
            st.caption("Grupo de compatibilidade G1: " + resultado["grupo_torre"])
    if resultado["base"]:
        st.success("Base candidata localizada no estoque provisório.")
        st.dataframe(pd.DataFrame(resultado["base"]), hide_index=True, use_container_width=True)
    if resultado["doadores"]:
        st.write("Válvulas doadoras compatíveis encontradas no estoque:" if resultado["tipo"] == "CORPO" else "Origens homologadas disponíveis para o componente:")
        opcoes = [x["codigo"] for x in resultado["doadores"]]
        legendas = {x["codigo"]: x for x in resultado["doadores"]}
        doadora = st.selectbox("Selecione a origem utilizada", opcoes,
            format_func=lambda c: ("%s — prioridade %s — saldo %s" %
                (c, legendas[c]["prioridade"], legendas[c]["quantidade"]))
                if "prioridade" in legendas[c] else c)
        st.caption("A origem selecionada é apenas uma simulação. Nenhum item será consumido ou reservado.")
        if resultado["tipo"] == "TORRE" and resultado["base"]:
            try:
                simulacao_torre = calcular_residual_torre(resultado, doadora)
            except ValueError as exc:
                st.warning(str(exc))
            else:
                st.subheader("Resultado da troca de torre")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Válvula vendida**")
                    st.code(simulacao_torre["produto_final"])
                with c2:
                    st.markdown("**Válvula residual prevista**")
                    st.code(simulacao_torre["produto_residual"])
                st.caption(simulacao_torre["observacao"])
                assinatura_torre = (simulacao_torre["produto_final"],
                                   simulacao_torre["valvula_base"],
                                   simulacao_torre["valvula_doadora"],
                                   simulacao_torre["produto_residual"])
                if st.button("Validar códigos da transformação de torre", key="validar_residual_torre"):
                    st.session_state["residual_torre_validado"] = assinatura_torre
                if st.session_state.get("residual_torre_validado") == assinatura_torre:
                    st.success("Códigos validados pelo operador nesta simulação.")
                else:
                    st.info("Confira a válvula vendida e o residual antes de validar.")
        if resultado["tipo"] == "CORPO":
            if resultado["base"]:
                try:
                    simulacao = calcular_residual_corpo(resultado, doadora)
                except ValueError as exc:
                    st.warning(f"Não foi possível calcular o residual: {exc}")
                else:
                    st.subheader("Resultado da troca de corpos")
                    esquerda, direita = st.columns(2)
                    with esquerda:
                        st.markdown("**Válvula final (pedido)**")
                        st.code(simulacao["produto_final"])
                    with direita:
                        st.markdown("**Válvula residual (retorno)**")
                        st.code(simulacao["produto_residual"])
                    st.caption(
                        f"Retirar corpo {simulacao['corpo_destino']} de {doadora}, "
                        f"transferir para {simulacao['valvula_base']} e montar "
                        f"o corpo {simulacao['corpo_origem']} na válvula doadora."
                    )
                    assinatura = (
                        simulacao["produto_final"], simulacao["valvula_base"],
                        simulacao["valvula_doadora"], simulacao["produto_residual"]
                    )
                    if st.button("Validar os dois códigos", key="validar_residual_corpo"):
                        st.session_state["residual_corpo_validado"] = assinatura
                    if st.session_state.get("residual_corpo_validado") == assinatura:
                        st.success("Códigos validados pelo operador nesta simulação.")
                    else:
                        st.info("Confirme os códigos da válvula vendida e da válvula residual.")
            else:
                st.warning("A válvula base não está disponível para formar o produto final.")
    if resultado.get("doadores_combinadas"):
        st.warning("Opções de prioridade 3: torre compatível com vedação diferente. Necessitam transformação combinada, ainda não implementada.")
        st.dataframe(pd.DataFrame(resultado["doadores_combinadas"]), hide_index=True, use_container_width=True)
    if resultado["pendencias"]:
        for texto in resultado["pendencias"]:
            st.warning(texto)
    st.caption("As sugestões usam regras por família, tamanho e rosca. "
               "A validação não movimenta estoque e não substitui a conferência técnica física.")

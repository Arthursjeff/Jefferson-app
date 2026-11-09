"""Laboratório administrativo/operacional para simular transformações."""
import io
import hashlib
import json
import logging
import pandas as pd
import streamlit as st
from core.motor_transformacoes import avaliar, consolidar_estoque, normalizar, calcular_residual_corpo, calcular_residual_torre, diagnosticar_componentes_torre
from core.transformacoes_kit_2030 import OPCOES, parse as parse_kit_2030, avaliar as avaliar_kit_2030, calcular_residual as calcular_residual_kit_2030
from core.catalogo_transformacoes import (
    listar_receitas, disponibilidade_receita, registrar_receita,
)
from core.permissoes import tem_acesso_modulo
from core.estoque_referencia import carregar_estoque_referencia
from core.conversor_erp_estoque import converter as converter_codigo_erp
from modules.laboratorio_catalogo_ui import (
    interface_cadastro_manual, interface_homologacao,
)

logger = logging.getLogger(__name__)


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



def _buscar_receitas(destino, grau=None):
    try:
        receitas = listar_receitas(destino, grau)
    except Exception:
        logger.exception("Falha na consulta do catálogo de transformações")
        st.warning("A biblioteca do Supabase não pôde ser consultada. A simulação continua disponível.")
        return None
    return receitas


def _mostrar_receitas(receitas, saldos=None):
    if not receitas:
        st.info("Nenhuma receita técnica validada encontrada para este produto.")
        return
    linhas = []
    for r in receitas:
        entradas = r.get("entradas") or []
        saidas = r.get("saidas") or []
        por_papel = {e.get("papel"): e.get("codigo") for e in entradas + saidas}
        disponivel = disponibilidade_receita(r, saldos) if saldos is not None else None
        linhas.append({
            "Grau": r.get("grau"),
            "Operação": r.get("subtipo"),
            "Base": por_papel.get("BASE", ""),
            "Doadora": por_papel.get("DOADORA", ""),
            "Residual": por_papel.get("RESIDUAL", ""),
            "Validações": r.get("total_validacoes", 0),
            "Quantidade na referência": ("Consta no levantamento" if disponivel else "Sem saldo registrado")
                                         if disponivel is not None else "Não consultado",
            "_disponivel": bool(disponivel),
        })
    linhas.sort(key=lambda x: (not x["_disponivel"], -(x["Validações"] or 0)))
    st.dataframe(pd.DataFrame([{k: v for k, v in linha.items() if k != "_disponivel"}
                               for linha in linhas]), hide_index=True, use_container_width=True)
    st.caption("A quantidade exibida é apenas a da referência histórica ou do arquivo importado. "
               "Não garante disponibilidade atual nem movimenta estoque.")


def _salvar_possibilidade(resultado, simulacao, saldos, demonstracao, chave):
    """A confirmação técnica cadastra receita, nunca movimenta estoque."""
    if demonstracao:
        st.warning("O estoque fictício é apenas para testes; não pode alimentar a biblioteca.")
        return
    if st.button("Salvar possibilidade no Supabase", key=chave):
        usuario = st.session_state.get("usuario")
        setor = st.session_state.get("setor")
        if not tem_acesso_modulo(usuario, setor, "Laboratório de Transformações"):
            st.error("Seu usuário não tem permissão para cadastrar possibilidades.")
            return
        estado = "VALIDADA" if setor == "ADMINISTRADOR" else "PENDENTE"
        try:
            receita, nova = registrar_receita(
                resultado, simulacao, usuario, estado=estado,
                origem="LABORATORIO",
                observacao=("Proposta técnica conferida pelo operador no motor; "
                            "estoque de referência não representa disponibilidade atual."),
            )
        except ValueError as erro:
            st.warning(str(erro))
        except Exception:
            logger.exception("Falha ao registrar receita técnica no Supabase")
            st.error("Não foi possível salvar no Supabase. Consulte o log do aplicativo.")
        else:
            if nova:
                st.success("Receita homologada no Supabase." if estado == "VALIDADA"
                           else "Proposta registrada como PENDENTE para homologação.")
            else:
                st.info("Esta combinação já está no Supabase; não foi duplicada.")
            atualizadas = _buscar_receitas(resultado["destino"], receita["grau"])
            if atualizadas is not None:
                st.session_state["laboratorio_catalogo_resultado"] = (
                    resultado["destino"], receita["grau"], atualizadas
                )


@st.cache_data(ttl=300, show_spinner=False)
def _obter_estoque_referencia_cache():
    return carregar_estoque_referencia()


def _chave_estoque(saldos):
    serializado = json.dumps(sorted(saldos.items()), separators=(",", ":"))
    return hashlib.sha256(serializado.encode("utf-8")).hexdigest()


def pagina_laboratorio_transformacoes():
    st.title("Laboratório de Transformações")
    st.caption("Simule com estoque ERP provisório e salve receitas validadas no Supabase. "
               "Salvar uma possibilidade nunca movimenta ou reserva estoque.")
    with st.expander("Biblioteca de transformações já validadas", expanded=False):
        codigo_busca = st.text_input("Código desejado para consultar a biblioteca", key="busca_codigo_catalogo")
        if st.button("Consultar receitas", key="consultar_catalogo"):
            st.session_state["laboratorio_catalogo_busca"] = (
                normalizar(codigo_busca), _buscar_receitas(codigo_busca)
            )
        busca = st.session_state.get("laboratorio_catalogo_busca")
        if busca and busca[0] == normalizar(codigo_busca) and busca[1] is not None:
            _mostrar_receitas(busca[1])
    interface_cadastro_manual()
    interface_homologacao()
    demonstracao = False
    with st.expander("Estoque para simulação", expanded=True):
        fonte = st.radio(
            "Fonte dos códigos e quantidades",
            ("Supabase — referência histórica", "Importar arquivo ERP", "Estoque fictício"),
            key="laboratorio_fonte_estoque", horizontal=True,
        )
        if fonte == "Supabase — referência histórica":
            try:
                inventario, saldos = _obter_estoque_referencia_cache()
            except Exception:
                logger.exception("Falha ao carregar o estoque historico do laboratorio")
                st.error("Estoque histórico indisponível no Supabase. "
                         "Use Importar arquivo ERP ou tente novamente.")
                st.stop()
            st.warning("SALDOS HISTÓRICOS, NÃO ATUALIZADOS. Referência de 03/11/2026; "
                       "não usar para confirmar atendimento de pedidos.")
            st.caption("Base compartilhada: " + inventario["referencia_externa"])
            st.metric("Códigos técnicos na referência", len(saldos))
        else:
            if fonte == "Estoque fictício":
                demonstracao = True
                dados = pd.DataFrame([
                    {"codigo": "1335BE04", "quantidade": 5, "numero_serie": ""},
                    {"codigo": "Z1335BA04", "quantidade": 2, "numero_serie": ""},
                ])
            else:
                arquivo = st.file_uploader(
                    "Carregar relatório ERP (.csv ou .xlsx)", type=["csv", "xlsx"],
                    key="transformacoes_arquivo")
                if arquivo is None:
                    st.info("Selecione um arquivo de estoque ou volte para a referência compartilhada.")
                    st.stop()
                try:
                    dados = _ler_estoque(arquivo)
                except Exception as exc:
                    st.error(f"Não foi possível ler o relatório: {exc}")
                    st.stop()
            st.caption(f"{len(dados)} linhas recebidas. Indique as colunas de código e quantidade.")
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
                col_serie = st.selectbox(
                    "Coluna da série (opcional)", opcoes_serie,
                    index=next((i + 1 for i, x in enumerate(colunas)
                                if "série" in str(x).lower() or "serie" in str(x).lower()), 0),
                )
            desc_col = next((x for x in colunas if "descri" in str(x).lower()), None)
            interpretar_erp = (st.checkbox(
                "Interpretar códigos ERP e conferir com a descrição",
                value=desc_col is not None,
                disabled=desc_col is None,
                help="Somente equivalências CONFIRMADAS entram na simulação; "
                     "as demais ficam na revisão e não somam ao saldo.",
                key="converter_erp_no_laboratorio"
            ) if not demonstracao else False)
            registros = []
            pendentes_conversao = []
            for _, linha in dados.iterrows():
                codigo_bruto = linha[col_codigo]
                codigo_final = codigo_bruto
                if interpretar_erp:
                    descricao = str(linha[desc_col] or "")
                    convertido = converter_codigo_erp(codigo_bruto, descricao)
                    if convertido.status != "CONFIRMADO":
                        pendentes_conversao.append({
                            "ERP": codigo_bruto,
                            "Status": convertido.status,
                            "Código sugerido": convertido.codigo_tecnico or "",
                            "Motivo": convertido.motivo,
                        })
                        continue
                    codigo_final = convertido.codigo_tecnico
                registros.append({
                    "codigo": codigo_final,
                    "quantidade": linha[col_qtd],
                    "numero_serie": linha[col_serie] if col_serie != "(sem série)" else "",
                })
            if interpretar_erp:
                st.caption(f"Conversor ERP: {len(registros)} linhas confirmadas; "
                           f"{len(pendentes_conversao)} não incluídas no saldo de simulação.")
                if pendentes_conversao:
                    with st.expander("Conferir conversões não confirmadas"):
                        st.dataframe(pd.DataFrame(pendentes_conversao),
                                     hide_index=True, use_container_width=True)
            saldos, _, rejeitados = consolidar_estoque(registros)
            if rejeitados:
                st.warning(f"{len(rejeitados)} linhas ignoradas por código ou quantidade inválidos.")
            st.metric("Códigos distintos na simulação", len(saldos))
            if col_serie != "(sem série)":
                st.caption("Séries são lidas apenas como referência, sem movimentação.")
            if not demonstracao:
                st.warning("Os saldos do arquivo importado não são confirmados em tempo real.")

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
    chave_atual = _chave_estoque(saldos)
    if st.button("Analisar possibilidades", type="primary"):
        st.session_state["laboratorio_estoque_analisado"] = chave_atual
        st.session_state["laboratorio_fonte_analisada"] = fonte
        st.session_state["laboratorio_carretel_analisado"] = dict(carreteis)
        if tipo == "Kit de Reparo":
            st.session_state["laboratorio_transformacoes_resultado"] = avaliar_kit_2030(
                codigo, op_kit, saldos, carreteis)
        else:
            st.session_state["laboratorio_transformacoes_resultado"] = avaliar(
                codigo, tipo.upper(), "VALVULA_VALVULA", saldos)
        grau_consulta = "KIT_REPARO" if tipo == "Kit de Reparo" else tipo.upper()
        cadastradas = _buscar_receitas(codigo, grau_consulta)
        st.session_state["laboratorio_catalogo_resultado"] = (
            normalizar(codigo), grau_consulta, cadastradas
        )
    resultado = st.session_state.get("laboratorio_transformacoes_resultado")
    if not resultado:
        return
    tipo_atual = "KIT" if tipo == "Kit de Reparo" else tipo.upper()
    if (normalizar(codigo) != resultado["destino"]
            or tipo_atual != resultado["tipo"]
            or (tipo_atual == "KIT" and op_kit != resultado.get("operacao"))
            or chave_atual != st.session_state.get("laboratorio_estoque_analisado")
            or fonte != st.session_state.get("laboratorio_fonte_analisada")
            or (tipo_atual == "KIT" and carreteis != st.session_state.get("laboratorio_carretel_analisado"))):
        st.info("A seleção ou os saldos mudaram. Clique em Analisar possibilidades para atualizar a simulação.")
        return
    catalogo = st.session_state.get("laboratorio_catalogo_resultado")
    grau_catalogo = "KIT_REPARO" if tipo_atual == "KIT" else tipo_atual
    if catalogo and catalogo[0:2] == (resultado["destino"], grau_catalogo) and catalogo[2]:
        st.subheader("Receitas já validadas — prioridade de consulta")
        _mostrar_receitas(catalogo[2], saldos)
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
                    _salvar_possibilidade(resultado, simu, saldos, demonstracao, "salvar_kit_catalogo")
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
        st.write("Válvulas doadoras compatíveis encontradas no estoque:" if resultado["tipo"] == "CORPO" else "Conjuntos G1 doadores compatíveis:")
        opcoes = [x["codigo"] for x in resultado["doadores"]]
        legendas = {x["codigo"]: x for x in resultado["doadores"]}
        doadora = st.selectbox("Selecione a origem utilizada", opcoes,
            format_func=lambda c: ("%s — prioridade %s — saldo %s" %
                (c, legendas[c]["prioridade"], legendas[c]["quantidade"]))
                if "prioridade" in legendas[c] else c)
        st.caption("A origem selecionada é apenas uma simulação. Nenhum item será consumido ou reservado.")
        if resultado["tipo"] == "TORRE" and resultado["base"]:
            bases_validas = legendas[doadora].get("bases_compativeis", [])
            base_torre = (st.selectbox("Selecione a válvula base", bases_validas,
                                      key="torre_base")
                          if len(bases_validas) > 1 else
                          bases_validas[0] if bases_validas else None)
            try:
                simulacao_torre = calcular_residual_torre(resultado, doadora, base_torre)
                diagnostico_g1 = diagnosticar_componentes_torre(resultado, doadora, base_torre)
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
                st.markdown("**Permuta integral dos conjuntos G1**")
                st.caption("A base recebe o conjunto completo da doadora; a doadora recebe o conjunto completo da base.")
                if diagnostico_g1["divergencias"]:
                    st.error("Troca bloqueada: incompatibilidades técnicas G1 detectadas.")
                    for divergencia in diagnostico_g1["divergencias"]:
                        st.warning(divergencia)
                else:
                    st.success("Conjuntos G1 compatíveis pelas regras técnicas cadastradas.")
                    st.caption("A única exceção admitida é a diferença de material da mola inox 303/304.")
                    assinatura_torre = (simulacao_torre["produto_final"],
                                       simulacao_torre["valvula_base"],
                                       simulacao_torre["valvula_doadora"],
                                       simulacao_torre["produto_residual"])
                    if st.button("Validar os dois códigos e a troca integral G1", key="validar_residual_torre"):
                        st.session_state["residual_torre_validado"] = assinatura_torre
                    if st.session_state.get("residual_torre_validado") == assinatura_torre:
                        st.success("Troca integral G1 validada nesta simulação, sem movimentação de estoque.")
                        _salvar_possibilidade(resultado, simulacao_torre, saldos, demonstracao, "salvar_torre_catalogo")
                    else:
                        st.info("Confira os códigos da válvula vendida e do residual.")
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
                        _salvar_possibilidade(resultado, simulacao, saldos, demonstracao, "salvar_corpo_catalogo")
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

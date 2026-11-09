"""Cadastro manual e homologação de possibilidades; não altera estoque."""
import logging

import streamlit as st

from core.catalogo_transformacoes import (
    registrar_receita, listar_pendentes, homologar_pendente,
)
from core.motor_transformacoes import familia, normalizar
from core.permissoes import tem_acesso_modulo

logger = logging.getLogger(__name__)


def interface_cadastro_manual():
    with st.expander("Cadastrar transformação conhecida — sem depender do saldo", expanded=False):
        st.caption("Use para uma combinação tecnicamente conhecida, mesmo fora do estoque histórico. "
                   "As propostas manuais ficam PENDENTES até a homologação administrativa.")
        with st.form("form_transf_manual", clear_on_submit=True):
            tipo = st.selectbox("Grau da transformação", ["TORRE", "CORPO", "KIT"])
            operacao = (st.selectbox("Operação do kit", ["NA_NF", "VEDACAO", "REFORCO"])
                        if tipo == "KIT" else None)
            a = st.text_input("A — Código do produto desejado")
            b = st.text_input("B — Código da válvula base")
            c = st.text_input("C — Código da doadora, kit ou carretel")
            d = st.text_input("D — Código do produto residual")
            obs = st.text_area("Justificativa técnica e componentes conferidos", max_chars=2000)
            enviar = st.form_submit_button("Enviar possibilidade para homologação")
        if not enviar:
            return
        usuario, setor = st.session_state.get("usuario"), st.session_state.get("setor")
        if not tem_acesso_modulo(usuario, setor, "Laboratório de Transformações"):
            st.error("Usuário sem acesso ao Laboratório.")
            return
        a, b, c, d = (normalizar(x) for x in (a, b, c, d))
        if not all((a, b, c, d)) or not obs.strip():
            st.warning("Preencha os quatro códigos e a justificativa técnica.")
            return
        if not familia(a):
            st.warning("O código do produto desejado não possui uma família reconhecível.")
            return
        resultado = {
            "tipo": tipo, "destino": a, "familia": familia(a),
            "operacao": operacao, "metodo": "VALVULA_VALVULA",
        }
        simulacao = {
            "produto_final": a, "valvula_base": b,
            "valvula_doadora": c, "produto_residual": d,
        }
        try:
            _, nova = registrar_receita(
                resultado, simulacao, usuario, estado="PENDENTE",
                origem="LABORATORIO_MANUAL", observacao=obs,
            )
        except ValueError as erro:
            st.warning(str(erro))
        except Exception:
            logger.exception("Falha no cadastro manual de transformação")
            st.error("Não foi possível enviar a possibilidade ao Supabase.")
        else:
            st.success("Proposta criada e enviada à homologação." if nova else
                       "Essa proposta já estava cadastrada no Supabase.")


def interface_homologacao():
    if st.session_state.get("setor") != "ADMINISTRADOR":
        return
    with st.expander("Homologação de possibilidades pendentes — administrador", expanded=False):
        if st.button("Atualizar lista de pendentes", key="consultar_pendentes_lab"):
            try:
                st.session_state["pendentes_lab"] = listar_pendentes()
            except Exception:
                logger.exception("Falha na consulta de propostas pendentes")
                st.error("Não foi possível consultar receitas pendentes.")
                return
        pendentes = st.session_state.get("pendentes_lab")
        if pendentes is None:
            st.caption("Clique para consultar a fila de propostas técnicas.")
            return
        if not pendentes:
            st.success("Nenhuma possibilidade pendente.")
            return
        st.caption(f"{len(pendentes)} propostas na lista. Verifique componentes e códigos antes de homologar.")
        opcoes = {r["id"]: r for r in pendentes}
        escolha = st.selectbox("Possibilidade para conferência", list(opcoes),
                               format_func=lambda v: (
                                   f"{opcoes[v]['produto_final']} — {opcoes[v]['grau']} "
                                   f"— cadastrado por {opcoes[v].get('registrada_por') or '?'}"))
        registro = opcoes[escolha]
        st.write("**Produto final:**", registro["produto_final"])
        st.write("**Entradas:**", registro["entradas"])
        st.write("**Saídas:**", registro["saidas"])
        st.write("**Justificativa:**", registro.get("observacao") or "Sem observação")
        confirmado = st.checkbox(
            "Conferi tecnicamente a base, a doadora, o produto e o residual.",
            key=f"homologar_confirma_{escolha}")
        if st.button("Homologar receita selecionada", disabled=not confirmado,
                     key=f"homologar_receita_{escolha}"):
            try:
                homologar_pendente(
                    escolha, st.session_state.get("usuario"), st.session_state.get("setor"))
            except Exception:
                logger.exception("Falha ao homologar possibilidade técnica")
                st.error("Não foi possível homologar. Atualize a lista e confira o registro.")
            else:
                st.session_state["pendentes_lab"] = None
                st.success("Receita homologada no Supabase e liberada para recomendação.")

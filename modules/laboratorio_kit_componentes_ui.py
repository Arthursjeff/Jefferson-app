"""Formulário guiado de componentes de kits para a equipe de Montagem."""
import logging

import pandas as pd
import streamlit as st

from core.catalogo_kit_componentes import (
    MODOS, GRUPOS, TIPOS, preparar_proposta_componentes,
)
from core.catalogo_transformacoes import (
    registrar_proposta_componentes_kit, corrigir_referencias_kit_pendente,
)
from core.permissoes import tem_acesso_modulo

logger = logging.getLogger(__name__)


def interface_kit_componentes():
    with st.expander("Kits por componentes — G2 / G3 / G4 / G5", expanded=False):
        st.caption(
            "Cadastre um kit montado com várias peças ou uma transformação de válvula "
            "com kit, carretel, diafragma, O-rings e reforços. Não é necessário saldo no ERP. "
            "Tudo fica PENDENTE até a homologação técnica."
        )
        with st.form("form_kit_por_componentes"):
            modo = st.selectbox("Tipo de montagem", list(MODOS), format_func=lambda x: MODOS[x])
            final = st.text_input("Produto final Jefferson", placeholder="K030AR2 ou 2030LAR12")
            base = st.text_input("Válvula base (se transformar uma válvula)",
                                 disabled=modo != "ALTERAR_VALVULA")
            st.markdown("**Peças utilizadas**")
            st.caption("Acrescente linhas com o botão +. Sem código ERP, deixe o campo Código vazio "
                       "e descreva a peça para identificação posterior.")
            modelo = pd.DataFrame([{
                "grupo": "G2", "tipo": "COMPONENTE", "codigo": "",
                "descricao": "", "quantidade": 1.0,
            }])
            editor = st.data_editor(
                modelo, num_rows="dynamic", hide_index=True,
                use_container_width=True, key="editor_componentes_kit",
                column_config={
                    "grupo": st.column_config.SelectboxColumn(
                        "Grupo (G2 a G5)", options=list(GRUPOS), required=True),
                    "tipo": st.column_config.SelectboxColumn(
                        "Tipo", options=list(TIPOS), required=True),
                    "codigo": st.column_config.TextColumn("Código ERP (opcional)"),
                    "descricao": st.column_config.TextColumn("Nome da peça"),
                    "quantidade": st.column_config.NumberColumn(
                        "Quantidade", min_value=0.001, max_value=1000, step=1.0),
                },
            )
            situacao = st.selectbox(
                "O que acontece com os componentes retirados?",
                ["NAO_HA_SOBRA", "RETORNO_IDENTIFICADO", "DESCARTE"],
                format_func=lambda x: {
                    "NAO_HA_SOBRA": "Não há sobra identificada",
                    "RETORNO_IDENTIFICADO": "Forma um residual com código",
                    "DESCARTE": "Peças retiradas serão descartadas",
                }[x],
            )
            residual = st.text_input("Código do residual", disabled=situacao != "RETORNO_IDENTIFICADO")
            observacao = st.text_area(
                "Justificativa técnica", max_chars=2000,
                placeholder="Descreva material, componentes trocados e o destino das peças antigas.",
            )
            enviar = st.form_submit_button("Registrar composição como PENDENTE", type="primary")
        if not enviar:
            return
        usuario, setor = st.session_state.get("usuario"), st.session_state.get("setor")
        if not tem_acesso_modulo(usuario, setor, "Laboratório de Transformações"):
            st.error("Sem acesso ao Laboratório.")
            return
        itens = [x for x in editor.to_dict("records")
                 if str(x.get("codigo") or "").strip() or str(x.get("descricao") or "").strip()]
        try:
            proposta = preparar_proposta_componentes(
                modo, final, base, itens, usuario, observacao,
                residual=residual, destino_residual=situacao,
            )
            _, nova = registrar_proposta_componentes_kit(proposta)
        except ValueError as erro:
            st.warning(str(erro))
        except Exception:
            logger.exception("Erro no cadastro de composição de kit")
            st.error("Não foi possível gravar a proposta no Supabase.")
        else:
            st.success("Proposta registrada como PENDENTE." if nova
                       else "Essa composição já estava registrada; não foi duplicada.")
            qtd = len(proposta["parametros_tecnicos"]["codigos_sem_erp"])
            if qtd:
                st.warning(f"{qtd} peça(s) sem código ERP. O administrador precisa "
                           "identificá-las antes de homologar.")


def interface_corrigir_kit_pendente(registro):
    """Corrige marcadores temporários de uma composição ainda não homologada."""
    parametros = registro.get("parametros_tecnicos") or {}
    faltantes = set(parametros.get("codigos_sem_erp") or [])
    if not faltantes:
        return
    st.warning("A proposta contém peças sem referência ERP. Preencha seus códigos reais "
               "para liberar a homologação.")
    with st.form("corrigir_referencias_" + registro["id"]):
        correcoes = {}
        for item in parametros.get("componentes") or []:
            anterior = item.get("codigo") or ""
            if anterior not in faltantes:
                continue
            rotulo = f"{item.get('grupo')}: {item.get('descricao')}"
            correcoes[anterior] = st.text_input("Código ERP — " + rotulo,
                                               key="ref_kit_" + registro["id"] + anterior)
        salvar = st.form_submit_button("Salvar identificação das peças")
    if salvar:
        try:
            corrigir_referencias_kit_pendente(
                registro["id"], {k: v for k, v in correcoes.items() if str(v).strip()},
                st.session_state.get("usuario"), st.session_state.get("setor"),
            )
        except ValueError as erro:
            st.warning(str(erro))
        except Exception:
            logger.exception("Falha ao corrigir códigos de peças do kit")
            st.error("Não foi possível corrigir as referências.")
        else:
            st.session_state["pendentes_lab"] = None
            st.success("Referências corrigidas. Atualize a lista de pendentes.")

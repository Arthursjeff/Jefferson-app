import streamlit as st
from core import (
    init_session,
    inject_css,
    gate_login,
    render_fila,
    render_criar_pedido,
)

st.set_page_config(
    page_title="Sistema de Pedidos",
    layout="wide",
)

init_session()
inject_css()

# =========================
# NÃO LOGADO
# =========================
if not st.session_state.logado:
    st.markdown(
        """
        <style>
          [data-testid="stSidebar"] { visibility: hidden; }
        </style>
        """,
        unsafe_allow_html=True
    )

    gate_login()
    st.stop()

# =========================
# LOGADO
# =========================
st.markdown(
    """
    <style>
      [data-testid="stSidebar"] { visibility: visible; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🏠 Sistema de Pedidos")
st.caption(
    f"Logado como **{st.session_state.nome_usuario}** "
    f"({st.session_state.setor_usuario})"
)

# =========================
# SIDEBAR ÚNICA
# =========================
with st.sidebar:
    st.markdown("## 📁 Navegação")

    pagina = st.radio(
        "",
        ["Fila de Pedidos", "Criar Pedido"],
        index=0
    )

    st.divider()

    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# =========================
# CONTEÚDO
# =========================
if pagina == "Criar Pedido":
    render_criar_pedido()
else:
    render_fila()

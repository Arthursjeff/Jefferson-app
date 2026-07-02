import streamlit as st
from core import (
    init_session,
    inject_css,
    gate_login,
    render_fila
)

st.set_page_config(page_title="Fila de Pedidos", layout="wide")

init_session()
inject_css()


if not st.session_state.get("logado", False):
    st.switch_page("app.py")

render_fila()

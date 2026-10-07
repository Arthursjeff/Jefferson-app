import streamlit as st
from modules.modulo_orcamentos.contatos_repository import salvar_comprador


def formulario_comprador(cliente_id, chave, contato=None):
    contato = contato or {}
    with st.form(chave):
        nome = st.text_input('Nome do comprador', value=contato.get('nome') or '')
        c1, c2 = st.columns(2)
        whatsapp = c1.text_input('WhatsApp', value=contato.get('whatsapp') or '')
        email = c2.text_input('E-mail', value=contato.get('email') or '')
        st.caption('Nome obrigatório. Preencha pelo menos WhatsApp ou e-mail.')
        ativo = st.checkbox('Comprador ativo', value=contato.get('ativo', True)) if contato else True
        salvar = st.form_submit_button('Salvar comprador' if contato else 'Cadastrar comprador', type='primary')
    if salvar:
        try:
            return salvar_comprador(cliente_id, nome, whatsapp, email, contato.get('id'), ativo)
        except Exception as erro:
            st.error(str(erro))
    return None

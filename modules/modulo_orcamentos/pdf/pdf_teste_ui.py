import streamlit as st
from datetime import date

from modules.modulo_orcamentos.pdf.gerador_pdf_teste import (
    gerar_pdf_orcamento,
)


def mostrar_teste_pdf(
    numero_orcamento,
    cliente,
    itens,
    observacao_geral,
    responsavel,
):

    st.divider()

    st.subheader("Protótipo visual do PDF")

    st.caption(
        "Esta versão usa dados fictícios apenas para desenvolvimento do layout."
    )

    if st.button(
        "Gerar protótipo PDF",
        use_container_width=True,
    ):

        pdf_bytes = gerar_pdf_orcamento(
            numero_orcamento=numero_orcamento,
            data_orcamento=date.today().strftime(
            "%d/%m/%Y"
            ),
            cliente=cliente,
            itens=itens,
            observacao_geral=observacao_geral,
            responsavel=responsavel,
        )

        st.session_state["pdf_teste_bytes"] = pdf_bytes


    if "pdf_teste_bytes" in st.session_state:

        pdf_bytes = st.session_state["pdf_teste_bytes"]

        st.success(
            "PDF gerado. Use o botão abaixo para abrir ou baixar."
        )

        st.download_button(
            "Abrir / Baixar protótipo PDF",
            data=pdf_bytes,
            file_name="proposta_jefferson_v3_teste.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

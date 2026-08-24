import base64

import streamlit as st

from modules.modulo_orcamentos.pdf.gerador_pdf_teste import (
    gerar_pdf_teste,
)


def mostrar_teste_pdf():

    st.divider()

    st.subheader("Protótipo visual do PDF")

    st.caption(
        "Esta versão usa dados fictícios apenas para desenvolvimento do layout."
    )

    if st.button(
        "Gerar protótipo PDF",
        use_container_width=True,
    ):

        pdf_bytes = gerar_pdf_teste()

        st.session_state["pdf_teste_bytes"] = pdf_bytes


    if "pdf_teste_bytes" in st.session_state:

        pdf_bytes = st.session_state["pdf_teste_bytes"]

        base64_pdf = base64.b64encode(
            pdf_bytes
        ).decode("utf-8")

        st.markdown(
            f"""
            <iframe
                src="data:application/pdf;base64,{base64_pdf}"
                width="100%"
                height="850"
                style="border:1px solid #ddd; border-radius:8px;"
            ></iframe>
            """,
            unsafe_allow_html=True,
        )

        st.download_button(
            "Baixar protótipo PDF",
            data=pdf_bytes,
            file_name="proposta_jefferson_v3_teste.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

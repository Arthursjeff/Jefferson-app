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

    st.subheader(
        "Gerar PDF do orçamento"
    )


    # =========================================================
    # GERAR PDF
    # =========================================================

    if st.button(
        "Gerar PDF",
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


        # =====================================================
        # GUARDAR PDF NO SESSION STATE
        # =====================================================

        st.session_state[
            "pdf_teste_bytes"
        ] = pdf_bytes


    # =========================================================
    # PDF GERADO
    # =========================================================

    if (
        "pdf_teste_bytes"
        in st.session_state
    ):

        pdf_bytes = (
            st.session_state[
                "pdf_teste_bytes"
            ]
        )


        # =====================================================
        # NÚMERO DO ORÇAMENTO
        # =====================================================
        #
        # Exemplo:
        #
        # 3288/26
        #
        # vira:
        #
        # 3288-26
        #
        # Isso evita problema com "/" no nome do arquivo.
        # =====================================================

        numero_arquivo = (
            str(
                numero_orcamento
                or "ORCAMENTO"
            )
            .strip()
            .replace(
                "/",
                "-"
            )
            .replace(
                "\\",
                "-"
            )
        )


        # =====================================================
        # NOME DO CLIENTE
        # =====================================================
        #
        # Prioridade:
        #
        # 1. Razão social
        # 2. Nome fantasia
        # 3. CLIENTE
        #
        # Depois pegamos somente a primeira palavra.
        # =====================================================

        nome_cliente = (
            cliente.get(
                "razao_social"
            )
            or cliente.get(
                "nome_fantasia"
            )
            or "CLIENTE"
        )


        primeiro_nome_cliente = (
            str(
                nome_cliente
            )
            .strip()
            .split()[0]
        )


        # =====================================================
        # NOME DO VENDEDOR
        # =====================================================
        #
        # Também pegamos somente o primeiro nome.
        # =====================================================

        if responsavel:

            nome_vendedor = (
                str(
                    responsavel
                )
                .strip()
                .split()[0]
            )

        else:

            nome_vendedor = (
                "VENDEDOR"
            )


        # =====================================================
        # NOME FINAL DO ARQUIVO
        # =====================================================
        #
        # Formato:
        #
        # Número orçamento - Cliente - Vendedor.pdf
        #
        # Exemplo:
        #
        # 3288-26 - METROVAL - Arthur.pdf
        #
        # =====================================================

        nome_arquivo = (
            f"{numero_arquivo} - "
            f"{primeiro_nome_cliente} - "
            f"{nome_vendedor}.pdf"
        )


        # =====================================================
        # RESULTADO
        # =====================================================

        st.success(
            "PDF gerado com sucesso."
        )


        st.download_button(
            "Abrir / Baixar PDF",
            data=pdf_bytes,
            file_name=nome_arquivo,
            mime="application/pdf",
            use_container_width=True,
        )

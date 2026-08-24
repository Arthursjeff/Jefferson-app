import streamlit as st

from core.clientes_importer import (
    preparar_clientes,
    dataframe_para_registros,
)

from core.clientes_database import importar_clientes_supabase

def pagina_importar_clientes():

    st.title("👥 Importação da Base de Clientes")

    st.write(
        "Envie o arquivo Excel bruto exportado pelo ERP. "
        "O sistema fará a seleção e tratamento das colunas automaticamente."
    )

    arquivo = st.file_uploader(
        "Arquivo de clientes",
        type=["xlsx", "xls"],
        key="arquivo_clientes",
    )

    if arquivo is None:
        st.info("Selecione o arquivo Excel exportado pelo ERP.")
        return

    try:

        with st.spinner("Processando arquivo..."):

            clientes, relatorio = preparar_clientes(
                arquivo
            )

        st.success("Arquivo processado com sucesso.")

        st.subheader("Resumo da importação")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Clientes no arquivo",
            relatorio["linhas_original"]
        )

        c2.metric(
            "Clientes processados",
            relatorio["linhas_processadas"]
        )

        c3.metric(
            "Colunas recebidas",
            relatorio["colunas_original"]
        )

        c4.metric(
            "Colunas utilizadas",
            relatorio["colunas_utilizadas"]
        )

        if relatorio["linhas_sem_codigo"] > 0:

            st.warning(
                f'{relatorio["linhas_sem_codigo"]} '
                "linha(s) foram ignoradas porque não possuem código."
            )

        codigos_nao_mapeados = relatorio[
            "codigos_tipo_cliente_nao_mapeados"
        ]

        if codigos_nao_mapeados:

            st.warning(
                "Foram encontrados códigos de tipo de cliente "
                "que ainda não estão mapeados."
            )

            st.write(codigos_nao_mapeados)

        if relatorio["colunas_nao_encontradas"]:

            with st.expander(
                "Colunas esperadas não encontradas"
            ):

                st.write(
                    relatorio[
                        "colunas_nao_encontradas"
                    ]
                )

        st.subheader("Prévia dos dados tratados")

        st.dataframe(
            clientes.head(100),
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        st.subheader("Atualizar base de clientes")

        st.warning(
            "Ao confirmar, os clientes existentes serão atualizados "
            "e os novos clientes serão adicionados ao Supabase."
        )

        confirmar = st.checkbox(
            "Confirmo que revisei a prévia e desejo atualizar a base.",
            key="confirmar_importacao_clientes",
        )

        if st.button(
            "Confirmar e atualizar Supabase",
            type="primary",
            disabled=not confirmar,
            use_container_width=True,
        ):

            try:

                registros = dataframe_para_registros(clientes)

                barra = st.progress(
                    0,
                    text="Preparando atualização..."
                )

                with st.spinner(
                    "Atualizando a base de clientes..."
                ):

                    resultado = importar_clientes_supabase(
                        registros
                    )

                barra.progress(
                    100,
                    text="Atualização concluída."
                )

                st.success(
                    f'Base atualizada com sucesso. '
                    f'{resultado["processados"]} clientes processados '
                    f'em {resultado["lotes"]} lote(s).'
                )

            except Exception as erro:

                st.error(
                    f"Erro ao atualizar Supabase: {erro}"
                )

    except Exception as erro:

        st.error(
            f"Erro ao processar arquivo: {erro}"
        )

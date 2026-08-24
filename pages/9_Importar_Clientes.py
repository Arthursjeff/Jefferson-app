import streamlit as st

from core.clientes_importer import preparar_clientes


st.set_page_config(
    page_title="Importar Clientes",
    page_icon="👥",
    layout="wide",
)


st.title("Importação da Base de Clientes")

st.write(
    "Envie o arquivo Excel bruto exportado pelo ERP. "
    "O sistema fará a seleção e tratamento das colunas automaticamente."
)


arquivo = st.file_uploader(
    "Arquivo de clientes",
    type=["xlsx", "xls"],
)


if arquivo is not None:

    try:

        with st.spinner("Processando arquivo..."):

            clientes, relatorio = preparar_clientes(
                arquivo
            )

        st.success("Arquivo processado com sucesso.")

        st.subheader("Resumo")

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

        if relatorio[
            "codigos_tipo_cliente_nao_mapeados"
        ]:

            st.warning(
                "Foram encontrados códigos de tipo de cliente "
                "que ainda não existem no mapa:"
            )

            st.write(
                relatorio[
                    "codigos_tipo_cliente_nao_mapeados"
                ]
            )

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

        st.info(
            "Nesta etapa os dados ainda NÃO foram enviados "
            "ao Supabase."
        )

    except Exception as erro:

        st.error(
            f"Erro ao processar arquivo: {erro}"
        )

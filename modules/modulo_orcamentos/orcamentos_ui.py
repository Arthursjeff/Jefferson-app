import streamlit as st

from modules.modulo_orcamentos.clientes_repository import buscar_clientes


def pagina_orcamentos():

    st.title("📄 Novo Orçamento")

    # ======================================================
    # DADOS DO ORÇAMENTO
    # ======================================================

    st.subheader("Dados do orçamento")

    numero_orcamento = st.text_input(
        "Número do orçamento",
        placeholder="Ex.: 3288/26",
        key="orcamento_numero",
    )

    # ======================================================
    # CLIENTE
    # ======================================================

    st.subheader("Cliente")

    busca_cliente = st.text_input(
        "Buscar cliente",
        placeholder="Digite código, razão social, nome fantasia ou CNPJ/CPF",
        key="orcamento_busca_cliente",
    )

    cliente_selecionado = None

    if busca_cliente.strip():

        try:

            clientes = buscar_clientes(busca_cliente)

            if not clientes:

                st.warning("Nenhum cliente encontrado.")

            else:

                opcoes_clientes = {}

                for cliente in clientes:

                    codigo = cliente.get("codigo_cliente") or ""
                    razao = (
                        cliente.get("razao_social")
                        or cliente.get("nome_fantasia")
                        or ""
                    )
                    documento = cliente.get("cnpj_cpf") or ""

                    label = f"{codigo} | {razao} | {documento}"

                    opcoes_clientes[label] = cliente

                escolha_cliente = st.selectbox(
                    "Selecione o cliente",
                    options=list(opcoes_clientes.keys()),
                    key="orcamento_cliente_select",
                )

                cliente_selecionado = opcoes_clientes[
                    escolha_cliente
                ]

        except Exception as erro:

            st.error(
                f"Erro ao buscar cliente: {erro}"
            )

    # ======================================================
    # CLIENTE SELECIONADO
    # ======================================================

    if cliente_selecionado:

        st.success("Cliente selecionado.")

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric(
                "Código",
                cliente_selecionado.get(
                    "codigo_cliente"
                ) or "-"
            )

        with c2:
            st.metric(
                "CNPJ/CPF",
                cliente_selecionado.get(
                    "cnpj_cpf"
                ) or "-"
            )

        with c3:
            st.metric(
                "Tipo de cliente",
                cliente_selecionado.get(
                    "tipo_cliente"
                ) or "-"
            )

        st.write(
            "**Razão Social:** "
            + (
                cliente_selecionado.get(
                    "razao_social"
                )
                or "-"
            )
        )

        st.write(
            "**Nome Fantasia:** "
            + (
                cliente_selecionado.get(
                    "nome_fantasia"
                )
                or "-"
            )
        )

        st.write(
            "**Cidade/UF:** "
            + (
                cliente_selecionado.get(
                    "cidade"
                )
                or "-"
            )
            + " / "
            + (
                cliente_selecionado.get(
                    "estado"
                )
                or "-"
            )
        )

        st.write(
            "**E-mail:** "
            + (
                cliente_selecionado.get(
                    "email"
                )
                or "-"
            )
        )

    st.divider()

    # ======================================================
    # PRÓXIMA ETAPA
    # ======================================================

    st.subheader("Itens do orçamento")

    st.info(
        "Na próxima etapa vamos adicionar "
        "código, tensão, quantidade, valor unitário e prazo."
    )

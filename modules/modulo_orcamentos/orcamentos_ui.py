import streamlit as st

from modules.modulo_orcamentos.clientes_repository import buscar_clientes
from modules.modulo_orcamentos.orcamentos_repository import salvar_orcamento

OPCOES_TENSAO = [
    "110/60HZ",
    "220/60HZ",
    "24VCC",
    "12VCC",
    "110/50HZ",
    "220/50HZ",
    "OUTRO",
]

OPCOES_PRAZO = [
    "IMEDIATO",
    "5 DIAS",
    "10 DIAS",
    "15 DIAS",
    "20 DIAS",
    "30 DIAS",
    "45 DIAS",
    "60 DIAS",
    "OUTRO",
]


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

    # ======================================================
    # ITENS DO ORÇAMENTO
    # ======================================================

    st.subheader("Itens do orçamento")

    # Inicializa a lista de itens
    if "orcamento_itens" not in st.session_state:
        st.session_state.orcamento_itens = []

    # ======================================================
    # ITENS JÁ ADICIONADOS
    # ======================================================

    if st.session_state.orcamento_itens:

        st.write("### Itens adicionados")

        total_orcamento = 0

        for indice, item in enumerate(
            st.session_state.orcamento_itens
        ):

            total_item = (
                item["quantidade"]
                * item["valor_unitario"]
            )

            total_orcamento += total_item

            with st.container(border=True):

                c1, c2 = st.columns([5, 1])

                with c1:

                    st.markdown(
                        f"### Item {indice + 1} — "
                        f"{item['codigo']}"
                    )

                    st.write(
                        f"**Tensão:** {item['tensao']}"
                    )

                    st.write(
                        f"**Quantidade:** "
                        f"{item['quantidade']}"
                    )

                    st.write(
                        f"**Valor unitário:** "
                        f"R$ {item['valor_unitario']:,.2f}"
                    )

                    st.write(
                        f"**Total do item:** "
                        f"R$ {total_item:,.2f}"
                    )

                    st.write(
                        f"**Prazo:** "
                        f"{item['prazo']}"
                    )

                    if item["observacao"]:

                        st.write(
                            f"**Observação:** "
                            f"{item['observacao']}"
                        )

                with c2:

                    if st.button(
                        "Excluir",
                        key=f"excluir_item_{indice}",
                        use_container_width=True,
                    ):

                        st.session_state.orcamento_itens.pop(
                            indice
                        )

                        st.rerun()

        st.metric(
            "Total do orçamento",
            f"R$ {total_orcamento:,.2f}"
        )

        st.divider()

    # ======================================================
    # ADICIONAR NOVO ITEM
    # ======================================================

    st.write("### Adicionar item")

    with st.form(
        "form_adicionar_item",
        clear_on_submit=True,
    ):

        codigo = st.text_input(
            "Código do produto",
            placeholder="Ex.: 1335BA04T",
        )

        tensao_selecionada = st.selectbox(
            "Tensão",
            options=OPCOES_TENSAO,
            index=None,
            placeholder="Digite para buscar...",
        )

        if tensao_selecionada == "OUTRO":
            tensao = st.text_input(
                "Outra tensão",
                placeholder="Digite a tensão manualmente",
            )
        else:
            tensao = tensao_selecionada or ""

        c1, c2 = st.columns(2)

        with c1:

            quantidade = st.number_input(
                "Quantidade",
                min_value=1,
                value=1,
                step=1,
            )

        with c2:

            valor_unitario = st.number_input(
                "Valor unitário (R$)",
                min_value=0.0,
                value=0.0,
                step=0.01,
                format="%.2f",
            )

        prazo_selecionado = st.selectbox(
            "Prazo",
            options=OPCOES_PRAZO,
            index=None,
            placeholder="Digite para buscar...",
        )

        if prazo_selecionado == "OUTRO":
            prazo = st.text_input(
                "Outro prazo",
                placeholder="Digite o prazo manualmente",
            )
        else:
            prazo = prazo_selecionado or ""
        
        observacao = st.text_area(
            "Observação do item",
            placeholder="Opcional",
        )

        adicionar_item = st.form_submit_button(
            "Adicionar item",
            type="primary",
            use_container_width=True,
        )

    if adicionar_item:

        if not codigo.strip():

            st.warning(
                "Informe o código do produto."
            )

        elif not tensao.strip():

            st.warning(
                "Informe a tensão."
            )

        elif not prazo.strip():

            st.warning(
                "Informe o prazo."
            )

        else:

            novo_item = {
                "codigo": codigo.strip().upper(),
                "tensao": tensao.strip().upper(),
                "quantidade": int(quantidade),
                "valor_unitario": float(
                    valor_unitario
                ),
                "prazo": prazo.strip(),
                "observacao": observacao.strip(),
            }

            st.session_state.orcamento_itens.append(
                novo_item
            )

            st.rerun()


    st.divider()

    st.subheader("Observações gerais")

    observacao_geral = st.text_area(
        "Observação do orçamento",
        placeholder="Informações gerais que devem constar no orçamento...",
        key="orcamento_observacao_geral",
    )


    st.divider()

    salvar = st.button(
        "💾 Salvar orçamento",
        type="primary",
        use_container_width=True,
    )

    if salvar:

        if not numero_orcamento.strip():

            st.warning(
                "Informe o número do orçamento."
            )

        elif not cliente_selecionado:

            st.warning(
                "Selecione um cliente."
            )

        elif not st.session_state.orcamento_itens:

            st.warning(
                "Adicione pelo menos um item."
            )

        else:

            try:

                with st.spinner(
                    "Salvando orçamento..."
                ):

                    orcamento_salvo = salvar_orcamento(
                        numero_orcamento=numero_orcamento,
                        cliente=cliente_selecionado,
                        itens=st.session_state.orcamento_itens,
                        criado_por=st.session_state.nome,
                        observacao_geral=observacao_geral,
                    )

                st.success(
                    f'Orçamento '
                    f'{orcamento_salvo["numero_orcamento"]} '
                    f'salvo com sucesso.'
                )

            except Exception as erro:

                st.error(
                    f"Erro ao salvar orçamento: {erro}"
                )

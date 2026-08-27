import streamlit as st

from modules.modulo_orcamentos.clientes_repository import (
    buscar_clientes,
)

from modules.modulo_orcamentos.orcamentos_repository import (
    salvar_orcamento,
)

from motor_descricao import (
    processar_produto,
)

from modules.modulo_orcamentos.imagens_repository import (
    obter_url_imagem,
)

from modules.modulo_orcamentos.pdf.pdf_teste_ui import (
    mostrar_teste_pdf,
)


# =============================================================
# OPÇÕES
# =============================================================

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


# =============================================================
# PÁGINA DE ORÇAMENTOS
# =============================================================

def pagina_orcamentos():

    st.title("📄 Novo Orçamento")


    # =========================================================
    # DADOS DO ORÇAMENTO
    # =========================================================

    st.subheader("Dados do orçamento")

    numero_orcamento = st.text_input(
        "Número do orçamento",
        placeholder="Ex.: 3288/26",
        key="orcamento_numero",
    )


    # =========================================================
    # CLIENTE
    # =========================================================

    st.subheader("Cliente")

    busca_cliente = st.text_input(
        "Buscar cliente",
        placeholder=(
            "Digite código, razão social, "
            "nome fantasia ou CNPJ/CPF"
        ),
        key="orcamento_busca_cliente",
    )

    cliente_selecionado = None


    if busca_cliente.strip():

        try:

            clientes = buscar_clientes(
                busca_cliente
            )

            if not clientes:

                st.warning(
                    "Nenhum cliente encontrado."
                )

            else:

                opcoes_clientes = {}

                for cliente in clientes:

                    codigo_cliente = (
                        cliente.get(
                            "codigo_cliente"
                        )
                        or ""
                    )

                    razao = (
                        cliente.get(
                            "razao_social"
                        )
                        or cliente.get(
                            "nome_fantasia"
                        )
                        or ""
                    )

                    documento = (
                        cliente.get(
                            "cnpj_cpf"
                        )
                        or ""
                    )

                    label = (
                        f"{codigo_cliente} | "
                        f"{razao} | "
                        f"{documento}"
                    )

                    opcoes_clientes[
                        label
                    ] = cliente


                escolha_cliente = st.selectbox(
                    "Selecione o cliente",
                    options=list(
                        opcoes_clientes.keys()
                    ),
                    key="orcamento_cliente_select",
                )

                cliente_selecionado = (
                    opcoes_clientes[
                        escolha_cliente
                    ]
                )


        except Exception as erro:

            st.error(
                f"Erro ao buscar cliente: {erro}"
            )


    # =========================================================
    # CLIENTE SELECIONADO
    # =========================================================

    if cliente_selecionado:

        st.success(
            "Cliente selecionado."
        )

        c1, c2, c3 = st.columns(3)


        with c1:

            st.metric(
                "Código",
                cliente_selecionado.get(
                    "codigo_cliente"
                )
                or "-"
            )


        with c2:

            st.metric(
                "CNPJ/CPF",
                cliente_selecionado.get(
                    "cnpj_cpf"
                )
                or "-"
            )


        with c3:

            st.metric(
                "Tipo de cliente",
                cliente_selecionado.get(
                    "tipo_cliente"
                )
                or "-"
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


    # =========================================================
    # ITENS DO ORÇAMENTO
    # =========================================================

    st.subheader(
        "Itens do orçamento"
    )


    # =========================================================
    # INICIALIZAR ITENS
    # =========================================================

    if "orcamento_itens" not in st.session_state:

        st.session_state.orcamento_itens = []


    # =========================================================
    # ITENS JÁ ADICIONADOS
    # =========================================================

    if st.session_state.orcamento_itens:

        st.write(
            "### Itens adicionados"
        )

        total_orcamento = 0


        for indice, item in enumerate(
            st.session_state.orcamento_itens
        ):

            total_item = (
                item["quantidade"]
                * item["valor_unitario"]
            )

            total_orcamento += (
                total_item
            )


            with st.container(
                border=True
            ):

                c1, c2 = st.columns(
                    [5, 1]
                )


                # =============================================
                # DADOS DO ITEM
                # =============================================

                with c1:

                    st.markdown(
                        f"### Item "
                        f"{indice + 1} — "
                        f"{item['codigo']}"
                    )


                    st.write(
                        f"**Tensão:** "
                        f"{item['tensao']}"
                    )


                    st.write(
                        f"**Quantidade:** "
                        f"{item['quantidade']}"
                    )


                    st.write(
                        f"**Valor unitário:** "
                        f"R$ "
                        f"{item['valor_unitario']:,.2f}"
                    )


                    st.write(
                        f"**Total do item:** "
                        f"R$ "
                        f"{total_item:,.2f}"
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


                    # =========================================
                    # TESTE TEMPORÁRIO DO MOTOR
                    # =========================================
                    #
                    # Aqui conseguimos confirmar que o item
                    # realmente trouxe V01 até V16.
                    #
                    # Depois podemos retirar esse expander.
                    # =========================================

                    if item.get(
                        "variaveis"
                    ):

                        variaveis = (
                            item[
                                "variaveis"
                            ]
                        )

                        with st.expander(
                            "Ver dados técnicos gerados"
                        ):

                            st.write(
                                "**V01 - Tipo:**",
                                variaveis.get(
                                    "V01"
                                )
                            )

                            st.write(
                                "**V02 - Atuação:**",
                                variaveis.get(
                                    "V02"
                                )
                            )

                            st.write(
                                "**V03 - Vias:**",
                                variaveis.get(
                                    "V03"
                                )
                            )

                            st.write(
                                "**V04 - Estado:**",
                                variaveis.get(
                                    "V04"
                                )
                            )

                            st.write(
                                "**V05 - Corpo:**",
                                variaveis.get(
                                    "V05"
                                )
                            )

                            st.write(
                                "**V06 - Vedação:**",
                                variaveis.get(
                                    "V06"
                                )
                            )

                            st.write(
                                "**V07 - Conexão:**",
                                variaveis.get(
                                    "V07"
                                )
                            )

                            st.write(
                                "**V08 - Rosca:**",
                                variaveis.get(
                                    "V08"
                                )
                            )

                            st.write(
                                "**V09 - Orifício:**",
                                variaveis.get(
                                    "V09"
                                )
                            )

                            st.write(
                                "**V10 - Pressão mínima:**",
                                variaveis.get(
                                    "V10"
                                )
                            )

                            st.write(
                                "**V11 - Pressão máxima:**",
                                variaveis.get(
                                    "V11"
                                )
                            )

                            st.write(
                                "**V12 - Temperatura:**",
                                variaveis.get(
                                    "V12"
                                )
                            )


                            # =================================
                            # V13 É UM DICIONÁRIO
                            # =================================

                            v13 = (
                                variaveis.get(
                                    "V13"
                                )
                                or {}
                            )

                            st.write(
                                "**V13 - Tipo da bobina:**",
                                v13.get(
                                    "tipo_bobina"
                                )
                            )

                            st.write(
                                "**V13 - Classe térmica:**",
                                v13.get(
                                    "classe_termica"
                                )
                            )

                            st.write(
                                "**V13 - Proteção:**",
                                v13.get(
                                    "protecao"
                                )
                            )

                            st.write(
                                "**V13 - Conexão elétrica:**",
                                v13.get(
                                    "conexao_eletrica"
                                )
                            )

                            st.write(
                                "**V13 - Certificação:**",
                                v13.get(
                                    "certificacao"
                                )
                            )


                            st.write(
                                "**V14 - Potência:**",
                                variaveis.get(
                                    "V14"
                                )
                            )


                            # =================================
                            # V15 É ESTRUTURADA
                            # =================================

                            v15 = (
                                variaveis.get(
                                    "V15"
                                )
                                or {}
                            )

                            extras = (
                                v15.get(
                                    "extras"
                                )
                                or []
                            )

                            st.write(
                                "**V15 - Extras:**"
                            )

                            if extras:

                                for extra in extras:

                                    st.write(
                                        f"- "
                                        f"{extra.get('codigo')}: "
                                        f"{extra.get('texto')}"
                                    )

                            else:

                                st.write(
                                    "Nenhum extra."
                                )


                            st.write(
                                "**V16 - Kv:**",
                                variaveis.get(
                                    "V16"
                                )
                            )

                            st.write(
                                "**V17 - Imagem:**",
                                variaveis.get(
                                    "V17"
                                )
                            )
                            nome_imagem = (
                                variaveis.get(
                                    "V17"
                                )
                            )

                            if nome_imagem:

                                url_imagem = (
                                    obter_url_imagem(
                                        nome_imagem
                                    )
                                )

                                st.image(
                                    url_imagem,
                                    width=300,
                                )

                            else:

                                st.info(
                                    "Imagem não identificada "
                                    "para este produto."
                                )

                
                # =============================================
                # EXCLUIR ITEM
                # =============================================

                with c2:

                    if st.button(
                        "Excluir",
                        key=(
                            f"excluir_item_"
                            f"{indice}"
                        ),
                        use_container_width=True,
                    ):

                        st.session_state.orcamento_itens.pop(
                            indice
                        )

                        st.rerun()


        st.metric(
            "Total do orçamento",
            f"R$ "
            f"{total_orcamento:,.2f}"
        )

        st.divider()


    # =========================================================
    # ADICIONAR NOVO ITEM
    # =========================================================

    st.write(
        "### Adicionar item"
    )


    with st.form(
        "form_adicionar_item",
        clear_on_submit=False,
    ):


        # =====================================================
        # CÓDIGO
        # =====================================================

        codigo = st.text_input(
            "Código do produto",
            placeholder="Ex.: 1335BA04T",
            key="rascunho_codigo",
        )


        # =====================================================
        # TENSÃO
        # =====================================================

        tensao_selecionada = (
            st.selectbox(
                "Tensão",
                options=OPCOES_TENSAO,
                index=None,
                placeholder="Digite para buscar...",
                key="rascunho_tensao",
            )
        )


        if (
            tensao_selecionada
            == "OUTRO"
        ):

            tensao = st.text_input(
                "Outra tensão",
                placeholder=(
                    "Digite a tensão "
                    "manualmente"
                ),
                key="rascunho_tensao_outro",
            )

        else:

            tensao = (
                tensao_selecionada
                or ""
            )


        # =====================================================
        # QUANTIDADE / VALOR
        # =====================================================

        c1, c2 = st.columns(2)


        with c1:

            quantidade = (
                st.number_input(
                    "Quantidade",
                    min_value=1,
                    value=1,
                    step=1,
                    key="rascunho_quantidade",
                )
            )


        with c2:

            valor_unitario = (
                st.number_input(
                    "Valor unitário (R$)",
                    min_value=0.0,
                    value=0.0,
                    step=0.01,
                    format="%.2f",
                    key="rascunho_valor",
                )
            )


        # =====================================================
        # PRAZO
        # =====================================================

        prazo_selecionado = (
            st.selectbox(
                "Prazo",
                options=OPCOES_PRAZO,
                index=None,
                placeholder="Digite para buscar...",
                key="rascunho_prazo",
            )
        )


        if (
            prazo_selecionado
            == "OUTRO"
        ):

            prazo = st.text_input(
                "Outro prazo",
                placeholder=(
                    "Digite o prazo "
                    "manualmente"
                ),
                key="rascunho_prazo_outro",
            )

        else:

            prazo = (
                prazo_selecionado
                or ""
            )


        # =====================================================
        # OBSERVAÇÃO
        # =====================================================

        observacao = st.text_area(
            "Observação do item",
            placeholder="Opcional",
            key="rascunho_observacao",
        )
        # =====================================================
        # BOTÃO
        # =====================================================

        adicionar_item = (
            st.form_submit_button(
                "Adicionar item",
                type="primary",
                use_container_width=True,
            )
        )


    # =========================================================
    # PROCESSAR NOVO ITEM
    # =========================================================

    if adicionar_item:


        # =====================================================
        # VALIDAÇÕES DO FORMULÁRIO
        # =====================================================

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

            codigo_normalizado = (
                codigo
                .strip()
                .upper()
            )

            tensao_normalizada = (
                tensao
                .strip()
                .upper()
            )


            # =================================================
            # CHAMAR MOTOR DE DESCRIÇÃO
            # =================================================

            try:

                produto_processado = (
                    processar_produto(
                        codigo_normalizado,
                        tensao_normalizada,
                    )
                )


            except Exception as erro:

                st.error(
                    "Erro ao processar "
                    f"o código: {erro}"
                )

                produto_processado = None


            # =================================================
            # VERIFICAR RESULTADO DO MOTOR
            # =================================================

            if produto_processado:


                if not produto_processado.get(
                    "sucesso"
                ):

                    st.error(
                        produto_processado.get(
                            "erro"
                        )
                        or (
                            "Não foi possível "
                            "interpretar o código."
                        )
                    )


                    # Mostra alertas do parser,
                    # caso existam.

                    parser = (
                        produto_processado.get(
                            "parser"
                        )
                        or {}
                    )

                    alertas = (
                        parser.get(
                            "alertas"
                        )
                        or []
                    )

                    for alerta in alertas:

                        st.warning(
                            alerta
                        )


                else:

                    # =========================================
                    # MOTOR FUNCIONOU
                    # =========================================

                    variaveis = (
                        produto_processado[
                            "variaveis"
                        ]
                    )


                    # =========================================
                    # CRIAR ITEM
                    # =========================================

                    novo_item = {

                        # Dados comerciais
                        "codigo":
                            codigo_normalizado,

                        "tensao":
                            tensao_normalizada,

                        "quantidade":
                            int(
                                quantidade
                            ),

                        "valor_unitario":
                            float(
                                valor_unitario
                            ),

                        "prazo":
                            prazo.strip(),

                        "observacao":
                            observacao.strip(),


                        # =====================================
                        # DADOS TÉCNICOS DO MOTOR
                        # =====================================
                        #
                        # Ficam no session_state.
                        #
                        # O repository atual NÃO salva esse
                        # campo no Supabase.
                        #
                        # =====================================

                        "variaveis":
                            variaveis,
                    }


                    # =========================================
                    # ADICIONAR À LISTA
                    # =========================================

                    st.session_state.orcamento_itens.append(
                        novo_item
                    )


                    # =========================================
                    # RECARREGAR TELA
                    # =========================================

                    st.rerun()


    # =========================================================
    # OBSERVAÇÕES GERAIS
    # =========================================================

    st.divider()

    st.subheader(
        "Observações gerais"
    )


    observacao_geral = (
        st.text_area(
            "Observação do orçamento",
            placeholder=(
                "Informações gerais que "
                "devem constar no orçamento..."
            ),
            key=(
                "orcamento_observacao_geral"
            ),
        )
    )


    # =========================================================
    # SALVAR ORÇAMENTO
    # =========================================================

    st.divider()


    salvar = st.button(
        "💾 Salvar orçamento",
        type="primary",
        use_container_width=True,
    )


    if salvar:


        # =====================================================
        # VALIDAÇÕES
        # =====================================================

        if not numero_orcamento.strip():

            st.warning(
                "Informe o número "
                "do orçamento."
            )


        elif not cliente_selecionado:

            st.warning(
                "Selecione um cliente."
            )


        elif not (
            st.session_state.orcamento_itens
        ):

            st.warning(
                "Adicione pelo menos um item."
            )


        else:

            try:

                with st.spinner(
                    "Salvando orçamento..."
                ):

                    orcamento_salvo = (
                        salvar_orcamento(
                            numero_orcamento=(
                                numero_orcamento
                            ),
                            cliente=(
                                cliente_selecionado
                            ),
                            itens=(
                                st.session_state
                                .orcamento_itens
                            ),
                            criado_por=(
                                st.session_state.nome
                            ),
                            observacao_geral=(
                                observacao_geral
                            ),
                        )
                    )


                st.success(
                    f'Orçamento '
                    f'{orcamento_salvo["numero_orcamento"]} '
                    f'salvo com sucesso.'
                )


            except Exception as erro:

                st.error(
                    "Erro ao salvar "
                    f"orçamento: {erro}"
                )


    # =========================================================
    # PDF DE TESTE
    # =========================================================

    mostrar_teste_pdf()

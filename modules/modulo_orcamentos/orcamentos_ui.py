import streamlit as st
import streamlit.components.v1 as components

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
# FUNÇÕES AUXILIARES DO FORMULÁRIO DE ITENS
# =============================================================

def converter_quantidade(valor):

    try:

        quantidade = int(
            str(valor).strip()
        )

        if quantidade <= 0:
            return None

        return quantidade

    except (ValueError, TypeError):

        return None


def converter_valor(valor):

    try:

        texto = (
            str(valor)
            .strip()
            .replace(".", "")
            .replace(",", ".")
        )

        if not texto:
            return None

        valor_convertido = float(
            texto
        )

        if valor_convertido < 0:
            return None

        return valor_convertido

    except (ValueError, TypeError):

        return None


def focar_campo_codigo():

    components.html(
        """
        <script>
        const inputs =
            window.parent.document.querySelectorAll(
                'input'
            );

        for (const input of inputs) {

            const ariaLabel =
                input.getAttribute('aria-label');

            if (
                ariaLabel === 'Código'
            ) {

                input.focus();
                input.select();
                break;
            }
        }
        </script>
        """,
        height=0,
    )


# =============================================================
# PÁGINA DE ORÇAMENTOS
# =============================================================

def pagina_orcamentos():

    st.title(
        "📄 Novo Orçamento"
    )


    # =========================================================
    # LIMPAR ORÇAMENTO
    # =========================================================

    with st.expander(
        "🗑️ Limpar orçamento"
    ):

        st.warning(
            "Esta ação apaga todos os dados "
            "do orçamento atual da tela."
        )

        confirmar_limpeza = (
            st.checkbox(
                "Confirmar limpeza",
                key="confirmar_limpeza_orcamento",
            )
        )

        if st.button(
            "Apagar tudo",
            disabled=(
                not confirmar_limpeza
            ),
            use_container_width=True,
        ):

            chaves_para_limpar = [
                "orcamento_itens",
                "orcamento_cliente_selecionado",
                "orcamento_numero",
                "orcamento_busca_cliente",
                "orcamento_cliente_select",
                "orcamento_observacao_geral",
                "rascunho_codigo",
                "rascunho_tensao",
                "rascunho_tensao_outro",
                "rascunho_quantidade",
                "rascunho_valor",
                "rascunho_prazo",
                "rascunho_prazo_outro",
                "rascunho_observacao",
                "pdf_teste_bytes",
                "confirmar_limpeza_orcamento",
            ]

            for chave in chaves_para_limpar:

                if chave in st.session_state:

                    del st.session_state[
                        chave
                    ]

            st.rerun()
    
    # =========================================================
    # INICIALIZAÇÃO DO SESSION STATE
    # =========================================================

    if (
        "orcamento_itens"
        not in st.session_state
    ):

        st.session_state.orcamento_itens = []

    # =========================================================
    # LIMPEZA DO FORMULÁRIO APÓS ADICIONAR ITEM
    # =========================================================

    if st.session_state.get(
        "limpar_novo_item",
        False,
    ):

        # Campos que devem ser limpos
        st.session_state[
            "rascunho_codigo"
        ] = ""

        st.session_state[
            "rascunho_quantidade"
        ] = ""

        st.session_state[
            "rascunho_valor"
        ] = ""

        st.session_state[
            "rascunho_observacao"
        ] = ""


        # Tensão NÃO é limpa.
        # Prazo NÃO é limpo.


        # Desliga a solicitação de limpeza
        st.session_state[
            "limpar_novo_item"
        ] = False

        st.session_state[
            "focar_codigo"
        ] = True
    
    if (
        "orcamento_cliente_selecionado"
        not in st.session_state
    ):

        st.session_state[
            "orcamento_cliente_selecionado"
        ] = None


    responsavel = (
        st.session_state.get(
            "nome"
        )
        or "-"
    )


    # =========================================================
    # DADOS DO ORÇAMENTO
    # =========================================================

    st.subheader(
        "Dados do orçamento"
    )


    numero_orcamento = st.text_input(
        "Número do orçamento",
        placeholder="Ex.: 3288/26",
        key="orcamento_numero",
    )


    # =========================================================
    # CLIENTE
    # =========================================================

    st.subheader(
        "Cliente"
    )


    busca_cliente = st.text_input(
        "Buscar cliente",
        placeholder=(
            "Digite código, razão social, "
            "nome fantasia ou CNPJ/CPF"
        ),
        key="orcamento_busca_cliente",
    )


    cliente_selecionado = (
        st.session_state.get(
            "orcamento_cliente_selecionado"
        )
    )


    # =========================================================
    # BUSCAR CLIENTES
    # =========================================================

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


                st.session_state[
                    "orcamento_cliente_selecionado"
                ] = cliente_selecionado


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


        c1, c2, c3 = st.columns(
            3
        )


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
    # ITENS JÁ ADICIONADOS
    # =========================================================

    if st.session_state.orcamento_itens:

        st.write(
            "### Itens adicionados"
        )

        total_orcamento = 0


        # =====================================================
        # CABEÇALHO
        # =====================================================

        (
            col_item,
            col_codigo,
            col_tensao,
            col_qtd,
            col_valor,
            col_total,
            col_prazo,
            col_acao,
        ) = st.columns(
            [0.5, 2.0, 1.4, 0.6, 1.2, 1.2, 1.2, 0.8]
        )

        col_item.markdown("**#**")
        col_codigo.markdown("**Código**")
        col_tensao.markdown("**Tensão**")
        col_qtd.markdown("**Qtd.**")
        col_valor.markdown("**Unitário**")
        col_total.markdown("**Total**")
        col_prazo.markdown("**Prazo**")
        col_acao.markdown("**Ação**")


        # =====================================================
        # ITENS
        # =====================================================

        for indice, item in enumerate(
            st.session_state.orcamento_itens
        ):

            total_item = (
                item["quantidade"]
                * item["valor_unitario"]
            )

            total_orcamento += total_item


            (
                col_item,
                col_codigo,
                col_tensao,
                col_qtd,
                col_valor,
                col_total,
                col_prazo,
                col_acao,
            ) = st.columns(
                [0.5, 2.0, 1.4, 0.6, 1.2, 1.2, 1.2, 0.8]
            )


            col_item.write(
                indice + 1
            )

            col_codigo.write(
                item["codigo"]
            )

            col_tensao.write(
                item["tensao"]
            )

            col_qtd.write(
                item["quantidade"]
            )

            col_valor.write(
                f"R$ {item['valor_unitario']:,.2f}"
            )

            col_total.write(
                f"R$ {total_item:,.2f}"
            )

            col_prazo.write(
                item["prazo"]
            )


            # =================================================
            # EXCLUIR
            # =================================================

            with col_acao:

                if st.button(
                    "🗑️",
                    key=(
                        f"excluir_item_"
                        f"{indice}"
                    ),
                    help="Excluir item",
                    use_container_width=True,
                ):

                    st.session_state.orcamento_itens.pop(
                        indice
                    )

                    st.rerun()


            # =================================================
            # DETALHES DO ITEM
            # =================================================

            with st.expander(
                f"Detalhes — {item['codigo']}"
            ):

                if item.get(
                    "observacao"
                ):

                    st.write(
                        "**Observação:**",
                        item["observacao"],
                    )


                variaveis = (
                    item.get(
                        "variaveis"
                    )
                    or {}
                )


                if variaveis:

                    c1, c2, c3 = st.columns(
                        3
                    )


                    # =========================================
                    # COLUNA 1
                    # =========================================

                    with c1:

                        st.write(
                            "**Tipo:**",
                            variaveis.get("V01"),
                        )

                        st.write(
                            "**Atuação:**",
                            variaveis.get("V02"),
                        )

                        st.write(
                            "**Vias:**",
                            variaveis.get("V03"),
                        )

                        st.write(
                            "**Estado:**",
                            variaveis.get("V04"),
                        )

                        st.write(
                            "**Corpo:**",
                            variaveis.get("V05"),
                        )

                        st.write(
                            "**Vedação:**",
                            variaveis.get("V06"),
                        )


                    # =========================================
                    # COLUNA 2
                    # =========================================

                    with c2:

                        st.write(
                            "**Conexão:**",
                            variaveis.get("V07"),
                        )

                        st.write(
                            "**Rosca:**",
                            variaveis.get("V08"),
                        )

                        st.write(
                            "**Orifício:**",
                            variaveis.get("V09"),
                        )

                        st.write(
                            "**Pressão mínima:**",
                            variaveis.get("V10"),
                        )

                        st.write(
                            "**Pressão máxima:**",
                            variaveis.get("V11"),
                        )

                        st.write(
                            "**Temperatura:**",
                            variaveis.get("V12"),
                        )


                    # =========================================
                    # COLUNA 3
                    # =========================================

                    with c3:

                        v13 = (
                            variaveis.get("V13")
                            or {}
                        )

                        st.write(
                            "**Bobina:**",
                            v13.get("tipo_bobina"),
                        )

                        st.write(
                            "**Classe térmica:**",
                            v13.get("classe_termica"),
                        )

                        st.write(
                            "**Proteção:**",
                            v13.get("protecao"),
                        )

                        st.write(
                            "**Conexão elétrica:**",
                            v13.get("conexao_eletrica"),
                        )

                        st.write(
                            "**Certificação:**",
                            v13.get("certificacao"),
                        )

                        st.write(
                            "**Potência:**",
                            variaveis.get("V14"),
                        )


                    # =========================================
                    # EXTRAS
                    # =========================================

                    v15 = (
                        variaveis.get("V15")
                        or {}
                    )

                    extras = (
                        v15.get("extras")
                        or []
                    )

                    if extras:

                        st.write(
                            "**Extras:**"
                        )

                        for extra in extras:

                            st.write(
                                f"- "
                                f"{extra.get('codigo')}: "
                                f"{extra.get('texto')}"
                            )


                    # =========================================
                    # KV
                    # =========================================

                    st.write(
                        "**Kv:**",
                        variaveis.get("V16"),
                    )


                    # =========================================
                    # IMAGEM
                    # =========================================

                    nome_imagem = (
                        variaveis.get("V17")
                    )

                    if nome_imagem:

                        url_imagem = (
                            obter_url_imagem(
                                nome_imagem
                            )
                        )

                        st.image(
                            url_imagem,
                            width=250,
                        )


        # =====================================================
        # TOTAL DO ORÇAMENTO
        # =====================================================

        st.divider()

        st.metric(
            "Total do orçamento",
            f"R$ {total_orcamento:,.2f}"
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
        # LINHA PRINCIPAL
        # =====================================================

        (
            coluna_codigo,
            coluna_tensao,
            coluna_quantidade,
            coluna_valor,
            coluna_prazo,
        ) = st.columns(
            [3.2, 2.0, 1.0, 1.7, 2.0]
        )


        # =====================================================
        # CÓDIGO
        # =====================================================

        with coluna_codigo:

            codigo = st.text_input(
                "Código",
                placeholder="Ex.: 1335BA04T",
                key="rascunho_codigo",
            )


        # =====================================================
        # TENSÃO
        # =====================================================

        with coluna_tensao:

            tensao_selecionada = (
                st.selectbox(
                    "Tensão",
                    options=OPCOES_TENSAO,
                    index=None,
                    placeholder="Selecione...",
                    key="rascunho_tensao",
                )
            )


        # =====================================================
        # QUANTIDADE
        # =====================================================

        with coluna_quantidade:

            quantidade_digitada = (
                st.text_input(
                    "Qtd.",
                    placeholder="1",
                    key="rascunho_quantidade",
                )
            )


        # =====================================================
        # VALOR UNITÁRIO
        # =====================================================

        with coluna_valor:

            valor_digitado = (
                st.text_input(
                    "Valor unit.",
                    placeholder="0,00",
                    key="rascunho_valor",
                )
            )


        # =====================================================
        # PRAZO
        # =====================================================

        with coluna_prazo:

            prazo_selecionado = (
                st.selectbox(
                    "Prazo",
                    options=OPCOES_PRAZO,
                    index=None,
                    placeholder="Selecione...",
                    key="rascunho_prazo",
                )
            )


        # =====================================================
        # OUTRA TENSÃO
        # =====================================================

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
        # OUTRO PRAZO
        # =====================================================

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

        observacao = st.text_input(
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

    if st.session_state.get(
        "focar_codigo",
        False,
    ):

        focar_campo_codigo()

        st.session_state[
            "focar_codigo"
        ] = False
    
    # =========================================================
    # PROCESSAR NOVO ITEM
    # =========================================================

    if adicionar_item:

        
        # =====================================================
        # CONVERTER QUANTIDADE
        # =====================================================

        quantidade = converter_quantidade(
            quantidade_digitada
        )


        # =====================================================
        # CONVERTER VALOR
        # =====================================================

        valor_unitario = converter_valor(
            valor_digitado
        )
        
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


        elif quantidade is None:

            st.warning(
                "Informe uma quantidade válida."
            )


        elif valor_unitario is None:

            st.warning(
                "Informe um valor unitário válido."
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
            # VERIFICAR RESULTADO
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

                        "variaveis":
                            variaveis,
                    }


                    # =========================================
                    # ADICIONAR
                    # =========================================

                    st.session_state.orcamento_itens.append(
                        novo_item
                    )

                    st.session_state[
                        "limpar_novo_item"
                    ] = True

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
            key="orcamento_observacao_geral",
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
                                responsavel
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
    # GERAR PDF
    # =========================================================
    #
    # AQUI APENAS CHAMAMOS A FUNÇÃO.
    #
    # A programação do PDF fica em:
    #
    # pdf/pdf_teste_ui.py
    # pdf/gerador_pdf_teste.py
    #
    # =========================================================

    if (
        numero_orcamento.strip()
        and cliente_selecionado
        and st.session_state.orcamento_itens
    ):

        mostrar_teste_pdf(
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
            observacao_geral=(
                observacao_geral
            ),
            responsavel=(
                responsavel
            ),
        )


    else:

        st.divider()

        st.caption(
            "Preencha o número do orçamento, "
            "selecione um cliente e adicione "
            "pelo menos um item para gerar o PDF."
        )

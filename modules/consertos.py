import streamlit as st

from core.consertos import (
    ESTAGIOS,
    adicionar_nota_cliente,
    avancar_com_dados,
    criar_conserto,
    definir_liberacao,
    listar_consertos,
    listar_itens,
    listar_movimentacoes,
)

LABELS = {
    "CHEGOU": "Chegou",
    "VERIFICADO": "Verificado",
    "CORRIGIDO": "Corrigido",
    "PRONTO_PARA_RETIRADA": "Tudo Pronto",
}

CORES = {
    "CHEGOU": "#FDBA74",
    "VERIFICADO": "#93C5FD",
    "CORRIGIDO": "#86EFAC",
    "PRONTO_PARA_RETIRADA": "#C4B5FD",
}


def _init():
    st.session_state.setdefault("conserto_aberto", None)
    st.session_state.setdefault("conserto_modal_novo", False)
    st.session_state.setdefault("conserto_qtd_itens", 1)
    st.session_state.setdefault("conserto_modal_transicao", None)
    st.session_state.setdefault("conserto_modal_nota_cliente", None)


def _fechar_novo():
    st.session_state.conserto_modal_novo = False
    st.session_state.conserto_qtd_itens = 1


@st.dialog("Novo Conserto")
def modal_novo_conserto():
    cliente = st.text_input("Cliente *", key="novo_conserto_cliente")
    veio_nf = st.radio(
        "Veio com NF do cliente? *",
        ["Não", "Sim"],
        horizontal=True,
        key="novo_conserto_veio_nf",
    )
    nota = ""
    if veio_nf == "Sim":
        nota = st.text_input("Número da NF do cliente *", key="novo_conserto_nf")

    st.markdown("#### Itens")
    itens = []
    qtd_linhas = st.session_state.conserto_qtd_itens
    for i in range(qtd_linhas):
        c1, c2 = st.columns([3, 1])
        with c1:
            codigo = st.text_input("Código *", key=f"novo_conserto_codigo_{i}")
        with c2:
            quantidade = st.number_input(
                "Quantidade *", min_value=1, value=1, step=1,
                key=f"novo_conserto_qtd_{i}",
            )
        itens.append({"codigo": codigo, "quantidade": quantidade})

    if st.button("+ Adicionar item", use_container_width=True):
        st.session_state.conserto_qtd_itens += 1
        st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cancelar", use_container_width=True):
            _fechar_novo()
            st.rerun()
    with c2:
        if st.button("Criar conserto", type="primary", use_container_width=True):
            if not cliente.strip():
                st.warning("Informe o cliente.")
                return
            if veio_nf == "Sim" and not nota.strip():
                st.warning("Informe o número da NF do cliente.")
                return
            if any(not item["codigo"].strip() for item in itens):
                st.warning("Informe o código de todos os itens.")
                return

            try:
                conserto = criar_conserto(
                    cliente=cliente,
                    chegou_com_nota=(veio_nf == "Sim"),
                    nota_fiscal_cliente=nota,
                    itens=itens,
                    usuario=st.session_state.nome,
                )
            except Exception as exc:
                st.error(f"Erro ao criar conserto: {exc}")
                return

            if not conserto:
                st.error("Não foi possível criar o conserto.")
                return

            _fechar_novo()
            st.success("Conserto criado em Chegou.")
            st.rerun()


@st.dialog("Adicionar NF do cliente")
def modal_nota_cliente():
    conserto = st.session_state.conserto_modal_nota_cliente
    if not conserto:
        return

    st.write(f"Conserto **#{conserto['id']} — {conserto['cliente']}**")
    nota = st.text_input("Número da NF do cliente *", key=f"nf_cliente_{conserto['id']}")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cancelar", use_container_width=True):
            st.session_state.conserto_modal_nota_cliente = None
            st.rerun()
    with c2:
        if st.button("Salvar NF", type="primary", use_container_width=True):
            if not nota.strip():
                st.warning("Informe o número da NF.")
                return
            if adicionar_nota_cliente(conserto["id"], nota, st.session_state.nome):
                st.session_state.conserto_modal_nota_cliente = None
                st.success("NF do cliente adicionada.")
                st.rerun()
            st.error("Erro ao adicionar a NF.")


@st.dialog("Avançar Conserto")
def modal_transicao():
    conserto = st.session_state.conserto_modal_transicao
    if not conserto:
        return

    origem = conserto["estagio_atual"]
    st.write(f"Conserto **#{conserto['id']} — {conserto['cliente']}**")

    texto = None
    nf_jefferson = None

    if origem == "CHEGOU":
        st.markdown("**CHEGOU → VERIFICADO**")
        texto = st.text_area(
            "Diagnóstico / verificação *",
            placeholder="Ex.: Bobina veio queimada.",
            key=f"diagnostico_{conserto['id']}",
        )
    elif origem == "VERIFICADO":
        st.markdown("**VERIFICADO → CORRIGIDO**")
        texto = st.text_area(
            "Serviço realizado / correção *",
            placeholder="Ex.: Bobina substituída conforme liberado.",
            key=f"correcao_{conserto['id']}",
        )
    elif origem == "CORRIGIDO":
        st.markdown("**CORRIGIDO → TUDO PRONTO**")
        nf_jefferson = st.text_input(
            "NF Jefferson *",
            placeholder="Digite o número da nossa NF",
            key=f"nf_jefferson_{conserto['id']}",
        )
        if not conserto.get("nota_fiscal_cliente"):
            st.warning("Este material ainda está sem NF do cliente.")
    else:
        st.info("Este conserto já está no último estágio.")
        if st.button("Fechar", use_container_width=True):
            st.session_state.conserto_modal_transicao = None
            st.rerun()
        return

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cancelar", use_container_width=True):
            st.session_state.conserto_modal_transicao = None
            st.rerun()
    with c2:
        if st.button("Confirmar e avançar", type="primary", use_container_width=True):
            if origem in ["CHEGOU", "VERIFICADO"] and not str(texto or "").strip():
                st.warning("O preenchimento deste campo é obrigatório.")
                return
            if origem == "CORRIGIDO" and not str(nf_jefferson or "").strip():
                st.warning("Informe a NF Jefferson.")
                return

            if avancar_com_dados(
                conserto=conserto,
                usuario=st.session_state.nome,
                setor_usuario=st.session_state.setor,
                texto=texto,
                nota_jefferson=nf_jefferson,
            ):
                st.session_state.conserto_modal_transicao = None
                st.session_state.conserto_aberto = None
                st.success("Conserto avançado.")
                st.rerun()
            st.error("Não foi possível avançar o conserto.")


def _render_card(conserto):
    cid = conserto["id"]
    aberto = st.session_state.conserto_aberto == cid
    tem_nf = bool(conserto.get("nota_fiscal_cliente"))
    nf_badge = " | NF cliente" if tem_nf else " | SEM NF"
    estagio = conserto.get("estagio_atual")
    campo_liberacao = {
        "CHEGOU": "chegou_liberado",
        "VERIFICADO": "verificado_liberado",
    }.get(estagio)
    liberado = bool(conserto.get(campo_liberacao)) if campo_liberacao else None
    sinal = " 🟢" if liberado is True else (" 🔴" if liberado is False else "")

    if not aberto:
        if st.button(
            f"{sinal} #{cid} - {conserto['cliente']}{nf_badge}",
            key=f"abrir_conserto_{cid}",
            use_container_width=True,
        ):
            st.session_state.conserto_aberto = cid
            st.rerun()
        return

    with st.container(border=True):
        st.markdown(f"**Conserto #{cid} — {conserto['cliente']}**")
        st.caption(f"Cadastrado por: {conserto.get('criado_por', '')}")

        if campo_liberacao:
            if liberado:
                st.success("🟢 Liberado para prosseguimento.")
                liberado_por = conserto.get(f"{estagio.lower()}_liberado_por")
                if liberado_por:
                    st.caption(f"Liberado por: {liberado_por}")
            else:
                st.error("🔴 Aguardando liberação administrativa.")
                if st.session_state.setor == "ADMINISTRADOR":
                    if st.button("🟢 Liberar prosseguimento", key=f"liberar_conserto_{cid}", use_container_width=True):
                        sucesso, mensagem = definir_liberacao(
                            conserto=conserto,
                            usuario=st.session_state.nome,
                            setor_usuario=st.session_state.setor,
                        )
                        if sucesso:
                            st.success(mensagem)
                            st.rerun()
                        st.warning(mensagem)

        if tem_nf:
            st.info(f"NF cliente: **{conserto['nota_fiscal_cliente']}**")
            if not conserto.get("chegou_com_nota"):
                st.caption("O material chegou sem NF; a nota foi adicionada posteriormente.")
        else:
            st.warning("Material sem NF do cliente.")

        itens = listar_itens(cid)
        st.markdown("**Itens**")
        for item in itens:
            st.write(f"• {item.get('codigo')} — Qtd. {item.get('quantidade')}")

        if conserto.get("diagnostico"):
            st.markdown(f"**Diagnóstico:** {conserto['diagnostico']}")
        if conserto.get("correcao"):
            st.markdown(f"**Correção:** {conserto['correcao']}")
        if conserto.get("nota_fiscal_jefferson"):
            st.success(f"NF Jefferson: **{conserto['nota_fiscal_jefferson']}**")

        if (
            not tem_nf
            and conserto.get("estagio_atual") != "PRONTO_PARA_RETIRADA"
        ):
            if st.button("Adicionar NF do cliente", key=f"add_nf_cliente_{cid}", use_container_width=True):
                st.session_state.conserto_modal_nota_cliente = conserto
                st.rerun()

        with st.expander("Histórico"):
            movimentos = listar_movimentacoes(cid)
            if not movimentos:
                st.caption("Nenhum evento registrado.")
            for mov in movimentos:
                st.write(f"**{mov.get('usuario', '')}** — {mov.get('observacao', '')}")
                st.caption(str(mov.get("criado_em", "")))

        c1, c2 = st.columns(2)
        with c1:
            if conserto.get("estagio_atual") != "PRONTO_PARA_RETIRADA":
                bloqueado_por_liberacao = campo_liberacao is not None and not liberado
                if st.button(
                    "Avançar",
                    key=f"avancar_conserto_{cid}",
                    type="primary",
                    use_container_width=True,
                    disabled=bloqueado_por_liberacao,
                ):
                    st.session_state.conserto_modal_transicao = conserto
                    st.rerun()
                if bloqueado_por_liberacao:
                    st.caption("Aguardando liberação do ADMINISTRADOR.")
        with c2:
            if st.button("Fechar", key=f"fechar_conserto_{cid}", use_container_width=True):
                st.session_state.conserto_aberto = None
                st.rerun()


def pagina_consertos():
    _init()

    if st.session_state.setor not in ["ADMINISTRADOR", "MONTAGEM"]:
        st.error("Você não possui permissão para acessar Consertos.")
        return

    st.title("Consertos")
    topo1, topo2, topo3 = st.columns([3, 1, 1])
    with topo1:
        st.caption("Recebimento, diagnóstico, correção e liberação de materiais.")
    with topo2:
        if st.button("🔄 Atualizar", use_container_width=True):
            st.rerun()
    with topo3:
        if st.button("+ Novo Conserto", type="primary", use_container_width=True):
            st.session_state.conserto_modal_novo = True
            st.rerun()

    consertos = listar_consertos()
    agrupados = {estagio: [] for estagio in ESTAGIOS}
    for conserto in consertos:
        estagio = conserto.get("estagio_atual")
        if estagio in agrupados:
            agrupados[estagio].append(conserto)

    colunas = st.columns(4)
    for idx, estagio in enumerate(ESTAGIOS):
        with colunas[idx]:
            st.markdown(f"### {LABELS[estagio]} ({len(agrupados[estagio])})")
            st.markdown(
                f"<div style='height:10px;background:{CORES[estagio]};"
                "border-radius:8px;margin-bottom:10px'></div>",
                unsafe_allow_html=True,
            )
            for conserto in agrupados[estagio]:
                _render_card(conserto)

    if st.session_state.conserto_modal_novo:
        modal_novo_conserto()
    if st.session_state.conserto_modal_nota_cliente:
        modal_nota_cliente()
    if st.session_state.conserto_modal_transicao:
        modal_transicao()

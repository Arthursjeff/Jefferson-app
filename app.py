import streamlit as st

from core.auth import validar_login
from modules.modulo_01.service import (
    ESTADOS_FILA,
    LABEL_ESTADOS,
    CORES_ESTADOS,
    obter_pedidos_por_estado,
    criar_novo_pedido,
    avancar_pedido,
    faturar_com_nota,
    cancelar,
    historico_pedido,
    adicionar_mensagem,
    obter_mensagens,
    remover_mensagem,
    quantidade_mensagens,
)


st.set_page_config(
    page_title="Jefferson App",
    page_icon="🧾",
    layout="wide",
)


def init_session():
    st.session_state.setdefault("logado", False)
    st.session_state.setdefault("usuario", None)
    st.session_state.setdefault("nome", None)
    st.session_state.setdefault("setor", None)
    st.session_state.setdefault("pedido_aberto", None)
    st.session_state.setdefault("show_nf_modal", False)
    st.session_state.setdefault("pedido_nf", None)

def abrir_modal_nf(pedido):
    st.session_state.show_nf_modal = True
    st.session_state.pedido_nf = pedido


def fechar_modal_nf():
    st.session_state.show_nf_modal = False
    st.session_state.pedido_nf = None


@st.dialog("🧾 Registrar Nota Fiscal")
def modal_nota_fiscal():
    pedido = st.session_state.get("pedido_nf")

    if not pedido:
        st.error("Pedido não encontrado.")
        return

    st.write(f"Pedido: **{pedido.get('numero_pedido')} - {pedido.get('cliente')}**")

    nota = st.text_input(
        "Número da Nota Fiscal",
        key=f"modal_nf_{pedido['id']}",
        placeholder="Digite o número da NF"
    )

    c1, c2 = st.columns(2)

    with c1:
        if st.button("Cancelar"):
            fechar_modal_nf()
            st.rerun()

    with c2:
        if st.button("Confirmar", type="primary"):
            sucesso, mensagem = faturar_com_nota(
                pedido=pedido,
                nota_fiscal=nota,
                usuario=st.session_state.nome,
                setor_usuario=st.session_state.setor,
            )

            if sucesso:
                fechar_modal_nf()
                st.session_state.pedido_aberto = None
                st.success(mensagem)
                st.rerun()
            else:
                st.warning(mensagem)
                
def tela_login():
    st.title("🔐 Login")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar", type="primary"):
        dados = validar_login(usuario, senha)

        if not dados:
            st.error("Usuário ou senha inválidos.")
            return

        st.session_state.logado = True
        st.session_state.usuario = dados["usuario"]
        st.session_state.nome = dados["nome"]
        st.session_state.setor = dados["setor"]
        st.rerun()


def pagina_criar_pedido():
    st.title("➕ Criar Pedido")

    numero = st.text_input("Número do pedido")
    cliente = st.text_input("Cliente")

    if st.button("Criar pedido", type="primary"):
        sucesso, mensagem = criar_novo_pedido(
            numero_pedido=numero,
            cliente=cliente,
            usuario=st.session_state.nome,
            setor_usuario=st.session_state.setor,
        )

        if sucesso:
            st.success(mensagem)
            st.rerun()
        else:
            st.warning(mensagem)


def pagina_fila():
    st.title("📦 Fila de Pedidos")

    if st.button("🔄 Atualizar"):
        st.rerun()

    pedidos_por_estado = obter_pedidos_por_estado()

    linha1 = st.columns(3)
    linha2 = st.columns(3)

    for idx, estado in enumerate(ESTADOS_FILA):
        coluna = linha1[idx] if idx < 3 else linha2[idx - 3]
        render_coluna(coluna, estado, pedidos_por_estado[estado])


def render_coluna(coluna, estado, pedidos):
    with coluna:
        st.markdown(f"### {LABEL_ESTADOS[estado]} ({len(pedidos)})")
        st.markdown(
            f"<div style='height:10px;background:{CORES_ESTADOS[estado]};"
            f"border-radius:8px;margin-bottom:10px'></div>",
            unsafe_allow_html=True,
        )

        for pedido in pedidos:
            pedido_id = pedido["id"]
            aberto = st.session_state.pedido_aberto == pedido_id

            label = f"{pedido['numero_pedido']} - {pedido['cliente']}"

            if not aberto:
                if st.button(label, key=f"abrir_{pedido_id}", use_container_width=True):
                    st.session_state.pedido_aberto = pedido_id
                    st.rerun()
            else:
                with st.container(border=True):
                    st.markdown(f"**{label}**")
                    st.caption(f"Criado por: {pedido.get('criado_por', '')}")
                    st.caption(f"Criado em: {pedido.get('criado_data', '')} às {pedido.get('criado_hora', '')}")
                    if pedido.get("nota_fiscal"):
                        st.info(f"🧾 Nota Fiscal: {pedido.get('nota_fiscal')}")                    

                    st.divider()

                    # =========================
                    # MENSAGENS
                    # =========================

                    qtd_msg = quantidade_mensagens(pedido_id)

                    with st.expander(f"💬 Mensagens ({qtd_msg})"):
                        mensagens = obter_mensagens(pedido_id)

                        if not mensagens:
                            st.caption("Nenhuma mensagem registrada.")
                        else:
                            for msg in mensagens:
                                st.markdown(f"**{msg.get('criado_por', '')}:** {msg.get('mensagem', '')}")

                                if st.button("Remover", key=f"remover_msg_{msg['id']}"):
                                    sucesso, mensagem = remover_mensagem(msg["id"])

                                    if sucesso:
                                        st.success(mensagem)
                                        st.rerun()
                                    else:
                                        st.warning(mensagem)

                        nova_msg = st.text_area(
                            "Nova mensagem",
                            key=f"nova_msg_{pedido_id}",
                            height=80,
                            placeholder="Escreva uma mensagem para este pedido..."
                        )

                        if st.button("Adicionar mensagem", key=f"add_msg_{pedido_id}"):
                            sucesso, mensagem = adicionar_mensagem(
                                pedido_id=pedido_id,
                                mensagem=nova_msg,
                                usuario=st.session_state.nome,
                            )

                            if sucesso:
                                st.success(mensagem)
                                st.rerun()
                            else:
                                st.warning(mensagem)

                    st.divider()

                    c1, c2 = st.columns(2)

                    with c1:
                        if estado == "MONTADOS" and st.session_state.setor == "VENDAS":
                            if st.button("🧾 Faturar", key=f"abrir_nf_{pedido_id}"):
                                abrir_modal_nf(pedido)
                                st.rerun()

                        else:
                            if st.button("➡️ Avançar", key=f"avancar_{pedido_id}"):
                                sucesso, mensagem = avancar_pedido(
                                    pedido=pedido,
                                    usuario=st.session_state.nome,
                                    setor_usuario=st.session_state.setor,
                                )

                                if sucesso:
                                    st.success(mensagem)
                                    st.session_state.pedido_aberto = None
                                    st.rerun()
                                else:
                                    st.warning(mensagem)

                    with c2:
                        if st.button("❌ Cancelar", key=f"cancelar_{pedido_id}"):
                            sucesso, mensagem = cancelar(
                                pedido_id=pedido_id,
                                usuario=st.session_state.nome,
                                setor_usuario=st.session_state.setor,
                            )

                            if sucesso:
                                st.success(mensagem)
                                st.session_state.pedido_aberto = None
                                st.rerun()
                            else:
                                st.warning(mensagem)

                    with st.expander("Histórico"):
                        movimentos = historico_pedido(pedido_id)

                        if not movimentos:
                            st.caption("Sem histórico.")
                        else:
                            for mov in movimentos:
                                st.write(
                                    f"{mov.get('origem')} → {mov.get('destino')} | "
                                    f"{mov.get('usuario')} | {mov.get('criado_em')}"
                                )

                    if st.button("Fechar", key=f"fechar_{pedido_id}"):
                        st.session_state.pedido_aberto = None
                        st.rerun()


init_session()

if not st.session_state.logado:
    tela_login()
    st.stop()
if st.session_state.show_nf_modal:
    modal_nota_fiscal()

with st.sidebar:
    st.markdown("## Jefferson App")
    st.caption(f"{st.session_state.nome} ({st.session_state.setor})")

    pagina = st.radio(
        "Navegação",
        ["Fila de Pedidos", "Criar Pedido"],
    )

    st.divider()

    if st.button("🚪 Sair"):
        st.session_state.clear()
        st.rerun()


if pagina == "Criar Pedido":
    pagina_criar_pedido()
else:
    pagina_fila()

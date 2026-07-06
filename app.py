import streamlit as st
import json
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
from core.admin import apagar_tudo
from core.auth import validar_login, USUARIOS
from modules.modulo_01.service import (
    ESTADOS_FILA,
    LABEL_ESTADOS,
    CORES_ESTADOS,
    obter_pedidos_por_estado,
    criar_novo_pedido,
    obter_notificacoes_pendentes,
    visualizar_notificacao,
    avancar_pedido,
    faturar_com_nota,
    cancelar,
    historico_pedido,
    ESTADOS_VISIVEIS,
    ESTADOS_OCULTOS,
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

def teste_notificacao_navegador():
    components.html(
        """
        <button onclick="notificar()" style="
            padding:10px 14px;
            border-radius:8px;
            border:1px solid #ccc;
            cursor:pointer;
        ">
            🔔 Testar notificação do navegador
        </button>

        <script>
        function notificar() {
            if (!("Notification" in window)) {
                alert("Este navegador não suporta notificações.");
                return;
            }

            if (Notification.permission === "granted") {
                new Notification("Jefferson App", {
                    body: "Teste de notificação da fila de pedidos.",
                    icon: "https://cdn-icons-png.flaticon.com/512/1827/1827370.png"
                });
            } else if (Notification.permission !== "denied") {
                Notification.requestPermission().then(function(permission) {
                    if (permission === "granted") {
                        new Notification("Jefferson App", {
                            body: "Notificações ativadas com sucesso.",
                            icon: "https://cdn-icons-png.flaticon.com/512/1827/1827370.png"
                        });
                    }
                });
            } else {
                alert("As notificações estão bloqueadas neste navegador.");
            }
        }
        </script>
        """,
        height=70,
    )

def init_session():
    st.session_state.setdefault("logado", False)
    st.session_state.setdefault("usuario", None)
    st.session_state.setdefault("nome", None)
    st.session_state.setdefault("setor", None)
    st.session_state.setdefault("pedido_aberto", None)
    st.session_state.setdefault("show_nf_modal", False)
    st.session_state.setdefault("filas_minimizadas", {})
    st.session_state.setdefault("show_trocar_operador", False)
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

def abrir_troca_operador():
    st.session_state.show_trocar_operador = True


def fechar_troca_operador():
    st.session_state.show_trocar_operador = False


@st.dialog("👤 Trocar operador")
def modal_trocar_operador():
    operadores = {
        usuario: dados
        for usuario, dados in USUARIOS.items()
        if dados["setor"] == "MONTAGEM"
    }

    opcoes = list(operadores.keys())

    novo_usuario = st.selectbox(
        "Selecione o operador",
        opcoes,
        format_func=lambda u: operadores[u]["nome"]
    )

    senha = st.text_input("Senha do operador", type="password")

    c1, c2 = st.columns(2)

    with c1:
        if st.button("Cancelar"):
            fechar_troca_operador()
            st.rerun()

    with c2:
        if st.button("Confirmar", type="primary"):
            dados = validar_login(novo_usuario, senha)

            if not dados:
                st.error("Senha inválida para este operador.")
                return

            st.session_state.usuario = dados["usuario"]
            st.session_state.nome = dados["nome"]
            st.session_state.setor = dados["setor"]

            fechar_troca_operador()
            st.success(f"Operador alterado para {dados['nome']}.")
            st.rerun()
                
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
    tipo_pedido = st.selectbox(
        "Tipo do pedido",
        ["NORMAL", "PROGRAMADO", "IMPORTACAO"]
    )

    data_prevista_faturamento = st.date_input("Data prevista de faturamento")    

    if st.button("Criar pedido", type="primary"):
        sucesso, mensagem = criar_novo_pedido(
            numero_pedido=numero,
            cliente=cliente,
            usuario=st.session_state.nome,
            setor_usuario=st.session_state.setor,
            tipo_pedido=tipo_pedido,
            data_prevista_faturamento=data_prevista_faturamento,
        )

        if sucesso:
            st.success(mensagem)
            st.rerun()
        else:
            st.warning(mensagem)

def verificar_notificacoes():
    if not st.session_state.logado:
        return

    setor = st.session_state.setor

    notificacoes = obter_notificacoes_pendentes(setor)

    if not notificacoes:
        return

    for notif in notificacoes:
        titulo = "Jefferson App"
        mensagem = notif.get("mensagem", "Nova notificação")

        components.html(
            f"""
            <script>
            if ("Notification" in window && Notification.permission === "granted") {{
                new Notification({json.dumps(titulo)}, {{
                    body: {json.dumps(mensagem)}
                }});
            }}
            </script>
            """,
            height=0,
        )

        visualizar_notificacao(notif["id"])
def pagina_fila():
    st.title("📦 Fila de Pedidos")
    if st.session_state.setor == "ADMINISTRADOR":
        with st.expander("⚙️ Administração"):
            teste_notificacao_navegador()
            c_admin1, c_admin2 = st.columns(2)

            with c_admin1:
                if st.button("📊 Gerar relatório", use_container_width=True):
                    st.info("Relatório ainda será configurado.")

            with c_admin2:
                confirmar = st.text_input(
                    "Digite APAGAR para limpar todos os dados",
                    key="confirmar_apagar_tudo"
                )

                if st.button("🗑️ Apagar tudo", use_container_width=True):
                    if confirmar != "APAGAR":
                        st.warning("Digite APAGAR para confirmar.")
                    else:
                        apagar_tudo()
                        st.success("Todos os dados foram apagados.")
                        st.rerun()
    
    if st.session_state.setor == "MONTAGEM":
        c_op1, c_op2 = st.columns([3, 1])

        with c_op1:
            st.caption(f"Operador atual: **{st.session_state.nome}**")

        with c_op2:
            if st.button("👤 Trocar operador", use_container_width=True):
                abrir_troca_operador()
                st.rerun()

    if st.button("🔄 Atualizar"):
        st.rerun()

    pedidos_por_estado = obter_pedidos_por_estado()

    with st.expander("📂 Programados / Importação"):
        ocultas = st.columns(2)

        for idx, estado in enumerate(ESTADOS_OCULTOS):
            render_coluna(ocultas[idx], estado, pedidos_por_estado[estado])

    st.divider()

    linha1 = st.columns(3)
    linha2 = st.columns(3)

    for idx, estado in enumerate(ESTADOS_VISIVEIS):
        coluna = linha1[idx] if idx < 3 else linha2[idx - 3]
        render_coluna(coluna, estado, pedidos_por_estado[estado])

def icone_tipo_pedido(tipo_pedido):
    if tipo_pedido == "IMPORTACAO":
        return "✈️ "
    if tipo_pedido == "PROGRAMADO":
        return "📅 "
    return ""

def render_coluna(coluna, estado, pedidos):
    with coluna:
        minimizada = st.session_state.filas_minimizadas.get(estado, False)        
        c_titulo, c_btn = st.columns([4, 1])

        with c_titulo:
            st.markdown(f"### {LABEL_ESTADOS[estado]} ({len(pedidos)})")

        with c_btn:
            if st.button("➕" if minimizada else "➖", key=f"min_{estado}"):
                st.session_state.filas_minimizadas[estado] = not minimizada
                st.rerun()
        st.markdown(
            f"<div style='height:10px;background:{CORES_ESTADOS[estado]};"
            f"border-radius:8px;margin-bottom:10px'></div>",
            unsafe_allow_html=True,
        )
        if minimizada:
            st.caption("Fila minimizada.")
            return
            
        for pedido in pedidos:
            pedido_id = pedido["id"]
            aberto = st.session_state.pedido_aberto == pedido_id

            icone = icone_tipo_pedido(pedido.get("tipo_pedido"))

            badges = ""

            if quantidade_mensagens(pedido_id) > 0:
                badges += " 💬"

            # futuramente
            # if quantidade_alertas(pedido_id) > 0:
            #     badges += " 🚨"

            # if pedido.get("foto_obrigatoria"):
            #     badges += " 📷"

            label = f"{icone}{pedido['numero_pedido']} - {pedido['cliente']}{badges}"

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
                        if estado == "MONTADOS" and st.session_state.setor in ["VENDAS", "ADMINISTRADOR"]:
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

if st.session_state.show_trocar_operador:
    modal_trocar_operador()

st_autorefresh(interval=15000, key="notificacoes_refresh")

verificar_notificacoes()

with st.sidebar:
    st.markdown("## Jefferson App")
    st.caption(f"{st.session_state.nome} ({st.session_state.setor})")

    if st.session_state.setor in ["VENDAS", "ADMINISTRADOR"]:
        paginas = [
            "Fila de Pedidos",
            "Criar Pedido",
        ]
    else:
        paginas = [
            "Fila de Pedidos",
        ]

    pagina = st.radio(
        "Navegação",
        paginas,
    )

    st.divider()

    if st.button("🚪 Sair"):
        st.session_state.clear()
        st.rerun()


if pagina == "Criar Pedido":
    if st.session_state.setor not in ["VENDAS", "ADMINISTRADOR"]:
        st.error("Você não possui permissão para acessar esta página.")
        st.stop()

    pagina_criar_pedido()
else:
    pagina_fila()

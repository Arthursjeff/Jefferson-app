import streamlit as st
import json
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
    obter_contagens_mensagens,
    obter_contagens_alertas,
    ESTADOS_VISIVEIS,
    ESTADOS_OCULTOS,
    adicionar_alerta,
    obter_alertas,
    remover_alerta,
    editar_dados_pedido,
    adicionar_mensagem,
    obter_mensagens,
    remover_mensagem,
)


st.set_page_config(
    page_title="Jefferson App",
    page_icon="🧾",
    layout="wide",
)

def ativar_notificacoes():
    components.html(
        """
        <div id="ativar_notificacoes"></div>

        <script>
        async function iniciar() {

            if (!("Notification" in window)) {
                document.getElementById("ativar_notificacoes").innerHTML =
                    "<b>Este navegador não suporta notificações.</b>";
                return;
            }

            if (Notification.permission === "granted") {
                return;
            }

            if (Notification.permission === "denied") {
                document.getElementById("ativar_notificacoes").innerHTML =
                    "<b>⚠️ As notificações estão bloqueadas neste navegador.</b>";
                return;
            }

            document.getElementById("ativar_notificacoes").innerHTML = `
                <button onclick="pedirPermissao()"
                    style="
                        background:#0e7490;
                        color:white;
                        border:none;
                        padding:10px 18px;
                        border-radius:8px;
                        cursor:pointer;
                        font-weight:bold;
                    ">
                    🔔 Ativar notificações
                </button>
            `;
        }

        async function pedirPermissao(){

            const permissao = await Notification.requestPermission();

            if(permissao==="granted"){

                new Notification("Jefferson App",{
                    body:"Notificações ativadas com sucesso!"
                });

                location.reload();

            }

        }

        iniciar();

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
    st.session_state.setdefault("form_pedido_id", 0)
    st.session_state.setdefault("show_editar_pedido", False)
    st.session_state.setdefault("show_alerta_modal", False)
    st.session_state.setdefault("pedido_alerta", None)
    st.session_state.setdefault("show_foto_modal", False)
    st.session_state.setdefault("pedido_foto", None)
    st.session_state.setdefault("show_teste_camera", False)
    st.session_state.setdefault("pedido_edicao", None)
    st.session_state.setdefault("show_nf_modal", False)
    st.session_state.setdefault("filas_minimizadas", {})
    st.session_state.setdefault("show_trocar_operador", False)
    st.session_state.setdefault("pedido_nf", None)

def abrir_modal_nf(pedido):
    st.session_state.show_nf_modal = True
    st.session_state.pedido_nf = pedido

def abrir_teste_camera():
    st.session_state.show_teste_camera = True

def abrir_modal_foto(pedido):
    st.session_state.show_foto_modal = True
    st.session_state.pedido_foto = pedido


def fechar_modal_foto():
    st.session_state.show_foto_modal = False
    st.session_state.pedido_foto = None


@st.dialog("📷 Foto obrigatória")
def modal_foto_obrigatoria():
    pedido = st.session_state.get("pedido_foto")

    if not pedido:
        st.error("Pedido não encontrado.")
        return

    st.write(f"Pedido: **{pedido.get('numero_pedido')} - {pedido.get('cliente')}**")
    st.warning("Para avançar de Faturado para Embalado, é obrigatório tirar uma foto.")

    foto = st.camera_input("Tirar foto da embalagem")

    c1, c2 = st.columns(2)

    with c1:
        if st.button("Cancelar"):
            fechar_modal_foto()
            st.rerun()

    with c2:
        if st.button("Confirmar e avançar", type="primary"):
            if not foto:
                st.warning("Tire uma foto antes de avançar.")
                return

            sucesso, mensagem = avancar_pedido(
                pedido=pedido,
                usuario=st.session_state.nome,
                setor_usuario=st.session_state.setor,
            )

            if sucesso:
                fechar_modal_foto()
                st.session_state.pedido_aberto = None
                st.success(mensagem)
                st.rerun()
            else:
                st.warning(mensagem)

def fechar_teste_camera():
    st.session_state.show_teste_camera = False    

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

def abrir_edicao_pedido(pedido):
    st.session_state.show_editar_pedido = True
    st.session_state.pedido_edicao = pedido


def fechar_edicao_pedido():
    st.session_state.show_editar_pedido = False
    st.session_state.pedido_edicao = None

@st.dialog("✏️ Editar pedido")
def modal_editar_pedido():
    pedido = st.session_state.get("pedido_edicao")

    if not pedido:
        st.error("Pedido não encontrado.")
        return

    numero = st.text_input(
        "Número do pedido",
        value=pedido.get("numero_pedido", ""),
    )

    cliente = st.text_input(
        "Cliente",
        value=pedido.get("cliente", ""),
    )

    tipo_pedido = st.selectbox(
        "Tipo do pedido",
        ["NORMAL", "PROGRAMADO", "IMPORTACAO"],
        index=["NORMAL", "PROGRAMADO", "IMPORTACAO"].index(
            pedido.get("tipo_pedido") or "NORMAL"
        ),
    )

    data_prevista = st.date_input(
        "Data prevista de faturamento",
        value=pedido.get("data_prevista_faturamento"),
    )

    nota_fiscal = st.text_input(
        "Nota Fiscal",
        value=pedido.get("nota_fiscal") or "",
    )

    c1, c2 = st.columns(2)

    with c1:
        if st.button("Cancelar"):
            fechar_edicao_pedido()
            st.rerun()

    with c2:
        if st.button("Salvar alterações", type="primary"):
            sucesso, mensagem = editar_dados_pedido(
                pedido=pedido,
                numero_pedido=numero,
                cliente=cliente,
                tipo_pedido=tipo_pedido,
                data_prevista_faturamento=data_prevista,
                nota_fiscal=nota_fiscal,
                usuario=st.session_state.nome,
                setor_usuario=st.session_state.setor,
            )

            if sucesso:
                fechar_edicao_pedido()
                st.success(mensagem)
                st.rerun()
            else:
                st.warning(mensagem)

def abrir_modal_alerta(pedido):
    st.session_state.show_alerta_modal = True
    st.session_state.pedido_alerta = pedido


def fechar_modal_alerta():
    st.session_state.show_alerta_modal = False
    st.session_state.pedido_alerta = None


@st.dialog("🚨 Criar alerta")
def modal_alerta():
    pedido = st.session_state.get("pedido_alerta")

    if not pedido:
        st.error("Pedido não encontrado.")
        return

    st.write(f"Pedido: **{pedido.get('numero_pedido')} - {pedido.get('cliente')}**")

    texto = st.text_area(
        "Texto do alerta",
        height=120,
        placeholder="Descreva o alerta..."
    )

    c1, c2 = st.columns(2)

    with c1:
        if st.button("Cancelar"):
            fechar_modal_alerta()
            st.rerun()

    with c2:
        if st.button("Criar alerta", type="primary"):
            sucesso, mensagem = adicionar_alerta(
                pedido=pedido,
                mensagem=texto,
                usuario=st.session_state.nome,
                setor_usuario=st.session_state.setor,
            )

            if sucesso:
                fechar_modal_alerta()
                st.success(mensagem)
                st.rerun()
            else:
                st.warning(mensagem)

def tela_login():
    st.title("🔐 Login")

    with st.form("form_login"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        entrar = st.form_submit_button("Entrar", type="primary")

    if entrar:
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

    with st.form(f"form_criar_pedido_{st.session_state.form_pedido_id}"):

        numero = st.text_input("Número do pedido")

        cliente = st.text_input("Cliente")

        tipo_pedido = st.selectbox(
            "Tipo do pedido",
            ["NORMAL", "PROGRAMADO", "IMPORTACAO"]
        )

        data_prevista_faturamento = st.date_input(
            "Data prevista de faturamento"
        )

        criar = st.form_submit_button(
            "Criar pedido",
            type="primary"
        )

    if criar:
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

            # Gera um formulário completamente novo
            st.session_state.form_pedido_id += 1

            st.rerun()

        else:
            st.warning(mensagem)

def verificar_notificacoes():
    if not st.session_state.logado:
        return

    usuario = st.session_state.usuario

    notificacoes = obter_notificacoes_pendentes(usuario)

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
                    body: {json.dumps(mensagem)},
                    icon: "https://cdn-icons-png.flaticon.com/512/1827/1827370.png",
                    requireInteraction: true
                }});
            }}
            </script>
            """,
            height=1,
        )

        visualizar_notificacao(notif["id"])

    st.rerun()
    
@st.fragment(run_every="15s")
def monitor_notificacoes():
    verificar_notificacoes()

@st.fragment
def render_kanban():
    pedidos_por_estado = obter_pedidos_por_estado()
    contagens_mensagens = obter_contagens_mensagens()
    contagens_alertas = obter_contagens_alertas()

    with st.expander("📂 Programados / Importação"):
        ocultas = st.columns(2)

        for idx, estado in enumerate(ESTADOS_OCULTOS):
            render_coluna(
                ocultas[idx],
                estado,
                pedidos_por_estado[estado],
                contagens_mensagens,
                contagens_alertas,
            )

    st.divider()

    linha1 = st.columns(3)
    linha2 = st.columns(3)

    for idx, estado in enumerate(ESTADOS_VISIVEIS):
        coluna = linha1[idx] if idx < 3 else linha2[idx - 3]

        render_coluna(
            coluna,
            estado,
            pedidos_por_estado[estado],
            contagens_mensagens,
            contagens_alertas,
        )

@st.dialog("📷 Teste de câmera")
def modal_teste_camera():
    st.write("Teste de captura de foto pelo navegador/celular.")

    foto = st.camera_input("Tirar foto")

    if foto:
        st.success("Foto capturada com sucesso.")
        st.image(foto, caption="Pré-visualização da foto capturada")

    if st.button("Fechar"):
        st.rerun()

def pagina_fila():
    st.title("📦 Fila de Pedidos")
    ativar_notificacoes()
    if st.session_state.setor == "ADMINISTRADOR":
        with st.expander("⚙️ Administração"):
            c_admin1, c_admin2 = st.columns(2)

            with c_admin1:
                if st.button("📊 Gerar relatório", use_container_width=True):
                    st.info("Relatório ainda será configurado.")

            with c_admin2:
                confirmar = st.text_input(
                    "Digite APAGAR para limpar todos os dados",
                    key="confirmar_apagar_tudo"
                )

                if st.button("📷 Testar câmera", use_container_width=True):
                    abrir_teste_camera()
                    st.rerun()
                    
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
    
    render_kanban()

def icone_tipo_pedido(tipo_pedido):
    if tipo_pedido == "IMPORTACAO":
        return "✈️ "
    if tipo_pedido == "PROGRAMADO":
        return "📅 "
    return ""

def render_coluna(coluna, estado, pedidos, contagens_mensagens, contagens_alertas):
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

            if contagens_mensagens.get(pedido_id, 0) > 0:
                badges += " 💬"

            if contagens_alertas.get(pedido_id, 0) > 0:
                badges += " 🚨"

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
                    if contagens_alertas.get(pedido_id, 0) > 0:
                        st.error("🚨 Este pedido possui alerta ativo.")

                        alertas = obter_alertas(pedido_id)

                        for alerta in alertas:
                            st.warning(
                                f"**{alerta.get('criado_por', '')}:** "
                                f"{alerta.get('mensagem', '')}"
                            )

                            if st.button("✅ Resolver alerta", key=f"resolver_alerta_{alerta['id']}"):
                                sucesso, mensagem = remover_alerta(alerta["id"])

                                if sucesso:
                                    st.success(mensagem)
                                    st.rerun()
                                else:
                                    st.warning(mensagem)                        
                    if st.session_state.setor == "ADMINISTRADOR":
                        if st.button("✏️ Editar pedido", key=f"editar_{pedido_id}"):
                            abrir_edicao_pedido(pedido)
                            st.rerun()
                    st.divider()

                    # =========================
                    # MENSAGENS
                    # =========================

                    qtd_msg = contagens_mensagens.get(pedido_id, 0)

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

                                # Apenas na transição FATURADO -> EMBALADO exige foto
                                if (
                                    estado == "FATURADO"
                                    and st.session_state.setor in ["MONTAGEM", "ADMINISTRADOR"]
                                ):
                                    abrir_modal_foto(pedido)
                                    st.rerun()

                                else:

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

                    
                    if st.button("🚨 Criar alerta", key=f"criar_alerta_{pedido_id}", use_container_width=True):
                        abrir_modal_alerta(pedido)
                        st.rerun()
                    
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

monitor_notificacoes()

if st.session_state.show_foto_modal:
    modal_foto_obrigatoria()

if st.session_state.show_editar_pedido:
    modal_editar_pedido()

if st.session_state.show_teste_camera:
    modal_teste_camera()

if st.session_state.show_alerta_modal:
    modal_alerta()

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

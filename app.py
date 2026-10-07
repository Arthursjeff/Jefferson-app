import streamlit as st
import json
import streamlit.components.v1 as components
from core.admin import apagar_tudo
from modules.modulo_orcamentos.orcamentos_ui import pagina_orcamentos
from modules.modulo_orcamentos.clientes_ui import pagina_clientes
from modules.modulo_orcamentos.clientes_importacao_ui import pagina_importar_clientes
from modules.analises import pagina_analises
from modules.consertos import pagina_consertos
from modules.consulta_fotos import pagina_consulta_pedidos
from core.auth import validar_login, USUARIOS
from modules.modulo_01.service import (
    ESTADOS_FILA,
    LABEL_ESTADOS,
    CORES_ESTADOS,
    obter_pedidos_por_estado,
    pesquisar_historico_retirados,
    salvar_foto_e_avancar,
    criar_novo_pedido,
    obter_notificacoes_pendentes,
    visualizar_notificacao,
    avancar_pedido,
    faturar_com_nota,
    alterar_status_expedicao,
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
    obter_destino_pedido,
    dados_peso_volumes_validos,
    registrar_peso_volumes,
    salvar_peso_volumes_e_avancar,
)


st.set_page_config(
    page_title="Jefferson App",
    page_icon="assets/icone_jefferson.png",
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
    st.session_state.setdefault("show_cancelar_modal", False)
    st.session_state.setdefault("pedido_cancelamento", None)
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
    st.session_state.setdefault("show_peso_volume_modal", False)
    st.session_state.setdefault("pedido_peso_volume", None)
    st.session_state.setdefault("peso_volume_avancar", False)

def abrir_modal_peso_volume(pedido, avancar=False):
    st.session_state.show_peso_volume_modal = True
    st.session_state.pedido_peso_volume = pedido
    st.session_state.peso_volume_avancar = avancar


def fechar_modal_peso_volume():
    st.session_state.show_peso_volume_modal = False
    st.session_state.pedido_peso_volume = None
    st.session_state.peso_volume_avancar = False


@st.dialog("📦 Peso e volumes")
def modal_peso_volume():
    pedido = st.session_state.get("pedido_peso_volume")
    avancar = st.session_state.get("peso_volume_avancar", False)

    if not pedido:
        st.error("Pedido não encontrado.")
        return

    st.write(f"Pedido: **{pedido.get('numero_pedido')} - {pedido.get('cliente')}**")

    if avancar:
        st.warning("Peso total e quantidade de volumes são obrigatórios para entrar em Montados.")
    else:
        st.caption("Você pode atualizar estes dados enquanto o pedido permanecer em Programados.")

    peso_atual = pedido.get("peso_total")
    volumes_atual = pedido.get("quantidade_volumes")

    peso = st.number_input(
        "Peso total (kg)",
        min_value=0.0,
        value=float(peso_atual) if peso_atual is not None else 0.0,
        step=0.001,
        format="%.3f",
        key=f"peso_total_{pedido['id']}",
    )

    volumes = st.number_input(
        "Quantidade de volumes",
        min_value=1,
        value=int(volumes_atual) if volumes_atual is not None and int(volumes_atual) > 0 else 1,
        step=1,
        key=f"quantidade_volumes_{pedido['id']}",
    )

    c1, c2 = st.columns(2)

    with c1:
        if st.button("Cancelar", key=f"cancelar_peso_volume_{pedido['id']}", use_container_width=True):
            fechar_modal_peso_volume()
            st.rerun()

    with c2:
        texto_botao = "Salvar e avançar" if avancar else "Salvar"
        if st.button(
            texto_botao,
            key=f"salvar_peso_volume_{pedido['id']}",
            type="primary",
            use_container_width=True,
        ):
            if avancar:
                sucesso, mensagem = salvar_peso_volumes_e_avancar(
                    pedido=pedido,
                    peso_total=peso,
                    quantidade_volumes=volumes,
                    usuario=st.session_state.nome,
                    setor_usuario=st.session_state.setor,
                )
            else:
                sucesso, mensagem = registrar_peso_volumes(
                    pedido=pedido,
                    peso_total=peso,
                    quantidade_volumes=volumes,
                    usuario=st.session_state.nome,
                    setor_usuario=st.session_state.setor,
                )

            if sucesso:
                fechar_modal_peso_volume()
                st.session_state.pedido_aberto = None
                st.success(mensagem)
                st.rerun()
            else:
                st.warning(mensagem)


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

            sucesso, mensagem = salvar_foto_e_avancar(
                pedido=pedido,
                foto=foto,
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

def abrir_modal_cancelamento(pedido):
    st.session_state.show_cancelar_modal = True
    st.session_state.pedido_cancelamento = pedido


def fechar_modal_cancelamento():
    st.session_state.show_cancelar_modal = False
    st.session_state.pedido_cancelamento = None

@st.dialog("❌ Confirmar cancelamento")
def modal_cancelamento():
    pedido = st.session_state.get("pedido_cancelamento")

    if not pedido:
        st.error("Pedido não encontrado.")
        return

    st.warning(
        "Esta ação cancelará o pedido. "
        "Digite APAGAR para confirmar."
    )

    st.write(
        f"Pedido: **{pedido.get('numero_pedido')} - "
        f"{pedido.get('cliente')}**"
    )

    confirmacao = st.text_input(
        "Confirmação",
        placeholder="Digite APAGAR",
        key=f"confirmar_cancelamento_{pedido['id']}",
    )

    c1, c2 = st.columns(2)

    with c1:
        if st.button(
            "Voltar",
            key=f"voltar_cancelamento_{pedido['id']}",
            use_container_width=True,
        ):
            fechar_modal_cancelamento()
            st.rerun()

    with c2:
        if st.button(
            "❌ Cancelar pedido",
            key=f"confirmar_cancelamento_botao_{pedido['id']}",
            type="primary",
            use_container_width=True,
        ):
            if confirmacao.strip().upper() != "APAGAR":
                st.warning("Digite APAGAR corretamente para confirmar.")
                return

            sucesso, mensagem = cancelar(
                pedido_id=pedido["id"],
                usuario=st.session_state.nome,
                setor_usuario=st.session_state.setor,
            )

            if sucesso:
                fechar_modal_cancelamento()
                st.session_state.pedido_aberto = None
                st.success(mensagem)
                st.rerun()
            else:
                st.warning(mensagem)


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
    if tipo_pedido == "CONSERTO":
        return "🔧 "
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

        if estado == "RETIRADO":
            st.caption("Exibindo retirados nos últimos 3 dias.")

            with st.expander("🔎 Pesquisar histórico"):
                with st.form("form_pesquisa_retirados"):
                    termo_retirados = st.text_input(
                        "Pedido, cliente ou nota fiscal",
                        placeholder="Digite para pesquisar no histórico completo",
                    )
                    buscar_retirados = st.form_submit_button(
                        "Buscar",
                        use_container_width=True,
                    )

                if buscar_retirados:
                    resultados_retirados = pesquisar_historico_retirados(termo_retirados)

                    if not str(termo_retirados or "").strip():
                        st.warning("Digite um pedido, cliente ou nota fiscal.")
                    elif not resultados_retirados:
                        st.info("Nenhum pedido retirado encontrado.")
                    else:
                        st.caption(f"{len(resultados_retirados)} resultado(s) encontrado(s).")

                        for resultado in resultados_retirados:
                            retirado_em = resultado.get("_retirado_em") or ""
                            retirado_formatado = retirado_em

                            try:
                                from datetime import datetime
                                data_retirada = datetime.fromisoformat(retirado_em)
                                retirado_formatado = data_retirada.strftime("%d/%m/%Y às %H:%M")
                            except (TypeError, ValueError):
                                pass

                            with st.container(border=True):
                                st.markdown(
                                    f"**Pedido {resultado.get('numero_pedido', '')} — "
                                    f"{resultado.get('cliente', '')}**"
                                )
                                st.write(f"Nota Fiscal: {resultado.get('nota_fiscal') or 'Não informada'}")
                                st.write(f"Retirado em: **{retirado_formatado}**")
                                st.write(
                                    f"Movimentado por: **{resultado.get('_retirado_por') or 'Não identificado'}**"
                                )

        if minimizada:
            st.caption("Fila minimizada.")
            return
            
        for pedido in pedidos:
            pedido_id = pedido["id"]
            aberto = st.session_state.pedido_aberto == pedido_id

            icone = icone_tipo_pedido(pedido.get("tipo_pedido"))

            badges = ""

            if estado in ["FATURADO", "EMBALADO"]:
                badges += f" {pedido.get('_icone_expedicao', '⚪')}"

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

                    if dados_peso_volumes_validos(pedido):
                        peso_formatado = f"{float(pedido.get('peso_total')):.3f}".replace(".", ",")
                        st.info(
                            f"📦 Peso: {peso_formatado} kg | "
                            f"Volumes: {int(pedido.get('quantidade_volumes'))}"
                        )
                    elif estado == "MONTADOS":
                        st.warning("📦 Peso e volumes pendentes (pedido anterior à nova validação).")

                    if (
                        estado == "PROGRAMADO"
                        and pedido.get("tipo_pedido") == "PROGRAMADO"
                        and st.session_state.setor in ["MONTAGEM", "ADMINISTRADOR"]
                    ):
                        texto_peso = (
                            "✏️ Editar peso e volumes"
                            if dados_peso_volumes_validos(pedido)
                            else "📦 Informar peso e volumes"
                        )
                        if st.button(texto_peso, key=f"peso_volume_programado_{pedido_id}", use_container_width=True):
                            abrir_modal_peso_volume(pedido, avancar=False)
                            st.rerun()

                    if (
                        estado == "MONTADOS"
                        and not dados_peso_volumes_validos(pedido)
                        and st.session_state.setor in ["MONTAGEM", "ADMINISTRADOR"]
                    ):
                        if st.button(
                            "📦 Regularizar peso e volumes",
                            key=f"regularizar_peso_volume_{pedido_id}",
                            use_container_width=True,
                        ):
                            abrir_modal_peso_volume(pedido, avancar=False)
                            st.rerun()
                    if estado in ["FATURADO", "EMBALADO"]:
                        status_atual = pedido.get("_status_expedicao", "PENDENTE")
                        nomes_status = {
                            "PENDENTE": "⚪ Pendente",
                            "AGUARDANDO": "🟡 Aguardando",
                            "LIBERADO": "🟢 Liberado",
                            "BLOQUEADO": "🔴 Bloqueado",
                        }
                        st.info(f"Status de expedição: **{nomes_status.get(status_atual, '⚪ Pendente')}**")

                        if st.session_state.setor in ["VENDAS", "ADMINISTRADOR"]:
                            st.caption("Atualizar status de expedição")
                            c_exp1, c_exp2, c_exp3 = st.columns(3)

                            opcoes_expedicao = [
                                (c_exp1, "🟡", "AGUARDANDO"),
                                (c_exp2, "🟢", "LIBERADO"),
                                (c_exp3, "🔴", "BLOQUEADO"),
                            ]

                            for coluna_exp, icone_exp, status_exp in opcoes_expedicao:
                                with coluna_exp:
                                    if st.button(
                                        icone_exp,
                                        key=f"status_expedicao_{status_exp}_{pedido_id}",
                                        use_container_width=True,
                                        disabled=status_atual == status_exp,
                                    ):
                                        sucesso, mensagem = alterar_status_expedicao(
                                            pedido=pedido,
                                            status_expedicao=status_exp,
                                            usuario=st.session_state.nome,
                                            setor_usuario=st.session_state.setor,
                                        )
                                        if sucesso:
                                            st.success(mensagem)
                                            st.rerun()
                                        else:
                                            st.warning(mensagem)

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
                                    destino = obter_destino_pedido(pedido)

                                    if destino == "MONTADOS" and not dados_peso_volumes_validos(pedido):
                                        abrir_modal_peso_volume(pedido, avancar=True)
                                        st.rerun()

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
                        if st.button(
                            "❌ Cancelar",
                            key=f"cancelar_{pedido_id}",
                            use_container_width=True,
                        ):
                            abrir_modal_cancelamento(pedido)
                            st.rerun()

                    
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

if st.session_state.show_peso_volume_modal and st.session_state.pedido_peso_volume:
    modal_peso_volume()

if st.session_state.show_trocar_operador:
    modal_trocar_operador()

monitor_notificacoes()

if st.session_state.show_foto_modal and st.session_state.pedido_foto:
    pedido_foto = st.session_state.pedido_foto

    if pedido_foto.get("setor_atual") == "FATURADO":
        modal_foto_obrigatoria()
    else:
        fechar_modal_foto()

if st.session_state.show_editar_pedido:
    modal_editar_pedido()

if st.session_state.show_teste_camera:
    modal_teste_camera()

if st.session_state.show_alerta_modal:
    modal_alerta()
if st.session_state.show_cancelar_modal:
    modal_cancelamento()

with st.sidebar:
    st.markdown("## Jefferson App")
    st.caption(f"{st.session_state.nome} ({st.session_state.setor})")

    if st.session_state.setor == "ADMINISTRADOR":
        paginas = [
            "Fila de Pedidos",
            "Criar Pedido",
            "Orçamentos",
            "Clientes",
            "Importar Clientes",
            "Análises",
            "Consertos",
            "Consulta de Pedidos",
        ]

    elif st.session_state.setor == "VENDAS":
        paginas = [
            "Fila de Pedidos",
            "Criar Pedido",
            "Orçamentos",
            "Clientes",
            "Consulta de Pedidos",
        ]

    elif st.session_state.setor == "MONTAGEM":
        paginas = [
            "Fila de Pedidos",
            "Orçamentos",
            "Clientes",
            "Consertos",
        ]

    else:
        paginas = [
            "Fila de Pedidos",
            "Orçamentos",
            "Clientes",
        ]

    pagina = st.radio(
        "Navegação",
        paginas,
    )

    if pagina == "Orçamentos":
        with st.expander("📄 Orçamentos", expanded=True):
            operacoes = ["Novo orçamento", "Buscar orçamento"] if st.session_state.setor in ("ADMINISTRADOR", "VENDAS", "MONTAGEM") else ["Buscar orçamento"]
            if st.session_state.get("orc_nav") not in operacoes:
                st.session_state["orc_nav"] = operacoes[0]
            st.radio("Operação", operacoes, key="orc_nav")

    st.divider()

    if st.button("🚪 Sair"):
        st.session_state.clear()
        st.rerun()


if pagina == "Criar Pedido":

    if st.session_state.setor not in ["VENDAS", "ADMINISTRADOR"]:
        st.error("Você não possui permissão para acessar esta página.")
        st.stop()

    pagina_criar_pedido()


elif pagina == "Clientes":

    pagina_clientes()


elif pagina == "Importar Clientes":

    if st.session_state.setor != "ADMINISTRADOR":
        st.error("A importação da base de clientes é permitida somente para administradores.")
        st.stop()

    pagina_importar_clientes()


elif pagina == "Análises":

    if st.session_state.setor != "ADMINISTRADOR":
        st.error("Esta página é exclusiva para administradores.")
        st.stop()

    pagina_analises()


elif pagina == "Consertos":

    if st.session_state.setor not in ["ADMINISTRADOR", "MONTAGEM"]:
        st.error("Você não possui permissão para acessar esta página.")
        st.stop()

    pagina_consertos()


elif pagina == "Consulta de Pedidos":

    if st.session_state.setor not in ["ADMINISTRADOR", "VENDAS"]:
        st.error("Você não possui permissão para acessar esta página.")
        st.stop()

    pagina_consulta_pedidos()


elif pagina == "Orçamentos":

    pagina_orcamentos()

else:

    pagina_fila()



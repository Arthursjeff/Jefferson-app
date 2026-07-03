import streamlit as st
from db import listar_pedidos, criar_pedido, mover_pedido

# ==========================================================
# CONFIGURAÇÕES GERAIS / CONSTANTES
# ==========================================================

USUARIOS = {
    "arthur": {
        "senha": "1234",
        "nome": "Arthur",
        "setor": "VENDAS",
        "permissoes": {
            "CRIAR_PEDIDO": True,
            "MOVE": {
                "MONTADOS": ["FATURADO"],
            },
        },
    },
    "amanda": {
        "senha": "1234",
        "nome": "Amanda",
        "setor": "VENDAS",
        "permissoes": {
            "CRIAR_PEDIDO": True,
            "MOVE": {},
        },
    },
    "joao": {
        "senha": "1234",
        "nome": "João",
        "setor": "MONTAGEM",
        "permissoes": {
            "CRIAR_PEDIDO": False,
            "MOVE": {
                "PEDIDO": ["EM_MONTAGEM"],
                "EM_MONTAGEM": ["MONTADOS"],
                "FATURADO": ["EMBALADO"],
                "EMBALADO": ["RETIRADO"],
            },
        },
    },
}

ESTADOS_VISUAIS = [
    "PEDIDO",
    "EM_MONTAGEM",
    "MONTADOS",
    "FATURADO",
    "EMBALADO",
    "RETIRADO",
]

ESTADO_LABEL = {
    "PEDIDO": "Pedidos",
    "EM_MONTAGEM": "Em Montagem",
    "MONTADOS": "Montados",
    "FATURADO": "Faturados",
    "EMBALADO": "Embalados",
    "RETIRADO": "Retirados",
}

COR_POR_ESTADO = {
    "PEDIDO": "#FFA500",
    "EM_MONTAGEM": "#FFF8B5",
    "MONTADOS": "#90EE90",
    "FATURADO": "#87CEFA",
    "EMBALADO": "#D8B4FE",
    "RETIRADO": "#A9A9A9",
}

# ==========================================================
# SESSION STATE
# ==========================================================

def init_session():
    st.session_state.setdefault("logado", False)
    st.session_state.setdefault("usuario_logado", None)
    st.session_state.setdefault("nome_usuario", None)
    st.session_state.setdefault("setor_usuario", None)
    st.session_state.setdefault("permissoes", {})
    st.session_state.setdefault("ui", {})
    st.session_state.ui.setdefault("pedido_aberto", None)

# ==========================================================
# CSS GLOBAL
# ==========================================================

def inject_css():
    st.markdown("""
    <style>
      [data-testid="stExpander"] {
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        margin: 4px 0;
      }
      details[data-testid="stExpander"] > summary {
        padding: 4px 8px !important;
        font-size: 0.9rem;
        line-height: 1.1;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .stButton { margin: 2px 0 !important; }
      .stButton button {
        padding: 4px 8px;
        line-height: 1.1;
        font-size: 0.85rem;
      }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# LOGIN
# ==========================================================

def gate_login():
    st.title("🔐 Login")

    usuario = st.text_input("Usuário").strip().lower()
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if usuario not in USUARIOS:
            st.error("Usuário inválido")
            return

        if senha != USUARIOS[usuario]["senha"]:
            st.error("Senha incorreta")
            return

        st.session_state.logado = True
        st.session_state.usuario_logado = usuario
        st.session_state.nome_usuario = USUARIOS[usuario]["nome"]
        st.session_state.setor_usuario = USUARIOS[usuario]["setor"]
        st.session_state.permissoes = USUARIOS[usuario]["permissoes"]

        st.rerun()

# ==========================================================
# HELPERS
# ==========================================================

def _hora_curta(p):
    return p.get("ultimo_mov_hora") or p.get("ultima_hora") or ""

def _usuario_curto(p):
    return p.get("ultimo_mov_usuario") or p.get("ultimo_usuario") or ""

def label_compacto(p):
    nome = f"{p['numero_pedido']} - {p['nome_pedido']}".upper()
    partes = [nome]
    if _hora_curta(p):
        partes.append(_hora_curta(p))
    if _usuario_curto(p):
        partes.append(_usuario_curto(p))
    return " — ".join(partes)

def toggle_pedido(pid):
    atual = st.session_state.ui.get("pedido_aberto")
    st.session_state.ui["pedido_aberto"] = None if atual == pid else pid

def pode_mover(estado_atual, destino):
    perms = st.session_state.permissoes.get("MOVE", {})
    return destino in perms.get(estado_atual, [])

# ==========================================================
# RENDER — CRIAR PEDIDO
# ==========================================================

def render_criar_pedido():
    st.title("➕ Criar Pedido")
    st.caption(
        f"Logado como **{st.session_state.usuario_logado}** "
        f"({st.session_state.setor_usuario})"
    )
    st.divider()

    numero = st.text_input("Número", key="numero")
    nome = st.text_input("Nome / Cliente", key="nome")

    tipo_pedido = st.radio(
        "Tipo do pedido",
        ["NORMAL", "PROGRAMADO", "IMPORTACAO"],
        horizontal=True
    )

    if st.session_state.permissoes.get("CRIAR_PEDIDO"):
        if st.button("Criar"):
            if not numero or not nome:
                st.warning("Preencha número e nome.")
            else:
                criar_pedido(
                    numero=numero,
                    nome=nome,
                    estado="PEDIDO",
                    status="ATIVO",
                    tipo=tipo_pedido,
                    usuario=st.session_state.usuario_logado
                )
                st.success("Pedido criado.")
                st.rerun()
    else:
        st.caption("🔒 Somente VENDAS pode criar pedidos.")

# ==========================================================
# RENDER — FILA
# ==========================================================

def render_fila():
    st.title("Fila de Pedidos")
    st.divider()

    pedidos = listar_pedidos()
    linhas = [st.columns(3), st.columns(3)]

    for idx, estado in enumerate(ESTADOS_VISUAIS):
        col = linhas[0][idx] if idx < 3 else linhas[1][idx - 3]
        render_setor(estado, col, pedidos)

def render_setor(estado, container, pedidos):
    pedidos_setor = [p for p in pedidos if p["estado_atual"] == estado]

    with container:
        st.markdown(f"### {ESTADO_LABEL[estado]} ({len(pedidos_setor)})")
        st.markdown(
            f"<div style='height:8px;background:{COR_POR_ESTADO[estado]};border-radius:8px'></div>",
            unsafe_allow_html=True
        )

        for p in pedidos_setor:
            aberto = st.session_state.ui["pedido_aberto"] == p["id"]

            if not aberto:
                if st.button(label_compacto(p), key=f"open-{p['id']}", use_container_width=True):
                    toggle_pedido(p["id"])
                    st.rerun()
            else:
                with st.container(border=True):
                    st.markdown(f"**{p['numero_pedido']} - {p['nome_pedido']}**")
                    st.caption(f"{_hora_curta(p)} • {_usuario_curto(p)}")

                    st.divider()
                    idx = ESTADOS_VISUAIS.index(estado)
                    c1, c2 = st.columns(2)

                    with c1:
                        if idx > 0:
                            destino = ESTADOS_VISUAIS[idx - 1]
                            if st.button("⬅️ Voltar", disabled=not pode_mover(estado, destino)):
                                mover_pedido(
                                    p["id"], estado, destino,
                                    st.session_state.usuario_logado,
                                    st.session_state.setor_usuario
                                )
                                toggle_pedido(p["id"])
                                st.rerun()
                        else:
                            st.button("⬅️ Voltar", disabled=True)

                    with c2:
                        if idx < len(ESTADOS_VISUAIS) - 1:
                            destino = ESTADOS_VISUAIS[idx + 1]
                            if st.button("➡️ Avançar", disabled=not pode_mover(estado, destino)):
                                mover_pedido(
                                    p["id"], estado, destino,
                                    st.session_state.usuario_logado,
                                    st.session_state.setor_usuario
                                )
                                toggle_pedido(p["id"])
                                st.rerun()
                        else:
                            st.button("➡️ Avançar", disabled=True)

                    if st.button("⬆️ Fechar"):
                        toggle_pedido(p["id"])
                        st.rerun()

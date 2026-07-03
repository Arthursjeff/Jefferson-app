import streamlit as st
from supabase import create_client
from datetime import datetime


# ======================
# REGRAS DE PERMISSÃO (BACKEND)
# ======================

PERMISSOES_POR_SETOR = {
    "VENDAS": {
        "MONTADOS": ["FATURADO"],
    },
    "MONTAGEM": {
        "PEDIDO": ["EM_MONTAGEM"],
        "EM_MONTAGEM": ["PROGRAMADOS_IMPORTACAO", "MONTADOS"],
        "PROGRAMADOS_IMPORTACAO": ["MONTADOS"],
        "FATURADO": ["EMBALADO"],
        "EMBALADO": ["RETIRADO"],
    },
}


# ======================
# CONEXÃO SUPABASE
# ======================

def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"]
    )


# ======================
# PEDIDOS
# ======================

def listar_pedidos():
    sb = get_supabase()
    return (
        sb.table("pedidos")
        .select("*")
        .order("criado_em")
        .execute()
        .data
    )


def criar_pedido(numero, nome, estado, status, usuario):
    sb = get_supabase()

    agora = datetime.utcnow().isoformat()

    # cria o pedido
    pedido = (
        sb.table("pedidos")
        .insert({
            "numero_pedido": numero,
            "nome_pedido": nome,
            "estado_atual": estado,
            "status": status,
            "tipo_pedido": tipo,
            "criado_por": usuario,
            "criado_em": agora,
            "ultimo_usuario": usuario,
            "ultima_hora": agora,
        })
        .execute()
        .data[0]
    )

    # registra evento de criação
    registrar_evento(
        pedido_id=pedido["id"],
        tipo_evento="CRIACAO",
        descricao=f"Pedido criado no estado {estado}",
        autor=usuario,
    )

    return pedido


def mover_pedido(pedido_id, estado_atual, novo_estado, usuario, setor_usuario):
    sb = get_supabase()

    # validar permissão
    destinos = PERMISSOES_POR_SETOR.get(setor_usuario, {}).get(estado_atual, [])
    if novo_estado not in destinos:
        return False

    res = (
        sb.table("pedidos")
        .update({
            "estado_atual": novo_estado,
            "ultimo_mov_usuario": usuario,
            "ultimo_mov_hora": datetime.utcnow().isoformat(),
        })
        .eq("id", pedido_id)
        .eq("estado_atual", estado_atual)
        .execute()
    )

    if not res.data:
        return False

    registrar_evento(
        pedido_id,
        "MOVIMENTACAO",
        f"{estado_atual} → {novo_estado}",
        usuario
    )

    return True


# ======================
# HISTÓRICO / EVENTOS
# ======================

def registrar_evento(pedido_id, tipo_evento, descricao, autor):
    sb = get_supabase()
    sb.table("pedido_eventos").insert({
        "pedido_id": pedido_id,
        "tipo_evento": tipo_evento,      # CRIACAO, MOVIMENTACAO, etc.
        "descricao": descricao,
        "autor": autor,
        "criado_em": datetime.utcnow().isoformat(),
    }).execute()


def listar_eventos_pedido(pedido_id):
    sb = get_supabase()
    return (
        sb.table("pedido_eventos")
        .select("*")
        .eq("pedido_id", pedido_id)
        .order("criado_em")
        .execute()
        .data
    )

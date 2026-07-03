from datetime import datetime
from core.database import supabase

TABELA_PEDIDOS = "fila_pedidos"
TABELA_MOVIMENTACOES = "fila_movimentacoes"


def _agora():
    return datetime.now()


def criar_pedido(numero_pedido: str, cliente: str, usuario: str):
    agora = _agora()

    dados = {
        "numero_pedido": str(numero_pedido).strip(),
        "cliente": str(cliente).strip().upper(),
        "criado_por": usuario,
        "criado_data": agora.date().isoformat(),
        "criado_hora": agora.time().strftime("%H:%M:%S"),
        "setor_atual": "PEDIDO",
        "status": "ATIVO",
    }

    response = supabase.table(TABELA_PEDIDOS).insert(dados).execute()

    pedido = response.data[0] if response.data else None

    if pedido:
        registrar_movimentacao(
            pedido_id=pedido["id"],
            origem=None,
            destino="PEDIDO",
            usuario=usuario,
            setor_usuario=None,
        )

    return pedido


def listar_pedidos(status: str = "ATIVO"):
    query = supabase.table(TABELA_PEDIDOS).select("*")

    if status:
        query = query.eq("status", status)

    response = query.order("criado_data", desc=False).execute()
    return response.data or []


def buscar_pedido_por_id(pedido_id: int):
    response = (
        supabase
        .table(TABELA_PEDIDOS)
        .select("*")
        .eq("id", pedido_id)
        .single()
        .execute()
    )

    return response.data


def mover_pedido(
    pedido_id: int,
    origem: str,
    destino: str,
    usuario: str,
    setor_usuario: str,
):
    response = (
        supabase
        .table(TABELA_PEDIDOS)
        .update({"setor_atual": destino})
        .eq("id", pedido_id)
        .eq("setor_atual", origem)
        .execute()
    )

    if not response.data:
        return False

    registrar_movimentacao(
        pedido_id=pedido_id,
        origem=origem,
        destino=destino,
        usuario=usuario,
        setor_usuario=setor_usuario,
    )

    return True


def cancelar_pedido(pedido_id: int, usuario: str):
    response = (
        supabase
        .table(TABELA_PEDIDOS)
        .update({"status": "CANCELADO"})
        .eq("id", pedido_id)
        .execute()
    )

    if response.data:
        registrar_movimentacao(
            pedido_id=pedido_id,
            origem=None,
            destino="CANCELADO",
            usuario=usuario,
            setor_usuario=None,
        )

    return bool(response.data)


def finalizar_pedido(pedido_id: int, usuario: str):
    response = (
        supabase
        .table(TABELA_PEDIDOS)
        .update({"status": "FINALIZADO"})
        .eq("id", pedido_id)
        .execute()
    )

    if response.data:
        registrar_movimentacao(
            pedido_id=pedido_id,
            origem=None,
            destino="FINALIZADO",
            usuario=usuario,
            setor_usuario=None,
        )

    return bool(response.data)


def registrar_movimentacao(
    pedido_id: int,
    origem: str | None,
    destino: str,
    usuario: str,
    setor_usuario: str | None,
):
    dados = {
        "pedido_id": pedido_id,
        "origem": origem,
        "destino": destino,
        "usuario": usuario,
        "setor_usuario": setor_usuario,
    }

    response = supabase.table(TABELA_MOVIMENTACOES).insert(dados).execute()
    return response.data[0] if response.data else None


def listar_movimentacoes(pedido_id: int):
    response = (
        supabase
        .table(TABELA_MOVIMENTACOES)
        .select("*")
        .eq("pedido_id", pedido_id)
        .order("criado_em", desc=False)
        .execute()
    )

    return response.data or []

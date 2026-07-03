from datetime import datetime
from core.database import supabase

TABELA_PEDIDOS = "fila_pedidos"
TABELA_MOVIMENTACOES = "fila_movimentacoes"


def criar_pedido(numero_pedido: str, cliente: str, usuario: str):
    agora = datetime.now()

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
            tipo_evento="CRIACAO",
            origem=None,
            destino="PEDIDO",
            usuario=usuario,
            observacao=f"Pedido criado por {usuario}."
        )

    return pedido


def listar_pedidos(status: str = "ATIVO"):
    query = supabase.table(TABELA_PEDIDOS).select("*")

    if status:
        query = query.eq("status", status)

    response = query.order("criado_data", desc=False).execute()
    return response.data or []


def mover_pedido(pedido_id: int, origem: str, destino: str, usuario: str):
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
        tipo_evento="MOVIMENTACAO",
        origem=origem,
        destino=destino,
        usuario=usuario,
        observacao=f"Pedido movido de {origem} para {destino} por {usuario}."
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
            tipo_evento="CANCELAMENTO",
            origem=None,
            destino="CANCELADO",
            usuario=usuario,
            observacao=f"Pedido cancelado por {usuario}."
        )

    return bool(response.data)


def registrar_movimentacao(
    pedido_id: int,
    tipo_evento: str,
    origem: str | None,
    destino: str,
    usuario: str,
    observacao: str = "",
):
    dados = {
        "pedido_id": pedido_id,
        "tipo_evento": tipo_evento,
        "origem": origem,
        "destino": destino,
        "usuario": usuario,
        "observacao": observacao,
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

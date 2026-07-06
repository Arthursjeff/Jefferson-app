from datetime import datetime
from core.database import supabase

TABELA_PEDIDOS = "fila_pedidos"
TABELA_MOVIMENTACOES = "fila_movimentacoes"


def criar_pedido(numero_pedido: str, cliente: str, usuario: str, tipo_pedido: str, data_prevista_faturamento):
    agora = datetime.now()

    dados = {
        "numero_pedido": str(numero_pedido).strip(),
        "cliente": str(cliente).strip().upper(),
        "criado_por": usuario,
        "criado_data": agora.date().isoformat(),
        "criado_hora": agora.time().strftime("%H:%M:%S"),
        "tipo_pedido": tipo_pedido,
        "data_prevista_faturamento": data_prevista_faturamento,        
        "setor_atual": "PEDIDO",
        "status": "ATIVO",
    }

    response = supabase.table(TABELA_PEDIDOS).insert(dados).execute()
    pedido = response.data[0] if response.data else None

    if pedido:
        registrar_movimentacao(
            pedido_id=pedido["id"],
            origem="",
            destino="PEDIDO",
            usuario=usuario,
            tipo_evento="CRIACAO",
            observacao=f"Pedido criado por {usuario}."
        )

    return pedido


def listar_pedidos(status: str = "ATIVO"):
    query = supabase.table(TABELA_PEDIDOS).select("*")

    if status:
        query = query.eq("status", status)

    response = query.order("id", desc=False).execute()
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
        origem=origem,
        destino=destino,
        usuario=usuario,
        tipo_evento="MOVIMENTACAO",
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
            origem="",
            destino="CANCELADO",
            usuario=usuario,
            tipo_evento="CANCELAMENTO",
            observacao=f"Pedido cancelado por {usuario}."
        )

    return bool(response.data)


def registrar_movimentacao(
    pedido_id: int,
    origem: str,
    destino: str,
    usuario: str,
    tipo_evento: str,
    observacao: str = "",
):
    dados = {
        "pedido_id": pedido_id,
        "origem": origem,
        "destino": destino,
        "usuario": usuario,
        "tipo_evento": tipo_evento,
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
    
def registrar_nota_fiscal(pedido_id: int, nota_fiscal: str, usuario: str):
    nota = str(nota_fiscal).strip()

    if not nota:
        return False

    response = (
        supabase
        .table(TABELA_PEDIDOS)
        .update({"nota_fiscal": nota})
        .eq("id", pedido_id)
        .execute()
    )

    if response.data:
        registrar_movimentacao(
            pedido_id=pedido_id,
            origem="MONTADOS",
            destino="FATURADO",
            usuario=usuario,
            tipo_evento="NOTA_FISCAL",
            observacao=f"Nota Fiscal {nota} registrada por {usuario}."
        )

    return bool(response.data)

def editar_pedido(
    pedido_id: int,
    numero_pedido: str,
    cliente: str,
    tipo_pedido: str,
    data_prevista_faturamento,
    nota_fiscal: str,
    usuario: str,
):
    dados = {
        "numero_pedido": str(numero_pedido).strip(),
        "cliente": str(cliente).strip().upper(),
        "tipo_pedido": tipo_pedido,
        "data_prevista_faturamento": str(data_prevista_faturamento),
        "nota_fiscal": str(nota_fiscal).strip() if nota_fiscal else None,
    }

    response = (
        supabase
        .table(TABELA_PEDIDOS)
        .update(dados)
        .eq("id", pedido_id)
        .execute()
    )

    if response.data:
        registrar_movimentacao(
            pedido_id=pedido_id,
            origem="",
            destino="",
            usuario=usuario,
            tipo_evento="EDICAO",
            observacao=f"Pedido editado por {usuario}."
        )

    return bool(response.data)

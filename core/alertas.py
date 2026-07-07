from core.database import supabase

TABELA_ALERTAS = "fila_alertas"


def criar_alerta(pedido_id: int, mensagem: str, usuario: str):
    texto = (mensagem or "").strip()

    if not texto:
        return None

    dados = {
        "pedido_id": pedido_id,
        "mensagem": texto,
        "criado_por": usuario,
        "ativo": True,
    }

    response = supabase.table(TABELA_ALERTAS).insert(dados).execute()
    return response.data[0] if response.data else None


def listar_alertas(pedido_id: int, apenas_ativos: bool = True):
    query = (
        supabase
        .table(TABELA_ALERTAS)
        .select("*")
        .eq("pedido_id", pedido_id)
    )

    if apenas_ativos:
        query = query.eq("ativo", True)

    response = query.order("criado_em", desc=False).execute()
    return response.data or []


def resolver_alerta(alerta_id: int):
    response = (
        supabase
        .table(TABELA_ALERTAS)
        .update({"ativo": False})
        .eq("id", alerta_id)
        .execute()
    )

    return bool(response.data)


def contar_alertas_ativos(pedido_id: int):
    alertas = listar_alertas(pedido_id, apenas_ativos=True)
    return len(alertas)

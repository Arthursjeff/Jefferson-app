from core.database import supabase

TABELA_MENSAGENS = "fila_mensagens"


def criar_mensagem(pedido_id: int, mensagem: str, usuario: str):
    texto = (mensagem or "").strip()

    if not texto:
        return None

    dados = {
        "pedido_id": pedido_id,
        "mensagem": texto,
        "criado_por": usuario,
        "ativa": True,
    }

    response = supabase.table(TABELA_MENSAGENS).insert(dados).execute()
    return response.data[0] if response.data else None


def listar_mensagens(pedido_id: int, apenas_ativas: bool = True):
    query = (
        supabase
        .table(TABELA_MENSAGENS)
        .select("*")
        .eq("pedido_id", pedido_id)
    )

    if apenas_ativas:
        query = query.eq("ativa", True)

    response = query.order("criado_em", desc=False).execute()
    return response.data or []


def desativar_mensagem(mensagem_id: int):
    response = (
        supabase
        .table(TABELA_MENSAGENS)
        .update({"ativa": False})
        .eq("id", mensagem_id)
        .execute()
    )

    return bool(response.data)


def contar_mensagens_ativas(pedido_id: int):
    mensagens = listar_mensagens(pedido_id, apenas_ativas=True)
    return len(mensagens)


def contar_mensagens_por_pedido():
    response = (
        supabase
        .table(TABELA_MENSAGENS)
        .select("pedido_id")
        .eq("ativa", True)
        .execute()
    )

    contagem = {}

    for item in response.data or []:
        pedido_id = item["pedido_id"]
        contagem[pedido_id] = contagem.get(pedido_id, 0) + 1

    return contagem

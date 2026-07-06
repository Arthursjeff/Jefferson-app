from core.database import supabase

TABELA_NOTIFICACOES = "fila_notificacoes"


def criar_notificacao(pedido_id: int, setor_destino: str, tipo: str, mensagem: str):
    dados = {
        "pedido_id": pedido_id,
        "setor_destino": setor_destino,
        "tipo": tipo,
        "mensagem": mensagem,
        "visualizado": False,
    }

    response = supabase.table(TABELA_NOTIFICACOES).insert(dados).execute()
    return response.data[0] if response.data else None


def listar_notificacoes_pendentes(setor_destino: str):
    response = (
        supabase
        .table(TABELA_NOTIFICACOES)
        .select("*")
        .eq("setor_destino", setor_destino)
        .eq("visualizado", False)
        .order("criado_em", desc=False)
        .execute()
    )

    return response.data or []


def marcar_notificacao_visualizada(notificacao_id: int):
    response = (
        supabase
        .table(TABELA_NOTIFICACOES)
        .update({"visualizado": True})
        .eq("id", notificacao_id)
        .execute()
    )

    return bool(response.data)


def marcar_todas_visualizadas(setor_destino: str):
    response = (
        supabase
        .table(TABELA_NOTIFICACOES)
        .update({"visualizado": True})
        .eq("setor_destino", setor_destino)
        .eq("visualizado", False)
        .execute()
    )

    return bool(response.data)

from core.database import supabase
from core.auth import USUARIOS

TABELA_NOTIFICACOES = "fila_notificacoes"


def criar_notificacao(
    pedido_id: int,
    setor_destino: str,
    tipo: str,
    mensagem: str,
    usuario_destino: str | None = None,
):
    dados = {
        "pedido_id": pedido_id,
        "setor_destino": setor_destino,
        "usuario_destino": usuario_destino,
        "tipo": tipo,
        "mensagem": mensagem,
        "visualizado": False,
    }

    response = supabase.table(TABELA_NOTIFICACOES).insert(dados).execute()
    return response.data[0] if response.data else None


def criar_notificacao_para_setor(
    pedido_id: int,
    setor_destino: str,
    tipo: str,
    mensagem: str,
):
    notificacoes = []

    for usuario, dados in USUARIOS.items():
        if dados.get("setor") == setor_destino:
            notificacao = criar_notificacao(
                pedido_id=pedido_id,
                setor_destino=setor_destino,
                usuario_destino=usuario,
                tipo=tipo,
                mensagem=mensagem,
            )
            notificacoes.append(notificacao)

    return notificacoes


def listar_notificacoes_pendentes(usuario_destino: str):
    response = (
        supabase
        .table(TABELA_NOTIFICACOES)
        .select("*")
        .eq("usuario_destino", usuario_destino)
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


def marcar_todas_visualizadas(usuario_destino: str):
    response = (
        supabase
        .table(TABELA_NOTIFICACOES)
        .update({"visualizado": True})
        .eq("usuario_destino", usuario_destino)
        .eq("visualizado", False)
        .execute()
    )

    return bool(response.data)

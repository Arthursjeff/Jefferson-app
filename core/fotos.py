from datetime import datetime
from zoneinfo import ZoneInfo
from core.database import supabase

BUCKET_FOTOS = "fotos-pedidos"
TABELA_FOTOS = "fila_fotos"


def salvar_foto_pedido(pedido_id: int, foto, usuario: str, tipo_evento: str):
    agora = datetime.now(ZoneInfo("America/Sao_Paulo"))
    datahora = agora.strftime("%Y%m%d_%H%M%S")

    arquivo_path = f"pedido_{pedido_id}/{tipo_evento}_{datahora}.jpg"

    conteudo = foto.getvalue()

    supabase.storage.from_(BUCKET_FOTOS).upload(
        arquivo_path,
        conteudo,
        {
            "content-type": "image/jpeg",
            "upsert": "false",
        },
    )

    dados = {
        "pedido_id": pedido_id,
        "tipo_evento": tipo_evento,
        "arquivo_path": arquivo_path,
        "criado_por": usuario,
        "criado_em": agora.isoformat(),
    }

    response = supabase.table(TABELA_FOTOS).insert(dados).execute()

    return response.data[0] if response.data else None

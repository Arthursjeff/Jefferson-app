"""Controle leve de alterações da fila, compartilhado entre as sessões Streamlit."""

from core.database import supabase


def obter_versao_fila() -> int:
    """Uma consulta de uma linha; alterações são registradas por triggers SQL."""
    resposta = (
        supabase.table("fila_revisao")
        .select("versao")
        .eq("id", 1)
        .limit(1)
        .execute()
    )
    if not resposta.data:
        raise RuntimeError("Controle de revisão da fila não encontrado no Supabase.")
    return int(resposta.data[0]["versao"])

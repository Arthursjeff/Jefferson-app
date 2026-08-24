from datetime import datetime, timezone

from core.database import supabase


TAMANHO_LOTE = 500


def importar_clientes_supabase(clientes):
    """
    Insere clientes novos e atualiza clientes existentes.

    A identificação é feita pelo codigo_cliente.
    O processamento ocorre em lotes para evitar requisições
    excessivamente grandes.
    """

    total = len(clientes)

    if total == 0:
        return {
            "sucesso": True,
            "total": 0,
            "processados": 0,
            "lotes": 0,
        }

    processados = 0
    lotes_processados = 0

    agora = datetime.now(timezone.utc).isoformat()

    for inicio in range(0, total, TAMANHO_LOTE):

        fim = inicio + TAMANHO_LOTE

        lote = clientes[inicio:fim]

        # Marca quando esses registros foram importados
        for cliente in lote:
            cliente["updated_at"] = agora
            cliente["ultima_importacao"] = agora

        supabase.table("clientes").upsert(
            lote,
            on_conflict="codigo_cliente"
        ).execute()

        processados += len(lote)
        lotes_processados += 1

    return {
        "sucesso": True,
        "total": total,
        "processados": processados,
        "lotes": lotes_processados,
    }

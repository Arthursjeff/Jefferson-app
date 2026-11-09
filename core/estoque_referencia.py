"""Consulta isolada da fotografia HISTÓRICA do ERP no Supabase.

Não produz estoque operacional, reservas ou movimentações.
"""
from core.database import supabase
from core.motor_transformacoes import normalizar

TABELA_INVENTARIOS = "estoque_inventarios"
TABELA_ITENS = "estoque_inventario_itens"
REFERENCIA_LABORATORIO = "ERP_2026-11-03_LAB_TRANSF_v1"


def carregar_estoque_referencia():
    """Retorna (metadados, saldos históricos) do último snapshot selecionado."""
    resposta = (
        supabase.table(TABELA_INVENTARIOS)
        .select("id,referencia_externa,origem,capturado_em,observacao,status")
        .eq("referencia_externa", REFERENCIA_LABORATORIO)
        .eq("status", "CONFIRMADO")
        .order("criado_em", desc=True).limit(1).execute()
    )
    registros = resposta.data or []
    if not registros:
        raise RuntimeError("Estoque de referência do Laboratório não encontrado.")
    inv = registros[0]
    saldos = {}
    inicio = 0
    while True:
        linhas = (
            supabase.table(TABELA_ITENS)
            .select("codigo,quantidade")
            .eq("inventario_id", inv["id"])
            .range(inicio, inicio + 999).execute()
        ).data or []
        for linha in linhas:
            codigo = normalizar(linha["codigo"])
            if codigo:
                saldos[codigo] = saldos.get(codigo, 0) + float(linha["quantidade"])
        if len(linhas) < 1000:
            break
        inicio += 1000
    return inv, saldos

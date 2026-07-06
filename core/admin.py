from core.database import supabase


def apagar_tudo():
    supabase.table("fila_mensagens").delete().neq("id", 0).execute()
    supabase.table("fila_alertas").delete().neq("id", 0).execute()
    supabase.table("fila_movimentacoes").delete().neq("id", 0).execute()
    supabase.table("fila_pedidos").delete().neq("id", 0).execute()
    return True

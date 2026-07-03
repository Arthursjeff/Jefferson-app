from core import config
from supabase import create_client

# Inicializa o cliente Supabase com as credenciais do config
supabase = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)

# Função para inserir um pedido
def inserir_pedido(dados_pedido):
    response = supabase.table("FILA-PEDIDOS").insert(dados_pedido).execute()
    return response

# Função para buscar pedidos
def buscar_pedidos():
    response = supabase.table("FILA-PEDIDOS").select("*").execute()
    return response

# Função para atualizar um pedido
def atualizar_pedido(id_pedido, novos_dados):
    response = supabase.table("FILA-PEDIDOS").update(novos_dados).eq("id", id_pedido).execute()
    return response

# Função para deletar um pedido
def deletar_pedido(id_pedido):
    response = supabase.table("FILA-PEDIDOS").delete().eq("id", id_pedido).execute()
    return response

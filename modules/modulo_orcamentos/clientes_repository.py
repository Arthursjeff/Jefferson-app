from core.database import supabase


def buscar_clientes(termo: str, limite: int = 20):
    termo = (termo or "").strip()

    if not termo:
        return []

    # Busca em código, razão social, nome fantasia e CNPJ/CPF
    resposta = (
        supabase
        .table("clientes")
        .select(
            "id,"
            "codigo_cliente,"
            "razao_social,"
            "nome_fantasia,"
            "cnpj_cpf,"
            "tipo_cliente,"
            "cidade,"
            "estado,"
            "email"
        )
        .or_(
            f"codigo_cliente.ilike.%{termo}%,"
            f"razao_social.ilike.%{termo}%,"
            f"nome_fantasia.ilike.%{termo}%,"
            f"cnpj_cpf.ilike.%{termo}%"
        )
        .limit(limite)
        .execute()
    )

    return resposta.data or []

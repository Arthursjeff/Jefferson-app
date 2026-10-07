from core.database import supabase
import re


def buscar_clientes(termo: str, limite: int = 20):
    termo = (termo or "").strip()
    if not termo:
        return []
    campos = "id,codigo_cliente,razao_social,nome_fantasia,cnpj_cpf,tipo_cliente,cidade,estado,email,validade_especial,pagamento_especial,frete_especial"
    encontrados = supabase.table("clientes").select(campos).eq("codigo_cliente", termo).limit(limite).execute().data or []
    documento = re.sub(r"[^A-Za-z0-9]", "", termo).upper()
    if len(documento) == 14:
        mascarado = f"{documento[:2]}.{documento[2:5]}.{documento[5:8]}/{documento[8:12]}-{documento[12:]}"
        encontrados += supabase.table("clientes").select(campos).in_("cnpj_cpf", [documento, mascarado]).limit(limite).execute().data or []
    for campo in ("codigo_cliente", "razao_social", "nome_fantasia"):
        encontrados += supabase.table("clientes").select(campos).ilike(campo, f"%{termo}%").limit(limite).execute().data or []
    return list({c["id"]: c for c in encontrados}.values())[:limite]

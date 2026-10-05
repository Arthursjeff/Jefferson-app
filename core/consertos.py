from datetime import datetime
from zoneinfo import ZoneInfo

from core.database import supabase

TABELA_CONSERTOS = "consertos"
TABELA_ITENS = "conserto_itens"
TABELA_MOVIMENTACOES = "conserto_movimentacoes"

ESTAGIOS = ["CHEGOU", "VERIFICADO", "CORRIGIDO", "PRONTO_PARA_RETIRADA"]


def _agora():
    return datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat()


def registrar_movimentacao(conserto_id, origem, destino, usuario, tipo_evento, observacao=""):
    dados = {
        "conserto_id": conserto_id,
        "origem": origem or "",
        "destino": destino or "",
        "usuario": usuario,
        "tipo_evento": tipo_evento,
        "observacao": observacao or "",
        "criado_em": _agora(),
    }
    response = supabase.table(TABELA_MOVIMENTACOES).insert(dados).execute()
    return response.data[0] if response.data else None


def criar_conserto(cliente, chegou_com_nota, nota_fiscal_cliente, itens, usuario):
    cliente = str(cliente or "").strip().upper()
    nota = str(nota_fiscal_cliente or "").strip() or None

    if not cliente:
        return None

    dados = {
        "cliente": cliente,
        "chegou_com_nota": bool(chegou_com_nota),
        "nota_fiscal_cliente": nota,
        "estagio_atual": "CHEGOU",
        "status": "ATIVO",
        "criado_por": usuario,
    }

    response = supabase.table(TABELA_CONSERTOS).insert(dados).execute()
    conserto = response.data[0] if response.data else None
    if not conserto:
        return None

    linhas = [
        {
            "conserto_id": conserto["id"],
            "codigo": str(item["codigo"]).strip().upper(),
            "quantidade": int(item["quantidade"]),
        }
        for item in itens
    ]

    try:
        supabase.table(TABELA_ITENS).insert(linhas).execute()
    except Exception:
        supabase.table(TABELA_CONSERTOS).delete().eq("id", conserto["id"]).execute()
        raise

    registrar_movimentacao(
        conserto["id"], "", "CHEGOU", usuario, "CRIACAO",
        f"Conserto recebido e cadastrado por {usuario}.",
    )
    return conserto


def listar_consertos():
    response = (
        supabase.table(TABELA_CONSERTOS)
        .select("*")
        .eq("status", "ATIVO")
        .order("id", desc=False)
        .execute()
    )
    return response.data or []


def listar_itens(conserto_id):
    response = (
        supabase.table(TABELA_ITENS)
        .select("*")
        .eq("conserto_id", conserto_id)
        .order("id", desc=False)
        .execute()
    )
    return response.data or []


def listar_movimentacoes(conserto_id):
    response = (
        supabase.table(TABELA_MOVIMENTACOES)
        .select("*")
        .eq("conserto_id", conserto_id)
        .order("criado_em", desc=False)
        .execute()
    )
    return response.data or []


def adicionar_nota_cliente(conserto_id, nota, usuario):
    nota = str(nota or "").strip()
    if not nota:
        return False

    dados = {
        "nota_fiscal_cliente": nota,
        "nota_cliente_adicionada_por": usuario,
        "nota_cliente_adicionada_em": _agora(),
    }
    response = supabase.table(TABELA_CONSERTOS).update(dados).eq("id", conserto_id).execute()
    if not response.data:
        return False

    registrar_movimentacao(
        conserto_id, "", "", usuario, "NOTA_CLIENTE",
        f"NF do cliente {nota} adicionada por {usuario}.",
    )
    return True


def avancar_com_dados(conserto, usuario, texto=None, nota_jefferson=None):
    origem = conserto.get("estagio_atual")
    if origem not in ESTAGIOS:
        return False
    idx = ESTAGIOS.index(origem)
    if idx >= len(ESTAGIOS) - 1:
        return False

    destino = ESTAGIOS[idx + 1]
    agora = _agora()
    dados = {"estagio_atual": destino}

    if origem == "CHEGOU" and destino == "VERIFICADO":
        dados.update({
            "diagnostico": str(texto or "").strip(),
            "verificado_por": usuario,
            "verificado_em": agora,
        })
    elif origem == "VERIFICADO" and destino == "CORRIGIDO":
        dados.update({
            "correcao": str(texto or "").strip(),
            "corrigido_por": usuario,
            "corrigido_em": agora,
        })
    elif origem == "CORRIGIDO" and destino == "PRONTO_PARA_RETIRADA":
        dados.update({
            "nota_fiscal_jefferson": str(nota_jefferson or "").strip(),
            "pronto_retirada_por": usuario,
            "pronto_retirada_em": agora,
        })

    response = (
        supabase.table(TABELA_CONSERTOS)
        .update(dados)
        .eq("id", conserto["id"])
        .eq("estagio_atual", origem)
        .execute()
    )
    if not response.data:
        return False

    observacao = f"Conserto movido de {origem} para {destino} por {usuario}."
    if texto:
        observacao += f" Registro: {str(texto).strip()}"
    if nota_jefferson:
        observacao += f" NF Jefferson: {str(nota_jefferson).strip()}"

    registrar_movimentacao(
        conserto["id"], origem, destino, usuario, "MOVIMENTACAO", observacao
    )
    return True

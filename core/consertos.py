from datetime import datetime
from zoneinfo import ZoneInfo

from core.database import supabase
from core.notificacoes import criar_notificacao_para_setor

TABELA_CONSERTOS = "consertos"
TABELA_ITENS = "conserto_itens"
TABELA_MOVIMENTACOES = "conserto_movimentacoes"
TABELA_FILA_PEDIDOS = "fila_pedidos"
TABELA_FILA_MOVIMENTACOES = "fila_movimentacoes"

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


def definir_liberacao(conserto, usuario, setor_usuario):
    if setor_usuario != "ADMINISTRADOR":
        return False, "Somente ADMINISTRADOR pode liberar o conserto."

    estagio = conserto.get("estagio_atual")
    if estagio == "CHEGOU":
        campo, campo_por, campo_em = "chegou_liberado", "chegou_liberado_por", "chegou_liberado_em"
    elif estagio == "VERIFICADO":
        campo, campo_por, campo_em = "verificado_liberado", "verificado_liberado_por", "verificado_liberado_em"
    else:
        return False, "Este estágio não possui liberação administrativa."

    if conserto.get(campo):
        return False, "Este estágio já está liberado."

    dados = {campo: True, campo_por: usuario, campo_em: _agora()}
    response = (
        supabase.table(TABELA_CONSERTOS)
        .update(dados)
        .eq("id", conserto["id"])
        .eq("estagio_atual", estagio)
        .eq(campo, False)
        .execute()
    )
    if not response.data:
        return False, "Não foi possível liberar. Atualize a página e tente novamente."

    registrar_movimentacao(
        conserto["id"], estagio, estagio, usuario, "LIBERACAO_ADMINISTRATIVA",
        f"{estagio} liberado para prosseguimento por {usuario}.",
    )
    return True, "Conserto liberado para prosseguimento."



def _criar_card_faturado_conserto(conserto, nota_jefferson, usuario):
    conserto_id = conserto["id"]

    existente = (
        supabase.table(TABELA_FILA_PEDIDOS)
        .select("id")
        .eq("conserto_id", conserto_id)
        .limit(1)
        .execute()
    )
    if existente.data:
        return existente.data[0]

    agora = datetime.now(ZoneInfo("America/Sao_Paulo"))
    dados = {
        "numero_pedido": f"CONS-{conserto_id}",
        "cliente": str(conserto.get("cliente") or "").strip().upper(),
        "criado_por": usuario,
        "criado_data": agora.date().isoformat(),
        "criado_hora": agora.time().strftime("%H:%M:%S"),
        "tipo_pedido": "CONSERTO",
        "data_prevista_faturamento": agora.date().isoformat(),
        "setor_atual": "FATURADO",
        "status": "ATIVO",
        "nota_fiscal": str(nota_jefferson).strip(),
        "conserto_id": conserto_id,
    }

    response = supabase.table(TABELA_FILA_PEDIDOS).insert(dados).execute()
    pedido = response.data[0] if response.data else None
    if not pedido:
        return None

    eventos = [
        {
            "pedido_id": pedido["id"],
            "origem": "",
            "destino": "FATURADO",
            "usuario": usuario,
            "tipo_evento": "CRIACAO_CONSERTO",
            "observacao": f"Card criado automaticamente a partir do Conserto #{conserto_id}.",
            "criado_em": _agora(),
        },
        {
            "pedido_id": pedido["id"],
            "origem": "FATURADO",
            "destino": "PENDENTE",
            "usuario": usuario,
            "tipo_evento": "STATUS_EXPEDICAO",
            "observacao": f"Status de expedição iniciado como Pendente após conclusão do Conserto #{conserto_id}.",
            "criado_em": _agora(),
        },
    ]
    supabase.table(TABELA_FILA_MOVIMENTACOES).insert(eventos).execute()

    criar_notificacao_para_setor(
        pedido_id=pedido["id"],
        setor_destino="MONTAGEM",
        tipo="PEDIDO_FATURADO",
        mensagem=f"Conserto faturado: CONS-{conserto_id} - {pedido['cliente']}",
    )
    return pedido

def avancar_com_dados(conserto, usuario, setor_usuario, texto=None, nota_jefferson=None):
    origem = conserto.get("estagio_atual")
    if origem not in ESTAGIOS:
        return False
    idx = ESTAGIOS.index(origem)
    if idx >= len(ESTAGIOS) - 1:
        return False

    destino = ESTAGIOS[idx + 1]

    if origem == "CHEGOU" and not conserto.get("chegou_liberado"):
        return False
    if origem == "VERIFICADO" and not conserto.get("verificado_liberado"):
        return False

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
        nota_final = str(nota_jefferson or "").strip()
        if not nota_final:
            return False

        try:
            pedido_fila = _criar_card_faturado_conserto(conserto, nota_final, usuario)
        except Exception:
            return False

        if not pedido_fila:
            return False

        dados.update({
            "nota_fiscal_jefferson": nota_final,
            "pronto_retirada_por": usuario,
            "pronto_retirada_em": agora,
            "pedido_fila_id": pedido_fila["id"],
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

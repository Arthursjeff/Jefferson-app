from core.pedidos import (
    criar_pedido,
    listar_pedidos,
    mover_pedido,
    editar_pedido,
    registrar_nota_fiscal,
    cancelar_pedido,
    listar_movimentacoes,
)

from core.alertas import (
    criar_alerta,
    listar_alertas,
    contar_alertas_por_pedido,
    resolver_alerta,
    contar_alertas_ativos,
)

from core.notificacoes import (
    criar_notificacao_para_setor,
    listar_notificacoes_pendentes,
    marcar_notificacao_visualizada,
)

from core.permissions import (
    pode_mover,
    pode_criar_pedido,
    pode_cancelar_pedido,
)
from core.mensagens import (
    criar_mensagem,
    listar_mensagens,
    contar_mensagens_por_pedido,
    desativar_mensagem,
    contar_mensagens_ativas,
)

ESTADOS_FILA = [
    "PEDIDO",
    "EM_MONTAGEM",
    "PROGRAMADO",
    "IMPORTACAO",
    "MONTADOS",
    "FATURADO",
    "EMBALADO",
    "RETIRADO",
]

ESTADOS_VISIVEIS = [
    "PEDIDO",
    "EM_MONTAGEM",
    "MONTADOS",
    "FATURADO",
    "EMBALADO",
    "RETIRADO",
]

ESTADOS_OCULTOS = [
    "PROGRAMADO",
    "IMPORTACAO",
]

LABEL_ESTADOS = {
    "PEDIDO": "Pedidos",
    "EM_MONTAGEM": "Em Montagem",
    "MONTADOS": "Montados",
    "FATURADO": "Faturados",
    "EMBALADO": "Embalados",
    "RETIRADO": "Retirados",
    "PROGRAMADO": "Programados",
    "IMPORTACAO": "Importação",    
}

CORES_ESTADOS = {
    "PEDIDO": "#FFA500",
    "EM_MONTAGEM": "#FFF8B5",
    "MONTADOS": "#90EE90",
    "FATURADO": "#87CEFA",
    "EMBALADO": "#D8B4FE",
    "RETIRADO": "#A9A9A9",
    "PROGRAMADO": "#C4B5FD",
    "IMPORTACAO": "#FDBA74",    
}


def obter_pedidos():
    return listar_pedidos(status="ATIVO")


def obter_pedidos_por_estado():
    pedidos = obter_pedidos()
    agrupado = {estado: [] for estado in ESTADOS_FILA}

    for pedido in pedidos:
        estado = pedido.get("setor_atual")
        if estado in agrupado:
            agrupado[estado].append(pedido)

    return agrupado


def criar_novo_pedido(numero_pedido: str, cliente: str, usuario: str, setor_usuario: str, tipo_pedido: str, data_prevista_faturamento):
    if not pode_criar_pedido(setor_usuario):
        return False, "Usuário sem permissão para criar pedidos."

    if not numero_pedido or not cliente:
        return False, "Preencha número do pedido e cliente."
        
    if not data_prevista_faturamento:
        return False, "Informe a data prevista de faturamento."
    
    pedido = criar_pedido(
        numero_pedido=numero_pedido,
        cliente=cliente,
        usuario=usuario,
        tipo_pedido=tipo_pedido,
        data_prevista_faturamento=str(data_prevista_faturamento),
    )
    
    if not pedido:
        return False, "Erro ao criar pedido."

    criar_notificacao_para_setor(
        pedido_id=pedido["id"],
        setor_destino="MONTAGEM",
        tipo="NOVO_PEDIDO",
        mensagem=f"Novo pedido criado: {pedido['numero_pedido']} - {pedido['cliente']}"
    )

    return True, "Pedido criado com sucesso."

def avancar_pedido(pedido: dict, usuario: str, setor_usuario: str):
    estado_atual = pedido.get("setor_atual")

    if estado_atual not in ESTADOS_FILA:
        return False, "Estado atual inválido."

    idx = ESTADOS_FILA.index(estado_atual)

    if idx >= len(ESTADOS_FILA) - 1:
        return False, "Pedido já está no último estágio."

    destino = ESTADOS_FILA[idx + 1]

    if estado_atual == "EM_MONTAGEM":
        tipo = pedido.get("tipo_pedido")

        if tipo == "PROGRAMADO":
            destino = "PROGRAMADO"
        elif tipo == "IMPORTACAO":
            destino = "IMPORTACAO"
        else:
            destino = "MONTADOS"

    if estado_atual in ["PROGRAMADO", "IMPORTACAO"]:
        destino = "MONTADOS"
    if not pode_mover(setor_usuario, estado_atual, destino):
        return False, "Usuário sem permissão para esta movimentação."

    sucesso = mover_pedido(
        pedido_id=pedido["id"],
        origem=estado_atual,
        destino=destino,
        usuario=usuario,
    )

    if not sucesso:
        return False, "Erro ao mover pedido."

    if destino == "MONTADOS":
        criar_notificacao_para_setor(
            pedido_id=pedido["id"],
            setor_destino="VENDAS",
            tipo="PEDIDO_MONTADO",
            mensagem=f"Pedido montado: {pedido['numero_pedido']} - {pedido['cliente']}"
        )

    return True, f"Pedido movido para {LABEL_ESTADOS[destino]}."


def cancelar(pedido_id: int, usuario: str, setor_usuario: str):
    if not pode_cancelar_pedido(setor_usuario):
        return False, "Usuário sem permissão para cancelar pedidos."

    sucesso = cancelar_pedido(
        pedido_id=pedido_id,
        usuario=usuario,
    )

    if not sucesso:
        return False, "Erro ao cancelar pedido."

    return True, "Pedido cancelado com sucesso."


def historico_pedido(pedido_id: int):
    return listar_movimentacoes(pedido_id)
  
# ======================================================
# MENSAGENS
# ======================================================

def adicionar_mensagem(pedido_id: int, mensagem: str, usuario: str):
    if not mensagem.strip():
        return False, "Mensagem vazia."

    criar_mensagem(
        pedido_id=pedido_id,
        mensagem=mensagem,
        usuario=usuario,
    )

    return True, "Mensagem adicionada."


def obter_mensagens(pedido_id: int):
    return listar_mensagens(pedido_id)


def remover_mensagem(mensagem_id: int):
    sucesso = desativar_mensagem(mensagem_id)

    if not sucesso:
        return False, "Erro ao remover mensagem."

    return True, "Mensagem removida."


def quantidade_mensagens(pedido_id: int):
    return contar_mensagens_ativas(pedido_id)

def faturar_com_nota(pedido: dict, nota_fiscal: str, usuario: str, setor_usuario: str):
    if setor_usuario not in ["VENDAS", "ADMINISTRADOR"]:
        return False, "Somente VENDAS ou ADMINISTRADOR pode faturar pedidos."

    if pedido.get("setor_atual") != "MONTADOS":
        return False, "A Nota Fiscal só pode ser registrada em pedidos montados."

    if not str(nota_fiscal).strip():
        return False, "Informe o número da Nota Fiscal."

    sucesso_nf = registrar_nota_fiscal(
        pedido_id=pedido["id"],
        nota_fiscal=nota_fiscal,
        usuario=usuario,
    )

    if not sucesso_nf:
        return False, "Erro ao registrar Nota Fiscal."

    sucesso_mov = mover_pedido(
        pedido_id=pedido["id"],
        origem="MONTADOS",
        destino="FATURADO",
        usuario=usuario,
    )
   
    if not sucesso_mov:
        return False, "Nota registrada, mas erro ao mover para Faturados."

    criar_notificacao_para_setor(
        pedido_id=pedido["id"],
        setor_destino="MONTAGEM",
        tipo="PEDIDO_FATURADO",
        mensagem=f"Pedido faturado: {pedido['numero_pedido']} - {pedido['cliente']}"
    )

    return True, "Nota Fiscal registrada e pedido faturado."

def obter_notificacoes_pendentes(usuario: str):
    return listar_notificacoes_pendentes(usuario)


def visualizar_notificacao(notificacao_id: int):
    return marcar_notificacao_visualizada(notificacao_id)

def editar_dados_pedido(
    pedido: dict,
    numero_pedido: str,
    cliente: str,
    tipo_pedido: str,
    data_prevista_faturamento,
    nota_fiscal: str,
    usuario: str,
    setor_usuario: str,
):
    if setor_usuario != "ADMINISTRADOR":
        return False, "Somente ADMINISTRADOR pode editar pedidos."

    if not numero_pedido or not cliente:
        return False, "Número do pedido e cliente são obrigatórios."

    sucesso = editar_pedido(
        pedido_id=pedido["id"],
        numero_pedido=numero_pedido,
        cliente=cliente,
        tipo_pedido=tipo_pedido,
        data_prevista_faturamento=data_prevista_faturamento,
        nota_fiscal=nota_fiscal,
        usuario=usuario,
    )

    if not sucesso:
        return False, "Erro ao editar pedido."

    return True, "Pedido editado com sucesso."

def adicionar_alerta(pedido: dict, mensagem: str, usuario: str, setor_usuario: str):
    texto = mensagem.strip()

    if not texto:
        return False, "Digite o texto do alerta."

    alerta = criar_alerta(
        pedido_id=pedido["id"],
        mensagem=texto,
        usuario=usuario,
    )

    if not alerta:
        return False, "Erro ao criar alerta."

    if setor_usuario == "MONTAGEM":
        setor_destino = "VENDAS"
    else:
        setor_destino = "MONTAGEM"

    criar_notificacao_para_setor(
        pedido_id=pedido["id"],
        setor_destino=setor_destino,
        tipo="ALERTA",
        mensagem=f"🚨 Alerta no pedido {pedido['numero_pedido']} - {pedido['cliente']}: {texto}"
    )

    return True, "Alerta criado com sucesso."


def obter_alertas(pedido_id: int):
    return listar_alertas(pedido_id)


def remover_alerta(alerta_id: int):
    sucesso = resolver_alerta(alerta_id)

    if sucesso:
        return True, "Alerta resolvido."

    return False, "Erro ao resolver alerta."


def quantidade_alertas(pedido_id: int):
    return contar_alertas_ativos(pedido_id)

def obter_contagens_mensagens():
    return contar_mensagens_por_pedido()


def obter_contagens_alertas():
    return contar_alertas_por_pedido()

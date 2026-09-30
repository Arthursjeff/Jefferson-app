from core.pedidos import (
    criar_pedido,
    listar_pedidos,
    mover_pedido,
    editar_pedido,
    registrar_nota_fiscal,
    cancelar_pedido,
    listar_movimentacoes,
    listar_movimentacoes_destino,
    listar_movimentacoes_tipo,
    registrar_movimentacao,
    salvar_peso_volumes,
)

from core.fotos import salvar_foto_pedido

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


def _mapa_retiradas():
    movimentacoes = listar_movimentacoes_destino("RETIRADO", origem="EMBALADO")
    mapa = {}

    # A consulta vem da mais recente para a mais antiga. Mantemos a última
    # movimentação EMBALADO -> RETIRADO de cada pedido.
    for mov in movimentacoes:
        pedido_id = mov.get("pedido_id")
        if pedido_id not in mapa:
            mapa[pedido_id] = mov

    return mapa


def _enriquecer_retirado(pedido: dict, movimentacao: dict):
    item = dict(pedido)
    item["_retirado_em"] = movimentacao.get("criado_em")
    item["_retirado_por"] = movimentacao.get("usuario")
    return item


STATUS_EXPEDICAO = {
    "PENDENTE": "⚪",
    "AGUARDANDO": "🟡",
    "LIBERADO": "🟢",
    "BLOQUEADO": "🔴",
}


def _mapa_status_expedicao():
    movimentacoes = listar_movimentacoes_tipo("STATUS_EXPEDICAO")
    mapa = {}

    # A consulta vem da mais recente para a mais antiga.
    for mov in movimentacoes:
        pedido_id = mov.get("pedido_id")
        if pedido_id not in mapa:
            mapa[pedido_id] = mov

    return mapa


def _enriquecer_status_expedicao(pedido: dict, movimentacao: dict = None):
    item = dict(pedido)
    status = "PENDENTE"

    if movimentacao and movimentacao.get("destino") in STATUS_EXPEDICAO:
        status = movimentacao.get("destino")

    item["_status_expedicao"] = status
    item["_icone_expedicao"] = STATUS_EXPEDICAO[status]
    return item


def obter_pedidos_por_estado():
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    pedidos = obter_pedidos()
    agrupado = {estado: [] for estado in ESTADOS_FILA}
    retiradas = _mapa_retiradas()
    status_expedicao = _mapa_status_expedicao()
    limite_retirados = datetime.now(ZoneInfo("America/Sao_Paulo")) - timedelta(days=3)

    for pedido in pedidos:
        estado = pedido.get("setor_atual")
        if estado not in agrupado:
            continue

        if estado == "RETIRADO":
            mov = retiradas.get(pedido.get("id"))
            if not mov or not mov.get("criado_em"):
                continue

            try:
                retirado_em = datetime.fromisoformat(mov["criado_em"])
                if retirado_em.tzinfo is None:
                    retirado_em = retirado_em.replace(tzinfo=ZoneInfo("America/Sao_Paulo"))
            except (TypeError, ValueError):
                continue

            if retirado_em < limite_retirados:
                continue

            agrupado[estado].append(_enriquecer_retirado(pedido, mov))
        elif estado in ["FATURADO", "EMBALADO"]:
            agrupado[estado].append(
                _enriquecer_status_expedicao(
                    pedido,
                    status_expedicao.get(pedido.get("id")),
                )
            )
        else:
            agrupado[estado].append(pedido)

    return agrupado


def pesquisar_historico_retirados(termo: str):
    termo = str(termo or "").strip().casefold()
    if not termo:
        return []

    retiradas = _mapa_retiradas()
    resultados = []

    for pedido in obter_pedidos():
        if pedido.get("setor_atual") != "RETIRADO":
            continue

        campos = (
            pedido.get("numero_pedido"),
            pedido.get("cliente"),
            pedido.get("nota_fiscal"),
        )

        if not any(termo in str(valor or "").casefold() for valor in campos):
            continue

        mov = retiradas.get(pedido.get("id"))
        if mov:
            resultados.append(_enriquecer_retirado(pedido, mov))

    resultados.sort(key=lambda p: p.get("_retirado_em") or "", reverse=True)
    return resultados


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

def obter_destino_pedido(pedido: dict):
    estado_atual = pedido.get("setor_atual")

    if estado_atual not in ESTADOS_FILA:
        return None

    idx = ESTADOS_FILA.index(estado_atual)

    if idx >= len(ESTADOS_FILA) - 1:
        return None

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

    return destino


def dados_peso_volumes_validos(pedido: dict):
    try:
        peso = float(pedido.get("peso_total"))
        volumes = int(pedido.get("quantidade_volumes"))
    except (TypeError, ValueError):
        return False

    return peso > 0 and volumes > 0


def registrar_peso_volumes(
    pedido: dict,
    peso_total,
    quantidade_volumes,
    usuario: str,
    setor_usuario: str,
):
    if setor_usuario not in ["MONTAGEM", "ADMINISTRADOR"]:
        return False, "Somente MONTAGEM ou ADMINISTRADOR pode informar peso e volumes."

    try:
        peso = float(peso_total)
        volumes = int(quantidade_volumes)
    except (TypeError, ValueError):
        return False, "Informe peso e quantidade de volumes válidos."

    if peso <= 0:
        return False, "O peso total deve ser maior que zero."

    if volumes <= 0:
        return False, "A quantidade de volumes deve ser maior que zero."

    estado_atual = pedido.get("setor_atual")
    tipo = pedido.get("tipo_pedido")

    pode_editar_antecipado = estado_atual == "PROGRAMADO" and tipo == "PROGRAMADO"
    regularizacao_legado = estado_atual == "MONTADOS" and not dados_peso_volumes_validos(pedido)

    if not pode_editar_antecipado and not regularizacao_legado:
        return False, "Peso e volumes não podem ser editados neste estágio."

    sucesso = salvar_peso_volumes(
        pedido_id=pedido["id"],
        peso_total=peso,
        quantidade_volumes=volumes,
        usuario=usuario,
    )

    if not sucesso:
        return False, "Erro ao salvar peso e volumes."

    return True, "Peso e volumes salvos com sucesso."


def salvar_peso_volumes_e_avancar(
    pedido: dict,
    peso_total,
    quantidade_volumes,
    usuario: str,
    setor_usuario: str,
):
    destino = obter_destino_pedido(pedido)

    if destino != "MONTADOS":
        return False, "Esta operação só pode ser usada ao avançar para Montados."

    try:
        peso = float(peso_total)
        volumes = int(quantidade_volumes)
    except (TypeError, ValueError):
        return False, "Informe peso e quantidade de volumes válidos."

    if peso <= 0:
        return False, "O peso total deve ser maior que zero."

    if volumes <= 0:
        return False, "A quantidade de volumes deve ser maior que zero."

    if not pode_mover(setor_usuario, pedido.get("setor_atual"), destino):
        return False, "Usuário sem permissão para esta movimentação."

    sucesso_dados = salvar_peso_volumes(
        pedido_id=pedido["id"],
        peso_total=peso,
        quantidade_volumes=volumes,
        usuario=usuario,
    )

    if not sucesso_dados:
        return False, "Erro ao salvar peso e volumes."

    pedido_atualizado = dict(pedido)
    pedido_atualizado["peso_total"] = peso
    pedido_atualizado["quantidade_volumes"] = volumes

    return avancar_pedido(
        pedido=pedido_atualizado,
        usuario=usuario,
        setor_usuario=setor_usuario,
    )


def avancar_pedido(pedido: dict, usuario: str, setor_usuario: str):
    estado_atual = pedido.get("setor_atual")

    if estado_atual not in ESTADOS_FILA:
        return False, "Estado atual inválido."

    destino = obter_destino_pedido(pedido)

    if destino is None:
        return False, "Pedido já está no último estágio."

    if not pode_mover(setor_usuario, estado_atual, destino):
        return False, "Usuário sem permissão para esta movimentação."

    if destino == "MONTADOS" and not dados_peso_volumes_validos(pedido):
        return False, "Informe o peso total e a quantidade de volumes antes de avançar para Montados."

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

def alterar_status_expedicao(
    pedido: dict,
    status_expedicao: str,
    usuario: str,
    setor_usuario: str,
):
    if setor_usuario not in ["VENDAS", "ADMINISTRADOR"]:
        return False, "Somente VENDAS ou ADMINISTRADOR pode alterar o status de expedição."

    if pedido.get("setor_atual") not in ["FATURADO", "EMBALADO"]:
        return False, "O status de expedição só pode ser alterado em Faturados ou Embalados."

    status = str(status_expedicao or "").strip().upper()
    if status not in STATUS_EXPEDICAO:
        return False, "Status de expedição inválido."

    nomes = {
        "PENDENTE": "Pendente",
        "AGUARDANDO": "Aguardando",
        "LIBERADO": "Liberado",
        "BLOQUEADO": "Bloqueado",
    }

    evento = registrar_movimentacao(
        pedido_id=pedido["id"],
        origem=pedido.get("setor_atual", ""),
        destino=status,
        usuario=usuario,
        tipo_evento="STATUS_EXPEDICAO",
        observacao=f"Status de expedição alterado para {nomes[status]} por {usuario}.",
    )

    if not evento:
        return False, "Erro ao atualizar status de expedição."

    return True, f"Status de expedição atualizado para {STATUS_EXPEDICAO[status]} {nomes[status]}."


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

    registrar_movimentacao(
        pedido_id=pedido["id"],
        origem="FATURADO",
        destino="PENDENTE",
        usuario=usuario,
        tipo_evento="STATUS_EXPEDICAO",
        observacao=f"Status de expedição iniciado como Pendente após faturamento por {usuario}.",
    )

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

def salvar_foto_e_avancar(
    pedido: dict,
    foto,
    usuario: str,
    setor_usuario: str,
):
    if not foto:
        return False, "Foto obrigatória."

    if pedido.get("setor_atual") != "FATURADO":
        return False, "A foto só é obrigatória para avançar de Faturado para Embalado."

    foto_salva = salvar_foto_pedido(
        pedido_id=pedido["id"],
        foto=foto,
        usuario=usuario,
        tipo_evento="FATURADO_PARA_EMBALADO",
    )

    if not foto_salva:
        return False, "Erro ao salvar foto."

    sucesso, mensagem = avancar_pedido(
        pedido=pedido,
        usuario=usuario,
        setor_usuario=setor_usuario,
    )

    if not sucesso:
        return False, mensagem

    return True, "Foto salva e pedido avançado com sucesso."

def quantidade_alertas(pedido_id: int):
    return contar_alertas_ativos(pedido_id)

def obter_contagens_mensagens():
    return contar_mensagens_por_pedido()


def obter_contagens_alertas():
    return contar_alertas_por_pedido()

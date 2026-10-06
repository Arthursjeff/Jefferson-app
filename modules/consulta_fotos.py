import re
import unicodedata
from datetime import datetime

import streamlit as st

from core.alertas import listar_alertas
from core.fotos import listar_fotos_pedido, obter_url_foto
from core.mensagens import listar_mensagens
from core.pedidos import listar_movimentacoes, listar_pedidos
from modules.modulo_orcamentos.clientes_repository import buscar_clientes


STATUS_LABELS = {
    "PEDIDO": "Pedidos",
    "EM_MONTAGEM": "Em Montagem",
    "PROGRAMADO": "Programados",
    "IMPORTACAO": "Importação",
    "MONTADOS": "Montados",
    "FATURADO": "Faturado",
    "EMBALADO": "Embalado",
    "RETIRADO": "Retirado",
}


def _normalizar(valor):
    texto = str(valor or "").strip().upper()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]", "", texto)


def _somente_digitos(valor):
    return re.sub(r"\D", "", str(valor or ""))


def _formatar_nota(valor):
    texto = str(valor or "").strip()
    if not texto:
        return "Não informada"

    digitos = _somente_digitos(texto)
    if digitos and len(digitos) == len(re.sub(r"[.\s-]", "", texto)):
        try:
            return f"{int(digitos):,}".replace(",", ".")
        except ValueError:
            pass
    return texto


def _formatar_data_hora(valor):
    if not valor:
        return "Data não registrada"
    try:
        dt = datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y às %H:%M:%S")
    except (TypeError, ValueError):
        return str(valor)


def _rotulo_cliente(cliente):
    nome = cliente.get("nome_fantasia") or cliente.get("razao_social") or "Sem nome"
    codigo = cliente.get("codigo_cliente") or "-"
    documento = cliente.get("cnpj_cpf") or "-"
    return f"{codigo} | {nome} | {documento}"


def _rotulo_pedido(pedido):
    return (
        f"{pedido.get('numero_pedido', '')} — "
        f"{pedido.get('cliente', '')} — "
        f"{_formatar_nota(pedido.get('nota_fiscal'))}"
    )


def _pedidos_do_cliente(cliente):
    pedidos = listar_pedidos(status=None)
    identificadores = [
        cliente.get("razao_social"),
        cliente.get("nome_fantasia"),
        cliente.get("codigo_cliente"),
    ]
    identificadores = [_normalizar(x) for x in identificadores if _normalizar(x)]

    encontrados = []
    for pedido in pedidos:
        cliente_pedido = _normalizar(pedido.get("cliente"))
        if not cliente_pedido:
            continue
        if any(
            identificador == cliente_pedido
            or (len(identificador) >= 4 and identificador in cliente_pedido)
            or (len(cliente_pedido) >= 4 and cliente_pedido in identificador)
            for identificador in identificadores
        ):
            encontrados.append(pedido)

    return sorted(encontrados, key=lambda p: p.get("id", 0), reverse=True)


def _buscar_por_pedido(numero):
    alvo = _normalizar(numero)
    if not alvo:
        return []
    return [
        p for p in listar_pedidos(status=None)
        if alvo in _normalizar(p.get("numero_pedido"))
    ]


def _buscar_por_nota(nota):
    alvo = _somente_digitos(nota)
    if not alvo:
        return []
    return [
        p for p in listar_pedidos(status=None)
        if alvo == _somente_digitos(p.get("nota_fiscal"))
    ]


def _selecionar_resultado(pedidos, key):
    if not pedidos:
        st.info("Nenhum pedido encontrado.")
        return None

    pedidos = sorted(pedidos, key=lambda p: p.get("id", 0), reverse=True)
    st.caption(f"{len(pedidos)} pedido(s) encontrado(s).")
    return st.selectbox(
        "Selecione o pedido",
        pedidos,
        format_func=_rotulo_pedido,
        key=key,
    )


def _mostrar_resumo(pedido):
    st.subheader(f"Pedido {pedido.get('numero_pedido', '')}")
    st.markdown(f"**{pedido.get('cliente', '')}**")

    c1, c2, c3 = st.columns(3)
    c1.metric("Nota", _formatar_nota(pedido.get("nota_fiscal")))
    c2.metric("Status atual", STATUS_LABELS.get(pedido.get("setor_atual"), pedido.get("setor_atual") or "-"))
    c3.metric("Tipo", pedido.get("tipo_pedido") or "NORMAL")

    c4, c5, c6 = st.columns(3)
    c4.metric("Criado por", pedido.get("criado_por") or "-")
    data_criacao = pedido.get("criado_data") or "-"
    hora_criacao = pedido.get("criado_hora") or ""
    c5.metric("Criação", f"{data_criacao} {hora_criacao}".strip())

    peso = pedido.get("peso_total")
    volumes = pedido.get("quantidade_volumes")
    if peso is not None and volumes is not None:
        peso_txt = f"{float(peso):.3f}".replace(".", ",")
        c6.metric("Peso / volumes", f"{peso_txt} kg / {int(volumes)}")
    else:
        c6.metric("Peso / volumes", "Não informado")

    if pedido.get("status") and pedido.get("status") != "ATIVO":
        st.warning(f"Situação do registro: {pedido.get('status')}")


def _mostrar_fotos(pedido):
    st.markdown("### Imagens")
    fotos = listar_fotos_pedido(pedido["id"])
    if not fotos:
        st.info("Este pedido não tem imagem cadastrada.")
        return

    for foto in fotos:
        url = obter_url_foto(foto.get("arquivo_path"))
        if url:
            legenda = (
                f"{_formatar_data_hora(foto.get('criado_em'))} — "
                f"{foto.get('criado_por') or 'Usuário não identificado'}"
            )
            st.image(url, caption=legenda)
        else:
            st.warning("Existe uma imagem cadastrada que não pôde ser carregada.")


def _mostrar_mensagens_alertas(pedido):
    mensagens = listar_mensagens(pedido["id"], apenas_ativas=False)
    alertas = listar_alertas(pedido["id"], apenas_ativos=False)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### Mensagens ({len(mensagens)})")
        if not mensagens:
            st.caption("Nenhuma mensagem registrada.")
        for msg in mensagens:
            estado = "Ativa" if msg.get("ativa", True) else "Removida"
            with st.container(border=True):
                st.markdown(f"**{msg.get('criado_por') or 'Usuário não identificado'}** · {estado}")
                st.write(msg.get("mensagem") or "")
                if msg.get("criado_em"):
                    st.caption(_formatar_data_hora(msg.get("criado_em")))

    with c2:
        st.markdown(f"### Alertas ({len(alertas)})")
        if not alertas:
            st.caption("Nenhum alerta registrado.")
        for alerta in alertas:
            estado = "Ativo" if alerta.get("ativo", True) else "Resolvido"
            with st.container(border=True):
                st.markdown(f"**{alerta.get('criado_por') or 'Usuário não identificado'}** · {estado}")
                st.write(alerta.get("mensagem") or "")
                if alerta.get("criado_em"):
                    st.caption(_formatar_data_hora(alerta.get("criado_em")))


def _mostrar_historico(pedido):
    st.markdown("### Histórico de movimentações")
    movimentacoes = listar_movimentacoes(pedido["id"])

    if not movimentacoes:
        st.info("Nenhuma movimentação registrada.")
        return

    for mov in reversed(movimentacoes):
        origem = mov.get("origem") or ""
        destino = mov.get("destino") or ""
        tipo = mov.get("tipo_evento") or "EVENTO"
        usuario = mov.get("usuario") or "Usuário não identificado"
        observacao = mov.get("observacao") or ""

        if tipo == "MOVIMENTACAO":
            evento = f"{STATUS_LABELS.get(origem, origem)} → {STATUS_LABELS.get(destino, destino)}"
        elif tipo == "CRIACAO":
            evento = "Pedido criado"
        elif tipo == "NOTA_FISCAL":
            evento = "Nota fiscal registrada"
        elif tipo == "PESO_VOLUMES":
            evento = "Peso e volumes registrados"
        elif tipo == "STATUS_EXPEDICAO":
            evento = "Status de expedição atualizado"
        elif tipo == "CANCELAMENTO":
            evento = "Pedido cancelado"
        elif tipo == "EDICAO":
            evento = "Pedido editado"
        else:
            evento = tipo.replace("_", " ").title()

        with st.container(border=True):
            st.markdown(f"**{_formatar_data_hora(mov.get('criado_em'))} — {usuario}**")
            st.write(evento)
            if observacao:
                st.caption(observacao)


def _mostrar_pedido(pedido):
    st.divider()
    _mostrar_resumo(pedido)
    _mostrar_fotos(pedido)
    _mostrar_mensagens_alertas(pedido)
    _mostrar_historico(pedido)


def pagina_consulta_pedidos():
    if st.session_state.get("setor") not in ["ADMINISTRADOR", "VENDAS"]:
        st.error("Você não possui permissão para acessar esta página.")
        st.stop()

    st.title("🔎 Consulta de Pedidos")
    st.caption("Consulte todo o histórico por cliente, número do pedido ou nota fiscal.")

    aba_cliente, aba_pedido, aba_nota = st.tabs(["Cliente", "Número do pedido", "Nota"])

    with aba_cliente:
        termo = st.text_input(
            "Cliente",
            placeholder="Digite nome, razão social, CNPJ/CPF ou código do cliente",
            key="consulta_pedido_cliente",
        )
        clientes = buscar_clientes(termo, limite=30) if termo.strip() else []

        if termo.strip() and not clientes:
            st.info("Nenhum cliente encontrado.")

        if clientes:
            cliente = st.selectbox(
                "Selecione o cliente",
                clientes,
                format_func=_rotulo_cliente,
                key="consulta_pedido_cliente_selecionado",
            )
            pedido = _selecionar_resultado(
                _pedidos_do_cliente(cliente),
                "consulta_pedido_resultado_cliente",
            )
            if pedido:
                _mostrar_pedido(pedido)

    with aba_pedido:
        numero = st.text_input(
            "Número do pedido",
            placeholder="Digite o número do pedido",
            key="consulta_pedido_numero",
        )
        if numero.strip():
            pedido = _selecionar_resultado(
                _buscar_por_pedido(numero),
                "consulta_pedido_resultado_numero",
            )
            if pedido:
                _mostrar_pedido(pedido)

    with aba_nota:
        nota = st.text_input(
            "Nota",
            placeholder="Ex.: 32.000 ou 32000",
            key="consulta_pedido_nota",
        )
        if nota.strip():
            pedido = _selecionar_resultado(
                _buscar_por_nota(nota),
                "consulta_pedido_resultado_nota",
            )
            if pedido:
                _mostrar_pedido(pedido)

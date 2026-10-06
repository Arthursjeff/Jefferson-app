import re
import unicodedata

import streamlit as st

from core.fotos import listar_fotos_pedido, obter_url_foto
from core.pedidos import listar_pedidos
from modules.modulo_orcamentos.clientes_repository import buscar_clientes


def _normalizar(valor):
    texto = str(valor or "").strip().upper()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]", "", texto)


def _rotulo_cliente(cliente):
    nome = cliente.get("nome_fantasia") or cliente.get("razao_social") or "Sem nome"
    codigo = cliente.get("codigo_cliente") or "-"
    documento = cliente.get("cnpj_cpf") or "-"
    return f"{codigo} | {nome} | {documento}"


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


def _buscar_pedido_numero(numero):
    alvo = _normalizar(numero)
    if not alvo:
        return []

    return [
        pedido
        for pedido in listar_pedidos(status=None)
        if _normalizar(pedido.get("numero_pedido")) == alvo
    ]


def _mostrar_foto(pedido):
    st.markdown(
        f"### Pedido {pedido.get('numero_pedido', '')} — {pedido.get('cliente', '')}"
    )

    fotos = listar_fotos_pedido(pedido["id"])
    if not fotos:
        st.info("Este pedido não tem imagem cadastrada.")
        return

    foto = fotos[0]
    url = obter_url_foto(foto.get("arquivo_path"))

    if not url:
        st.warning("A imagem está cadastrada, mas não foi possível carregá-la.")
        return

    st.image(url, caption=f"Foto do pedido {pedido.get('numero_pedido', '')}")


def pagina_consulta_fotos():
    if st.session_state.get("setor") != "ADMINISTRADOR":
        st.error("Esta página é exclusiva para administradores.")
        st.stop()

    st.title("📷 Consulta de Fotos")
    st.caption("Consulte por cliente ou diretamente pelo número do pedido.")

    aba_cliente, aba_pedido = st.tabs(["Cliente", "Número do pedido"])

    with aba_cliente:
        termo = st.text_input(
            "Cliente",
            placeholder="Digite nome, razão social, CNPJ/CPF ou código do cliente",
            key="consulta_foto_cliente",
        )

        clientes = buscar_clientes(termo, limite=30) if termo.strip() else []

        if termo.strip() and not clientes:
            st.info("Nenhum cliente encontrado.")

        if clientes:
            cliente = st.selectbox(
                "Selecione o cliente",
                clientes,
                format_func=_rotulo_cliente,
                key="consulta_foto_cliente_selecionado",
            )

            pedidos = _pedidos_do_cliente(cliente)

            if not pedidos:
                st.info("Nenhum pedido desse cliente foi encontrado na fila.")
            else:
                st.caption(f"{len(pedidos)} pedido(s) encontrado(s).")
                pedido = st.selectbox(
                    "Selecione o pedido",
                    pedidos,
                    format_func=lambda p: (
                        f"{p.get('numero_pedido', '')} — "
                        f"{p.get('cliente', '')} — "
                        f"{p.get('setor_atual', '')}"
                    ),
                    key="consulta_foto_pedido_cliente",
                )
                _mostrar_foto(pedido)

    with aba_pedido:
        numero = st.text_input(
            "Número do pedido",
            placeholder="Digite o número exato do pedido",
            key="consulta_foto_numero_pedido",
        )

        if numero.strip():
            pedidos = _buscar_pedido_numero(numero)

            if not pedidos:
                st.info("Pedido não encontrado.")
            else:
                pedido = pedidos[0]
                _mostrar_foto(pedido)

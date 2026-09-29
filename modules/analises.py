from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from core.database import supabase

TABELA_MOVIMENTACOES = "fila_movimentacoes"

CLASSIFICACOES_MOVIMENTACAO = {
    ("PEDIDO", "EM_MONTAGEM"): "Iniciou montagem",
    ("EM_MONTAGEM", "MONTADOS"): "Finalizou montagem",
    ("EM_MONTAGEM", "PROGRAMADO"): "Programou pedido",
    ("EM_MONTAGEM", "IMPORTACAO"): "Programou importação",
    ("PROGRAMADO", "MONTADOS"): "Recebeu programação",
    ("IMPORTACAO", "MONTADOS"): "Recebeu importação",
    ("MONTADOS", "FATURADO"): "Faturou pedido",
    ("FATURADO", "EMBALADO"): "Embalou pedido",
    ("EMBALADO", "RETIRADO"): "Liberou na porta",
}

ORDEM_INTERACOES = [
    "Criou pedido",
    "Iniciou montagem",
    "Finalizou montagem",
    "Programou pedido",
    "Programou importação",
    "Recebeu programação",
    "Recebeu importação",
    "Faturou pedido",
    "Embalou pedido",
    "Liberou na porta",
]


def _tipo_interacao(movimentacao):
    tipo_evento = movimentacao.get("tipo_evento")

    if tipo_evento == "CRIACAO":
        return "Criou pedido"

    if tipo_evento == "MOVIMENTACAO":
        chave = (movimentacao.get("origem"), movimentacao.get("destino"))
        return CLASSIFICACOES_MOVIMENTACAO.get(chave)

    return None


def _ordenar_tipos(tipos):
    ordem = {tipo: indice for indice, tipo in enumerate(ORDEM_INTERACOES)}
    return sorted(tipos, key=lambda tipo: (ordem.get(tipo, 999), tipo))


def listar_todas_movimentacoes():
    registros = []
    inicio = 0
    lote = 1000

    while True:
        resposta = (
            supabase.table(TABELA_MOVIMENTACOES)
            .select("*")
            .order("criado_em", desc=False)
            .range(inicio, inicio + lote - 1)
            .execute()
        )
        dados = resposta.data or []
        registros.extend(dados)
        if len(dados) < lote:
            break
        inicio += lote

    return registros


def _data_evento(valor):
    if not valor:
        return None
    try:
        return datetime.fromisoformat(str(valor).replace("Z", "+00:00")).date()
    except (TypeError, ValueError):
        return None


def pagina_analises():
    if st.session_state.get("setor") != "ADMINISTRADOR":
        st.error("Esta página é exclusiva para administradores.")
        st.stop()

    st.title("📊 Análises")
    st.caption("Módulo administrativo de indicadores do Jefferson App.")

    st.subheader("Interações operacionais da fila")
    st.caption("Considera criação de pedidos e ações realizadas nas etapas da fila.")

    historico = listar_todas_movimentacoes()

    interacoes = []
    for registro in historico:
        tipo_interacao = _tipo_interacao(registro)
        if tipo_interacao:
            item = dict(registro)
            item["tipo_interacao"] = tipo_interacao
            interacoes.append(item)

    if not interacoes:
        st.info("Ainda não existem interações operacionais registradas.")
        return

    datas_validas = [_data_evento(m.get("criado_em")) for m in interacoes]
    datas_validas = [d for d in datas_validas if d]
    hoje = date.today()
    primeira_data = min(datas_validas) if datas_validas else hoje

    c1, c2 = st.columns([1, 2])
    with c1:
        periodo = st.selectbox(
            "Período",
            ["Todo o período", "Hoje", "Últimos 7 dias", "Este mês", "Personalizado"],
        )

    data_inicio = primeira_data
    data_fim = hoje

    if periodo == "Hoje":
        data_inicio = data_fim = hoje
    elif periodo == "Últimos 7 dias":
        data_inicio = hoje - timedelta(days=6)
    elif periodo == "Este mês":
        data_inicio = hoje.replace(day=1)
    elif periodo == "Personalizado":
        with c2:
            intervalo = st.date_input(
                "Intervalo",
                value=(primeira_data, hoje),
                min_value=primeira_data,
                max_value=hoje,
            )
        if isinstance(intervalo, (tuple, list)) and len(intervalo) == 2:
            data_inicio, data_fim = intervalo
        else:
            st.info("Selecione a data inicial e a data final.")
            return

    filtradas_periodo = [
        m for m in interacoes
        if (d := _data_evento(m.get("criado_em"))) and data_inicio <= d <= data_fim
    ]

    usuarios_historico = sorted({
        str(m.get("usuario") or "Sem usuário") for m in filtradas_periodo
    })
    tipos_historico = _ordenar_tipos({
        m["tipo_interacao"] for m in filtradas_periodo
    })

    f1, f2 = st.columns(2)
    with f1:
        usuarios_sel = st.multiselect(
            "Usuários",
            usuarios_historico,
            default=usuarios_historico,
        )
    with f2:
        tipos_sel = st.multiselect(
            "Tipos de interação",
            tipos_historico,
            default=tipos_historico,
        )

    filtradas = [
        m for m in filtradas_periodo
        if str(m.get("usuario") or "Sem usuário") in usuarios_sel
        and m["tipo_interacao"] in tipos_sel
    ]

    total = len(filtradas)
    usuarios_ativos = len({
        str(m.get("usuario") or "Sem usuário") for m in filtradas
    })
    pedidos_envolvidos = len({
        m.get("pedido_id") for m in filtradas if m.get("pedido_id") is not None
    })

    k1, k2, k3 = st.columns(3)
    k1.metric("Total de interações", total)
    k2.metric("Usuários com atividade", usuarios_ativos)
    k3.metric("Pedidos envolvidos", pedidos_envolvidos)

    if not filtradas:
        st.warning("Nenhuma interação encontrada com os filtros selecionados.")
        return

    por_usuario = Counter(
        str(m.get("usuario") or "Sem usuário") for m in filtradas
    )
    ranking = pd.DataFrame([
        {"Usuário": usuario, "Interações": qtd}
        for usuario, qtd in por_usuario.most_common()
    ])

    st.markdown("#### Interações por usuário")
    st.bar_chart(ranking.set_index("Usuário"))

    matriz = defaultdict(Counter)
    for m in filtradas:
        usuario = str(m.get("usuario") or "Sem usuário")
        matriz[usuario][m["tipo_interacao"]] += 1

    tipos_tabela = [tipo for tipo in tipos_sel if tipo in tipos_historico]
    composicao = []
    for usuario in usuarios_sel:
        total_usuario = sum(matriz[usuario][tipo] for tipo in tipos_tabela)
        linha = {"Usuário": usuario, "Total": total_usuario}
        for tipo in tipos_tabela:
            linha[tipo] = matriz[usuario][tipo]
        composicao.append(linha)

    composicao.sort(key=lambda linha: (-linha["Total"], linha["Usuário"]))

    st.markdown("#### Interações por usuário e classificação")
    st.dataframe(
        pd.DataFrame(composicao),
        use_container_width=True,
        hide_index=True,
    )

    por_tipo = Counter(m["tipo_interacao"] for m in filtradas)
    df_tipos = pd.DataFrame([
        {"Interação": tipo, "Quantidade": por_tipo[tipo]}
        for tipo in tipos_tabela
    ])

    st.markdown("#### Distribuição das interações")
    st.bar_chart(df_tipos.set_index("Interação"))
    st.dataframe(df_tipos, use_container_width=True, hide_index=True)

    with st.expander("Ver interações detalhadas"):
        detalhes = []
        for m in sorted(
            filtradas,
            key=lambda x: str(x.get("criado_em") or ""),
            reverse=True,
        ):
            detalhes.append({
                "Data/hora": m.get("criado_em"),
                "Usuário": m.get("usuario"),
                "Interação": m.get("tipo_interacao"),
                "Pedido ID": m.get("pedido_id"),
            })

        st.dataframe(
            pd.DataFrame(detalhes),
            use_container_width=True,
            hide_index=True,
        )

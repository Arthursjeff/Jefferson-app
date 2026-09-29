from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from core.database import supabase
from core.auth import USUARIOS

TABELA_MOVIMENTACOES = "fila_movimentacoes"

LABEL_EVENTOS = {
    "CRIACAO": "Criação de pedido",
    "MOVIMENTACAO": "Movimentação na fila",
    "PESO_VOLUMES": "Peso e volumes",
    "CANCELAMENTO": "Cancelamento",
    "NOTA_FISCAL": "Nota fiscal",
    "EDICAO": "Edição de pedido",
}


def _label_evento(tipo):
    return LABEL_EVENTOS.get(tipo, str(tipo or "SEM_TIPO").replace("_", " ").title())


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

    st.subheader("Movimentações da fila")

    movimentacoes = listar_todas_movimentacoes()
    if not movimentacoes:
        st.info("Ainda não existem movimentações registradas.")
        return

    datas_validas = [_data_evento(m.get("criado_em")) for m in movimentacoes]
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
        m for m in movimentacoes
        if (d := _data_evento(m.get("criado_em"))) and data_inicio <= d <= data_fim
    ]

    usuarios_historico = sorted({str(m.get("usuario") or "Sem usuário") for m in filtradas_periodo})
    tipos_historico = sorted({str(m.get("tipo_evento") or "SEM_TIPO") for m in filtradas_periodo})

    f1, f2 = st.columns(2)
    with f1:
        usuarios_sel = st.multiselect(
            "Usuários",
            usuarios_historico,
            default=usuarios_historico,
        )
    with f2:
        tipos_sel = st.multiselect(
            "Tipos de movimentação",
            tipos_historico,
            default=tipos_historico,
            format_func=_label_evento,
        )

    filtradas = [
        m for m in filtradas_periodo
        if str(m.get("usuario") or "Sem usuário") in usuarios_sel
        and str(m.get("tipo_evento") or "SEM_TIPO") in tipos_sel
    ]

    total = len(filtradas)
    usuarios_ativos = len({m.get("usuario") for m in filtradas})
    pedidos_movimentados = len({m.get("pedido_id") for m in filtradas if m.get("pedido_id") is not None})

    k1, k2, k3 = st.columns(3)
    k1.metric("Total de movimentações", total)
    k2.metric("Usuários com atividade", usuarios_ativos)
    k3.metric("Pedidos envolvidos", pedidos_movimentados)

    if not filtradas:
        st.warning("Nenhuma movimentação encontrada com os filtros selecionados.")
        return

    por_usuario = Counter(str(m.get("usuario") or "Sem usuário") for m in filtradas)
    ranking = pd.DataFrame(
        [{"Usuário": usuario, "Movimentações": qtd} for usuario, qtd in por_usuario.most_common()]
    )

    st.markdown("#### Movimentações por usuário")
    st.bar_chart(ranking.set_index("Usuário"))
    st.dataframe(ranking, use_container_width=True, hide_index=True)

    matriz = defaultdict(Counter)
    for m in filtradas:
        usuario = str(m.get("usuario") or "Sem usuário")
        tipo = str(m.get("tipo_evento") or "SEM_TIPO")
        matriz[usuario][tipo] += 1

    tipos_presentes = sorted({tipo for contagem in matriz.values() for tipo in contagem})
    composicao = []
    for usuario, total_usuario in por_usuario.most_common():
        linha = {"Usuário": usuario, "Total": total_usuario}
        for tipo in tipos_presentes:
            linha[_label_evento(tipo)] = matriz[usuario][tipo]
        if matriz[usuario]:
            tipo_mais, qtd_mais = matriz[usuario].most_common(1)[0]
            linha["Tipo mais frequente"] = _label_evento(tipo_mais)
            linha["Qtd. tipo mais frequente"] = qtd_mais
        composicao.append(linha)

    st.markdown("#### Tipos de movimentação por usuário")
    st.dataframe(pd.DataFrame(composicao), use_container_width=True, hide_index=True)

    eventos = Counter(str(m.get("tipo_evento") or "SEM_TIPO") for m in filtradas)
    df_eventos = pd.DataFrame(
        [{"Tipo": _label_evento(tipo), "Quantidade": qtd} for tipo, qtd in eventos.most_common()]
    )
    st.markdown("#### Distribuição por tipo")
    st.bar_chart(df_eventos.set_index("Tipo"))

    with st.expander("Ver movimentações detalhadas"):
        detalhes = []
        for m in sorted(filtradas, key=lambda x: str(x.get("criado_em") or ""), reverse=True):
            detalhes.append({
                "Data/hora": m.get("criado_em"),
                "Usuário": m.get("usuario"),
                "Tipo": _label_evento(m.get("tipo_evento")),
                "Pedido ID": m.get("pedido_id"),
                "Origem": m.get("origem"),
                "Destino": m.get("destino"),
                "Observação": m.get("observacao"),
            })
        st.dataframe(pd.DataFrame(detalhes), use_container_width=True, hide_index=True)

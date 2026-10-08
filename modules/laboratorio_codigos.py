"""Diagnóstico somente leitura do motor de códigos Jefferson."""
import streamlit as st
from motor_descricao import processar_produto
from components.kits import codigo_parece_kit, processar_kit
from components.internos.torre import identificar_conjunto_torre
from components.internos.diafragma import identificar_conjunto_diafragma
from components.internos.pistao import identificar_conjunto_pistao
from components.internos.carretel import identificar_conjunto_carretel
from components.internos.orings import identificar_orings


def _valor(dados, *chaves):
    for chave in chaves:
        if dados.get(chave) is not None:
            return dados[chave]
    return None


def _diagnosticar_valvula(resultado):
    parser = resultado.get("parser") or {}
    variaveis = resultado.get("variaveis") or {}
    familia = _valor(parser, "familia")
    vedacao = _valor(parser, "vedacao", "codigo_vedacao") or variaveis.get("V06")
    material = _valor(parser, "material_corpo", "material") or variaveis.get("V05")
    tamanho = _valor(parser, "tamanho", "bitola", "conexao") or variaveis.get("V07")
    estado = _valor(parser, "estado", "posicao") or variaveis.get("V03")
    sufixos = parser.get("sufixos") or []
    avisos = []
    if not familia:
        avisos.append("Família não identificada: componentes não calculados.")
        return {}, avisos
    grupos = {}
    regras = {
        "G1 - Torre": lambda: identificar_conjunto_torre(familia, material=material, estado=estado, vedacao=vedacao, bitola=tamanho),
        "G2 - Diafragma": lambda: identificar_conjunto_diafragma(familia, tamanho=tamanho, vedacao=vedacao, material_corpo=material, sufixos=sufixos),
        "G3 - Pistão": lambda: identificar_conjunto_pistao(familia, tamanho=tamanho, vedacao=vedacao, material_corpo=material, sufixos=sufixos),
        "G4 - Carretel": lambda: identificar_conjunto_carretel(familia, estado=estado, material_corpo=material),
        "G5 - O-rings": lambda: identificar_orings(familia, vedacao=vedacao, tamanho=tamanho),
    }
    for nome, executar in regras.items():
        try:
            grupos[nome] = executar()
        except Exception as erro:
            grupos[nome] = {"erro": str(erro)}
            avisos.append(f"{nome}: falha ao executar a regra.")
    if not material:
        avisos.append("Material do corpo não identificado; materiais dependentes podem ficar indefinidos.")
    if not tamanho:
        avisos.append("Tamanho não identificado; agrupamentos podem ficar indefinidos.")
    return grupos, avisos


def pagina_laboratorio_codigos():
    if st.session_state.get("setor") != "ADMINISTRADOR":
        st.error("Acesso exclusivo para administradores.")
        st.stop()

    st.title("Laboratório de Códigos")
    st.caption("Diagnóstico técnico somente leitura. Não cria orçamentos, pedidos ou registros.")
    codigo = st.text_input("Código da válvula ou do kit de reparo", key="lab_codigo").strip().upper()
    tensao = st.text_input("Tensão (opcional, para descrição da válvula)", key="lab_tensao")
    if not st.button("Analisar código", type="primary"):
        return
    if not codigo:
        st.warning("Informe um código.")
        return
    try:
        kit = codigo_parece_kit(codigo)
        resultado = processar_kit(codigo) if kit else processar_produto(codigo, tensao)
    except Exception as erro:
        st.error(f"Falha ao processar o código: {erro}")
        return

    st.subheader("Resultado da interpretação")
    if resultado.get("sucesso"):
        st.success("Código interpretado pelo motor.")
    else:
        st.warning(resultado.get("erro") or "Interpretação incompleta.")
    with st.expander("Parser e identificação", expanded=True):
        st.json(resultado.get("parser") or {})
    with st.expander("Variáveis e descrição", expanded=True):
        if resultado.get("descricao"):
            st.write(resultado["descricao"])
        st.json(resultado.get("variaveis") or {})
    if kit:
        grupos = (resultado.get("parser") or {}).get("componentes") or {}
        st.info("Kit: a composição segue as regras atualmente implementadas. O agrupamento físico de tamanhos ainda pode estar pendente.")
        avisos = []
    else:
        grupos, avisos = _diagnosticar_valvula(resultado)
    st.subheader("Componentes internos")
    for nome, dados in grupos.items():
        with st.expander(nome, expanded=False):
            if dados:
                st.json(dados)
            else:
                st.caption("Nenhum componente identificado pelas regras atuais.")
    if avisos:
        st.subheader("Pontos para validação")
        for aviso in avisos:
            st.warning(aviso)
    with st.expander("Diagnóstico completo (JSON)"):
        st.json({"codigo": codigo, "tipo": "KIT" if kit else "VALVULA", "resultado": resultado, "grupos": grupos, "avisos": avisos})

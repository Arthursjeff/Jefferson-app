"""Conferência legível, sem modificar as rotinas de orçamento."""
import streamlit as st
from components.motor_componentes import consultar_codigo

CAMPOS = {
    "V01": "Tipo de produto", "V02": "Tipo de atuação", "V03": "Número de vias",
    "V04": "Estado da válvula", "V05": "Material do corpo",
    "V06": "Material da vedação", "V07": "Tamanho da conexão",
    "V08": "Tipo de conexão", "V09": "Orifício interno",
    "V10": "Pressão mínima", "V11": "Pressão máxima",
    "V12": "Temperatura", "V13": "Dados da bobina",
    "V14": "Potência da bobina", "V15": "Informações adicionais",
    "V16": "Coeficiente de vazão (Kv)", "V17": "Imagem",
}
NOMES = {
    "torre_externa": "Torre externa", "componentes_internos": "Componentes internos",
    "nucleo_movel": "Núcleo móvel", "mola_nucleo": "Mola do núcleo móvel",
    "assento": "Assento", "mola_cadeirinha": "Mola da cadeirinha",
    "cadeirinha": "Cadeirinha", "carretel": "Carretel",
    "diafragma": "Diafragma", "mola": "Mola", "pulmao": "Pulmão",
    "pistao": "Pistão", "mola_pistao": "Mola do pistão",
    "aro_pistao": "Aro do pistão", "mola_interna_aro": "Mola interna do aro",
    "grupo_tamanho": "Grupo de tamanho", "tamanho_corpo": "Tamanho do corpo",
    "material_corpo": "Material do corpo", "vedacao_pistao": "Vedação do pistão",
    "vedacao": "Vedação", "material": "Material", "familia": "Família",
    "quantidade": "Quantidade", "local": "Local", "tamanho": "Tamanho",
    "estado": "Funcionamento", "construcao": "Construção", "formato": "Formato",
    "variante": "Variante", "variante_construtiva": "Variante construtiva",
    "grupo": "Grupo", "grupo_familia": "Grupo da família", "final": "Final",
}
OCULTOS = {"grupo_componente", "nome_grupo", "identidade", "sistema",
           "kit_reparo_exclui_torre_externa", "regra", "regra_detalhada",
           "validacao_pendente", "observacao_vedacao", "fora_kit_reparo"}


def _nome(chave):
    return NOMES.get(chave, str(chave).replace("_", " ").capitalize())


def _texto(valor):
    if valor is None or valor == "":
        return "Não identificado"
    if isinstance(valor, bool):
        return "Sim" if valor else "Não"
    if isinstance(valor, (list, tuple)):
        return ", ".join(_texto(x) for x in valor) if valor else "Não informado"
    return str(valor).replace("_", " ")


def _campos(dados, nivel=0):
    if isinstance(dados, list):
        for item in dados:
            if isinstance(item, dict):
                _campos(item, nivel)
                st.divider()
            else:
                st.write("• " + _texto(item))
        return
    if not isinstance(dados, dict):
        st.write(_texto(dados))
        return
    for chave, valor in dados.items():
        if chave in OCULTOS:
            continue
        if isinstance(valor, (dict, list)):
            if valor:
                st.markdown("**" + _nome(chave) + "**")
                _campos(valor, nivel + 1)
        else:
            st.write("**" + _nome(chave) + ":** " + _texto(valor))


def pagina_laboratorio_codigos():
    if st.session_state.get("setor") != "ADMINISTRADOR":
        st.error("Acesso exclusivo para administradores.")
        st.stop()
    st.title("Conferência de Códigos")
    st.caption("Confira informações de válvulas e kits sem criar orçamentos.")
    with st.form("conferencia_codigo"):
        codigo = st.text_input("Código do produto").strip().upper()
        tensao = st.text_input("Tensão (opcional)")
        enviar = st.form_submit_button("Consultar", type="primary")
    if not enviar:
        return
    if not codigo:
        st.warning("Informe um código.")
        return
    try:
        consulta = consultar_codigo(codigo, tensao)
    except Exception as erro:
        st.error("Não foi possível interpretar o código. Confira a entrada ou solicite revisão.")
        st.caption("Detalhe para suporte: " + str(erro))
        return
    resultado = consulta["resultado"]
    variaveis = resultado.get("variaveis") or {}
    parser = resultado.get("parser") or {}
    st.subheader("Identificação do produto")
    st.write("**Código:** " + codigo)
    st.write("**Categoria:** " + ("Kit de reparo" if consulta["kit"] else "Válvula / produto"))
    if not resultado.get("sucesso"):
        st.warning(resultado.get("erro") or "Identificação incompleta.")
    else:
        st.success("Código interpretado.")
    if resultado.get("descricao"):
        st.write("**Descrição:** " + str(resultado["descricao"]))
    if parser.get("familia"):
        st.write("**Família:** " + str(parser["familia"]))

    st.subheader("Características")
    if consulta["kit"]:
        for campo in ("V01", "V06", "V07"):
            if variaveis.get(campo) is not None:
                st.write("**" + CAMPOS.get(campo, campo) + ":** " + _texto(variaveis[campo]))
        aplicacao = variaveis.get("V18") or {}
        if aplicacao.get("sequencial_tamanho") is not None and not aplicacao.get("tamanhos_aplicaveis"):
            st.warning("A correspondência entre o número do kit e o tamanho da válvula ainda precisa ser validada.")
        st.subheader("Itens previstos no kit de reparo")
        for campo, nome in [("V20", "G1 — Núcleo e torre"), ("V21", "G2 — Diafragma"),
                            ("V22", "G3 — Pistão"), ("V23", "G4 — Carretel"), ("V24", "G5 — O-rings")]:
            with st.expander(nome):
                itens = variaveis.get(campo) or []
                if itens:
                    for item in itens:
                        st.write("• " + _texto(item))
                else:
                    st.info("Nenhum item listado para este grupo. A composição pode estar incompleta.")
        st.info("A composição do kit ainda está em validação; não utilize esta tela como lista de separação.")
    else:
        for campo, nome in CAMPOS.items():
            valor = variaveis.get(campo)
            if valor is None or campo == "V17":
                continue
            if isinstance(valor, dict):
                with st.expander(nome):
                    _campos(valor)
            else:
                st.write("**" + nome + ":** " + _texto(valor))
        st.subheader("Kit de reparo correspondente")
        sugestao = consulta.get("kit_correspondente") or {}
        status = sugestao.get("status", "não determinado")
        if sugestao.get("codigo"):
            st.markdown("### " + sugestao["codigo"])
        if status == "identificado pelo mapeamento atual":
            st.success("Kit identificado conforme as regras de tamanho cadastradas.")
        elif status.startswith("provável"):
            st.warning("Kit provável — precisa de conferência antes de utilizar.")
        else:
            st.info("Ainda não foi possível determinar o código do kit.")
        if sugestao.get("motivo"):
            st.write(sugestao["motivo"])
        if sugestao.get("tamanho"):
            st.caption("Tamanho consultado: " + sugestao["tamanho"])
        st.caption("A identificação não substitui a confirmação técnica da composição do kit.")
        st.subheader("Componentes da válvula")
        st.caption("Os componentes físicos da válvula não são necessariamente fornecidos no kit.")
        for nome, dados in consulta["grupos"].items():
            with st.expander(nome):
                if dados:
                    if isinstance(dados, list):
                        _campos(dados)
                    elif isinstance(dados, dict) and "componentes" in dados:
                        _campos(dados["componentes"])
                        if "componentes_internos" in dados:
                            st.markdown("**Detalhamento interno**")
                            _campos(dados["componentes_internos"])
                    else:
                        _campos(dados)
                else:
                    st.info("Não identificado neste grupo. Pode ser ausência do componente ou regra ainda não cadastrada.")
        for aviso in consulta["pendencias"]:
            st.warning(aviso)
    st.caption("Resultados gerados pelas regras atualmente cadastradas. A conferência física continua necessária.")

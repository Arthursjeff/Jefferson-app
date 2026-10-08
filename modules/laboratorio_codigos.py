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


ROTULOS = {
    "familia": "Família", "grupo": "Grupo", "grupo_familia": "Família do conjunto",
    "grupo_tamanho": "Grupo de tamanho", "tamanho": "Tamanho", "tamanho_corpo": "Tamanho do corpo",
    "material": "Material", "material_corpo": "Material do corpo",
    "vedacao": "Vedação", "vedacao_pistao": "Vedação do pistão",
    "estado": "Funcionamento", "construcao": "Construção", "variante": "Variante",
    "variante_construtiva": "Variante construtiva", "ancorada": "Ancorado",
    "formato": "Formato", "quantidade": "Quantidade", "local": "Local",
    "regra": "Critério de identificação", "sistema": "Sistema",
    "tipo": "Tipo", "final": "Final", "prefixos": "Prefixos", "sufixos": "Sufixos",
    "codigo_vedacao": "Código da vedação", "sequencial_tamanho": "Sequência do tamanho",
    "tamanhos_aplicaveis": "Tamanhos aplicáveis", "fora_kit_reparo": "Fora do kit de reparo",
    "construcao": "Construção", "regra_detalhada": "Regra detalhada",
    "nucleo_movel": "Núcleo móvel", "mola_nucleo": "Mola do núcleo móvel",
    "mola_pistao": "Mola do pistão", "pistao": "Pistão",
    "diafragma": "Diafragma", "mola": "Mola", "pulmao": "Pulmão",
    "carretel": "Carretel", "cadeirinha": "Cadeirinha",
    "mola_cadeirinha": "Mola da cadeirinha", "aro_pistao": "Aro do pistão",
    "mola_interna_aro": "Mola interna do aro", "assento": "Assento",
    "torre": "Torre", "torre_externa": "Torre externa",
    "componentes_internos": "Componentes internos",
    "identidade": "Identificação técnica", "componentes": "Componentes",
    "observacao_vedacao": "Observação sobre a vedação",
    "validacao_pendente": "Validações pendentes",
}
VARIAVEIS = {
    "V01": "Tipo de produto", "V02": "Vias e posições",
    "V03": "Funcionamento", "V04": "Acionamento",
    "V05": "Material do corpo", "V06": "Material da vedação",
    "V07": "Conexão / tamanho", "V08": "Orifício",
    "V09": "Pressão mínima", "V10": "Pressão máxima",
    "V11": "Temperatura", "V12": "Bobina",
    "V13": "Características da bobina", "V14": "Proteção",
    "V15": "Conexão elétrica", "V16": "Potência",
    "V17": "Tensão", "V18": "Aplicação do kit",
    "V20": "G1 — Núcleo e torre", "V21": "G2 — Diafragma",
    "V22": "G3 — Pistão", "V23": "G4 — Carretel",
    "V24": "G5 — O-rings",
}
IGNORAR = {"grupo_componente", "nome_grupo", "kit_reparo_exclui_torre_externa"}


def _rotulo(chave):
    return ROTULOS.get(str(chave), VARIAVEIS.get(str(chave), str(chave).replace("_", " ").capitalize()))


def _texto(valor):
    if valor is None or valor == "":
        return "Ainda não definido"
    if isinstance(valor, bool):
        return "Sim" if valor else "Não"
    if isinstance(valor, (list, tuple, set)):
        return ", ".join(_texto(v) for v in valor) if valor else "Nenhum"
    return str(valor).replace("_", " ")


def _mostrar_campos(dados):
    """Exibe informações técnicas em texto, nunca em JSON."""
    if isinstance(dados, list):
        if not dados:
            st.caption("Nenhum componente listado pelas regras atuais.")
        for item in dados:
            if isinstance(item, dict):
                _mostrar_campos(item)
                st.divider()
            else:
                st.write("• " + _texto(item))
        return
    if not isinstance(dados, dict):
        st.write(_texto(dados))
        return
    for chave, valor in dados.items():
        if chave in IGNORAR:
            continue
        if isinstance(valor, (dict, list)) and valor:
            st.markdown("**" + _rotulo(chave) + "**")
            _mostrar_campos(valor)
        elif isinstance(valor, (dict, list)):
            st.caption(_rotulo(chave) + ": informação não cadastrada")
        else:
            st.write("**" + _rotulo(chave) + ":** " + _texto(valor))


def pagina_laboratorio_codigos():
    if st.session_state.get("setor") != "ADMINISTRADOR":
        st.error("Acesso exclusivo para administradores.")
        st.stop()

    st.title("Conferência de Códigos")
    st.caption("Consulte as informações já cadastradas para conferir válvulas e kits de reparo. Nenhum dado é alterado.")
    with st.form("consulta_laboratorio"):
        codigo = st.text_input("Código da válvula ou do kit de reparo").strip().upper()
        tensao = st.text_input("Tensão, se houver (opcional)")
        consultar = st.form_submit_button("Consultar", type="primary")
    if not consultar:
        return
    if not codigo:
        st.warning("Digite um código para consultar.")
        return

    kit = codigo_parece_kit(codigo)
    try:
        resultado = processar_kit(codigo) if kit else processar_produto(codigo, tensao)
    except Exception as erro:
        st.error("Não foi possível consultar este código. Encaminhe o código para revisão do sistema.")
        st.caption("Detalhe técnico: " + str(erro))
        return

    st.subheader("1. Identificação")
    st.write("**Código consultado:** " + codigo)
    st.write("**Tipo:** " + ("Kit de reparo" if kit else "Válvula ou outro produto"))
    if not resultado.get("sucesso"):
        st.warning(resultado.get("erro") or "O sistema ainda não conseguiu identificar todas as informações.")
    else:
        st.success("Código reconhecido.")
    if resultado.get("descricao"):
        st.write("**Descrição:** " + str(resultado["descricao"]))

    parser = resultado.get("parser") or {}
    variaveis = resultado.get("variaveis") or {}
    if parser.get("familia"):
        st.write("**Família:** " + str(parser["familia"]))
    st.subheader("2. Características identificadas")
    if isinstance(variaveis, dict) and variaveis:
        for chave, valor in variaveis.items():
            if chave in {"V18", "V20", "V21", "V22", "V23", "V24"}:
                continue
            st.write("**" + VARIAVEIS.get(chave, _rotulo(chave)) + ":** " + _texto(valor) if not isinstance(valor, (dict, list)) else "**" + VARIAVEIS.get(chave, _rotulo(chave)) + ":**")
            if isinstance(valor, (dict, list)):
                _mostrar_campos(valor)
    else:
        st.info("Nenhuma característica adicional disponível.")

    if kit:
        grupos = parser.get("componentes") or {}
        st.caption("Os componentes abaixo são os que o sistema identifica para o kit; os agrupamentos de tamanho ainda podem precisar de conferência.")
        avisos = []
    else:
        grupos, avisos = _diagnosticar_valvula(resultado)

    st.subheader("3. Conferência dos componentes")
    st.caption("Abra cada grupo para conferir materiais, vedações e tamanhos.")
    if not grupos:
        st.info("Nenhum componente pôde ser identificado para este código.")
    for nome, dados in grupos.items():
        with st.expander(nome):
            if dados is None or dados == [] or dados == {}:
                st.info("Nenhum componente identificado neste grupo. Isso não confirma ausência física; pode faltar uma regra cadastrada.")
            elif isinstance(dados, dict) and dados.get("erro"):
                st.warning("Não foi possível consultar este grupo. Solicite revisão.")
            else:
                _mostrar_campos(dados)

    st.subheader("4. Informações para conferir")
    if avisos:
        for aviso in avisos:
            st.warning(aviso)
    else:
        st.info("Confira os materiais e tamanhos acima com a peça ou o catálogo. Informações exibidas refletem as regras atualmente cadastradas.")

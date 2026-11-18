"""Certificados de Qualidade: emissão somente com dados da Fila de Pedidos.

O módulo não consulta o ERP e não modifica dados de pedidos ou o motor.
Aprovações técnicas ficam em um histórico próprio, com acesso ADMIN.
"""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO
import re
from pathlib import Path
from xml.sax.saxutils import escape

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)

from core.database import supabase
from core.pedido_itens_comerciais import listar_itens_pedido
from modules.modulo_01.rastreabilidade import listar_series
from motor_descricao import processar_produto
from modules.certificados_correcao_service import (
    CAMPOS_EDITAVEIS, CAMPOS_POR_TENSAO, carregar_correcoes, aplicar_correcoes,
    registrar_correcao, normalizar_codigo,
)


VERDE = colors.HexColor("#2B8B5C")
CINZA = colors.HexColor("#424242")
LOGO = Path(__file__).resolve().parents[1] / "assets" / "icone_jefferson.png"
NOMES_MESES = (
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
)
CAMPOS_TECNICOS = {
    "V01": "Produto", "V02": "Acionamento", "V03": "Vias",
    "V04": "Operação", "V05": "Corpo", "V06": "Vedações",
    "V07": "Conexão", "V08": "Tipo de rosca",
    "V09": "Orifício", "V10": "Pressão mínima",
    "V11": "Pressão máxima", "V12": "Temperatura",
    "V13": "Bobina", "V14": "Potência", "V16": "Coeficiente de vazão (Kv)",
}


def _somente_digitos(valor):
    return re.sub(r"\D", "", str(valor or ""))


def _nf_normalizada(valor):
    digitos = _somente_digitos(valor)
    return str(int(digitos)) if digitos else ""


def buscar_nf_da_fila(consulta):
    """Consulta SOMENTE fila_pedidos e confere igualdade numérica da NF.

    Suporta 40688 e 40.688 sem uma varredura de todo o histórico.
    """
    numero = _nf_normalizada(consulta)
    if not numero or len(numero) > 15:
        return []
    nf_pontuada = f"{int(numero):,}".replace(",", ".")
    variantes = list({
        str(consulta or "").strip(), numero, nf_pontuada,
        f"NF-{numero.zfill(9)}",
    })
    resposta = (
        supabase.table("fila_pedidos")
        .select("id,numero_pedido,cliente,nota_fiscal,setor_atual,status")
        .in_("nota_fiscal", variantes)
        .order("id", desc=True)
        .limit(100)
        .execute()
    )
    return [
        pedido for pedido in (resposta.data or [])
        if _nf_normalizada(pedido.get("nota_fiscal")) == numero
        and str(pedido.get("status") or "").upper() != "CANCELADO"
    ]


def obter_data_faturamento_fila(pedido_id):
    """Obtém a data registrada na própria fila; nunca consulta documentos ERP."""
    resposta = (
        supabase.table("fila_movimentacoes")
        .select("criado_em,tipo_evento,destino")
        .eq("pedido_id", pedido_id)
        .eq("tipo_evento", "NOTA_FISCAL")
        .order("criado_em", desc=True)
        .limit(1)
        .execute()
    )
    linhas = resposta.data or []
    if not linhas:
        resposta = (
            supabase.table("fila_movimentacoes")
            .select("criado_em,tipo_evento,destino")
            .eq("pedido_id", pedido_id)
            .eq("destino", "FATURADO")
            .order("criado_em", desc=False)
            .limit(1)
            .execute()
        )
        linhas = resposta.data or []
    if not linhas or not linhas[0].get("criado_em"):
        return None
    try:
        return datetime.fromisoformat(
            str(linhas[0]["criado_em"]).replace("Z", "+00:00")
        ).date()
    except (TypeError, ValueError):
        return None


def _decimal(valor):
    try:
        return Decimal(str(valor if valor is not None else "0"))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def _qtd(valor):
    decimal = _decimal(valor)
    if decimal == decimal.to_integral_value():
        return str(int(decimal))
    return format(decimal.normalize(), "f").replace(".", ",")


def _texto(valor):
    if valor is None or valor == "":
        return ""
    if isinstance(valor, dict):
        partes = []
        for chave, dado in valor.items():
            if dado is None or dado == "" or dado == [] or dado == {}:
                continue
            if isinstance(dado, (dict, list)):
                partes.append(_texto(dado))
            else:
                partes.append(str(dado))
        return " | ".join(x for x in partes if x)
    if isinstance(valor, (list, tuple)):
        return ", ".join(_texto(parte) for parte in valor if parte is not None)
    return str(valor)


def _ausente(valor):
    texto = _texto(valor).strip().casefold()
    return not texto or texto in {
        "não identificado", "nao identificado", "não informado",
        "nao informado", "indefinido", "none", "null", "-",
    }


def preparar_item(item, series, correcoes=None):
    """Interpreta o motor e aplica SOMENTE as correções aprovadas ao certificado."""
    codigo = str(item.get("codigo") or "").strip().upper()
    tensao = str(item.get("tensao") or "").strip()
    quantidade = _decimal(item.get("quantidade"))
    erros = []
    if not codigo:
        erros.append("Código do produto não informado.")
    if not tensao:
        erros.append("Tensão não registrada na fila.")
    if quantidade <= 0:
        erros.append("Quantidade do item inválida.")

    registros = [s for s in series if s.get("pedido_item_id") == item.get("id")]
    numero_series = []
    total_series = Decimal("0")
    if not registros:
        erros.append("Rastreabilidade não registrada para este item.")
    for registro in registros:
        qtd_serie = _decimal(registro.get("quantidade"))
        if qtd_serie <= 0:
            erros.append("Quantidade de série inválida.")
        total_series += qtd_serie
        if registro.get("sem_numero"):
            if len(registros) > 1:
                erros.append("Registro 'sem número' misturado a outras séries.")
            numero_series.append("Sem número de série")
        else:
            numero = str(registro.get("numero_serie") or "").strip()
            if not numero:
                erros.append("Número de série vazio.")
            else:
                numero_series.append(numero)
    if registros and total_series != quantidade:
        erros.append(
            f"Soma das séries ({_qtd(total_series)}) diferente da quantidade "
            f"do item ({_qtd(quantidade)})."
        )

    variaveis = {}
    origens = {}
    try:
        resultado = processar_produto(codigo, tensao)
        if not resultado.get("sucesso"):
            erros.append(
                "Motor de descrição não interpretou o código: "
                + str(resultado.get("erro") or "verifique o modelo")
            )
        else:
            variaveis, origens = aplicar_correcoes(
                resultado.get("variaveis") or {}, item, correcoes or {}
            )
            if variaveis.get("CLASSE_PRODUTO") == "BOBINA":
                erros.append("Bobina avulsa: este modelo de certificado é para válvulas.")
            for chave in ("V05", "V06", "V10", "V11", "V12"):
                if _ausente(variaveis.get(chave)):
                    erros.append(
                        f"Característica técnica ausente: "
                        f"{CAMPOS_TECNICOS[chave]}."
                    )
    except Exception as exc:
        erros.append("Falha na interpretação técnica do código.")
        import logging
        logging.getLogger(__name__).exception(
            "Falha do motor de certificados para %s: %s", codigo, exc
        )
    return {
        "id": item.get("id"), "codigo": codigo, "tensao": tensao,
        "quantidade": quantidade, "series": numero_series,
        "variaveis": variaveis, "origens": origens,
        "erros": list(dict.fromkeys(erros)),
    }


def _estilos():
    return {
        "titulo": ParagraphStyle(
            "titulo_cert", fontName="Helvetica-Bold",
            fontSize=15, leading=19, textColor=CINZA,
            alignment=TA_CENTER, spaceAfter=16,
        ),
        "normal": ParagraphStyle(
            "normal_cert", fontName="Helvetica",
            fontSize=10, leading=15, textColor=CINZA, alignment=TA_LEFT,
            spaceAfter=10,
        ),
        "pequeno": ParagraphStyle(
            "pequeno_cert", fontName="Helvetica",
            fontSize=9.5, leading=14, textColor=CINZA,
        ),
        "rotulo": ParagraphStyle(
            "rotulo_cert", fontName="Helvetica-Bold",
            fontSize=10, leading=15, textColor=CINZA,
        ),
        "secao": ParagraphStyle(
            "secao_cert", fontName="Helvetica-Bold",
            fontSize=11, leading=15, textColor=VERDE,
            spaceBefore=13, spaceAfter=7,
        ),
    }


def _p(texto, estilo):
    return Paragraph(escape(_texto(texto)).replace("\n", "<br/>"), estilo)


def _tabela(linhas, estilos, larguras=(57*mm, 112*mm)):
    linhas_pdf = [
        [_p(rotulo, estilos["rotulo"]), _p(valor, estilos["pequeno"])]
        for rotulo, valor in linhas
    ]
    tabela = Table(linhas_pdf, colWidths=list(larguras), hAlign="LEFT")
    tabela.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.HexColor("#D7D7D7")),
    ]))
    return tabela


def _moldura(canvas, doc, com_marca):
    canvas.saveState()
    w, h = A4
    if com_marca:
        if LOGO.is_file():
            try:
                from reportlab.lib.utils import ImageReader
                img = ImageReader(str(LOGO))
                iw, ih = img.getSize()
                max_w, max_h = 35*mm, 18*mm
                fator = min(max_w / iw, max_h / ih)
                canvas.drawImage(
                    img, 20*mm, h-30*mm,
                    width=iw*fator, height=ih*fator, mask="auto",
                )
            except (OSError, ValueError):
                pass
        canvas.setFont("Helvetica-Bold", 11)
        canvas.setFillColor(CINZA)
        canvas.drawRightString(w-20*mm, h-21*mm, "Jefferson do Brasil")
        canvas.setFont("Helvetica-Bold", 7.5)
        canvas.drawRightString(w-20*mm, h-26*mm, "VÁLVULAS SOLENOIDES")
    canvas.setStrokeColor(VERDE)
    canvas.setLineWidth(1.1)
    canvas.line(20*mm, 27*mm, w-20*mm, 27*mm)
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.setFillColor(CINZA)
    canvas.drawString(20*mm, 22*mm, "Jefferson Solenoidbras Ltda.")
    canvas.setFont("Helvetica", 7)
    canvas.drawRightString(
        w-20*mm, 22*mm, "CNPJ 56.541.642/0001-52"
    )
    canvas.drawString(
        20*mm, 17*mm,
        "Rua Cristiano Angeli, 1.316 - São Bernardo do Campo - SP - Brasil"
    )
    canvas.drawRightString(w-20*mm, 12*mm, f"Página {doc.page}")
    canvas.restoreState()


def gerar_pdf_certificados(pedido, data_faturamento, itens, com_marca=True):
    """Gera PDF em memória. Nenhuma escrita no Supabase ou no disco."""
    if not itens or any(i["erros"] for i in itens):
        raise ValueError("Há itens sem validação técnica ou rastreabilidade.")
    if data_faturamento is None:
        raise ValueError("Data do faturamento não encontrada na fila.")

    arquivo = BytesIO()
    doc = SimpleDocTemplate(
        arquivo, pagesize=A4,
        topMargin=37*mm, bottomMargin=37*mm,
        leftMargin=20*mm, rightMargin=20*mm,
        title=f"Certificado de Qualidade - NF {pedido['nota_fiscal']}",
        author="Jefferson Solenoidbras Ltda.",
    )
    estilo = _estilos()
    elementos = []
    for idx, item in enumerate(itens):
        if idx:
            elementos.append(PageBreak())
        v = item["variaveis"]
        emissao = date.today()
        texto_data = (
            f"São Bernardo do Campo, {emissao.day} de "
            f"{NOMES_MESES[emissao.month-1]} de {emissao.year}."
        )
        elementos.append(Spacer(1, 8*mm))
        elementos.append(Paragraph("CERTIFICADO DE QUALIDADE", estilo["titulo"]))
        elementos.append(_p(texto_data, estilo["normal"]))
        elementos.append(_p(
            "Estamos especificando os materiais e faixas de trabalho das "
            "válvulas solenoides de nossa fabricação, marca JEFFERSON, "
            "que se identificam como:",
            estilo["normal"],
        ))
        elementos.append(_tabela([
            ("CATÁLOGO Nº:", item["codigo"]),
            ("Nota fiscal:", pedido.get("nota_fiscal")),
            ("Pedido:", pedido.get("numero_pedido")),
            ("Cliente:", pedido.get("cliente")),
            ("Data de faturamento:", data_faturamento.strftime("%d/%m/%Y")),
            ("Quantidade:", _qtd(item["quantidade"])),
            ("Nº de série:", ", ".join(item["series"])),
        ], estilo))

        elementos.append(Paragraph("Materiais", estilo["secao"]))
        elementos.append(_tabela([
            ("Corpo:", _texto(v.get("V05"))),
            ("Torre:", "AISI 316 (padrão do certificado original)"),
            ("Mola de retorno:", "AISI 302 (padrão do certificado original)"),
            ("Vedações:", _texto(v.get("V06"))),
            ("Bobina:", _texto(v.get("V13")) or "Não aplicável"),
            ("Tensão de acionamento:", item["tensao"]),
        ], estilo))

        elementos.append(Paragraph("Dados de processo", estilo["secao"]))
        processo = [
            ("Pressão de trabalho:",
                f"{_texto(v.get('V10'))} a {_texto(v.get('V11'))}"),
            ("Estanqueidade:", "100%"),
            ("Temperatura:", _texto(v.get("V12"))),
            ("Operação:", " / ".join(
                x for x in (_texto(v.get("V03")), _texto(v.get("V04"))) if x
            )),
            ("Conexão:", " ".join(
                x for x in (_texto(v.get("V07")), _texto(v.get("V08"))) if x
            )),
        ]
        for chave, rotulo in (
            ("V01", "Tipo de produto:"), ("V02", "Acionamento:"),
            ("V09", "Orifício:"), ("V14", "Potência da bobina:"),
            ("V16", "Vazão (Kv):"),
        ):
            if not _ausente(v.get(chave)):
                processo.append((rotulo, _texto(v.get(chave))))
        elementos.append(_tabela(processo, estilo))

        elementos.append(Spacer(1, 8*mm))
        elementos.append(_p(
            "* Garantia: 12 meses, exceto partes elétricas (bobinas).",
            estilo["normal"],
        ))
        elementos.append(_p(
            "Certificamos que os dados informados se cumprem em cada uma "
            "das unidades fabricadas e que foram cumpridos todos os "
            "requisitos de prova em nosso manual de controle de qualidade.",
            estilo["normal"],
        ))
        elementos.append(Spacer(1, 10*mm))
        elementos.append(_p("Jefferson Solenoidbras Ltda.", estilo["rotulo"]))
        elementos.append(_p("Arthur Henrique Rosa | Área Técnica", estilo["pequeno"]))

    doc.build(
        elementos,
        onFirstPage=lambda canv, obj: _moldura(canv, obj, com_marca),
        onLaterPages=lambda canv, obj: _moldura(canv, obj, com_marca),
    )
    return arquivo.getvalue()


def _editor_correcao(item, pedido, correcoes):
    """Admin homologa um campo de cada vez; alterações sempre auditadas."""
    codigo = normalizar_codigo(item["codigo"])
    item_id = item["id"]
    campos = [campo for campo in CAMPOS_EDITAVEIS if campo in CAMPOS_TECNICOS]
    faltantes = [
        c for c in ("V05", "V06", "V10", "V11", "V12")
        if _ausente(item["variaveis"].get(c))
    ]
    with st.expander("Corrigir característica técnica", expanded=bool(faltantes)):
        campo = st.selectbox(
            "Qual característica precisa de correção?",
            options=campos,
            index=campos.index(faltantes[0]) if faltantes else 0,
            format_func=lambda c: f"{CAMPOS_TECNICOS[c]} ({c})",
            key=f"cert_campo_{item_id}",
        )
        valor_atual = _texto(item["variaveis"].get(campo))
        origem = item.get("origens", {}).get(campo)
        st.caption(
            "Valor usado no certificado: "
            + (valor_atual or "Não identificado")
            + (
                f" | Correção {origem['escopo'].lower()} aprovada por "
                f"{origem['usuario']}"
                if origem else " | Motor de descrição"
            )
        )
        if campo in CAMPOS_POR_TENSAO:
            st.info(
                "Para bobina/potência, a correção permanente só será aplicada "
                "à mesma tensão registrada neste item."
            )
        with st.form(f"cert_form_corr_{item_id}", clear_on_submit=False):
            valor_novo = st.text_input(
                "Novo valor técnico homologado",
                value=valor_atual, max_chars=500,
                key=f"cert_valor_{item_id}_{campo}",
            )
            escopo = st.radio(
                "Abrangência da correção",
                ["PONTUAL", "PERMANENTE"],
                format_func=lambda x: (
                    "Somente este item deste pedido/NF" if x == "PONTUAL"
                    else "Todos os certificados do mesmo código exato"
                ),
                key=f"cert_escopo_{item_id}",
            )
            justificativa = st.text_area(
                "Fonte ou justificativa técnica da especificação",
                placeholder="Ex.: catálogo Jefferson revisado, ficha técnica aprovada...",
                max_chars=2000,
                key=f"cert_justificativa_{item_id}",
            )
            conferir = st.checkbox(
                "Conferi a especificação técnica e autorizo o registro "
                "desta correção.",
                key=f"cert_aprovar_{item_id}_{campo}",
            )
            salvar = st.form_submit_button("Validar e salvar correção")
        if salvar:
            if not conferir:
                st.warning("Confirme a validação técnica antes de salvar.")
            else:
                try:
                    registrar_correcao(
                        pedido_id=pedido["id"], item_id=item_id,
                        codigo=codigo, campo=campo, tensao=item["tensao"],
                        escopo=escopo, valor_anterior=valor_atual,
                        valor_corrigido=valor_novo,
                        justificativa=justificativa,
                        usuario=st.session_state.get("usuario"),
                    )
                except Exception as exc:
                    import logging
                    logging.getLogger(__name__).exception(
                        "Não foi possível registrar correção: %s", exc
                    )
                    st.error(
                        "Correção não registrada. Confira o valor, a justificativa "
                        "e a conexão com o banco."
                    )
                else:
                    st.session_state["cert_pdf_confirmado"] = False
                    st.success("Correção homologada e registrada no histórico.")
                    st.rerun()

    ativas = item.get("origens", {})
    if ativas:
        with st.expander("Revogar uma correção vigente deste item"):
            campo_revogar = st.selectbox(
                "Correção aplicada",
                options=list(ativas),
                format_func=lambda c: (
                    f"{CAMPOS_TECNICOS.get(c, c)} | "
                    f"{ativas[c]['escopo']} | {ativas[c]['valor_corrigido']}"
                ),
                key=f"cert_reversao_campo_{item_id}",
            )
            atual = ativas[campo_revogar]
            with st.form(f"cert_reversao_form_{item_id}"):
                motivo = st.text_area(
                    "Motivo da revogação (obrigatório)",
                    max_chars=2000,
                )
                confirmacao = st.checkbox(
                    "Confirmo a revogação da correção selecionada."
                )
                revogar = st.form_submit_button("Revogar correção")
            if revogar:
                if not confirmacao:
                    st.warning("Confirme a revogação.")
                else:
                    try:
                        registrar_correcao(
                            pedido_id=pedido["id"], item_id=item_id,
                            codigo=codigo, campo=campo_revogar,
                            tensao=item["tensao"],
                            escopo=atual["escopo"],
                            valor_anterior=atual["valor_corrigido"],
                            valor_corrigido="",
                            justificativa=motivo,
                            usuario=st.session_state.get("usuario"),
                            acao="REVOGAR",
                        )
                    except Exception as exc:
                        import logging
                        logging.getLogger(__name__).exception(
                            "Erro ao revogar correção: %s", exc
                        )
                        st.error("A revogação não foi registrada.")
                    else:
                        st.session_state["cert_pdf_confirmado"] = False
                        st.success("Revogação registrada, sem apagar o histórico.")
                        st.rerun()

    eventos = [
        e for e in correcoes.get("historico", [])
        if e["codigo"] == codigo and (
            e["escopo"] == "PERMANENTE" or e["pedido_item_id"] == item_id
        )
    ]
    if eventos:
        with st.expander("Histórico de aprovações e revogações"):
            st.dataframe(
                [{
                    "Quando": str(e.get("criado_em") or "")[:19],
                    "Escopo": e["escopo"],
                    "Ação": e["acao"],
                    "Característica": CAMPOS_TECNICOS.get(e["campo"], e["campo"]),
                    "Anterior": e.get("valor_anterior") or "-",
                    "Valor aprovado": e.get("valor_corrigido") or "-",
                    "Responsável": e.get("usuario") or "-",
                    "Justificativa": e.get("justificativa") or "-",
                } for e in eventos[:50]],
                hide_index=True,
                use_container_width=True,
            )


def pagina_certificados_qualidade():
    """Visível somente ao ADMINISTRADOR, independentemente da navegação."""
    if st.session_state.get("setor") != "ADMINISTRADOR":
        st.error("Acesso exclusivo para administradores.")
        st.stop()

    st.title("Certificados de Qualidade")
    st.caption(
        "Emissão a partir da Fila de Pedidos, sem consulta ao ERP. "
        "Correções técnicas aprovadas são registradas separadamente "
        "e não alteram os dados da fila ou o motor de descrição."
    )
    with st.form("cert_buscar_nf", clear_on_submit=False):
        consulta = st.text_input(
            "Número da NF da fila", placeholder="Ex.: 40.688 ou 40688",
            max_chars=35,
        )
        pesquisar = st.form_submit_button("Buscar NF", type="primary")
    if pesquisar:
        st.session_state["cert_nf_pesquisada"] = consulta.strip()
    consulta = st.session_state.get("cert_nf_pesquisada", "")
    if not consulta:
        return

    try:
        pedidos = buscar_nf_da_fila(consulta)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception("Erro na busca da NF: %s", exc)
        st.error("Não foi possível consultar a fila. Tente novamente.")
        return
    if not pedidos:
        st.warning("NF não encontrada na Fila de Pedidos.")
        return

    mapa_pedidos = {p["id"]: p for p in pedidos}
    pedido_id = st.selectbox(
        "Pedido associado à NF",
        options=list(mapa_pedidos),
        format_func=lambda ident: (
            f"Pedido {mapa_pedidos[ident].get('numero_pedido') or '-'} | "
            f"{mapa_pedidos[ident].get('cliente') or '-'} | "
            f"NF {mapa_pedidos[ident].get('nota_fiscal') or '-'}"
        ),
        key="cert_pedido_selecionado",
    )
    pedido = mapa_pedidos[pedido_id]

    try:
        itens = listar_itens_pedido(pedido_id)
        series = listar_series(pedido_id, itens=itens)
        data_faturamento = obter_data_faturamento_fila(pedido_id)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception("Erro ao carregar pedido: %s", exc)
        st.error("Não foi possível carregar os itens e a rastreabilidade.")
        return
    if not itens:
        st.warning(
            "Este pedido não possui itens cadastrados na tabela da fila. "
            "A emissão não usará o histórico do ERP como alternativa."
        )
        return

    st.write("**Cliente:**", pedido.get("cliente") or "Não informado")
    st.write("**NF:**", pedido.get("nota_fiscal"))
    st.write("**Pedido:**", pedido.get("numero_pedido") or "Não informado")
    st.write(
        "**Data de faturamento registrada na fila:**",
        data_faturamento.strftime("%d/%m/%Y")
        if data_faturamento else "Não registrada",
    )
    if data_faturamento is None:
        st.error("Não há evento de faturamento na fila. PDF indisponível.")

    por_id = {i["id"]: i for i in itens}
    ids = list(por_id)
    selecionados = st.multiselect(
        "Itens para o certificado",
        options=ids, default=ids,
        format_func=lambda ident: (
            f"{por_id[ident].get('codigo') or 'Sem código'} | "
            f"{_qtd(por_id[ident].get('quantidade'))} un. | "
            f"{por_id[ident].get('tensao') or 'Sem tensão'}"
        ),
    )
    if not selecionados:
        st.info("Selecione ao menos um item.")
        return

    try:
        correcoes = carregar_correcoes(
            pedido_id, [por_id[ident] for ident in selecionados]
        )
    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception(
            "Erro ao consultar correções técnicas: %s", exc
        )
        st.error("Não foi possível consultar a base de correções técnicas.")
        return
    preparados = [
        preparar_item(por_id[ident], series, correcoes)
        for ident in selecionados
    ]
    habilitados = bool(data_faturamento) and all(
        not item["erros"] for item in preparados
    )
    for item in preparados:
        with st.expander(
            f"{item['codigo']} | Quantidade {_qtd(item['quantidade'])} | "
            + ("Dados conferidos" if not item["erros"] else "Revisão necessária"),
            expanded=bool(item["erros"]),
        ):
            st.write("**Números de série:**", ", ".join(item["series"]) or "-")
            for chave, nome in CAMPOS_TECNICOS.items():
                valor = _texto(item["variaveis"].get(chave))
                if valor:
                    st.write(f"**{nome}:** {valor}")
                    if chave in item["origens"]:
                        fonte = item["origens"][chave]
                        st.caption(
                            f"Revisado ({fonte['escopo'].lower()}) por "
                            f"{fonte['usuario']}."
                        )
            st.caption(
                "Campos fixos herdados do certificado Excel: torre AISI 316, "
                "mola de retorno AISI 302, estanqueidade 100% e garantia 12 meses."
            )
            for erro in item["erros"]:
                st.warning(erro)
        _editor_correcao(item, pedido, correcoes)

    modelo = st.radio(
        "Modelo do documento",
        ["COM MARCA", "SEM MARCA"],
        horizontal=True,
    )
    confirmacao = st.checkbox(
        "Confirmo que as especificações técnicas, os materiais fixos "
        "do modelo e as inspeções de qualidade foram verificados "
        "para os itens selecionados.",
        value=False,
        key="cert_pdf_confirmado",
    )
    if not habilitados:
        st.error(
            "A emissão está bloqueada até regularizar os dados "
            "indicados acima. Use 'Corrigir característica técnica' para "
            "campos de descrição, ou ajuste rastreabilidade na fila."
        )
        return
    if not confirmacao:
        st.info("Confirme a verificação técnica para habilitar a emissão.")
        return

    try:
        pdf = gerar_pdf_certificados(
            pedido, data_faturamento, preparados,
            com_marca=(modelo == "COM MARCA"),
        )
    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception("Falha na geração do PDF: %s", exc)
        st.error("Não foi possível gerar o PDF. Verifique os dados do pedido.")
        return

    st.download_button(
        "Baixar Certificado de Qualidade (PDF)",
        data=pdf, mime="application/pdf",
        file_name=(
            "certificado_nf_"
            + (_nf_normalizada(pedido.get("nota_fiscal")) or "sem_nf")
            + ".pdf"
        ),
        type="primary",
    )
    st.caption(
        "PDF gerado em memória. A emissão não altera a fila nem o motor. "
        "Apenas aprovações e revogações técnicas são gravadas separadamente."
    )

"""Novo, consulta, revisão e reaproveitamento de orçamentos."""
import copy
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo
import streamlit as st
from motor_descricao import processar_produto
from components.kits import codigo_parece_kit, processar_kit
from modules.modulo_orcamentos.clientes_repository import buscar_clientes
from modules.modulo_orcamentos.imagens_repository import obter_url_imagem
from modules.modulo_orcamentos.orcamentos_repository import (
    TIPOS_PRIMEIRO_CONTATO, PADROES, obter_opcoes_comerciais,
    buscar_primeiro_contato, salvar_primeiro_contato, cliente_do_contato,
    buscar_orcamentos, carregar_orcamento, salvar_orcamento,
)
from modules.modulo_orcamentos.pdf.gerador_pdf_teste import gerar_pdf_orcamento, formatar_reais

OPCOES_TENSAO = ['110/60HZ', '220/60HZ', '24VCC', '12VCC', '110/50HZ', '220/50HZ', 'KIT DE REPARO', 'OUTRO']
OPCOES_PRAZO = ['IMEDIATO', '5 DIAS', '10 DIAS', '15 DIAS', '20 DIAS', '30 DIAS', '45 DIAS', '60 DIAS', 'OUTRO']


def novo_rascunho():
    return {'numero': '', 'cliente': None, 'itens': [], 'observacao': '',
            'condicoes': dict(PADROES), 'modo': 'NOVO', 'anterior_id': None,
            'origem_id': None, 'revisao': 0, 'salvo_id': None}


def iniciar_rascunho(dados=None):
    st.session_state['orc_draft'] = dados or novo_rascunho()
    st.session_state['orc_nonce'] = st.session_state.get('orc_nonce', 0) + 1
    st.session_state.pop('orc_cliente_resultados', None)
    st.session_state.pop('orc_especial', None)
    st.session_state.pop('orc_contato_encontrado', None)
    st.session_state.pop('orc_cnpj', None)
    st.session_state.pop('orc_edit_index', None)
    if st.session_state.get('orc_nav') != 'Novo orçamento':
        st.session_state['orc_nav'] = 'Novo orçamento'


def defaults_cliente(cliente):
    return {'validade_proposta': cliente.get('validade_especial') or PADROES['validade_proposta'],
            'condicao_pagamento': cliente.get('pagamento_especial') or PADROES['condicao_pagamento'],
            'frete': cliente.get('frete_especial') or PADROES['frete']}


def selecionar_cliente(cliente, nonce):
    draft = st.session_state['orc_draft']
    draft['cliente'] = cliente
    draft['condicoes'] = defaults_cliente(cliente)
    for campo, valor in draft['condicoes'].items():
        st.session_state[f'orc_{campo}_{nonce}'] = valor


def processar_item(codigo, tensao, quantidade, valor, prazo, observacao):
    codigo = codigo.strip().upper()
    if not codigo or not prazo.strip():
        raise ValueError('Informe código e prazo.')
    try:
        qtd = int(str(quantidade).strip())
        preco = Decimal(str(valor).strip().replace('.', '').replace(',', '.'))
    except (ValueError, InvalidOperation):
        raise ValueError('Informe quantidade inteira e preço no formato 1.234,56.')
    if qtd <= 0 or not preco.is_finite() or preco < 0:
        raise ValueError('Quantidade deve ser positiva e preço não pode ser negativo.')
    kit = codigo_parece_kit(codigo)
    tensao = 'KIT DE REPARO' if kit else tensao.strip().upper()
    if not tensao:
        raise ValueError('Informe a tensão.')
    resultado = processar_kit(codigo) if kit else processar_produto(codigo, tensao)
    if not resultado or not resultado.get('sucesso'):
        raise ValueError((resultado or {}).get('erro') or 'Não foi possível interpretar o código.')
    return {'codigo': codigo, 'tensao': tensao, 'quantidade': qtd,
            'valor_unitario': float(preco.quantize(Decimal('0.01'))),
            'prazo': prazo.strip(), 'observacao': observacao.strip(),
            'variaveis': resultado.get('variaveis') or {},
            'descricao': resultado.get('descricao')}


def completar_item(item):
    item = copy.deepcopy(item)
    if not item.get('variaveis'):
        resultado = processar_kit(item['codigo']) if codigo_parece_kit(item['codigo']) else processar_produto(item['codigo'], item.get('tensao') or '')
        if resultado and resultado.get('sucesso'):
            item['variaveis'] = resultado.get('variaveis') or {}
            item['descricao'] = resultado.get('descricao')
        else:
            item['_erro_tecnico'] = (resultado or {}).get('erro') or 'Código não interpretado.'
    item['valor_unitario'] = float(item['valor_unitario'])
    item['observacao'] = item.get('observacao') or ''
    return item


def carregar_para_edicao(o, modo):
    d = novo_rascunho()
    d.update(numero=o['numero_orcamento'] if modo == 'REVISAO' else '',
             cliente=copy.deepcopy(o['cliente']) if modo != 'SIMILAR' else None,
             itens=[completar_item(item) for item in o['itens']],
             observacao=o.get('observacao_geral') or '', modo=modo,
             anterior_id=o['id'] if modo == 'REVISAO' else None,
             origem_id=o['id'] if modo in ('DUPLICADO', 'SIMILAR') else None,
             revisao=(o.get('revisao') or 0) + 1 if modo == 'REVISAO' else 0,
             condicoes={k: o.get(k) or v for k,v in PADROES.items()})
    iniciar_rascunho(d)


def editar_item(indice):
    st.markdown('**Editar item**')
    d = st.session_state['orc_draft']
    item = d['itens'][indice]
    with st.form(f'editar_item_{indice}'):
        c1,c2 = st.columns(2)
        codigo = c1.text_input('Código', value=item['codigo'])
        tensao = c2.text_input('Tensão', value=item.get('tensao') or '')
        c1,c2,c3 = st.columns(3)
        qtd = c1.text_input('Quantidade', value=str(item['quantidade']))
        valor = c2.text_input('Valor unitário', value=f"{float(item['valor_unitario']):.2f}".replace('.', ','))
        prazo = c3.text_input('Prazo', value=item.get('prazo') or '')
        obs = st.text_area('Observação do item', value=item.get('observacao') or '')
        aplicar = st.form_submit_button('Aplicar ao orçamento', type='primary')
    if st.button('Cancelar edição',key=f'cancel_edit_{indice}'):
        st.session_state.pop('orc_edit_index', None)
        st.rerun()
    if aplicar:
        try:
            d['itens'][indice] = processar_item(codigo,tensao,qtd,valor,prazo,obs)
            st.session_state.pop('orc_edit_index', None)
            st.rerun()
        except Exception as erro:
            st.error(str(erro))


def render_cliente(d, nonce):
    st.subheader('Cliente')
    bloqueado = d['modo'] in ('REVISAO','DUPLICADO') or d.get('salvo_id')
    if not bloqueado:
        with st.form(f'buscar_cliente_{nonce}'):
            termo = st.text_input('Buscar cliente', placeholder='Código, empresa ou CNPJ')
            buscar = st.form_submit_button('Buscar cliente')
        if buscar:
            codigo = termo.strip()
            if codigo in TIPOS_PRIMEIRO_CONTATO:
                st.session_state['orc_especial'] = codigo
                st.session_state.pop('orc_cliente_resultados',None)
                st.session_state.pop('orc_contato_encontrado',None)
                st.session_state.pop('orc_cnpj',None)
                d['cliente'] = None
            else:
                st.session_state.pop('orc_especial',None)
                st.session_state.pop(f'cliente_select_{nonce}',None)
                st.session_state['orc_cliente_resultados'] = buscar_clientes(termo)
                resultados = st.session_state['orc_cliente_resultados']
                exatos = [c for c in resultados if str(c['codigo_cliente']) == codigo]
                if len(exatos) == 1:
                    selecionar_cliente(exatos[0],nonce)
        especiais = st.session_state.get('orc_especial')
        if especiais:
            with st.container(border=True):
                tipo = TIPOS_PRIMEIRO_CONTATO[especiais]
                st.markdown(f'**Primeiro contato — {tipo} • código {especiais}**')
                with st.form(f'cnpj_contato_{nonce}_{especiais}'):
                    cnpj = st.text_input('CNPJ', help='Com ou sem pontuação.')
                    consultar = st.form_submit_button('Consultar CNPJ')
                if consultar:
                    st.session_state['orc_cnpj'] = cnpj
                    st.session_state['orc_contato_encontrado'] = buscar_primeiro_contato(cnpj)
                    d['cliente'] = None
                    st.session_state['orc_contact_nonce'] = st.session_state.get('orc_contact_nonce',0)+1
                if st.session_state.get('orc_cnpj'):
                    existente = st.session_state.get('orc_contato_encontrado') or {}
                    if existente:
                        st.info('Primeiro contato encontrado. Confira os dados antes de confirmar.')
                    key = f"{nonce}_{especiais}_{st.session_state.get('orc_contact_nonce',0)}"
                    with st.form(f'contato_{key}'):
                        empresa = st.text_input('Nome da empresa',value=existente.get('nome_empresa') or '')
                        canais = ['E-mail','WhatsApp','Telefone']
                        canal = st.selectbox('Forma de contato',canais,index=canais.index(existente.get('canal_contato','E-mail')))
                        contato = st.text_input('E-mail ou número de contato',value=existente.get('endereco_contato') or '')
                        nome_contato = st.text_input('Nome da pessoa de contato (opcional)',value=existente.get('nome_contato') or '',placeholder='Ex.: Luan')
                        confirmar = st.form_submit_button('Confirmar primeiro contato')
                    if confirmar:
                        row = salvar_primeiro_contato(st.session_state['orc_cnpj'],empresa,tipo,canal,contato,st.session_state.get('nome') or '-',nome_contato=nome_contato)
                        selecionar_cliente(cliente_do_contato(row,especiais),nonce)
                        st.success('Primeiro contato confirmado.')
        resultados = st.session_state.get('orc_cliente_resultados') or []
        if resultados:
            escolha = st.selectbox('Resultados de clientes',range(len(resultados)),index=None,
                format_func=lambda i: f"{resultados[i]['codigo_cliente']} | {resultados[i].get('razao_social') or resultados[i].get('nome_fantasia')} | {resultados[i].get('cnpj_cpf') or ''}",key=f'cliente_select_{nonce}')
            if escolha is not None and st.button('Usar este cliente',key=f'usar_cliente_{nonce}'):
                cliente = resultados[escolha]
                if str(cliente['codigo_cliente']) in TIPOS_PRIMEIRO_CONTATO:
                    st.session_state['orc_especial'] = str(cliente['codigo_cliente'])
                    st.session_state.pop('orc_cliente_resultados',None)
                    d['cliente'] = None
                    st.rerun()
                selecionar_cliente(cliente,nonce)
        elif buscar and not especiais:
            st.info('Nenhum cliente encontrado.')
    if d['cliente']:
        cliente = d['cliente']
        with st.container(border=True):
            st.write(f"**{cliente.get('razao_social') or cliente.get('nome_fantasia') or '-'}**")
            c1,c2,c3 = st.columns(3)
            c1.metric('Código',cliente.get('codigo_cliente') or '-')
            c2.metric('CNPJ/CPF',cliente.get('cnpj_cpf') or '-')
            c3.metric('Tipo',cliente.get('tipo_cliente') or '-')
            if cliente.get('endereco_contato'):
                st.caption(f"{cliente.get('canal_contato')}: {cliente['endereco_contato']}")
            if cliente.get('nome_contato'):
                st.caption(f"Pessoa de contato: {cliente['nome_contato']}")


def botao_pdf(o, key):
    try:
        itens = [completar_item(item) for item in o['itens']]
        erros = [i for i in itens if i.get('_erro_tecnico')]
        if erros:
            st.warning('Não foi possível interpretar um item para gerar o PDF: '+erros[0]['codigo'])
            return
        data = o.get('data_proposta') or (o.get('criado_em') or '')[:10]
        data = datetime.strptime(data,'%Y-%m-%d').strftime('%d/%m/%Y')
        condicoes = {k:o.get(k) or v for k,v in PADROES.items()}
        arquivo = gerar_pdf_orcamento(o['numero_orcamento'],data,o['cliente'],itens,
            o.get('observacao_geral') or '',o['criado_por'],revisao=o.get('revisao') or 0,
            condicoes_comerciais=condicoes)
        cliente_nome = o['cliente'].get('razao_social') or o['cliente'].get('nome_fantasia') or 'CLIENTE'
        nome = f"{o['numero_orcamento'].replace('/','-')} - {cliente_nome.split()[0]} - R{o.get('revisao') or 0}.pdf"
        nome = re.sub(r'[\\/:*?"<>|]','-',nome)
        st.download_button('Abrir / Baixar PDF',arquivo,file_name=nome,mime='application/pdf',key=key)
    except Exception as erro:
        st.error(f'Erro ao gerar PDF: {erro}')


def pagina_novo():
    d = st.session_state['orc_draft']
    nonce = st.session_state['orc_nonce']
    labels = {'NOVO':'Novo orçamento','REVISAO':'Revisar orçamento','DUPLICADO':'Duplicar orçamento','SIMILAR':'Criar orçamento similar'}
    st.title('📄 '+labels[d['modo']])
    if st.button('Iniciar outro orçamento',key='reset_orc'):
        st.session_state['orc_confirmar_limpeza'] = True
    if st.session_state.get('orc_confirmar_limpeza'):
        st.warning('Isso descarta os dados que ainda não foram salvos nesta tela.')
        c1,c2 = st.columns(2)
        if c1.button('Confirmar limpeza'):
            st.session_state.pop('orc_confirmar_limpeza',None)
            iniciar_rascunho(); st.rerun()
        if c2.button('Continuar neste orçamento'):
            st.session_state.pop('orc_confirmar_limpeza',None);st.rerun()
    salvo = bool(d.get('salvo_id'))
    d['numero'] = st.text_input('Número do orçamento',value=d['numero'],placeholder='Ex.: 1000/26',
        disabled=d['modo']=='REVISAO' or salvo,key=f'numero_{nonce}')
    st.caption(f"Revisão {d['revisao']} • Vendedor: {st.session_state.get('nome') or '-'}")
    render_cliente(d,nonce)
    opcoes = obter_opcoes_comerciais()
    st.subheader('Condições comerciais')
    cols = st.columns(3)
    for col,(campo,titulo,tipo) in zip(cols,[('validade_proposta','Validade','VALIDADE'),('condicao_pagamento','Pagamento','PAGAMENTO'),('frete','Frete','FRETE')]):
        escolhas = list(opcoes[tipo])
        atual = d['condicoes'][campo]
        if atual not in escolhas:
            escolhas.append(atual)
        widget_key = f'orc_{campo}_{nonce}'
        if widget_key not in st.session_state:
            st.session_state[widget_key] = atual
        d['condicoes'][campo] = col.selectbox(titulo,escolhas,disabled=salvo,key=widget_key)
    st.subheader('Itens do orçamento')
    total = 0
    for indice,item in enumerate(d['itens']):
        valor_total = item['quantidade']*float(item['valor_unitario']);total+=valor_total
        with st.container(border=True):
            st.write(f"**{indice+1:02d} • {item['codigo']}** | {item.get('tensao')} | Qtd. {item['quantidade']} | Unitário {formatar_reais(float(item['valor_unitario']))} | Total {formatar_reais(valor_total)} | {item.get('prazo')}")
            if not salvo:
                c1,c2 = st.columns(2)
                if c1.button('Editar item',key=f'edit_{nonce}_{indice}'):
                    st.session_state['orc_edit_index'] = indice
                if c2.button('Excluir item',key=f'del_{nonce}_{indice}'):
                    d['itens'].pop(indice)
                    st.session_state.pop('orc_edit_index', None)
                    st.rerun()
                if st.session_state.get('orc_edit_index') == indice:
                    editar_item(indice)
            with st.expander('Detalhes do item'):
                st.write(item.get('descricao') or item.get('observacao') or 'Sem observação adicional.')
                if item.get('observacao'):
                    st.write('**Observação do item:**', item['observacao'])
                if item.get('_erro_tecnico'):
                    st.warning(item['_erro_tecnico'])
                v = item.get('variaveis') or {}
                cols = st.columns(3)
                for n,(chave,titulo) in enumerate([
                    ('V01','Tipo'),('V02','Operação'),('V03','Vias'),('V04','Posição'),
                    ('V05','Corpo'),('V06','Vedação'),('V07','Conexão / tamanhos'),
                    ('V08','Rosca'),('V09','Orifício'),('V10','Pressão mínima'),
                    ('V11','Pressão máxima'),('V12','Temperatura'),('V14','Potência'),('V16','Kv')]):
                    if v.get(chave):
                        cols[n%3].write(f"**{titulo}:** {v[chave]}")
                for chave,titulo in [('V20','Torre'),('V21','Diafragma'),('V22','Pistão'),('V23','Carretel'),('V24','O-rings')]:
                    if v.get(chave):
                        st.write(f"**{titulo}:** "+', '.join(v[chave]))
                if v.get('V17'):
                    url_imagem = obter_url_imagem(v['V17'])
                    if url_imagem:
                        st.image(url_imagem,width=250)
    st.metric('Total do orçamento',formatar_reais(total))
    if not salvo:
        st.markdown('### Adicionar item')
        # Os seletores ficam fora do formulário para OUTRO abrir sem enviar o item.
        c1,c2 = st.columns(2)
        tensao_sel = c1.selectbox('Tensão',OPCOES_TENSAO,index=None,key='orc_tensao')
        prazo_sel = c2.selectbox('Prazo',OPCOES_PRAZO,index=None,key='orc_prazo')
        tensao_outro = st.text_input('Outra tensão',key='orc_tensao_outro') if tensao_sel=='OUTRO' else ''
        prazo_outro = st.text_input('Outro prazo',key='orc_prazo_outro') if prazo_sel=='OUTRO' else ''
        with st.form(f'adicionar_{nonce}',clear_on_submit=False):
            c1,c2,c3 = st.columns([3.2,1,1.7])
            codigo = c1.text_input('Código',key=f'add_codigo_{nonce}')
            quantidade = c2.text_input('Qtd.',key=f'add_qtd_{nonce}')
            valor = c3.text_input('Valor unit.',placeholder='0,00',key=f'add_valor_{nonce}')
            obs = st.text_input('Observação do item',key=f'add_obs_{nonce}')
            adicionar = st.form_submit_button('Adicionar item',type='primary')
        if adicionar:
            try:
                d['itens'].append(processar_item(codigo,tensao_outro if tensao_sel=='OUTRO' else tensao_sel or '',
                    quantidade,valor,prazo_outro if prazo_sel=='OUTRO' else prazo_sel or '',obs))
                st.session_state['orc_limpar_item'] = nonce
                st.rerun()
            except Exception as erro:
                st.error(str(erro))
    d['observacao'] = st.text_area('Observação da proposta',value=d['observacao'],disabled=salvo,key=f'obs_{nonce}')
    if not salvo and st.button('Salvar revisão' if d['modo']=='REVISAO' else 'Salvar orçamento',type='primary',use_container_width=True,disabled=st.session_state.get('orc_edit_index') is not None):
        try:
            if not d['cliente']:
                raise ValueError('Selecione um cliente ou confirme o primeiro contato.')
            if any(i.get('_erro_tecnico') for i in d['itens']):
                raise ValueError('Edite os itens cujo código não foi interpretado.')
            o = salvar_orcamento(d['numero'],d['cliente'],d['itens'],st.session_state.get('nome') or '-',
                d['observacao'],d['condicoes'],d['modo'],d['anterior_id'],d['origem_id'])
            d['salvo_id']=o['id'];d['revisao']=o['revisao'];st.rerun()
        except Exception as erro:
            st.error(str(erro))
    if d.get('salvo_id'):
        st.success(f"Orçamento {d['numero']} • revisão {d['revisao']} salvo.")
        o = carregar_orcamento(d['salvo_id'])
        botao_pdf(o,f'pdf_novo_{nonce}')
        st.caption('Para alterar uma versão salva, use Buscar orçamento → Revisar.')


def iniciar_revisao(o):
    try:
        ultimas = buscar_orcamentos(o['numero_orcamento'],'Número do orçamento')
        if not ultimas:
            raise ValueError('Orçamento não encontrado.')
        carregar_para_edicao(carregar_orcamento(ultimas[0]['id']),'REVISAO')
    except Exception as erro:
        st.session_state['orc_erro_callback'] = str(erro)


def pagina_buscar():
    st.title('🔎 Buscar orçamento')
    with st.form('buscar_orc'):
        modo = st.selectbox('Buscar por',['Número do orçamento','Código do cliente','CNPJ','Nome da empresa'])
        termo = st.text_input('Pesquisa',placeholder='Informe o número completo, código, CNPJ ou empresa')
        buscar = st.form_submit_button('Buscar')
    if buscar:
        st.session_state['orc_resultados'] = buscar_orcamentos(termo,modo)
        st.session_state.pop('orc_consulta_id',None)
    resultados = st.session_state.get('orc_resultados')
    if resultados is None:
        return
    if not resultados:
        st.info('Nenhum orçamento encontrado.');return
    st.caption(f'{len(resultados)} versão(ões) encontrada(s).')
    escolha = st.selectbox('Orçamentos e revisões',range(len(resultados)),
        format_func=lambda i:f"{resultados[i]['numero_orcamento']} • revisão {resultados[i].get('revisao') or 0} • {resultados[i].get('data_proposta') or ''} • {resultados[i].get('criado_por') or ''}",key='orc_escolha_resultado')
    if st.button('Abrir orçamento'):
        st.session_state['orc_consulta_id'] = resultados[escolha]['id']
    if not st.session_state.get('orc_consulta_id'):
        return
    o = carregar_orcamento(st.session_state['orc_consulta_id'])
    cliente = o['cliente']
    st.subheader(f"{o['numero_orcamento']} • revisão {o.get('revisao') or 0}")
    st.write(f"**Cliente:** {cliente.get('razao_social') or cliente.get('nome_fantasia')} | **Código:** {cliente.get('codigo_cliente')} | **CNPJ:** {cliente.get('cnpj_cpf')}")
    st.write(f"**Data:** {o.get('data_proposta')} | **Vendedor:** {o.get('criado_por')}")
    st.dataframe([{k:i.get(k) for k in ('ordem','codigo','tensao','quantidade','valor_unitario','prazo','observacao')} for i in o['itens']],hide_index=True,use_container_width=True)
    st.write('**Observação:**',o.get('observacao_geral') or '-')
    st.write('**Condições:**', ' | '.join(str(o.get(k) or v) for k,v in PADROES.items()))
    if any(not o.get(k) for k in PADROES):
        st.caption('Registro anterior à configuração comercial: campos sem valor usam os padrões atuais ao gerar o PDF.')
    c1,c2,c3 = st.columns(3)
    pode_editar = st.session_state.get('setor') in ('VENDAS','ADMINISTRADOR','MONTAGEM')
    c1.button('Revisar',use_container_width=True,disabled=not pode_editar,on_click=iniciar_revisao,args=(o,))
    c2.button('Duplicar',use_container_width=True,disabled=not pode_editar,on_click=carregar_para_edicao,args=(o,'DUPLICADO'))
    c3.button('Criar similar',use_container_width=True,disabled=not pode_editar,on_click=carregar_para_edicao,args=(o,'SIMILAR'))
    botao_pdf(o,f"pdf_consulta_{o['id']}")


def pagina_orcamentos():
    if 'orc_draft' not in st.session_state:
        st.session_state['orc_draft'] = novo_rascunho()
        st.session_state['orc_nonce'] = 1
    limpar = st.session_state.pop('orc_limpar_item',None)
    if limpar is not None:
        for campo in ('codigo','qtd','valor','obs'):
            st.session_state[f'add_{campo}_{limpar}'] = ''
    erro_callback = st.session_state.pop('orc_erro_callback',None)
    if erro_callback:
        st.error(erro_callback)
    try:
        if st.session_state.get('orc_nav','Novo orçamento') == 'Buscar orçamento':
            pagina_buscar()
        elif st.session_state.get('setor') in ('VENDAS','ADMINISTRADOR','MONTAGEM'):
            pagina_novo()
        else:
            st.info('Use Buscar orçamento para consultar as propostas.')
    except Exception as erro:
        st.error(f'Não foi possível carregar os dados do orçamento: {erro}')


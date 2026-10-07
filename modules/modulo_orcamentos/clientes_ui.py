import streamlit as st
from modules.modulo_orcamentos.clientes_repository import buscar_clientes, salvar_condicoes_cliente
from modules.modulo_orcamentos.orcamentos_repository import obter_cliente, obter_opcoes_comerciais, TIPOS_PRIMEIRO_CONTATO
from modules.modulo_orcamentos.contatos_repository import listar_compradores
from modules.modulo_orcamentos.contatos_ui import formulario_comprador


def pagina_clientes():
    st.title('👥 Clientes')
    try:
        with st.form('clientes_busca'):
            termo = st.text_input('Buscar cliente', placeholder='Código, empresa ou CNPJ')
            buscar = st.form_submit_button('Buscar cliente')
        if buscar:
            resultados = buscar_clientes(termo)
            st.session_state['clientes_resultados'] = resultados
            st.session_state.pop('clientes_aberto', None)
            st.session_state.pop('clientes_escolha', None)
            exatos = [c for c in resultados if str(c['codigo_cliente']) == termo.strip()]
            if len(exatos) == 1:
                st.session_state['clientes_aberto'] = exatos[0]['id']
        resultados = st.session_state.get('clientes_resultados') or []
        if resultados:
            escolha = st.selectbox('Clientes encontrados', range(len(resultados)), index=None,
                format_func=lambda i: f"{resultados[i]['codigo_cliente']} | {resultados[i].get('razao_social') or resultados[i].get('nome_fantasia')} | {resultados[i].get('cnpj_cpf') or ''}",key='clientes_escolha')
            if escolha is not None and st.button('Abrir cliente'):
                st.session_state['clientes_aberto'] = resultados[escolha]['id']
        elif buscar:
            st.info('Nenhum cliente encontrado.')
        cliente_id = st.session_state.get('clientes_aberto')
        if not cliente_id:
            return
        c = obter_cliente(cliente_id)
        if not c:
            st.info('Cliente não encontrado.'); return
        st.subheader(c.get('razao_social') or c.get('nome_fantasia') or 'Cliente')
        st.write(f"**Código:** {c.get('codigo_cliente')} | **CNPJ/CPF:** {c.get('cnpj_cpf')} | **Tipo:** {c.get('tipo_cliente')}")
        if str(c.get('codigo_cliente')) in TIPOS_PRIMEIRO_CONTATO:
            st.info('Este é um código de primeiro contato. Os dados de cada empresa são preenchidos no orçamento.'); return
        pode_editar = st.session_state.get('setor') in ('ADMINISTRADOR','VENDAS','MONTAGEM')
        st.subheader('Condições especiais')
        st.caption('Usar padrão aplica 3 dias de validade, 28 dias de pagamento e frete FOB. O orçamento permite alterar essas escolhas.')
        opcoes = obter_opcoes_comerciais()
        with st.form(f'condicoes_cliente_{cliente_id}'):
            valores = []
            cols = st.columns(3)
            for col, (campo,titulo,categoria) in zip(cols,[('validade_especial','Validade','VALIDADE'),('pagamento_especial','Pagamento','PAGAMENTO'),('frete_especial','Frete','FRETE')]):
                escolhas = ['Usar padrão'] + opcoes[categoria]
                atual = c.get(campo) or 'Usar padrão'
                if atual not in escolhas:
                    escolhas.append(atual)
                escolha_comercial = col.selectbox(titulo, escolhas,index=escolhas.index(atual),disabled=not pode_editar)
                valores.append(None if escolha_comercial == 'Usar padrão' else escolha_comercial)
            salvar = st.form_submit_button('Salvar condições especiais',disabled=not pode_editar)
        if salvar:
            salvar_condicoes_cliente(cliente_id,*valores)
            st.success('Condições especiais salvas. Serão aplicadas ao selecionar este cliente em novos orçamentos.')
        st.subheader('Compradores')
        contatos = listar_compradores(cliente_id,apenas_ativos=False)
        if contatos:
            st.dataframe([{'Nome':r['nome'],'WhatsApp':r.get('whatsapp') or '', 'E-mail':r.get('email') or '', 'Ativo':r['ativo']} for r in contatos],hide_index=True,use_container_width=True)
        else:
            st.info('Nenhum comprador cadastrado.')
        if pode_editar:
            with st.expander('Cadastrar comprador'):
                n = st.session_state.get('clientes_contato_nonce',0)
                novo = formulario_comprador(cliente_id,f'comprador_cliente_{cliente_id}_{n}')
                if novo:
                    st.session_state['clientes_contato_nonce'] = n+1
                    st.session_state['clientes_msg'] = 'Comprador cadastrado.'
                    st.rerun()
            if contatos:
                escolhido = st.selectbox('Editar comprador',range(len(contatos)),index=None,
                    format_func=lambda i:contatos[i]['nome']+(' (inativo)' if not contatos[i]['ativo'] else ''),key=f'cliente_contato_editar_{cliente_id}')
                if escolhido is not None:
                    row = contatos[escolhido]
                    versao = st.session_state.get('clientes_edicao_nonce',0)
                    editado = formulario_comprador(cliente_id,f'editar_comprador_{row["id"]}_{versao}',row)
                    if editado:
                        st.session_state['clientes_edicao_nonce'] = versao+1
                        st.session_state['clientes_msg'] = 'Comprador atualizado. Os vínculos dos orçamentos foram preservados.'
                        st.rerun()
        msg = st.session_state.pop('clientes_msg',None)
        if msg:
            st.success(msg)
    except Exception as erro:
        st.error(f'Não foi possível carregar ou salvar os dados do cliente: {erro}')

"""Consulta e persistência de orçamentos; salvamento transacional via RPC."""
import re
from decimal import Decimal, InvalidOperation
from core.database import supabase

TIPOS_PRIMEIRO_CONTATO = {
    '184': 'Revenda', '251': 'Consumidor final', '350': 'Manutenção',
    '620': 'Engenharia e projetos', '840': 'Fabricante',
}
PADROES = {'validade_proposta': '3 dias', 'condicao_pagamento': '28 dias', 'frete': 'FOB'}


def normalizar_documento(valor):
    return re.sub(r'[^A-Za-z0-9]', '', str(valor or '')).upper()


def obter_opcoes_comerciais():
    rows = supabase.table('orcamento_opcoes_comerciais').select('*').eq('ativo', True).order('ordem').execute().data or []
    return {tipo: [r['valor'] for r in rows if r['categoria'] == tipo]
            for tipo in ('VALIDADE', 'PAGAMENTO', 'FRETE')}


def obter_cliente(cliente_id):
    rows = supabase.table('clientes').select('*').eq('id', cliente_id).limit(1).execute().data or []
    return rows[0] if rows else None


def buscar_primeiro_contato(cnpj):
    rows = supabase.table('primeiros_contatos').select('*').eq(
        'cnpj_normalizado', normalizar_documento(cnpj)).limit(1).execute().data or []
    return rows[0] if rows else None


def salvar_primeiro_contato(cnpj, empresa, tipo, canal, contato, usuario, nome_contato=''):
    documento = normalizar_documento(cnpj)
    if len(documento) != 14 or not empresa.strip() or not contato.strip():
        raise ValueError('Informe CNPJ com 14 caracteres, empresa e contato.')
    anterior = buscar_primeiro_contato(documento)
    dados = {'cnpj': documento, 'nome_empresa': empresa.strip(), 'tipo_cliente': tipo,
             'canal_contato': canal, 'endereco_contato': contato.strip(),
             'nome_contato': (nome_contato or '').strip() or None}
    if anterior:
        from datetime import datetime, timezone
        dados['atualizado_em'] = datetime.now(timezone.utc).isoformat()
        rows = supabase.table('primeiros_contatos').update(dados).eq('id', anterior['id']).execute().data
    else:
        dados['criado_por'] = usuario
        rows = supabase.table('primeiros_contatos').insert(dados).execute().data
    if not rows:
        raise ValueError('Não foi possível confirmar o primeiro contato.')
    return rows[0]


def cliente_do_contato(contato, codigo):
    doc = normalizar_documento(contato['cnpj'])
    cnpj = f'{doc[:2]}.{doc[2:5]}.{doc[5:8]}/{doc[8:12]}-{doc[12:]}' if len(doc) == 14 else doc
    return {'id': None, 'primeiro_contato_id': contato['id'], 'codigo_cliente': codigo,
            'razao_social': contato['nome_empresa'], 'cnpj_cpf': cnpj,
            'tipo_cliente': contato['tipo_cliente'], 'canal_contato': contato['canal_contato'],
            'endereco_contato': contato['endereco_contato'],
            'nome_contato': contato.get('nome_contato')}


def cliente_do_orcamento(orcamento):
    if orcamento.get('primeiro_contato_id'):
        rows = supabase.table('primeiros_contatos').select('*').eq(
            'id', orcamento['primeiro_contato_id']).limit(1).execute().data or []
        if rows:
            return cliente_do_contato(rows[0], orcamento.get('codigo_cliente'))
        raise ValueError('Primeiro contato não encontrado.')
    if orcamento.get('cliente_id'):
        cliente = obter_cliente(orcamento['cliente_id'])
        if cliente:
            return cliente
        raise ValueError('Cadastro do cliente não encontrado.')
    # Compatibilidade com registros antigos sem vínculo.
    return {k: orcamento.get(k) for k in ('codigo_cliente', 'razao_social',
        'nome_fantasia', 'cnpj_cpf', 'tipo_cliente', 'cidade', 'estado', 'email')}


def carregar_orcamento(orcamento_id):
    rows = supabase.table('orcamentos').select('*').eq('id', orcamento_id).limit(1).execute().data or []
    if not rows:
        raise ValueError('Orçamento não encontrado.')
    o = rows[0]
    o['cliente'] = cliente_do_orcamento(o)
    o['itens'] = supabase.table('orcamento_itens').select('*').eq(
        'orcamento_id', o['id']).order('ordem').execute().data or []
    return o


def consultar_todas_versoes(filtro):
    resultado = []
    inicio = 0
    while True:
        pagina = filtro(supabase.table('orcamentos').select('*')).order('criado_em', desc=True).range(inicio, inicio+499).execute().data or []
        resultado.extend(pagina)
        if len(pagina) < 500:
            return resultado
        inicio += 500


def buscar_orcamentos(termo, modo):
    termo = str(termo or '').strip()
    if not termo:
        return []
    if modo == 'Número do orçamento':
        rows = supabase.table('orcamentos').select('*').eq('numero_orcamento', termo).order('revisao', desc=True).execute().data or []
    else:
        campo = 'codigo_cliente' if modo == 'Código do cliente' else 'razao_social'
        clientes_query = supabase.table('clientes').select('id')
        contatos_query = supabase.table('primeiros_contatos').select('id')
        if modo == 'CNPJ':
            documento = normalizar_documento(termo)
            # Inclui cadastros com documento armazenado com ou sem pontuação.
            mascarado = documento
            if len(documento) == 14:
                mascarado = f'{documento[:2]}.{documento[2:5]}.{documento[5:8]}/{documento[8:12]}-{documento[12:]}'
            clientes_query = clientes_query.in_('cnpj_cpf', list({documento, mascarado}))
            contatos_query = contatos_query.eq('cnpj_normalizado', documento)
        elif modo == 'Código do cliente':
            clientes_query = clientes_query.eq('codigo_cliente', termo)
            contatos_query = None
        else:
            clientes_query = clientes_query.ilike('razao_social', f'%{termo}%')
            contatos_query = contatos_query.ilike('nome_empresa', f'%{termo}%')
        clientes = clientes_query.limit(200).execute().data or []
        if modo == 'Nome da empresa':
            clientes += supabase.table('clientes').select('id').ilike('nome_fantasia', f'%{termo}%').limit(200).execute().data or []
        contatos = contatos_query.limit(200).execute().data or [] if contatos_query is not None else []
        encontrados = []
        if clientes:
            encontrados += consultar_todas_versoes(lambda q: q.in_('cliente_id', [r['id'] for r in clientes]))
        if contatos:
            encontrados += consultar_todas_versoes(lambda q: q.in_('primeiro_contato_id', [r['id'] for r in contatos]))
        # Código especial retorna orçamentos de todos os primeiros contatos desse código.
        if modo == 'Código do cliente':
            encontrados += consultar_todas_versoes(lambda q: q.eq('codigo_cliente', termo))
        # Recupera também dados antigos, caso ainda não tenham vínculo.
        if modo == 'Nome da empresa':
            encontrados += consultar_todas_versoes(lambda q: q.ilike('razao_social', f'%{termo}%'))
        rows = list({r['id']: r for r in encontrados}.values())
        rows.sort(key=lambda r: (r.get('criado_em') or '', r.get('revisao') or 0), reverse=True)
    return rows


def salvar_orcamento(numero_orcamento, cliente, itens, criado_por,
                     observacao_geral='', condicoes=None, modo='NOVO',
                     revisao_anterior_id=None, origem_id=None):
    condicoes = condicoes or PADROES
    dados = {'numero_orcamento': numero_orcamento.strip(), 'cliente_id': cliente.get('id'),
             'codigo_cliente': cliente.get('codigo_cliente'),
             'primeiro_contato_id': cliente.get('primeiro_contato_id'),
             'criado_por': criado_por, 'observacao_geral': observacao_geral.strip(),
             'tipo_criacao': modo, 'revisao_anterior_id': revisao_anterior_id,
             'orcamento_origem_id': origem_id, **condicoes}
    valores = []
    for item in itens:
        try:
            preco = Decimal(str(item['valor_unitario'])).quantize(Decimal('0.01'))
        except InvalidOperation:
            raise ValueError('Preço inválido.')
        if not preco.is_finite():
            raise ValueError('Preço inválido.')
        valores.append({**{k: item.get(k) for k in ('codigo', 'tensao', 'quantidade', 'prazo', 'observacao')},
                        'valor_unitario': str(preco)})
    try:
        resposta = supabase.rpc('salvar_orcamento_app', {'p_dados': dados, 'p_itens': valores}).execute()
    except Exception as erro:
        if 'PGRST202' in str(erro) or 'schema cache' in str(erro):
            raise ValueError('Execute primeiro o SQL sql/02_salvamento_orcamentos.sql do GitHub no Supabase.') from erro
        raise
    if not resposta.data:
        raise ValueError('O banco não confirmou o salvamento.')
    return resposta.data


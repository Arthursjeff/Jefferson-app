from core.database import supabase


def listar_compradores(cliente_id, apenas_ativos=True):
    query = supabase.table('contatos_clientes').select('*').eq('cliente_id', cliente_id)
    if apenas_ativos:
        query = query.eq('ativo', True)
    return query.order('nome').execute().data or []


def obter_comprador(contato_id):
    if not contato_id:
        return None
    rows = supabase.table('contatos_clientes').select('*').eq('id', contato_id).limit(1).execute().data or []
    return rows[0] if rows else None


def salvar_comprador(cliente_id, nome, whatsapp, email, contato_id=None, ativo=True):
    nome, whatsapp, email = nome.strip(), whatsapp.strip(), email.strip()
    if not nome or not (whatsapp or email):
        raise ValueError('Informe o nome do comprador e pelo menos WhatsApp ou e-mail.')
    dados = {'nome': nome, 'whatsapp': whatsapp or None, 'email': email or None, 'ativo': bool(ativo)}
    if contato_id:
        rows = supabase.table('contatos_clientes').update(dados).eq('id', contato_id).eq('cliente_id', cliente_id).execute().data or []
    else:
        rows = supabase.table('contatos_clientes').insert({**dados, 'cliente_id': cliente_id}).execute().data or []
    if not rows:
        raise ValueError('Não foi possível salvar o comprador desse cliente.')
    return rows[0]

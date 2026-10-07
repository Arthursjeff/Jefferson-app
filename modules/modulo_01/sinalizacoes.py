"""Sinalizações de fila calculadas por etapa e persistidas no histórico existente."""
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from core.database import supabase
from core.pedidos import registrar_movimentacao

FUSO = ZoneInfo('America/Sao_Paulo')
TIPOS = ['CRIACAO', 'MOVIMENTACAO', 'JUSTIFICATIVA_MONTADOS', 'ANTECIPACAO_PROGRAMADO']


def instante(valor):
    try:
        data = datetime.fromisoformat(str(valor).replace('Z', '+00:00'))
        return data.replace(tzinfo=FUSO) if data.tzinfo is None else data.astimezone(FUSO)
    except (TypeError, ValueError):
        return None


def somar_dias_uteis(inicio, quantidade):
    data = inicio
    while quantidade:
        data += timedelta(days=1)
        if data.weekday() < 5:
            quantidade -= 1
    return data


def dia_util_anterior(valor):
    data = instante(valor)
    if not data:
        return None
    dia = data.date() - timedelta(days=1)
    while dia.weekday() >= 5:
        dia -= timedelta(days=1)
    return dia


def dados_evento(evento):
    try:
        dados = json.loads(evento.get('observacao') or '{}')
        return dados if isinstance(dados, dict) else {}
    except (ValueError, TypeError):
        return {}


def calcular_sinalizacao(pedido, eventos, agora=None):
    agora = agora or datetime.now(FUSO)
    estado = pedido.get('setor_atual')
    movimentos = [e for e in eventos if e.get('tipo_evento') in ('MOVIMENTACAO','CRIACAO')
                  and e.get('destino') == estado and e.get('origem') != estado and instante(e.get('criado_em'))]
    entrada = max(movimentos, key=lambda e:(instante(e['criado_em']),e['id']), default=None)
    resultado = {'entrada_id': entrada['id'] if entrada else None, 'montados_atrasado': False,
                 'justificativa': None, 'programado_sinalizado': False, 'antecipado': False}
    if estado == 'MONTADOS' and entrada:
        limite = somar_dias_uteis(instante(entrada['criado_em']),3)
        resultado['montados_limite'] = limite
        resultado['montados_atrasado'] = agora >= limite
        justificativas = [e for e in eventos if e.get('tipo_evento') == 'JUSTIFICATIVA_MONTADOS'
                         and dados_evento(e).get('entrada_id') == entrada['id']
                         and str(dados_evento(e).get('texto') or '').strip()]
        if justificativas:
            resultado['justificativa'] = max(justificativas,key=lambda e:(instante(e['criado_em']),e['id']))
    if estado == 'PROGRAMADO':
        anterior = dia_util_anterior(pedido.get('data_prevista_faturamento'))
        resultado['programado_automatico'] = anterior is not None and agora.date() >= anterior
        resultado['antecipado'] = bool(entrada and any(e.get('tipo_evento') == 'ANTECIPACAO_PROGRAMADO'
            and dados_evento(e).get('entrada_id') == entrada['id'] for e in eventos))
        resultado['programado_sinalizado'] = resultado['programado_automatico'] or resultado['antecipado']
    return resultado


def obter_eventos(pedidos):
    ids = [p['id'] for p in pedidos if p.get('setor_atual') in ('MONTADOS','PROGRAMADO')]
    mapa = {}
    for inicio in range(0,len(ids),100):
        lote = ids[inicio:inicio+100]
        pagina = 0
        while True:
            rows = supabase.table('fila_movimentacoes').select('*').in_('pedido_id',lote).in_('tipo_evento',TIPOS).order('criado_em',desc=True).order('id',desc=True).range(pagina,pagina+499).execute().data or []
            for evento in rows:
                mapa.setdefault(evento['pedido_id'],[]).append(evento)
            if len(rows)<500:
                break
            pagina += 500
    return mapa


def enriquecer_pedidos(pedidos, agora=None):
    eventos = obter_eventos(pedidos)
    agora = agora or datetime.now(FUSO)
    return [dict(p, _sinalizacao=calcular_sinalizacao(p,eventos.get(p['id'],[]),agora)) for p in pedidos]


def registrar_sinalizacao(pedido_id, entrada_id, usuario, setor, tipo, texto=''):
    if setor not in ('VENDAS','ADMINISTRADOR'):
        return False, 'Somente Comercial/Vendas ou Administrador pode realizar esta ação.'
    if tipo not in ('JUSTIFICATIVA_MONTADOS','ANTECIPACAO_PROGRAMADO'):
        return False, 'Ação inválida.'
    estado = 'MONTADOS' if tipo == 'JUSTIFICATIVA_MONTADOS' else 'PROGRAMADO'
    if tipo == 'JUSTIFICATIVA_MONTADOS' and not texto.strip():
        return False, 'Preencha a justificativa.'
    rows = supabase.table('fila_pedidos').select('*').eq('id',pedido_id).eq('status','ATIVO').eq('setor_atual',estado).limit(1).execute().data or []
    if not rows:
        return False, 'O pedido não está mais nesta etapa. Atualize a fila.'
    sinal = enriquecer_pedidos(rows)[0]['_sinalizacao']
    if entrada_id is None or sinal['entrada_id'] != entrada_id:
        return False, 'A entrada nesta etapa mudou ou não tem histórico. Atualize a fila.'
    if tipo == 'JUSTIFICATIVA_MONTADOS' and not sinal['montados_atrasado']:
        return False, 'O pedido ainda não completou três dias úteis em Montados.'
    if (tipo == 'JUSTIFICATIVA_MONTADOS' and sinal['justificativa']) or (tipo == 'ANTECIPACAO_PROGRAMADO' and sinal['antecipado']):
        return True, 'A sinalização já foi registrada.'
    evento = registrar_movimentacao(pedido_id=pedido_id,origem=estado,destino=estado,usuario=usuario,
        tipo_evento=tipo,observacao=json.dumps({'entrada_id':entrada_id,'texto':texto.strip()},ensure_ascii=False))
    return (True,'Justificativa salva.' if tipo == 'JUSTIFICATIVA_MONTADOS' else 'Pedido sinalizado para faturamento antecipado.') if evento else (False,'Não foi possível salvar a sinalização.')

#!/usr/bin/env python3
"""Leitor PRN V5 (prévia auditável, SEM escrita no Supabase).
Uso: python leitor_prn_v5.py entrada.prn --saida pasta
Saídas CSV: documentos_comerciais, conjuntos_itens, itens_comerciais, auditoria.
"""
import argparse, csv, hashlib, json, re
from pathlib import Path
from decimal import Decimal, InvalidOperation
from collections import Counter, defaultdict

NUM = r'-?\d[\d.]*,\d+'
HEADER = re.compile(r'^\s*(?P<numero>\d{1,6}/\d{2})\s+(?P<status>[CFEP])\s+(?P<d1>\d{2}/\d{2}/\d{4})(?:\s+(?P<d2>\d{2}/\d{2}/\d{4}))?\s+(?P<resto>.+)$', re.I)
ITEM_START = re.compile(r'^\s*(?P<erp>[A-Z0-9][A-Z0-9\-./]*)\s+Grade\s*:\s*(?P<resto>.*)$',re.I)
ITEM_END = re.compile(r'(?P<qtd>'+NUM+r')\s*\((?P<unidade>[^)]*)\)\s*[xX×]\s*(?P<unit>'+NUM+r')\s*=\s*(?P<total>'+NUM+r')\s*$',re.I)
MONEY = re.compile(r'(?<!\S)'+NUM+r'(?!\S)')
NF = re.compile(r'\bNF\s*[-:]?\s*\d+\b',re.I)
TECH = re.compile(r'(?<![A-Z0-9])(?P<code>(?:ZC?|)?\s*\d{4}\s*[A-Z][A-Z0-9\-./]*)(?![A-Z0-9])',re.I)
GRADE = re.compile(r'^\s*(?P<tensao>(?:\d{1,4}(?:/\d{1,3})?(?:\s*V(?:CC|CA|DC|AC))?))\s*-\s*(?=Z?\s*\d{4}|\S)',re.I)
SKIP = re.compile(r'^\s*(?:PEDIDO\s+DATA|JEFFERSON SOLENOIDBRAS|Lista dos pedidos|WP-40|\d\d/\d\d/\d{4}\s+\d\d:\d\d:\d\d\s+Pag:|[-_=]+\s*$)',re.I)

def dec(v):
    try:return Decimal(v.replace('.','').replace(',','.'))
    except (InvalidOperation,AttributeError):return None

def fmt(v):return format(v,'f') if v is not None else ''

def read_lines(p):
    raw=p.read_bytes()
    for encoding in ('cp1252','latin1'):
        try:return raw.decode(encoding).splitlines()
        except UnicodeDecodeError:pass
    return raw.decode('latin1',errors='replace').splitlines()

def parse_header(m, source, line):
    rest=m['resto']; nf=NF.search(rest)
    # Financial columns follow customer name (and optional NF).
    money=list(MONEY.finditer(rest))
    if not money:return None,'Cabeçalho sem valor financeiro reconhecível'
    first=money[0]
    customer=rest[:first.start()]
    if nf and nf.start()<first.start():customer=customer[:nf.start()]
    customer=customer.strip()
    if not customer:return None,'Cabeçalho sem cliente'
    total=dec(first.group())
    key=f'PRN:{m["numero"].upper()}'
    return {'chave_importacao':key,'numero_documento':m['numero'],'tipo_documento':'PEDIDO_HISTORICO',
            'situacao_erp':m['status'].upper(),'data_original':m['d1'],
            'data_faturamento':m['d2'] or '', 'cliente_nome_original':customer,
            'nota_fiscal':nf.group().replace(' ','') if nf else '',
            'valor_cabecalho':fmt(total),'arquivo_origem':source,'linha_origem':line,
            'conjunto_chave':key+':R0','revisao_itens':0},None

def parse_item(text, document_key, position, source, line):
    start=ITEM_START.match(text)
    if not start:return None,'Item sem padrão Grade:'
    end=ITEM_END.search(start['resto'])
    if not end:return None,'Item sem quantidade/unidade/preço/total completos'
    desc=start['resto'][:end.start()].strip()
    g=GRADE.match(desc)
    tensao=g['tensao'].strip() if g else ''
    desc2=desc[g.end():].strip() if g else desc
    tech=TECH.search(desc2)
    code=re.sub(r'\s+','',tech['code']).upper() if tech else ''
    qtd,unit,total=[dec(end[x]) for x in ('qtd','unit','total')]
    if None in (qtd,unit,total):return None,'Valor numérico inválido'
    item={'conjunto_chave':document_key+':R0','ordem':position,'codigo_erp':start['erp'].upper(),
          'codigo_tecnico':code,'familia':re.search(r'\d{4}',code).group() if re.search(r'\d{4}',code) else '',
          'tensao':tensao,'descricao_original':desc,'quantidade':fmt(qtd),
          'unidade':end['unidade'].strip().replace('ﾇ','Ç'),
          'valor_unitario':fmt(unit),'valor_total':fmt(total),
          'peso_unitario':'','arquivo_origem':source,'linha_origem':line,'texto_original':text.strip()}
    return item,None

def write_csv(path, rows, columns):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore',delimiter=';');w.writeheader();w.writerows(rows)

def run(input_path, output_dir):
    source=input_path.name; lines=read_lines(input_path)
    documents=[]; items=[]; issues=[]; counts=Counter(); current=None; pending=None
    def issue(line, kind, text, key=None):
        issues.append({'arquivo':source,'linha':line,'documento':key or (current or {}).get('chave_importacao',''),
                       'tipo':kind,'texto_original':text[:2000]})
    def finish_pending():
        nonlocal pending
        if pending:
            text,line=pending
            item,error=parse_item(text,current['chave_importacao'] if current else '',counts['pos'],source,line)
            if error:issue(line,error,text)
            elif current:
                items.append(item)
                counts['pos']+=1
                if not item['codigo_tecnico']:issue(line,'Código técnico não reconhecido',text)
                if Decimal(item['quantidade'])*Decimal(item['valor_unitario'])-Decimal(item['valor_total']) > Decimal('0.02') or Decimal(item['valor_total'])-Decimal(item['quantidade'])*Decimal(item['valor_unitario']) > Decimal('0.02'):
                    issue(line,'Diferença quantidade x valor unitário',text)
            else:issue(line,'Item sem documento',text)
            pending=None
    for idx,raw in enumerate(lines,1):
        counts['linhas']+=1
        line=raw.replace('\xa0',' ').replace('ﾇ','Ç').rstrip()
        m=HEADER.match(line)
        if m:
            finish_pending()
            doc,error=parse_header(m,source,idx)
            if error:issue(idx,error,line);current=None;continue
            current=doc;documents.append(doc);counts['pos']=1
            continue
        start=ITEM_START.match(line)
        if start:
            finish_pending()
            pending=(line,idx)
            if ITEM_END.search(start['resto']):finish_pending()
            continue
        if pending:
            if not line.strip() or SKIP.match(line):
                # Headers/page boundaries can occur between an item's lines.
                continue
            joined=pending[0]+' '+line.strip()
            if ITEM_END.search(joined):
                pending=(joined,pending[1]);finish_pending()
            elif len(joined)<1500:
                pending=(joined,pending[1])
            else:
                finish_pending()
            continue
        if ('Grade:' in line or re.search(r'\d+,\d+\s*\(',line)) and not SKIP.match(line):
            issue(idx,'Possível item não reconhecido',line)
    finish_pending()
    seen=set()
    for d in documents:
        key=d['chave_importacao']
        if key in seen:issue(d['linha_origem'],'Documento repetido no arquivo',key,key)
        seen.add(key)
    sums=defaultdict(lambda:Decimal(0)); nitems=Counter()
    for item in items:
        k=item['conjunto_chave'].removesuffix(':R0');sums[k]+=Decimal(item['valor_total']);nitems[k]+=1
    for d in documents:
        key=d['chave_importacao'];diff=Decimal(d['valor_cabecalho'])-sums[key]
        if nitems[key]==0:issue(d['linha_origem'],'Documento sem itens (preservado)',d['numero_documento'],key)
        elif abs(diff)>Decimal('0.02'):issue(d['linha_origem'],'Diferença total cabeçalho x soma itens',f'Cabeçalho={d["valor_cabecalho"]}; itens={fmt(sums[key])}; diferença={fmt(diff)}',key)
        d['quantidade_itens']=nitems[key];d['soma_itens']=fmt(sums[key]);d['diferenca']=fmt(diff)
    sets=[{'conjunto_chave':d['conjunto_chave'],'revisao':0,'documento_chave':d['chave_importacao'],
           'conjunto_anterior':'','quantidade_itens':d['quantidade_itens']} for d in documents]
    output_dir.mkdir(parents=True,exist_ok=True)
    write_csv(output_dir/'documentos_comerciais.csv',documents,list(documents[0]) if documents else ['chave_importacao'])
    write_csv(output_dir/'conjuntos_itens.csv',sets,list(sets[0]) if sets else ['conjunto_chave'])
    write_csv(output_dir/'itens_comerciais.csv',items,list(items[0]) if items else ['conjunto_chave'])
    write_csv(output_dir/'auditoria.csv',issues,['arquivo','linha','documento','tipo','texto_original'])
    report={'arquivo':source,'linhas_lidas':len(lines),'documentos':len(documents),'itens':len(items),
            'documentos_sem_itens':sum(not d['quantidade_itens'] for d in documents),
            'ocorrencias_auditoria':len(issues),'auditoria_por_tipo':dict(Counter(i['tipo'] for i in issues)),
            'total_cabecalhos':fmt(sum((Decimal(d['valor_cabecalho']) for d in documents),Decimal(0))),
            'total_itens':fmt(sum((Decimal(i['valor_total']) for i in items),Decimal(0)))}
    (output_dir/'resumo.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('arquivo',type=Path);p.add_argument('--saida',type=Path,default=Path('saida_v5'))
    a=p.parse_args();print(json.dumps(run(a.arquivo,a.saida),ensure_ascii=False,indent=2))
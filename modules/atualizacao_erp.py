"""Importação incremental de PRN ERP — exclusiva da Administração."""
import csv
import io
import json
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import pandas as pd
import streamlit as st
from core.database import supabase
from modules.leitor_prn_v5 import run

def _csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))

def _data(valor):
    return datetime.strptime(valor, "%d/%m/%Y").date().isoformat() if valor else None

def _num(valor):
    return Decimal(str(valor or "0"))

def _ident_item(i):
    return (str(i.get("codigo_erp") or "").strip().upper(),
            str(i.get("descricao_original") or "").strip(),
            str(i.get("tensao_original") or i.get("tensao") or "").strip(),
            _num(i.get("quantidade")), _num(i.get("preco_unitario") or i.get("valor_unitario")),
            _num(i.get("valor_total_item") or i.get("valor_total")))

def _igual(doc, antigo, itens, antigos):
    return (
        doc["situacao_erp"] == antigo.get("situacao_erp")
        and doc["data_documento"] == antigo.get("data_documento")
        and (doc["data_faturamento"] or None) == (antigo.get("data_faturamento") or None)
        and doc["cliente_nome_erp"].strip() == str(antigo.get("cliente_nome_erp") or "").strip()
        and (doc["nota_fiscal"] or "") == (antigo.get("nota_fiscal") or "")
        and _num(doc["valor_total_cabecalho"]) == _num(antigo.get("valor_total_cabecalho"))
        and Counter(_ident_item(i) for i in itens) == Counter(_ident_item(i) for i in antigos)
    )

def _lotes(valores, tamanho=40):
    for pos in range(0, len(valores), tamanho):
        yield valores[pos:pos+tamanho]

def _buscar(tabela, campo, valores, colunas="*"):
    saida=[]
    for lote in _lotes(list(valores)):
        offset=0
        while True:
            rows=(supabase.table(tabela).select(colunas).in_(campo,lote)
                  .order("id").range(offset,offset+999).execute().data or [])
            saida.extend(rows)
            if len(rows)<1000:break
            offset+=1000
    return saida

def preparar(arquivo):
    with tempfile.TemporaryDirectory() as tmp:
        entrada=Path(tmp)/Path(arquivo.name).name
        entrada.write_bytes(arquivo.getvalue())
        pasta=Path(tmp)/"saida"
        resumo=run(entrada,pasta)
        documentos=_csv(pasta/"documentos_comerciais.csv")
        itens=_csv(pasta/"itens_comerciais.csv")
        auditoria=_csv(pasta/"auditoria.csv")
    por_doc=defaultdict(list)
    for item in itens:
        por_doc[item["conjunto_chave"].removesuffix(":R0")].append(item)
    contagem=Counter(d["numero_documento"] for d in documentos)
    numeros=list(contagem)
    existentes={x["numero_erp"]:x for x in _buscar("documentos_comerciais","numero_erp",numeros)}
    itens_existentes=defaultdict(list)
    ids=[x["id"] for x in existentes.values()]
    if ids:
        for i in _buscar("itens_comerciais","documento_id",ids):
            itens_existentes[i["documento_id"]].append(i)
    problemas=defaultdict(list)
    for a in auditoria:
        if a.get("documento"):problemas[a["documento"]].append(a["tipo"])
    linhas=[]; payload=[]
    for d in documentos:
        chave=d["chave_importacao"]; numero=d["numero_documento"]
        its=por_doc.get(chave,[])
        doc={"chave_origem":chave,"numero_erp":numero,"situacao_erp":d["situacao_erp"],
             "data_documento":_data(d["data_original"]),"data_faturamento":_data(d["data_faturamento"]),
             "cliente_nome_erp":d["cliente_nome_original"],"nota_fiscal":d["nota_fiscal"],
             "valor_total_cabecalho":d["valor_cabecalho"],"valor_itens_calculado":d["soma_itens"],
             "arquivo_origem":d["arquivo_origem"],"linha_origem":d["linha_origem"]}
        novos=[{"codigo_erp":i["codigo_erp"],"descricao_original":i["descricao_original"],
                "codigo_tecnico_sugerido":i["codigo_tecnico"],"familia_sugerida":i["familia"],
                "tensao_original":i["tensao"],"quantidade":i["quantidade"],
                "unidade":i["unidade"],"preco_unitario":i["valor_unitario"],
                "valor_total_item":i["valor_total"],"linha_origem":i["linha_origem"],
                "linha_bruta":i["texto_original"]} for i in its]
        velho=existentes.get(numero)
        status="Novo" if not velho else "Atualizar"
        if velho and _igual(doc,velho,novos,itens_existentes[velho["id"]]):status="Igual"
        erro=problemas.get(chave,[])
        if contagem[numero]>1:erro.append("Número repetido no PRN")
        if not its:erro.append("Documento sem itens")
        if abs(_num(d["diferenca"]))>Decimal("0.02"):erro.append("Divergência de valores")
        if d["situacao_erp"] not in ("P","E","F"):erro.append("Situação não suportada")
        if velho and {"P":1,"E":2,"F":3}.get(velho.get("situacao_erp"),0)>{"P":1,"E":2,"F":3}.get(d["situacao_erp"],0):
            erro.append("Regressão de situação")
        if erro:status="Revisar"
        linhas.append({"Número ERP":numero,"Cliente":doc["cliente_nome_erp"],
                       "Situação ERP":doc["situacao_erp"],"Resultado":status,
                       "Itens":len(novos),"Valor (R$)":float(_num(doc["valor_total_cabecalho"])),
                       "Observações":"; ".join(sorted(set(erro)))})
        if status in ("Novo","Atualizar"):payload.append((doc,novos))
    return resumo,linhas,payload,auditoria

def pagina_atualizacao_erp():
    if st.session_state.get("setor")!="ADMINISTRADOR":
        st.error("Acesso exclusivo da Administração.")
        st.stop()
    st.title("Atualização ERP · PRN")
    st.caption("Conversor V5 · comparação por número completo do ERP · prévia antes da gravação.")
    arquivo=st.file_uploader("Arquivo PRN exportado do ERP",type=["prn"],key="prn_importador")
    if not arquivo:return
    assinatura=(arquivo.name,len(arquivo.getvalue()),__import__("hashlib").sha256(arquivo.getvalue()).hexdigest())
    if st.session_state.get("prn_assinatura")!=assinatura:
        st.session_state.pop("prn_previa",None)
        st.session_state["prn_assinatura"]=assinatura
    if st.button("Analisar PRN e comparar com Supabase",type="primary"):
        with st.spinner("Lendo PRN e comparando documentos e itens..."):
            try:st.session_state["prn_previa"]=preparar(arquivo)
            except Exception as exc:st.error(f"Falha na análise: {exc}")
    previa=st.session_state.get("prn_previa")
    if not previa:return
    resumo,linhas,payload,auditoria=previa
    cont=Counter(x["Resultado"] for x in linhas)
    cols=st.columns(4)
    for col,nome in zip(cols,["Novo","Atualizar","Igual","Revisar"]):
        col.metric(nome,cont[nome])
    st.dataframe(pd.DataFrame(linhas),use_container_width=True,hide_index=True)
    st.caption(f"Linhas PRN: {resumo['linhas_lidas']} | Documentos: {len(linhas)} | Ocorrências de auditoria: {len(auditoria)}")
    if auditoria:
        with st.expander("Auditoria do conversor V5"):
            st.dataframe(pd.DataFrame(auditoria),use_container_width=True)
    st.warning("Documentos com inconsistências ficam bloqueados. Atualizações preservam a versão anterior em histórico.")
    if not payload:
        st.info("Nenhum documento seguro para inserir ou atualizar.")
        return
    confirmado=st.checkbox(f"Confirmo a importação de {len(payload)} documentos novos ou alterados.",key="prn_confirmado")
    if st.button("Gravar no Supabase",disabled=not confirmado,type="primary"):
        feitos=Counter();falhas=[]
        barra=st.progress(0)
        for pos,(doc,its) in enumerate(payload,1):
            try:
                retorno=supabase.rpc("sincronizar_documento_prn",{"p_doc":doc,"p_itens":its}).execute()
                feitos[str(retorno.data)]+=1
            except Exception as exc:
                falhas.append({"Número ERP":doc["numero_erp"],"Erro":str(exc)})
            barra.progress(pos/len(payload))
        st.success(f"Processados: {sum(feitos.values())}. Falhas: {len(falhas)}.")
        if falhas:st.dataframe(pd.DataFrame(falhas),use_container_width=True)
        st.session_state.pop("prn_previa",None)
        st.cache_data.clear()
        st.info("Analise novamente o PRN para confirmar os registros atualizados.")

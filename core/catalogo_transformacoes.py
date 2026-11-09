"""Biblioteca técnica de transformações. Não executa nem reserva estoque."""
from datetime import datetime, timezone
import hashlib
import json

from core.database import supabase
from core.motor_transformacoes import normalizar

TABELA_POSSIBILIDADES = "transformacoes_possiveis"
# Tabelas de execução futura: estoque_operacoes, estoque_movimentacoes.
VERSAO_CATALOGO = "laboratorio-2026-11-v1"
CAMPOS_CONSULTA = (
    "id,grau,subtipo,produto_final,entradas,saidas,estado,"
    "total_validacoes,ultima_validacao_em,validada_por"
)


def preparar_receita(resultado, simulacao, usuario):
    """Mapeia a simulação A/B/C/D para as colunas EXISTENTES do Supabase."""
    tipo = resultado.get("tipo")
    grau = {"CORPO": "CORPO", "TORRE": "TORRE", "KIT": "KIT_REPARO"}.get(tipo)
    if not grau:
        raise ValueError("Tipo de transformação não aceito no catálogo.")
    subtipo = (
        "BSP_NPT" if grau == "CORPO" else
        "G1_INTEGRAL" if grau == "TORRE" else
        resultado.get("operacao")
    )
    if not subtipo:
        raise ValueError("Operação de kit não definida.")
    usuario = str(usuario or "").strip().lower()
    if not usuario:
        raise ValueError("Identifique o operador antes de validar a receita.")
    base = normalizar(simulacao.get("valvula_base"))
    doadora = normalizar(simulacao.get("valvula_doadora") or simulacao.get("origem"))
    final = normalizar(simulacao.get("produto_final"))
    residual = normalizar(simulacao.get("produto_residual"))
    if not all((base, doadora, final, residual)):
        raise ValueError("Receita incompleta: produto, base, doadora e residual são obrigatórios.")
    if final != normalizar(resultado.get("destino")):
        raise ValueError("O produto final não corresponde ao solicitado.")
    entradas = [
        {"papel": "BASE", "codigo": base, "quantidade": 1},
        {"papel": "DOADORA", "codigo": doadora, "quantidade": 1},
    ]
    saidas = [
        {"papel": "PRODUTO_FINAL", "codigo": final, "quantidade": 1},
        {"papel": "RESIDUAL", "codigo": residual, "quantidade": 1},
    ]
    # A ordem e o papel de cada item importam: base e doadora não são intercambiáveis.
    identidade = {
        "grau": grau, "subtipo": subtipo,
        "entradas": entradas, "saidas": saidas,
    }
    assinatura = hashlib.sha256(
        json.dumps(identidade, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    agora = datetime.now(timezone.utc).isoformat()
    return {
        "assinatura": assinatura,
        "grau": grau,
        "subtipo": subtipo,
        "familia": resultado.get("familia"),
        "produto_final": final,
        "entradas": entradas,
        "saidas": saidas,
        "parametros_tecnicos": {
            "operacao": resultado.get("operacao") or subtipo,
            "metodo": resultado.get("metodo") or "VALVULA_VALVULA",
            "grupo_torre": resultado.get("grupo_torre"),
            "construcao_torre": resultado.get("construcao_torre"),
            "tipo_residual": simulacao.get("tipo_residual") or "VALVULA",
            "validacao_manual": True,
        },
        "versao_regra": VERSAO_CATALOGO,
        "estado": "VALIDADA",
        "origem_cadastro": "LABORATORIO",
        "registrada_por": usuario,
        "validada_por": usuario,
        "primeira_validacao_em": agora,
        "ultima_validacao_em": agora,
        "total_validacoes": 1,
    }


def listar_receitas(produto_final, grau=None, limite=100):
    """Busca receitas aprovadas por código exato, nunca por semelhança insegura."""
    codigo = normalizar(produto_final)
    if not codigo:
        return []
    consulta = (
        supabase.table(TABELA_POSSIBILIDADES)
        .select(CAMPOS_CONSULTA)
        .eq("produto_final", codigo)
        .eq("estado", "VALIDADA")
    )
    if grau:
        consulta = consulta.eq("grau", grau)
    resposta = consulta.order("ultima_validacao_em", desc=True).limit(min(max(int(limite), 1), 100)).execute()
    return resposta.data or []


def disponibilidade_receita(receita, saldos):
    """Saldos indicativos do arquivo ERP, não reservas nem estoque transacional."""
    consumo = {}
    for item in receita.get("entradas") or []:
        codigo = normalizar(item.get("codigo"))
        consumo[codigo] = consumo.get(codigo, 0) + float(item.get("quantidade", 1))
    return bool(consumo) and all(saldos.get(codigo, 0) >= qtd for codigo, qtd in consumo.items())


def registrar_receita(resultado, simulacao, usuario):
    """Grava só receitas validadas; assinatura única evita duplicação ao clicar de novo."""
    dados = preparar_receita(resultado, simulacao, usuario)
    assinatura = dados["assinatura"]
    encontrados = (
        supabase.table(TABELA_POSSIBILIDADES)
        .select("id,estado")
        .eq("assinatura", assinatura).limit(1).execute()
    ).data or []
    if encontrados:
        anterior = encontrados[0]
        if anterior["estado"] == "VALIDADA":
            return anterior, False
        if anterior["estado"] == "BLOQUEADA":
            raise ValueError("Esta receita está bloqueada e requer revisão administrativa.")
        # Um rascunho com a mesma assinatura pode ser homologado pelo operador.
        agora = datetime.now(timezone.utc).isoformat()
        atualizado = (
            supabase.table(TABELA_POSSIBILIDADES)
            .update({
                "estado": "VALIDADA", "validada_por": dados["validada_por"],
                "primeira_validacao_em": agora, "ultima_validacao_em": agora,
                "total_validacoes": 1, "atualizado_em": agora,
            })
            .eq("id", anterior["id"]).eq("estado", "PENDENTE")
            .execute()
        )
        if atualizado.data:
            return atualizado.data[0], True
        return registrar_receita(resultado, simulacao, usuario)
    try:
        inserido = supabase.table(TABELA_POSSIBILIDADES).insert(dados).execute()
    except Exception as erro:
        # Proteção adicional se dois usuários tentarem registrar a mesma receita juntos.
        if str(getattr(erro, "code", "")) != "23505":
            raise
        repetida = (
            supabase.table(TABELA_POSSIBILIDADES)
            .select("id,estado")
            .eq("assinatura", assinatura).limit(1).execute()
        ).data or []
        if repetida and repetida[0]["estado"] == "VALIDADA":
            return repetida[0], False
        raise
    if not inserido.data:
        raise RuntimeError("O Supabase não confirmou o cadastro da receita.")
    return inserido.data[0], True

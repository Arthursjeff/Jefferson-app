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


def preparar_receita(resultado, simulacao, usuario, estado="VALIDADA", origem="LABORATORIO", observacao=None):
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
        {"papel": "PRODUTO", "codigo": final, "quantidade": 1},
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
    if estado not in ("VALIDADA", "PENDENTE"):
        raise ValueError("Estado de cadastro inválido.")
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
            "origem_avaliacao": "DECLARADA" if origem == "LABORATORIO_MANUAL" else "MOTOR_TECNICO",
        },
        "versao_regra": VERSAO_CATALOGO,
        "estado": estado,
        "origem_cadastro": origem,
        "registrada_por": usuario,
        "validada_por": usuario if estado == "VALIDADA" else None,
        "primeira_validacao_em": agora if estado == "VALIDADA" else None,
        "ultima_validacao_em": agora if estado == "VALIDADA" else None,
        "total_validacoes": 1 if estado == "VALIDADA" else 0,
        "observacao": (str(observacao).strip() or None) if observacao else None,
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



def _itens_comparaveis(itens):
    """Normalização equivalente à função SQL canonizar_itens_transformacao."""
    somas = {}
    for item in itens or []:
        chave = (normalizar(item.get("codigo")), str(item.get("papel") or "").strip().upper())
        somas[chave] = somas.get(chave, 0) + float(item.get("quantidade", 0))
    return sorted((codigo, papel, quantidade)
                  for (codigo, papel), quantidade in somas.items())


def _mesma_receita(existente, dados):
    """A assinatura real é recalculada pelo trigger do PostgreSQL."""
    return (
        existente.get("grau") == dados["grau"]
        and existente.get("subtipo") == dados["subtipo"]
        and existente.get("produto_final") == dados["produto_final"]
        and _itens_comparaveis(existente.get("entradas")) == _itens_comparaveis(dados["entradas"])
        and _itens_comparaveis(existente.get("saidas")) == _itens_comparaveis(dados["saidas"])
        and (existente.get("parametros_tecnicos") or {}) == dados["parametros_tecnicos"]
    )


def _localizar_equivalente(dados):
    # A consulta usa o índice existente (produto_final, estado); o trigger
    # calcula SHA256 com jsonb canônico e sobrescreve a assinatura do cliente.
    resposta = (
        supabase.table(TABELA_POSSIBILIDADES)
        .select("id,estado,grau,subtipo,produto_final,entradas,saidas,parametros_tecnicos")
        .eq("produto_final", dados["produto_final"])
        .eq("grau", dados["grau"])
        .limit(1000).execute()
    )
    return next((r for r in (resposta.data or []) if _mesma_receita(r, dados)), None)


def registrar_receita(resultado, simulacao, usuario, estado="VALIDADA",
                     origem="LABORATORIO", observacao=None):
    """Registra hipótese pendente ou receita validada, sem alterar estoque."""
    dados = preparar_receita(resultado, simulacao, usuario, estado=estado,
                            origem=origem, observacao=observacao)
    existente = _localizar_equivalente(dados)
    if existente:
        if existente["estado"] == "VALIDADA":
            return existente, False
        if existente["estado"] == "BLOQUEADA":
            raise ValueError("Esta receita está bloqueada e requer revisão administrativa.")
        if estado == "PENDENTE":
            return existente, False
        # Rascunhos equivalentes podem ser validados; receitas já aprovadas
        # nunca têm parâmetros técnicos alterados, conforme trigger do banco.
        agora = datetime.now(timezone.utc).isoformat()
        atualizado = (
            supabase.table(TABELA_POSSIBILIDADES)
            .update({
                "estado": "VALIDADA", "validada_por": dados["validada_por"],
                "primeira_validacao_em": agora, "ultima_validacao_em": agora,
                "total_validacoes": 1,
            })
            .eq("id", existente["id"]).eq("estado", "PENDENTE").execute()
        )
        if atualizado.data:
            return atualizado.data[0], True
        atual = _localizar_equivalente(dados)
        if atual and atual["estado"] == "VALIDADA":
            return atual, False
        raise RuntimeError("A receita foi alterada por outro usuário. Consulte novamente.")
    try:
        inserido = supabase.table(TABELA_POSSIBILIDADES).insert(dados).execute()
    except Exception as erro:
        if str(getattr(erro, "code", "")) != "23505":
            raise
        # O trigger calcula outra assinatura; não consultar pelo hash do cliente.
        repetida = _localizar_equivalente(dados)
        if repetida and repetida["estado"] == "VALIDADA":
            return repetida, False
        if repetida and repetida["estado"] == "BLOQUEADA":
            raise ValueError("Receita bloqueada. Solicite revisão administrativa.") from erro
        raise
    if not inserido.data:
        raise RuntimeError("O Supabase não confirmou o cadastro da receita.")
    return inserido.data[0], True

def listar_pendentes(limite=100):
    """Fila de homologação exclusivamente para uso na área administrativa."""
    resposta = (
        supabase.table(TABELA_POSSIBILIDADES)
        .select("id,grau,subtipo,produto_final,entradas,saidas,"
                "registrada_por,criado_em,observacao")
        .eq("estado", "PENDENTE")
        .order("criado_em", desc=False)
        .limit(min(max(int(limite), 1), 100)).execute()
    )
    return resposta.data or []


def homologar_pendente(receita_id, usuario, setor):
    """Homologação explícita; só o perfil administrador pode liberar para recomendação."""
    if setor != "ADMINISTRADOR":
        raise PermissionError("Somente o administrador pode homologar receitas.")
    usuario = str(usuario or "").strip().lower()
    if not usuario or not receita_id:
        raise ValueError("Informe operador e receita para homologação.")
    agora = datetime.now(timezone.utc).isoformat()
    resposta = (
        supabase.table(TABELA_POSSIBILIDADES)
        .update({
            "estado": "VALIDADA",
            "validada_por": usuario,
            "primeira_validacao_em": agora,
            "ultima_validacao_em": agora,
            "total_validacoes": 1,
        })
        .eq("id", receita_id)
        .eq("estado", "PENDENTE")
        .execute()
    )
    if not resposta.data:
        raise RuntimeError("A receita não está pendente ou foi atualizada por outro operador.")
    return resposta.data[0]

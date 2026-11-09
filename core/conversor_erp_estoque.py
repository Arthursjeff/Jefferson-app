"""Validação conservadora para saldos ERP, reutilizando o conversor V0.6 do APP.

A função sugerir_codigo continua sendo a única fonte de regras e referências.
Somente código corroborado pela descrição pode compor o estoque de simulação.
"""
from dataclasses import dataclass

from core.conversor_erp_pedido import sugerir_codigo
from core.motor_erp_regras import categoria, codigo_na_descricao, normal

KITS_LAB = frozenset((
    "K030A2", "K030AR2", "K030V2", "K030VR2",
    "K30A2", "K30AR2", "K30V2", "K30VR2",
))
KITS_INTERNOS = {
    "202-0509": "K030AR2",
    "202-0515": "K30A2",
}


@dataclass(frozen=True)
class ResultadoEstoque:
    codigo_erp: str
    codigo_tecnico: str | None
    status: str
    metodo: str
    motivo: str


def converter(codigo_erp, descricao=""):
    erp = normal(codigo_erp)
    desc = str(descricao or "").upper()
    if not erp:
        return ResultadoEstoque(erp, None, "PENDENTE", "entrada", "Código vazio")
    if erp.startswith("EXP") or "EM CORTE" in desc:
        return ResultadoEstoque(erp, None, "PENDENTE", "exposicao",
                               "Item de exposição / peça em corte excluído do saldo de referência")
    if erp in KITS_INTERNOS:
        tecnico = KITS_INTERNOS[erp]
        variante = tecnico.replace("A2", "A02")
        if "KIT" in desc and (tecnico in normal(desc) or variante in normal(desc)):
            return ResultadoEstoque(erp, tecnico, "CONFIRMADO", "kit_interno_descricao",
                                   "Kit interno identificado pelo código e pela descrição")
        return ResultadoEstoque(erp, None, "PENDENTE", "kit_interno",
                               "Kit interno não confirmado na descrição")
    if erp in KITS_LAB:
        if "KIT" in desc:
            return ResultadoEstoque(erp, erp, "CONFIRMADO", "kit_identificado",
                                   "Código técnico do kit presente no ERP")
        return ResultadoEstoque(erp, None, "PENDENTE", "kit", "Tipo de kit não confirmado")
    tipo = categoria(erp, desc)
    if tipo != "VALVULA":
        return ResultadoEstoque(erp, None, "PENDENTE", "tipo_produto",
                               "Item não classificado como válvula")
    retorno = sugerir_codigo({"codigo_erp": erp, "descricao_original": desc})
    situacao = str(retorno.get("situacao") or "")
    if situacao.startswith("CONFLITO"):
        return ResultadoEstoque(erp, None, "DIVERGENTE", "motor_erp_v06",
                               situacao)
    tecnico = normal(retorno.get("codigo_sugerido"))
    descrito = codigo_na_descricao(desc)
    if tecnico and descrito and tecnico == descrito:
        return ResultadoEstoque(erp, tecnico, "CONFIRMADO", "conversor_v06_descricao",
                               "Motor ERP e descrição técnica concordam")
    if tecnico and descrito and tecnico != descrito:
        return ResultadoEstoque(erp, None, "DIVERGENTE", "descricao",
                               "Código da descrição diverge do código sugerido")
    if tecnico:
        origem = retorno.get("origem_sugestao") or ""
        if origem == "REGRA":
            return ResultadoEstoque(erp, tecnico, "INFERIDO", "regra_familia",
                                   "Inferência sem conferência documental")
        return ResultadoEstoque(erp, tecnico, "REFERENCIA_TABELA", "mapa_historico",
                               "Correspondência histórica ainda não confirmada pela descrição")
    return ResultadoEstoque(erp, None, "PENDENTE", "sem_regra",
                           situacao or "Código sem equivalência segura")

from core.database import supabase


def salvar_orcamento(
    numero_orcamento,
    cliente,
    itens,
    criado_por,
    observacao_geral="",
):
    """
    Salva o cabeçalho do orçamento e seus itens.
    """

    if not cliente:
        raise ValueError("Cliente não selecionado.")

    if not itens:
        raise ValueError("O orçamento não possui itens.")

    valor_total = sum(
        item["quantidade"] * item["valor_unitario"]
        for item in itens
    )

    dados_orcamento = {
        "numero_orcamento": numero_orcamento.strip(),

        "cliente_id": cliente.get("id"),
        "codigo_cliente": cliente.get("codigo_cliente"),
        "razao_social": cliente.get("razao_social"),
        "nome_fantasia": cliente.get("nome_fantasia"),
        "cnpj_cpf": cliente.get("cnpj_cpf"),
        "tipo_cliente": cliente.get("tipo_cliente"),
        "cidade": cliente.get("cidade"),
        "estado": cliente.get("estado"),
        "email": cliente.get("email"),

        "criado_por": criado_por,
        "valor_total": valor_total,
        "observacao_geral": observacao_geral.strip() or None,
        "status": "RASCUNHO",
    }

    resposta = (
        supabase
        .table("orcamentos")
        .insert(dados_orcamento)
        .execute()
    )

    if not resposta.data:
        raise Exception("Não foi possível criar o orçamento.")

    orcamento = resposta.data[0]
    orcamento_id = orcamento["id"]

    dados_itens = []

    for indice, item in enumerate(itens, start=1):

        total_item = (
            item["quantidade"]
            * item["valor_unitario"]
        )

        dados_itens.append({
            "orcamento_id": orcamento_id,
            "ordem": indice,
            "codigo": item["codigo"],
            "tensao": item["tensao"],
            "quantidade": item["quantidade"],
            "valor_unitario": item["valor_unitario"],
            "valor_total": total_item,
            "prazo": item["prazo"],
            "observacao": item["observacao"] or None,
        })

    resposta_itens = (
        supabase
        .table("orcamento_itens")
        .insert(dados_itens)
        .execute()
    )

    if not resposta_itens.data:
        # Evita deixar orçamento vazio caso ocorra erro nos itens
        (
            supabase
            .table("orcamentos")
            .delete()
            .eq("id", orcamento_id)
            .execute()
        )

        raise Exception(
            "O orçamento foi criado, mas ocorreu erro ao salvar os itens."
        )

    return orcamento

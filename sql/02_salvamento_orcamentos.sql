BEGIN;

-- Uma chamada salva a versão e todos os seus itens na mesma transação.
CREATE OR REPLACE FUNCTION public.salvar_orcamento_app(
    p_dados jsonb, p_itens jsonb
) RETURNS jsonb
LANGUAGE plpgsql SECURITY INVOKER
SET search_path = public, pg_temp
AS $$
DECLARE
    novo public.orcamentos%ROWTYPE;
    anterior public.orcamentos%ROWTYPE;
    item jsonb;
    numero text := trim(p_dados->>'numero_orcamento');
    modo text := coalesce(p_dados->>'tipo_criacao', 'NOVO');
    versao integer := 0;
    total numeric := 0;
    quantidade integer;
    preco numeric;
    posicao integer := 0;
BEGIN
    IF numero IS NULL OR numero = '' THEN
        RAISE EXCEPTION 'Informe o número do orçamento.';
    END IF;
    IF modo NOT IN ('NOVO', 'REVISAO', 'DUPLICADO', 'SIMILAR') THEN
        RAISE EXCEPTION 'Operação inválida.';
    END IF;
    IF modo <> 'REVISAO' AND numero !~ '^[0-9]+/[0-9]{2}$' THEN
        RAISE EXCEPTION 'Use o número completo com ano, por exemplo 1000/26.';
    END IF;
    IF nullif(trim(p_dados->>'criado_por'), '') IS NULL THEN
        RAISE EXCEPTION 'Vendedor responsável não informado.';
    END IF;
    IF p_itens IS NULL OR jsonb_typeof(p_itens) <> 'array' THEN
        RAISE EXCEPTION 'Itens inválidos.';
    END IF;
    IF jsonb_array_length(p_itens) = 0 THEN
        RAISE EXCEPTION 'Adicione pelo menos um item.';
    END IF;

    -- Serializa salvamentos do mesmo número para evitar duas revisões iguais.
    PERFORM pg_advisory_xact_lock(hashtextextended(numero, 0));
    SELECT * INTO anterior FROM public.orcamentos
    WHERE numero_orcamento = numero
    ORDER BY revisao DESC LIMIT 1;

    IF modo = 'REVISAO' THEN
        IF anterior.id IS NULL THEN
            RAISE EXCEPTION 'Orçamento não encontrado.';
        END IF;
        IF anterior.id IS DISTINCT FROM
            nullif(p_dados->>'revisao_anterior_id', '')::bigint THEN
            RAISE EXCEPTION 'Existe uma revisão mais recente. Busque novamente antes de revisar.';
        END IF;
        versao := anterior.revisao + 1;
        -- Cliente e número não podem ser trocados durante uma revisão.
        p_dados := p_dados || jsonb_build_object(
            'cliente_id', anterior.cliente_id,
            'codigo_cliente', anterior.codigo_cliente,
            'primeiro_contato_id', anterior.primeiro_contato_id);
    ELSIF anterior.id IS NOT NULL THEN
        RAISE EXCEPTION 'Esse número já existe. Use Revisar ou escolha outro número.';
    END IF;

    IF nullif(p_dados->>'cliente_id', '') IS NULL
       AND nullif(p_dados->>'primeiro_contato_id', '') IS NULL THEN
        RAISE EXCEPTION 'Selecione um cliente ou confirme o primeiro contato.';
    END IF;

    -- Confere as escolhas no catálogo, sem aceitar condições livres no app.
    IF NOT EXISTS (SELECT 1 FROM public.orcamento_opcoes_comerciais
        WHERE categoria = 'VALIDADE' AND ativo
          AND valor = p_dados->>'validade_proposta')
       OR NOT EXISTS (SELECT 1 FROM public.orcamento_opcoes_comerciais
        WHERE categoria = 'PAGAMENTO' AND ativo
          AND valor = p_dados->>'condicao_pagamento')
       OR NOT EXISTS (SELECT 1 FROM public.orcamento_opcoes_comerciais
        WHERE categoria = 'FRETE' AND ativo
          AND valor = p_dados->>'frete') THEN
        RAISE EXCEPTION 'Selecione validade, pagamento e frete válidos.';
    END IF;

    FOR item IN SELECT value FROM jsonb_array_elements(p_itens) LOOP
        quantidade := (item->>'quantidade')::integer;
        preco := (item->>'valor_unitario')::numeric;
        IF quantidade IS NULL OR quantidade <= 0 OR preco IS NULL OR preco < 0
           OR preco::text IN ('NaN','Infinity','-Infinity') THEN
            RAISE EXCEPTION 'Quantidade ou preço inválido.';
        END IF;
        IF nullif(trim(item->>'codigo'), '') IS NULL
           OR nullif(trim(item->>'tensao'), '') IS NULL
           OR nullif(trim(item->>'prazo'), '') IS NULL THEN
            RAISE EXCEPTION 'Código, tensão e prazo são obrigatórios em cada item.';
        END IF;
        total := total + quantidade * round(preco, 2);
    END LOOP;

    INSERT INTO public.orcamentos (
        numero_orcamento, revisao, cliente_id, codigo_cliente,
        primeiro_contato_id, revisao_anterior_id, orcamento_origem_id,
        tipo_criacao, data_proposta, criado_por, valor_total,
        observacao_geral, status, validade_proposta, condicao_pagamento, frete
    ) VALUES (
        numero, versao, nullif(p_dados->>'cliente_id','')::bigint,
        p_dados->>'codigo_cliente',
        nullif(p_dados->>'primeiro_contato_id','')::bigint,
        CASE WHEN modo = 'REVISAO' THEN anterior.id ELSE NULL END,
        nullif(p_dados->>'orcamento_origem_id','')::bigint,
        modo, (now() AT TIME ZONE 'America/Sao_Paulo')::date,
        p_dados->>'criado_por', round(total, 2),
        nullif(trim(p_dados->>'observacao_geral'), ''), 'FINALIZADO',
        p_dados->>'validade_proposta', p_dados->>'condicao_pagamento', p_dados->>'frete'
    ) RETURNING * INTO novo;

    FOR item IN SELECT value FROM jsonb_array_elements(p_itens) LOOP
        posicao := posicao + 1;
        quantidade := (item->>'quantidade')::integer;
        preco := round((item->>'valor_unitario')::numeric, 2);
        INSERT INTO public.orcamento_itens (
            orcamento_id, ordem, codigo, tensao, quantidade,
            valor_unitario, valor_total, prazo, observacao
        ) VALUES (
            novo.id, posicao, upper(trim(item->>'codigo')), item->>'tensao',
            quantidade, preco, quantidade * preco, item->>'prazo',
            nullif(trim(item->>'observacao'), '')
        );
    END LOOP;
    RETURN to_jsonb(novo);
END;
$$;

REVOKE ALL ON FUNCTION public.salvar_orcamento_app(jsonb, jsonb)
    FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.salvar_orcamento_app(jsonb, jsonb)
    TO service_role;

-- A ligação de revisões/origens impede apagar versões usadas no histórico.
-- Não cria políticas públicas nem modifica os dados existentes.
NOTIFY pgrst, 'reload schema';
COMMIT;

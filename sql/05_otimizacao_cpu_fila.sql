-- Otimização não destrutiva da fila. Não remove nem modifica dados históricos.
-- Manter este arquivo no repositório para rastrear a migração aplicada no Supabase.

CREATE TABLE IF NOT EXISTS public.fila_revisao (
    id smallint PRIMARY KEY CHECK (id = 1),
    versao bigint NOT NULL DEFAULT 0,
    atualizado_em timestamptz NOT NULL DEFAULT now()
);
INSERT INTO public.fila_revisao (id) VALUES (1) ON CONFLICT (id) DO NOTHING;

ALTER TABLE public.fila_revisao ENABLE ROW LEVEL SECURITY;
GRANT SELECT ON public.fila_revisao TO service_role;
REVOKE ALL ON public.fila_revisao FROM anon, authenticated;

CREATE OR REPLACE FUNCTION public.registrar_revisao_fila()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
SET search_path = '' AS $$
BEGIN
    UPDATE public.fila_revisao
       SET versao = versao + 1,
           atualizado_em = clock_timestamp()
     WHERE id = 1;
    RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION public.registrar_revisao_fila() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.registrar_revisao_fila() FROM anon, authenticated;

-- Um único incremento por comando SQL (inclusive inserções em lote).
DO $$
DECLARE nome_tabela text;
BEGIN
    FOREACH nome_tabela IN ARRAY ARRAY[
        'fila_pedidos', 'fila_movimentacoes', 'fila_alertas',
        'fila_mensagens', 'fila_pedido_itens', 'fila_pedido_series',
        'fila_fotos'
    ]
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS trg_revisao_fila ON public.%I', nome_tabela);
        EXECUTE format(
            'CREATE TRIGGER trg_revisao_fila AFTER INSERT OR UPDATE OR DELETE ON public.%I '
            || 'FOR EACH STATEMENT EXECUTE FUNCTION public.registrar_revisao_fila()',
            nome_tabela
        );
    END LOOP;
END;
$$;

-- Índices alinhados com os filtros efetivos de cada consulta.
CREATE INDEX IF NOT EXISTS idx_fila_pedidos_status_setor
    ON public.fila_pedidos (status, setor_atual);
CREATE INDEX IF NOT EXISTS idx_fila_mov_pedido_tipo_criado
    ON public.fila_movimentacoes (pedido_id, tipo_evento, criado_em DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_fila_mov_retiradas
    ON public.fila_movimentacoes (destino, origem, tipo_evento, criado_em DESC);
CREATE INDEX IF NOT EXISTS idx_fila_mov_tipo_criado
    ON public.fila_movimentacoes (tipo_evento, criado_em DESC);
CREATE INDEX IF NOT EXISTS idx_fila_alertas_ativos_pedido
    ON public.fila_alertas (pedido_id) WHERE ativo IS TRUE;
CREATE INDEX IF NOT EXISTS idx_fila_mensagens_ativas_pedido
    ON public.fila_mensagens (pedido_id) WHERE ativa IS TRUE;
CREATE INDEX IF NOT EXISTS idx_fila_notificacoes_pendentes
    ON public.fila_notificacoes (usuario_destino, criado_em)
    WHERE visualizado IS FALSE;

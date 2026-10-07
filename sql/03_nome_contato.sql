BEGIN;

-- Nome da pessoa contatada: opcional, independente do vendedor da proposta.
ALTER TABLE public.primeiros_contatos
    ADD COLUMN IF NOT EXISTS nome_contato text;

NOTIFY pgrst, 'reload schema';
COMMIT;

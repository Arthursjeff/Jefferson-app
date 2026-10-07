# Ativar compradores no orçamento

Com a tabela `contatos_clientes` e o campo `orcamentos.contato_cliente_id` já criados,
execute todo o arquivo `sql/04_salvamento_com_comprador.sql` no SQL Editor do Supabase.
Ele cria a função que salva proposta, itens e comprador na mesma transação.
O app usa essa função para evitar salvar uma proposta sem o vínculo escolhido.

No aplicativo:

1. Abra **Clientes**, busque código, empresa ou CNPJ e abra o cadastro.
2. Configure validade, pagamento e frete em **Condições especiais**; **Usar padrão**
   remove a exceção daquele campo. Os padrões são 3 dias, 28 dias e FOB.
3. Cadastre os compradores com nome e pelo menos WhatsApp ou e-mail.
4. Em **Novo orçamento**, selecione o cliente e o comprador. Um único comprador ativo
   é selecionado automaticamente; com vários, a escolha é obrigatória.
5. Use **Cadastrar novo comprador** para cadastrá-lo sem sair do orçamento.
6. Em **Buscar orçamento**, o comprador aparece junto dos dados da versão.

Uma revisão permite trocar o comprador e preserva o vínculo da versão anterior.
Duplicação mantém o comprador ativo do mesmo cliente; similar limpa o vínculo para
selecionar o comprador do outro cliente. Sem compradores ativos, o orçamento pode
prosseguir sem vínculo. Um contato inativo continua consultável nos orçamentos antigos.

O comprador é uma informação interna e não aparece no PDF. A tela Clientes substitui
a importação na navegação para Administrador, Vendas e Montagem. Os dados principais
dos clientes existentes permanecem consultáveis; esta tela altera condições especiais
e compradores.

Os testes de interface usam persistência simulada e o interpretador real dos produtos.
A função SQL foi validada sintaticamente; a integração real precisa ser conferida
no aplicativo depois da execução do SQL.

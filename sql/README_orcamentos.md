# Ativação dos fluxos de orçamento

O primeiro SQL já executado prepara primeiros contatos, opções comerciais,
exceções no cadastro de clientes e identificação das revisões.

## Ativar o salvamento

1. Abra `sql/02_salvamento_orcamentos.sql` neste repositório e copie todo o conteúdo.
2. No Supabase, abra **SQL Editor → New query**, cole e execute.
3. Atualize a página do aplicativo e abra **Orçamentos → Novo orçamento**.

Esse SQL cria uma função que salva a proposta e seus itens na mesma transação.
Se um item falhar, nenhuma parte da proposta fica salva. A função também evita
duplicar números e impede salvar uma revisão baseada numa versão desatualizada.
Ela usa a conexão de servidor já existente no app; mantém o RLS e não cria acesso público.

## Conferir a operação

- Crie uma proposta com um número disponível no formato `1000/26`; salve e baixe o PDF.
- Busque esse número e clique em **Revisar**. Cliente e número ficam bloqueados;
  edite um item, aplique ao orçamento e salve. A revisão zero permanece consultável.
- **Duplicar** reaproveita os itens e o cliente com outro número, começando na revisão zero.
- **Criar similar** reaproveita os itens e permite selecionar outro cliente.
- Para primeiro contato, informe `184`, `251`, `350`, `620` ou `840` na busca de cliente.
  Consulte o CNPJ, confira empresa e contato e confirme o cadastro antes de salvar a proposta.
- Validade, pagamento e frete vêm das exceções do cliente ou dos padrões
  **3 dias / 28 dias / FOB**. Alterações na proposta não modificam o cadastro do cliente.

Todos os usuários do app podem consultar. Criação e revisão mantêm os setores
Vendas, Administrador e Montagem. O número é informado manualmente e inclui o ano:
`1000/25` e `1000/26` são propostas distintas.

Os testes locais cobrem os fluxos de tela com persistência simulada, o interpretador
real dos itens e a geração do PDF. A função SQL foi validada sintaticamente;
a integração com o banco real deve ser conferida após a execução no Supabase.

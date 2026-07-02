# Regras de Desenvolvimento

## Objetivo

Manter o projeto organizado, modular e escalável.

---

# Estrutura

## app.py

Responsável apenas por iniciar a aplicação.

Não deve conter regras de negócio.

---

## pages/

Responsável apenas pelas telas.

As páginas não devem acessar diretamente o banco de dados.

As páginas apenas chamam funções dos módulos.

---

## modules/

Cada módulo deve conter toda a regra de negócio referente à sua funcionalidade.

Exemplo:

Módulo 01

- consultas
- validações
- regras
- processos

---

## core/

Contém recursos compartilhados por toda a aplicação.

Exemplos:

- autenticação
- banco de dados
- configurações
- permissões

---

## components/

Componentes visuais reutilizáveis.

Exemplo:

- cards
- tabelas
- menus
- cabeçalhos
- rodapés

---

## assets/

Arquivos estáticos.

Exemplo:

- imagens
- ícones
- logos

---

# Banco de Dados

Toda comunicação com o Supabase deverá passar pelo core.

Nenhuma página deverá acessar diretamente o banco de dados.

---

# Filosofia

O crescimento do sistema deverá ocorrer através da criação de novos módulos, evitando alterações na estrutura principal da plataforma.

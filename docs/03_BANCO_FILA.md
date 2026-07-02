# Banco de Dados - Módulo Fila

## Objetivo

Definir as tabelas necessárias para o funcionamento inicial da Fila de Pedidos.

## Tabelas iniciais

### usuarios

Armazena os usuários do sistema.

Campos:
- id
- nome
- setor
- ativo
- criado_em

---

### pedidos

Armazena os pedidos da fila.

Campos:
- id
- numero_pedido
- cliente
- estagio_atual
- status
- observacoes
- criado_por
- criado_em
- atualizado_em

---

### historico_pedidos

Registra as movimentações dos pedidos.

Campos:
- id
- pedido_id
- estagio_anterior
- estagio_novo
- usuario
- data_movimento
- observacao

---

## Estágios permitidos

- Pedidos
- Em Montagem
- Programados / Importação
- Montados
- Faturados
- Embalados
- Retirados

## Status possíveis

- Ativo
- Cancelado
- Finalizado

## Observação

Esta estrutura é inicial e poderá ser expandida após a validação da fila com os supervisores.

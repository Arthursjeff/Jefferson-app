# Módulo Fila de Pedidos

## Objetivo

Controlar o avanço dos pedidos entre os setores e estágios operacionais.

Este será o módulo principal da primeira validação do Jefferson App.

## Setores iniciais

### Vendas

Usuários:
- Amanda
- Arthur
- Carla
- Jaqueline
- Marilene
- Romulo

### Montagem

Usuários:
- João
- Ricardo
- Marco

## Estágios da fila

1. Pedidos
2. Em Montagem
3. Programados / Importação
4. Montados
5. Faturados
6. Embalados
7. Retirados

## Permissões iniciais

### Vendas

Pode:
- Criar pedido
- Mover de Montados para Faturados
- Cancelar pedido

### Montagem

Pode:
- Mover de Pedidos para Em Montagem
- Mover de Em Montagem para Programados / Importação
- Mover de Em Montagem para Montados
- Mover de Programados / Importação para Montados
- Mover de Faturados para Embalados
- Mover de Embalados para Retirados

## Dados mínimos de um pedido

- Número do pedido
- Cliente
- Data de criação
- Setor responsável
- Estágio atual
- Status
- Observações
- Usuário que criou
- Última atualização

## Validação inicial

A primeira versão será considerada válida se permitir:

- Login por usuário ou setor
- Criação de pedidos
- Visualização da fila
- Movimentação entre estágios conforme permissões
- Registro básico das alterações

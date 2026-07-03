# Módulo 01 - Especificação Funcional

## Objetivo

O Módulo 01 representa a primeira funcionalidade oficial do Jefferson App.

Seu objetivo é controlar todo o fluxo operacional dos pedidos entre os setores da empresa, registrando cada movimentação realizada pelos usuários e permitindo o acompanhamento do andamento dos pedidos em tempo real.

Esta será a primeira funcionalidade apresentada para validação pelos supervisores.

---

# Objetivos do módulo

O módulo deverá permitir:

- Criar novos pedidos.
- Visualizar os pedidos por estágio.
- Movimentar pedidos entre os estágios permitidos.
- Controlar permissões por usuário.
- Registrar todas as movimentações.
- Registrar mensagens importantes.
- Registrar alertas.
- Registrar Nota Fiscal.
- Consultar histórico.
- Exportar informações.

---

# Usuários

O sistema trabalha com dois grupos de usuários.

## Grupo 01 - Vendas

Responsável pelo relacionamento comercial.

Permissões:

- Criar pedidos.
- Cancelar pedidos.
- Registrar Nota Fiscal.
- Movimentar pedidos de Montados para Faturados.
- Criar alertas.
- Editar mensagens fixadas.

---

## Grupo 02 - Montagem

Responsável pela produção.

Permissões:

- Movimentar pedidos entre os estágios de produção.
- Criar alertas.
- Editar mensagens fixadas.

---

# Fluxo principal

Todo pedido deverá seguir obrigatoriamente o seguinte fluxo:

Pedidos

↓

Em Montagem

↓

Programados / Importação (quando aplicável)

↓

Montados

↓

Faturados

↓

Embalados

↓

Retirados

---

# Pedido

Cada pedido deverá possuir, no mínimo, as seguintes informações.

## Identificação

- ID interno
- Número do pedido
- Nome do pedido

---

## Situação

- Estágio atual
- Status

---

## Controle

- Usuário responsável pela última movimentação
- Horário da última movimentação

---

## Informações adicionais

- Mensagem fixada
- Nota Fiscal
- Marca Programação
- Marca Importação

---

## Histórico

Cada pedido deverá armazenar todas as movimentações realizadas durante sua existência.

Nenhuma movimentação deverá ser perdida.

---

# Alertas

Os alertas são mensagens temporárias utilizadas para comunicação entre setores.

Características:

- Associados a um pedido.
- Possuem autor.
- Possuem horário.
- Possuem mensagem.
- Permanecem disponíveis até serem visualizados.

---

# Mensagem fixada

Cada pedido poderá possuir uma mensagem permanente.

Características:

- Editável.
- Sempre visível no cartão.
- Registrada no histórico quando alterada.

---

# Nota Fiscal

Quando um pedido atingir o estágio Montados, deverá ser possível registrar o número da Nota Fiscal.

Após o registro, o pedido poderá seguir para o estágio Faturados.

---

# Programação / Importação

Alguns pedidos poderão ser classificados como:

- Programação
- Importação

Essas classificações servem para organizar pedidos especiais e poderão ser utilizadas em filtros específicos do sistema.

---

# Histórico

Toda ação executada deverá ser registrada.

Exemplos:

- Pedido criado.
- Mudança de estágio.
- Registro de Nota Fiscal.
- Cancelamento.
- Alteração de mensagem.
- Criação de alerta.

O histórico deverá permanecer associado ao pedido durante todo o seu ciclo de vida.

---

# Exportação

O módulo deverá permitir exportar os dados da fila.

A exportação deverá incluir:

- Pedidos.
- Histórico.
- Alertas.
- Pedidos arquivados.

---

# Arquivamento

Pedidos cancelados ou encerrados deverão ser arquivados.

O arquivamento deverá preservar:

- Histórico completo.
- Alertas.
- Mensagens fixadas.
- Situação final.
- Data do arquivamento.

---

# Objetivo da primeira versão

A primeira versão será considerada concluída quando permitir:

- Login.
- Criação de pedidos.
- Controle completo da fila.
- Controle de permissões.
- Histórico completo.
- Exportação dos dados.

Funcionalidades futuras poderão ser adicionadas sem alterar a arquitetura principal do módulo.

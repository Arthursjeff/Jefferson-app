# Estrutura Técnica - Jefferson App

## Objetivo

Definir como o projeto será organizado tecnicamente antes de novas alterações no código.

## Estrutura planejada

```text
Jefferson-app/
│
├── app.py
├── requirements.txt
│
├── core/
│   ├── config.py
│   ├── database.py
│   ├── auth.py
│   └── permissions.py
│
├── modules/
│   └── fila/
│       ├── service.py
│       ├── repository.py
│       └── rules.py
│
├── pages/
│   ├── 1_Dashboard.py
│   └── 2_Fila_de_Pedidos.py
│
├── components/
│   ├── layout.py
│   └── cards.py
│
├── assets/
│
└── docs/

# Diagnóstico ERP → Jefferson — 15/10/2026

**Origem:** leitura das tabelas `public.itens_comerciais` no projeto APP-JEFF, exclusivamente registros com `classificacao_status` em `NAO_IDENTIFICADA`, `NAO_RECONHECIDO`, `NAO_RECONHECIDA`.

**Base de equivalências:** relação tabulada enviada pelo usuário em 15/10/2026. Cadastro histórico **não auditado**.

## Cobertura

| Resultado | Códigos ERP distintos | Ocorrências |
|---|---:|---:|
| Referência histórica com aparência de código técnico/kit | 299 | 3.807 |
| Referência histórica descritiva / sem conversão técnica direta | 132 | 4.690 |
| Sem referência, mas regra coincide com código explícito na descrição (proposta para auditoria) | 6 | 8 |
| Sem referência, item identificado pelo próprio código | 9 | 176 |
| Sem equivalência suficiente | 9 | 95 |
| **Total** | **455** | **8.776** |

Assim, **431 códigos** (8.497 ocorrências) têm correspondência exata na tabela histórica; isso NÃO significa 431 códigos tecnicamente certificados.

Classificação aproximada por tipo após refinamento: 193 válvulas, 161 kits, 46 bobinas, 37 peças, 18 outros. Tipos são inferências a partir de código + descrição, não classificação oficial de estoque.

## Variações de descrição e tensão

**224 códigos**, representando **8.281 ocorrências**, possuem mais de uma descrição no histórico. O relatório detalhado registra `quantidade_descricoes_distintas` por código.

**Atenção:** as descrições do CSV foram selecionadas por `MAX(descricao_original)` e são **uma amostra representativa**, não a descrição de cada ocorrência. Não determinar tensão elétrica somente com base nessa descrição. Preservar `tensao_original` por linha para a futura integração.

## Validação independente do dicionário exato

Usando o motor experimental V0.5 *sem* consulta exata ao dicionário:

- 3.525 pares históricos possuem destino com formato aparente de código de válvula.
- O motor conseguiu inferir 2.878 desses códigos pela estrutura.
- 2.683 inferências coincidiam exatamente com o destino histórico; 195 divergiram.
- A concordância entre as inferências emitidas foi **93,2%**, medida **contra a tabela antiga, não contra especificações técnicas auditadas**.
- As divergências incluem sufixos especiais, construção Z/ZC, formatação de indicadores, famílias parecidas e cadastros possivelmente incorretos.

Não é seguro liberar atualização automática de todos os códigos na produção com esses números.

## Exemplos de regras inferidas que coincidem com descrição no PRN, mas ainda requerem auditoria

- `35-EZC35BE4T` → `EZC1335BE04T`
- `42-EZ42BV12` → `EZ1342BV12`
- `60-PE60TV2` → `PE1360TV02`
- `65-E65BV17UT` → `E1365BV17UT`
- `65-EZ65BV17U` → `EZ1365BV17U`
- `90-EZ90IV4T` → `EZ1390IV04T`

## Casos relevantes ainda pendentes

- `K036A1`, `K036A2`, `K036V3R`: kits reconhecíveis, mas sem equivalência exata na lista; normalização do tamanho deve seguir regras específicas de kits.
- `SUD-36630`: termopar identificado pela descrição, mas sem referência técnica inequívoca.
- `785032`, `785033`, `785036`, `785037`: cadastros de corpo/peças com descrição, exigem cadastro próprio e não código de válvula acabada.
- `VALV5`: designação genérica sem equivalência segura.

## Regras de segurança da análise

1. Todas as linhas do relatório têm `atualizar_supabase = NAO`.
2. Não houve atualização ou inserção em `itens_comerciais` nem alteração do importador PRN V5.
3. Antes da integração operacional: validar exceções, preservar tensão, origem e ID por linha, e testar no evento **Criar Pedido**, sem reprocessar PRN a cada importação.
4. O código ERP original deve ser preservado; o código técnico será um campo distinto e versionado.
5. Sem disponibilidade/estoque confirmado, o motor de transformação de válvulas não deve sugerir substituições físicas.

Arquivo detalhado: [455 códigos](./erp_2026-10-15_455_codigos.csv).

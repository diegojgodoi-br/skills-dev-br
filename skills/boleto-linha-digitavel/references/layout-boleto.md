# Layout do boleto e algoritmos

## Boleto bancário: código de barras (44 posições)

| Posição | Tam. | Conteúdo |
|---|---|---|
| 1-3 | 3 | Código do banco |
| 4 | 1 | Moeda (`9` = Real) |
| 5 | 1 | DV geral (módulo 11) |
| 6-9 | 4 | Fator de vencimento |
| 10-19 | 10 | Valor (centavos, sem vírgula) |
| 20-44 | 25 | Campo livre (definido por cada banco) |

## Boleto bancário: linha digitável (47 dígitos)

```
AAABC.CCCCX DDDDD.DDDDDY EEEEE.EEEEEZ K UUUUVVVVVVVVVV
```

| Campo | Conteúdo | DV |
|---|---|---|
| 1 | Banco (3) + moeda (1) + posições 20-24 do código de barras | X: módulo 10 |
| 2 | Posições 25-34 | Y: módulo 10 |
| 3 | Posições 35-44 | Z: módulo 10 |
| 4 | K = DV geral do código de barras (posição 5) | — |
| 5 | Fator (4) + valor (10) | — |

Os DVs X, Y e Z **não existem** no código de barras. Para converter linha → barras: `banco+moeda` + `K` + `fator+valor` + campo1[5..9] + campo2[1..10] + campo3[1..10].

## Arrecadação (começa com 8): código de barras (44)

| Posição | Conteúdo |
|---|---|
| 1 | `8` (produto arrecadação) |
| 2 | Segmento: 1 prefeituras, 2 saneamento, 3 energia/gás, 4 telecom, 5 órgãos governamentais, 6 carnês, 7 multas de trânsito, 9 uso do banco |
| 3 | Identificador de valor: `6` valor em reais (DV mód. 10), `7` referência (mód. 10), `8` valor em reais (mód. 11), `9` referência (mód. 11) |
| 4 | DV geral |
| 5-15 | Valor (11, centavos) |
| 16-19 | Identificação da empresa/órgão (no segmento 6: posições 16-23 = CNPJ, 8 primeiros dígitos) |
| 20-44 | Campo livre da empresa |

**Linha digitável (48):** 4 blocos de 11 dígitos do código de barras, cada um seguido do seu DV, calculado com o **mesmo módulo** indicado na posição 3.

## Algoritmos

**Módulo 10** (DVs dos campos e arrecadação 6/7): da direita para a esquerda, multiplique por 2, 1, 2, 1… Se o produto passar de 9, some os algarismos (12 → 1+2). DV = (10 − soma mod 10) mod 10.

**Módulo 11, bancário** (DV geral, posição 5): pesos 2 a 9 da direita para a esquerda, repetindo, sobre as 43 posições sem a 5ª. DV = 11 − (soma mod 11). Se der 0, 10 ou 11 → **1**.

**Módulo 11, arrecadação** (identificador 8/9): mesmos pesos. Resto 0 ou 1 → **0**; senão 11 − resto.

**Fator de vencimento**
- Vencimentos até 21/02/2025: `fator = dias desde 07/10/1997` (21/02/2025 = 9999).
- A partir de 22/02/2025: `fator = 1000 + dias desde 22/02/2025`.
- Para ler: calcule a data nas duas bases e use a mais próxima da data atual (ou da data de emissão, se conhecida).

## Linhas reais para teste

| Banco | Linha digitável | Resultado esperado |
|---|---|---|
| Itaú (341) | `34191.09008 72564.898723 32408.290008 1 10010000082831` | Válida, R$ 828,31, fator 1001 (23/02/2025 pela regra) |
| Caixa (104) | `10499.00127 00200.001287 70000.000128 1 10990000016000` | Válida, R$ 160,00, fator 1099 |

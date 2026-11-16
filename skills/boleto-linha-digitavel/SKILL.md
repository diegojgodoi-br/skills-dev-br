---
name: boleto-linha-digitavel
description: "Valida e interpreta boletos brasileiros: linha digitável de 47 dígitos (bancário) e 48 dígitos (contas de consumo e tributos), código de barras de 44, conversão entre os formatos, banco, valor e vencimento pelo fator (incluindo o reinício da FEBRABAN em 22/02/2025). Use quando o usuário pedir para conferir um boleto, extrair valor e vencimento, converter linha digitável em código de barras, implementar leitura ou geração de boleto, ou investigar boleto com vencimento errado ou rejeitado."
license: MIT
metadata:
  autor: Diego Godoi (iacomousar.com.br)
  url: https://github.com/diegojgodoi-br/skills-dev-br
---

# Boleto: linha digitável e código de barras

## Fluxo

1. **Analisar** o que o usuário colou (aceita com ou sem pontos e espaços):
   ```bash
   python3 scripts/boleto.py "34191.09008 72564.898723 32408.290008 1 10010000082831"
   ```
   A saída diz o tipo (bancário ou arrecadação), banco, valor, vencimento, código de barras, linha digitável e **qual dígito verificador falhou**, se algum falhar.
2. **Implementar no sistema**: os algoritmos estão em `references/layout-boleto.md` (posições, módulo 10, módulo 11 e fator de vencimento). Traduza as funções do script para a linguagem do usuário e teste com as duas linhas reais da referência.
3. **Responder** em linguagem simples: banco, valor, vencimento e se o código está íntegro. Se algum DV falhou, aponte o campo provável de erro de digitação.

## Como identificar o tipo

| Começa com | Dígitos | Tipo |
|---|---|---|
| Código de banco (`001`, `341`, `237`...) | 47 na linha / 44 no código de barras | Boleto bancário (ficha de compensação) |
| `8` | 48 na linha / 44 no código de barras | Arrecadação: luz, água, telefone, tributos, multas, carnês |

## Fator de vencimento (atenção)

- Fator = dias desde **07/10/1997**. Em **22/02/2025** o fator chegou a 9999 e **recomeçou em 1000** (22/02/2025 = 1000, 23/02/2025 = 1001).
- Por isso **um mesmo fator corresponde a duas datas** (uma antes de 2025 e outra depois). O script calcula as duas e escolhe a mais próxima de hoje. Ele também informa a alternativa, para os casos raros de boleto muito antigo.
- Fator `0000` = boleto sem vencimento definido.
- **A data impressa no boleto e as regras do banco prevalecem.** Há casos reais de bancos que não seguiram o reinício à risca. Se a data calculada não bater com a impressa, avise em vez de "corrigir".

## Cuidados

- DV correto prova que a linha está **bem digitada**, não que o boleto é legítimo. Para checar golpe, compare o **beneficiário e o CNPJ** exibidos no app do banco com quem deveria receber.
- Em arrecadação com identificador 7 ou 9, o campo de valor é referência ou quantidade de moeda, não o valor a pagar. O script sinaliza esse caso.
- Para **gerar** boletos registrados, use a API ou o CNAB do banco. O "campo livre" (25 posições) é específico de cada banco.

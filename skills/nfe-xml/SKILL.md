---
name: nfe-xml
description: "Lê XMLs de NF-e e NFC-e (modelos 55 e 65): valida a chave de acesso de 44 posições (inclusive com CNPJ alfanumérico), extrai emitente, destinatário, itens, NCM, CFOP, totais, impostos e protocolo da SEFAZ, e gera CSV para Excel/BI. Use quando o usuário enviar XMLs de nota fiscal, pedir para conferir, somar ou cruzar notas, montar planilha de compras ou vendas a partir de XML, validar uma chave de acesso ou entender um campo do XML, incluindo os grupos de IBS e CBS da reforma tributária."
license: MIT
metadata:
  autor: Diego Godoi (iacomousar.com.br)
  url: https://github.com/diegojgodoi-br/skills-dev-br
---

# NF-e: ler XML e validar chave de acesso

## Fluxo

1. **Validar uma chave** (44 posições, com ou sem o prefixo `NFe`):
   ```bash
   python3 scripts/nfe.py chave 52060433009911002506550120000007800267301615
   ```
   Mostra UF, ano/mês, CNPJ do emitente, modelo, série, número, tipo de emissão e se o DV confere.
2. **Ler XMLs** (arquivo ou pasta inteira, busca recursiva):
   ```bash
   python3 scripts/nfe.py ler pasta_xmls --csv relatorio     # gera relatorio_notas.csv e relatorio_itens.csv
   python3 scripts/nfe.py ler nota.xml --json
   ```
   O CSV usa `;` e vírgula decimal, e abre direto no Excel em português. Arquivos que não são NF-e vão para a lista de erros sem interromper o lote.
3. **Analisar**: com o CSV em mãos, responda o que o usuário pediu (total por fornecedor, por CFOP, por NCM, notas sem protocolo de autorização, chaves inválidas etc.). Faça as contas com código, nunca de cabeça. Se o usuário quiser planilha, entregue a planilha.

## O que conferir sempre

- **Autorização**: `cStat` 100 (autorizada) ou 150 (autorizada fora do prazo). Um XML sem `protNFe` não prova que a nota foi autorizada. Para ter certeza, consulte a chave no portal da SEFAZ.
- **Chave x conteúdo**: a UF, o CNPJ, a série e o número da chave devem bater com `ide` e `emit`.
- **Entrada x saída**: `tpNF` 0 = entrada, 1 = saída. O CFOP começa com 1/2/3 (entrada) ou 5/6/7 (saída).
- **Duplicidade**: a mesma chave em dois arquivos (comum quando se baixa de mais de uma fonte).

## Reforma tributária (IBS/CBS)

Desde 2026 o XML pode trazer o grupo `IBSCBS` em cada item (`det/imposto/IBSCBS`) e totais em `total/IBSCBSTot` (NT 2025.002-RTC). O script indica por item se o grupo existe (`tem_grupo_ibscbs`) e guarda os totais como estão no XML (`ibs_cbs_totais`), sem depender da versão do leiaute. A nota técnica ainda está mudando: para interpretar campo a campo, consulte a versão vigente no Portal Nacional da NF-e.

## Cuidados

- Os XMLs têm dados de clientes (CPF, endereço). Não cole em serviços externos sem necessidade e não publique os CSVs.
- Esta skill **lê** XML. Para **emitir** NF-e é preciso certificado digital, assinatura XML e webservices da SEFAZ. Nesse caso, recomende uma biblioteca mantida pela comunidade (ex.: NFePHP, ACBr) em vez de escrever do zero.
- Mapa de campos em `references/campos-xml-nfe.md`.

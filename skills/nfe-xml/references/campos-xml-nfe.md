# Mapa rápido do XML da NF-e (leiaute 4.00)

Namespace: `http://www.portalfiscal.inf.br/nfe`. O XML autorizado vem como `nfeProc` > `NFe` + `protNFe`.

## Chave de acesso (44 posições)

| Posições | Tam. | Campo | Observação |
|---|---|---|---|
| 1-2 | 2 | cUF | Código IBGE da UF (41 = PR, 35 = SP, 52 = GO…) |
| 3-6 | 4 | AAMM | Ano e mês de emissão |
| 7-20 | 14 | CNPJ do emitente | Pode ter letras nas posições 7-18 (CNPJ alfanumérico) |
| 21-22 | 2 | mod | 55 = NF-e, 65 = NFC-e |
| 23-25 | 3 | serie | |
| 26-34 | 9 | nNF | Número da nota |
| 35 | 1 | tpEmis | 1 = normal; outros valores = contingências |
| 36-43 | 8 | cNF | Código numérico aleatório |
| 44 | 1 | cDV | Módulo 11, pesos 2-9 da direita para a esquerda; resto 0 ou 1 → 0 |

Com CNPJ alfanumérico, cada caractere vale **ASCII − 48** no cálculo do DV (para dígitos, nada muda). Regex: `^[0-9]{6}[A-Z0-9]{12}[0-9]{26}$`.

Exemplo para teste (Manual de Orientação do Contribuinte): `52060433009911002506550120000007800267301615`.

## Caminhos mais usados

| Informação | Caminho |
|---|---|
| Chave | atributo `Id` de `infNFe` (sem o prefixo `NFe`) |
| Número / série / modelo | `ide/nNF`, `ide/serie`, `ide/mod` |
| Data de emissão | `ide/dhEmi` |
| Entrada/saída | `ide/tpNF` (0/1) |
| Natureza da operação | `ide/natOp` |
| Emitente | `emit/CNPJ` (ou `CPF`), `emit/xNome`, `emit/enderEmit/UF` |
| Destinatário | `dest/CNPJ`, `dest/CPF` ou `dest/idEstrangeiro`; `dest/xNome` |
| Itens | `det` (atributo `nItem`) → `prod/cProd`, `xProd`, `NCM`, `CFOP`, `uCom`, `qCom`, `vUnCom`, `vProd` |
| Impostos do item | `det/imposto/ICMS`, `IPI`, `PIS`, `COFINS`, `IBSCBS` |
| Totais | `total/ICMSTot/vProd`, `vDesc`, `vFrete`, `vICMS`, `vST`, `vIPI`, `vPIS`, `vCOFINS`, `vNF` |
| Totais IBS/CBS | `total/IBSCBSTot` (reforma tributária, NT 2025.002-RTC) |
| Pagamento | `pag/detPag/tPag`, `vPag` |
| Protocolo | `protNFe/infProt/cStat`, `xMotivo`, `nProt`, `dhRecbto` |

## cStat mais comuns no protocolo

| cStat | Significado |
|---|---|
| 100 | Autorizado o uso da NF-e |
| 150 | Autorizado o uso, fora do prazo |
| 110 / 301 / 302 | Uso denegado |
| 135 | Evento registrado e vinculado à NF-e. É o retorno do evento de cancelamento (XML separado, `procEventoNFe`); o `protNFe` da autorização continua mostrando 100 |

Em caso de dúvida sobre a situação atual (cancelada, por exemplo), consulte a chave no portal da SEFAZ ou com o serviço de consulta de protocolo.

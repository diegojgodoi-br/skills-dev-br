# NFS-e nacional: campos e fontes

Mapeamento de **novembro de 2026**. Namespace: `http://www.sped.fazenda.gov.br/nfse`. Leiaute 1.00/1.01.

## Chave de acesso (50 posições)

| Posição | Tam. | Campo |
|---|---|---|
| 1–7 | 7 | Código IBGE do município |
| 8 | 1 | Ambiente gerador: 1 = sistema próprio do município, 2 = Sefin Nacional |
| 9 | 1 | Tipo de inscrição: 1 = CPF, 2 = CNPJ |
| 10–23 | 14 | CPF (com 000 à esquerda) ou CNPJ do emitente |
| 24–36 | 13 | Número da NFS-e |
| 37–40 | 4 | Ano e mês de emissão (AAMM) |
| 41–49 | 9 | Código numérico |
| 50 | 1 | Dígito verificador |

No XML o atributo `Id` de `infNFSe` é `NFS` + a chave (53 caracteres).

**Em aberto:** a regra do DV e o uso de letras (CNPJ alfanumérico) na chave da NFS-e não estão nos manuais públicos consultados. Não rejeite chave por DV; confirme na consulta pública.

## Id da DPS

`DPS` + município emissor (7) + tipo de inscrição (1) + CPF/CNPJ (14) + série (5) + número da DPS (15) = 45 caracteres.

Faixas de série: 00001–49999 API do contribuinte; 50000–69999 aplicativo; 70000–79999 emissor web.

## Estrutura principal

```
NFSe
└─ infNFSe (Id="NFS...")
   ├─ xLocEmi, nNFSe, xLocIncid, ambGer, cStat, dhProc
   ├─ emit (CNPJ/CPF, IM, xNome, enderNac)
   ├─ valores (vBC, pAliqAplic, vISSQN, vTotalRet, vLiq)
   └─ DPS
      └─ infDPS (Id="DPS...")
         ├─ tpAmb, dhEmi, verAplic, serie, nDPS, dCompet, tpEmit, cLocEmi
         ├─ prest (CNPJ/CPF, IM, regTrib: opSimpNac, regApTribSN, regEspTrib)
         ├─ toma (CNPJ/CPF/NIF, xNome, end)
         ├─ serv
         │  ├─ locPrest (cLocPrestacao)
         │  └─ cServ (cTribNac, cTribMun, xDescServ, cNBS)
         ├─ valores
         │  ├─ vServPrest (vServ)
         │  └─ trib
         │     ├─ tribMun (tribISSQN, tpRetISSQN)
         │     └─ totTrib
         └─ IBSCBS (finNFSe, indFinal, cIndOp, indDest, valores/trib/gIBSCBS: CST, cClassTrib, gTribRegular, gDif)
```

Totais de IBS/CBS da nota aparecem em `infNFSe` (ex.: `vIBSTot`, `vCBS`, `vTotNF`) conforme a NT SE/CGNFS-e 004.

## DANFSe (NT SE/CGNFS-e 008)

Novo modelo em vigor desde agosto de 2026: chave de 50 dígitos em bloco único, QR Code para a consulta pública, bloco "Tributação IBS/CBS", marcas d'água CANCELADA e SUBSTITUÍDA.

## Fontes

- Portal NFS-e (gov.br/nfse): Manual dos Contribuintes – API do Emissor Público Nacional, FAQ, esquemas XSD v1.01, NT SE/CGNFS-e 004 (leiaute RTC) e 008 (DANFSe).
- Consulta pública: https://www.nfse.gov.br/consultapublica

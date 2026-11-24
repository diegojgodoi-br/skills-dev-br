---
name: nfse-nacional
description: "Trabalha com a NFS-e do padrão nacional (Emissor Nacional / Sistema Nacional NFS-e): decompõe a chave de acesso de 50 posições e o Id da DPS, lê pastas de XML de NFS-e e DPS, extrai prestador, tomador, serviço, ISS, retenção, valor líquido e o grupo IBS/CBS da reforma, aponta notas duplicadas ou só com DPS e gera CSV para Excel. Use quando o usuário enviar XMLs de nota de serviço, pedir para conferir ou somar NFS-e, montar planilha de serviços tomados ou prestados, entender um campo do XML ou da DANFSe, ou integrar um sistema à API do Sistema Nacional NFS-e."
license: MIT
metadata:
  autor: Diego Godoi (iacomousar.com.br)
  url: https://github.com/diegojgodoi-br/skills-dev-br
---

# NFS-e padrão nacional

## Fluxo

1. **Entender uma chave ou Id de DPS:**
   ```bash
   python3 scripts/nfse.py chave 41130022212345678000195000000000012326111234567891
   python3 scripts/nfse.py dps DPS411300221234567800019500001000000000000123
   ```
   Mostra município (IBGE), ambiente gerador, CPF/CNPJ, número, ano/mês e código. O script **não confere o dígito verificador**: a regra não está nos manuais públicos e quem gera a chave é o Sistema Nacional. Para provar que a nota existe, use a consulta pública (`https://www.nfse.gov.br/consultapublica`).
2. **Ler XMLs** (arquivo ou pasta, busca recursiva):
   ```bash
   python3 scripts/nfse.py ler pasta_xmls --csv relatorio     # gera relatorio_nfse.csv
   python3 scripts/nfse.py ler nota.xml --json
   ```
   O CSV usa `;` e vírgula decimal. Arquivos que não são NFS-e vão para a lista de erros sem parar o lote.
3. **Analisar:** responda o que foi pedido (total por tomador, por código de tributação, ISS retido x não retido, notas sem grupo IBS/CBS, duplicadas). Faça as contas com código.

## O que conferir sempre

- **NFS-e x DPS:** a DPS é o pedido do emissor. Só o XML com `infNFSe` (e `nNFSe`, `dhProc`) é a nota gerada. O script marca quando o arquivo é só a DPS.
- **Município de incidência:** o ISS pode ser devido em município diferente do emissor (`xLocIncid`). Isso muda guia e retenção.
- **Retenção de ISS:** `tpRetISSQN` 1 = não retido, 2 = retido pelo tomador, 3 = retido pelo intermediário. Quem toma o serviço precisa recolher quando é 2.
- **Valor líquido:** `vLiq` = serviço menos retenções e descontos. Líquido maior que o serviço é erro.
- **Reforma tributária:** desde 2026 a DPS pode trazer o grupo `IBSCBS` (`cIndOp`, `CST`, `cClassTrib`). O script indica se existe. Para simular valores, use a skill `reforma-tributaria-ibs-cbs`.
- **Duplicidade:** a mesma chave em dois arquivos (comum ao baixar do portal e do e-mail).

## Para quem integra

- API do Sistema Nacional: `POST /nfse` (envia a DPS assinada e recebe a NFS-e), `GET /nfse/{chaveAcesso}`, `GET /dps/{id}`, eventos em `/nfse/{chaveAcesso}/eventos`. Há ambiente de **produção restrita** para testes.
- Autenticação com certificado digital ICP-Brasil (mTLS) e DPS assinada. Use uma biblioteca mantida pela comunidade em vez de escrever assinatura XML do zero.
- No emissor nacional, alguns campos municipais **não devem ser enviados** (ex.: `cTribMun` em certos casos); a rejeição costuma vir daí. Consulte a nota técnica vigente.
- Mapa de campos, fontes e pontos em aberto em `references/campos-nfse.md`.

## Cuidados

- XMLs têm dados de clientes (CPF, endereço). Não publique os CSVs.
- Municípios com sistema próprio ainda podem emitir no padrão deles; o script lê só o leiaute nacional.
- Regras e leiaute mudam por nota técnica. Diga ao usuário que o mapeamento foi feito em novembro de 2026.

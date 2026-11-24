# Transição, campos e fontes

Regras conferidas em **novembro de 2026**. Confira a versão vigente antes de ir para produção.

## Calendário (EC 132/2023 e LC 214/2025)

| Ano | CBS | IBS | ICMS/ISS | PIS/Cofins | IPI |
|---|---|---|---|---|---|
| 2026 | 0,9% (teste) | 0,1% (teste) | integrais | vigentes | vigente |
| 2027 | referência − 0,1 p.p. | 0,05% UF + 0,05% município | integrais | **extintos** | zero, exceto ZFM |
| 2028 | referência − 0,1 p.p. | 0,05% + 0,05% | integrais | — | zero, exceto ZFM |
| 2029 | referência | sobe para compensar | 90% | — | zero, exceto ZFM |
| 2030 | referência | sobe | 80% | — | zero, exceto ZFM |
| 2031 | referência | sobe | 70% | — | zero, exceto ZFM |
| 2032 | referência | sobe | 60% | — | zero, exceto ZFM |
| 2033 | integral | integral | **extintos** | — | zero, exceto ZFM |

- **2026:** os valores de teste são destacados na nota e podem ser compensados com PIS/Cofins. Quem cumpre as obrigações acessórias fica dispensado de recolher. Optantes do Simples Nacional ficam fora do teste. A LC 227/2026 prevê que, se houver autuação por falha em obrigação acessória em 2026, o contribuinte é intimado e tem 60 dias para regularizar sem multa.
- **Alíquota de referência:** fixada por resolução do Senado a partir de cálculo do TCU. A soma IBS + CBS tem uma trava de revisão: se a estimativa para 2033 passar de 26,5%, o governo deve propor ajuste.
- **Imposto Seletivo** (produtos prejudiciais à saúde ou ao meio ambiente) começa em 2027.

## Simples Nacional

- Continua como regime diferenciado e recolhe IBS/CBS no DAS conforme os tributos atuais forem substituídos.
- Pode optar pelo **regime regular** de IBS/CBS (escolha semestral a partir de 2027), passando a destacar o tributo cheio e a dar crédito integral ao cliente.
- Prazos de opção e cancelamento são definidos por resoluções do CGSN. Confira a resolução vigente antes de orientar.

## Campos no sistema

| Onde | Campo | Formato |
|---|---|---|
| Cadastro de item | CST IBS/CBS | 3 dígitos |
| Cadastro de item | `cClassTrib` (classificação tributária) | 6 dígitos |
| NF-e/NFC-e, por item | grupo `det/imposto/IBSCBS` | NT 2025.002-RTC |
| NF-e/NFC-e, total | `total/IBSCBSTot` | NT 2025.002-RTC |
| NFS-e nacional | grupo `IBSCBS` no DPS (`cIndOp`, `gIBSCBS` com `CST` e `cClassTrib`) | NT SE/CGNFS-e 004 |

Tabela oficial de CST e `cClassTrib`: Portal Nacional da NF-e e Portal da NFS-e.

## Fontes

- Emenda Constitucional 132/2023 e Lei Complementar 214/2025 (arts. 125 a 129 e 348 tratam da transição).
- Lei Complementar 227/2026 (CGIBS, processo administrativo, ajustes de 2026).
- TCU, Painel da Reforma Tributária (cronograma de fixação das alíquotas de referência).
- Notas técnicas: NF-e NT 2025.002-RTC; NFS-e NT SE/CGNFS-e 004 e 008 (DANFSe).

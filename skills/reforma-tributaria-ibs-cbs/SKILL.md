---
name: reforma-tributaria-ibs-cbs
description: "Explica e simula a reforma tributária do consumo (IBS, CBS e Imposto Seletivo): calendário de transição de 2026 a 2033, cálculo 'por fora' com reduções de 30%, 60% e alíquota zero, separação de preço com tributo embutido, apuração débito x crédito e o que muda no sistema (NF-e, NFS-e, cadastro de produtos, split payment). Use quando o usuário perguntar quanto vai pagar de IBS/CBS, pedir para simular preço ou margem na reforma, adaptar ERP, PDV ou emissor de nota aos grupos IBSCBS, explicar a reforma para um cliente, ou citar LC 214/2025, CST e cClassTrib."
license: MIT
metadata:
  autor: Diego Godoi (iacomousar.com.br)
  url: https://github.com/diegojgodoi-br/skills-dev-br
---

# Reforma tributária: IBS e CBS na prática

## Fluxo

1. **Situe no calendário.** Antes de qualquer conta, descubra o ano da operação. Rode:
   ```bash
   python3 scripts/reforma.py calendario
   ```
   2026 é teste (CBS 0,9% e IBS 0,1%). De 2027 em diante a CBS é cheia e a alíquota de referência é fixada pelo Senado.
2. **Pegue as alíquotas certas.** Para 2026 o script já sabe. Para 2027 em diante **pergunte ao usuário ou confira a resolução do Senado vigente** e passe `--cbs`/`--ibs`. Nunca invente a alíquota de referência: estimativas de jornal não servem para preço nem para nota.
3. **Simule** (sempre com o script, nunca de cabeça):
   ```bash
   python3 scripts/reforma.py simular 1000 --ano 2026
   python3 scripts/reforma.py simular 1000 --ano 2027 --cbs <alíquota> --reducao 60
   python3 scripts/reforma.py por-dentro 1150 --cbs <cbs> --ibs <ibs>      # separa a base de um preço final
   python3 scripts/reforma.py apurar --vendas 100000 --compras 40000 --cbs <cbs> --ibs <ibs>
   ```
4. **Entregue** no formato que o usuário pediu: para dono de negócio, um quadro curto (preço, tributo, o que muda); para dev, a lista de campos e regras de `references/transicao-e-campos.md`; para contador, a apuração com débitos, créditos e saldo.

## Conceitos que o usuário precisa entender

- **Cálculo por fora:** IBS e CBS não entram na própria base (diferente do ICMS hoje). Preço de R$ 1.000 com 10% vira R$ 1.100.
- **Não cumulatividade ampla:** em regra, tudo que a empresa compra com IBS/CBS destacado gera crédito, exceto uso e consumo pessoal. O crédito depende de o fornecedor ter destacado e, com o split payment, de o tributo ter sido efetivamente pago.
- **Split payment:** o tributo é separado no momento do pagamento (cartão, Pix, boleto) e vai direto ao Fisco. Impacta o fluxo de caixa de quem hoje usa o imposto como capital de giro.
- **Reduções:** 60% (saúde, educação, medicamentos, alimentos fora da cesta, insumos agropecuários e outros), 30% (profissões intelectuais regulamentadas), alíquota zero (Cesta Básica Nacional e itens específicos). A lista exata está nos anexos da LC 214/2025: confira o item, não a categoria.
- **Simples Nacional:** continua existindo. A empresa pode recolher IBS/CBS dentro do DAS ou optar pelo regime regular para dar crédito cheio ao cliente PJ. Essa escolha pesa em quem vende para empresas.

## Para quem programa

- **Cadastro de produto/serviço** ganha CST de IBS/CBS (3 dígitos) e `cClassTrib` (6 dígitos). Sem isso a nota sai errada ou é rejeitada.
- **NF-e/NFC-e:** grupo `IBSCBS` por item e `IBSCBSTot` no total (NT 2025.002-RTC). Para ler XMLs, use a skill `nfe-xml`.
- **NFS-e:** o padrão nacional traz o grupo IBS/CBS. Para ler e conferir, use a skill `nfse-nacional`.
- **Preço e margem:** guarde base e tributo separados. Não calcule tributo sobre um preço que já tem tributo.
- **Arredondamento:** some por item e arredonde em centavos, como na nota. Use `Decimal`, nunca `float`.

## Cuidados

- Normas da reforma ainda estão saindo (resoluções do Senado, regulamentos do CGIBS, notas técnicas). Diga ao usuário a data das regras usadas e recomende confirmar com o contador antes de mudar preço ou contrato.
- Isto não é consultoria tributária. Benefícios específicos (ZFM, regimes específicos como combustíveis, financeiro, imóveis, saúde suplementar) têm regras próprias: sinalize e encaminhe.
- Detalhes do calendário, campos e fontes em `references/transicao-e-campos.md`.

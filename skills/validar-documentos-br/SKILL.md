---
name: validar-documentos-br
description: "Valida, gera dígito verificador e adapta sistemas para CPF e CNPJ, incluindo o CNPJ alfanumérico (letras e números, em vigor desde julho de 2026). Use quando o usuário pedir para validar CPF/CNPJ, escrever ou revisar função de validação, preparar banco de dados, máscaras, APIs ou integrações para o CNPJ alfanumérico, ou investigar por que um CNPJ com letras está sendo rejeitado."
license: MIT
metadata:
  autor: Diego Godoi (iacomousar.com.br)
  url: https://github.com/diegojgodoi-br/skills-dev-br
---

# Validar documentos brasileiros (CPF e CNPJ alfanumérico)

## Regras que você precisa aplicar

**CPF**: 11 dígitos, 2 DVs por módulo 11 (pesos 10..2 e depois 11..2; resto 0 ou 1 vira 0). Sequências repetidas (111.111.111-11) são inválidas.

**CNPJ** (IN RFB nº 2.229/2024; novas inscrições alfanuméricas desde julho de 2026; os CNPJs existentes não mudam):
- 14 posições. As **12 primeiras** aceitam `0-9` e `A-Z` (maiúsculas). Os **2 últimos (DV) são sempre números**.
- Cada caractere vale **código ASCII − 48**: `0`-`9` continuam valendo 0-9; `A`=17, `B`=18 … `Z`=42.
- DV1: pesos `5,4,3,2,9,8,7,6,5,4,3,2` nas 12 posições. DV2: pesos `6,5,4,3,2,9,8,7,6,5,4,3,2` nas 13 posições (base + DV1). Resto < 2 → 0; senão 11 − resto.
- Para CNPJ só com números o resultado é idêntico ao algoritmo antigo. Um validador novo funciona para os dois formatos.
- Exemplo oficial (Serpro/RFB) para teste: `12.ABC.345/01DE-35`.

## Fluxo

1. **Validar ou calcular DV**: use `scripts/documentos_br.py` (Python), `scripts/documentos_br.php` (PHP 7.4+) ou `scripts/documentos_br.js` (JS/TS). As três versões foram testadas entre si e contra o exemplo oficial. Copie a do stack do usuário em vez de reescrever.
   ```bash
   python3 scripts/documentos_br.py validar 12.ABC.345/01DE-35
   python3 scripts/documentos_br.py dv-cnpj 12ABC34501DE
   ```
2. **Revisar código existente**: procure validações que quebram com letras. Leia `references/adaptar-cnpj-alfanumerico.md` e varra o projeto pelos padrões listados lá (`\d{14}`, `is_numeric`, `parseInt`, `BIGINT`, máscara `99.999.999/9999-99`, `intval`, comparação numérica, `LPAD` com zeros).
3. **Entregar**: diga o que muda em cada camada (banco, back-end, front-end, integrações, relatórios) com o trecho exato a trocar. Para dados de teste, gere CNPJs alfanuméricos válidos com `dv-cnpj` ou use o Simulador Nacional de CNPJ da Receita.

## Cuidados

- Normalize antes de validar: remova `.`, `/`, `-`, espaços e converta para maiúsculas. Guarde **sem máscara** e em `CHAR(14)`/`VARCHAR(14)`, nunca em coluna numérica.
- Validar o DV prova só que o número é bem formado, **não que a empresa existe ou está ativa**. Para isso é preciso consultar a Receita ou um serviço de consulta.
- Não gere CPF/CNPJ "válidos" para cadastrar em sistemas reais de terceiros. Gerar DV é para testes e homologação do próprio sistema.

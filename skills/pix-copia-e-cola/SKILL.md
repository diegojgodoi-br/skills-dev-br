---
name: pix-copia-e-cola
description: "Gera, lê e valida Pix copia e cola (BR Code / QR Code Pix) seguindo o Manual de Padrões para Iniciação do Pix do Banco Central: campos EMV, CRC16, txid, valor, estático x dinâmico. Use quando o usuário pedir para gerar um QR Code ou código Pix, decodificar um copia e cola, descobrir por que um Pix é rejeitado pelo banco (CRC inválido, campo errado), implementar geração de Pix em PHP/JS/Python ou revisar uma integração Pix."
license: MIT
metadata:
  autor: Diego Godoi (iacomousar.com.br)
  url: https://github.com/diegojgodoi-br/skills-dev-br
---

# Pix copia e cola (BR Code)

O "copia e cola" é o texto que vai dentro do QR Code. Ele é uma sequência TLV: cada campo é `ID (2 dígitos) + tamanho (2 dígitos) + valor`. Os campos estão em `references/campos-brcode.md`.

## Fluxo

1. **Ler/diagnosticar um código**: rode `scripts/pix_brcode.py ler "<código>"`. A saída mostra a chave, o valor, o nome, a cidade, o txid, se o código é estático ou dinâmico e os problemas encontrados (CRC, moeda, formato do valor, campo Pix ausente).
2. **Gerar um Pix estático** (cobrança simples, sem integração com banco):
   ```bash
   python3 scripts/pix_brcode.py gerar --chave email@empresa.com --nome "Minha Loja" --cidade Londrina --valor 49.90 --txid PEDIDO123
   ```
   O gerador reproduz byte a byte o exemplo do manual do Banco Central (CRC `1D3D`). Para gerar a imagem do QR Code, use uma biblioteca de QR (ex.: `qrcode` em Python, `endroid/qr-code` em PHP) sobre o texto gerado.
3. **Implementar no sistema do usuário**: traduza `gerar_estatico` e `crc16_ccitt` para a linguagem dele, sem mudar a lógica. Depois teste com o exemplo do BCB (ver referência).

## Regras que mais causam erro

- **O CRC é calculado sobre o texto inteiro INCLUINDO `6304`** e o resultado vai no final, com 4 hex maiúsculos. Algoritmo: CRC16/CCITT-FALSE (polinômio `0x1021`, inicial `0xFFFF`).
- **Valor** com ponto e 2 casas (`12.50`), sem separador de milhar. Sem o campo 54, a pessoa digita o valor no app.
- **Nome** até 25 caracteres e **cidade** até 15. Prefira sem acento, porque alguns apps rejeitam.
- **txid no estático**: até 25 caracteres alfanuméricos ou `***` quando não houver.
- **Tamanho** de cada campo com 2 dígitos e contado em caracteres. Errar o tamanho do campo 26 (chave) quebra o código todo.
- Chave de telefone no formato `+5543999999999`. Chave aleatória (EVP) em minúsculas, como foi cadastrada.

## Estático x dinâmico

- **Estático**: o código já tem chave e valor. Serve para cobrança simples e não confirma o pagamento sozinho.
- **Dinâmico**: o campo Pix traz uma **URL** (subcampo 25) e os dados são buscados na API do PSP do recebedor. Para confirmar o pagamento automaticamente (webhook), é preciso usar a **API Pix do banco/PSP** (cobrança `cob`/`cobv`, certificado mTLS). A skill gera e lê o código, mas não substitui essa integração.

## Cuidados

- Confirme sempre a chave e o nome do recebedor antes de publicar um QR. Golpes trocam a chave mantendo o nome.
- O manual do Pix é atualizado com frequência (a versão 2.10.0 saiu em agosto de 2026). Os campos básicos acima são estáveis, mas confira o manual vigente para recursos novos (Pix Automático, Pix por aproximação etc.).

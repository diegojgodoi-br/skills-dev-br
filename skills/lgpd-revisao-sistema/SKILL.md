---
name: lgpd-revisao-sistema
description: "Revisa um sistema (código, banco de dados, logs, formulários, integrações) sob a ótica da LGPD (Lei 13.709/2018): mapeia dados pessoais e sensíveis, aponta excesso de coleta, dados em log, falta de retenção, senhas fracas, lacunas nos direitos dos titulares e prepara a resposta a incidente no prazo da ANPD. Use quando o usuário pedir para adequar um sistema à LGPD, fazer inventário ou mapa de dados pessoais, revisar privacidade de um projeto, preparar resposta a vazamento ou montar o checklist técnico de LGPD para desenvolvedores."
license: MIT
metadata:
  autor: Diego Godoi (iacomousar.com.br)
  url: https://github.com/diegojgodoi-br/skills-dev-br
---

# Revisão de LGPD para sistemas

Esta skill faz a **parte técnica** da adequação: onde estão os dados pessoais, como entram, onde ficam, quem acessa, quanto tempo ficam e como saem. A conclusão jurídica (base legal adequada, contratos, políticas) é do jurídico ou do encarregado (DPO). Deixe isso explícito no relatório.

## Fluxo

1. **Escopo**: qual sistema, quais partes você tem (código, schema do banco, prints de telas, lista de integrações) e se ele trata dados de crianças/adolescentes ou dados sensíveis.
2. **Varredura automática** (roda local, não envia nada para fora):
   ```bash
   python3 scripts/mapear_dados_pessoais.py caminho/do/projeto --md mapa.md
   ```
   Ela encontra campos com dado pessoal/sensível, dados reais esquecidos no repositório, dados indo para log e senhas com hash fraco. O relatório **mascara** os dados que encontra. Leia o contexto de cada ponto antes de classificar: a varredura dá pistas, não conclusões.
3. **Revisão guiada**: percorra `references/checklist-lgpd-dev.md` (coleta, armazenamento, acesso, retenção, compartilhamento, direitos dos titulares, segurança, incidentes) e marque cada item como OK, lacuna ou não se aplica, com evidência (arquivo:linha, tabela, tela).
4. **Entregar** um relatório com:
   - Inventário: dado → finalidade → onde está → quem acessa → retenção → compartilhado com quem
   - Lacunas por prioridade: **Alta** (dado sensível exposto, senha fraca, dado pessoal em log ou repositório, sem controle de acesso), **Média** (sem retenção/descarte, coleta excessiva, sem trilha de auditoria), **Baixa** (melhorias de processo)
   - Correção técnica concreta para cada lacuna
   - Pontos que precisam de decisão do jurídico/DPO (base legal, consentimento, transferência internacional)

## Incidente com dados pessoais (vazamento)

Se o usuário relatar um incidente, priorize:
1. **Conter** (revogar credenciais, fechar o acesso, preservar logs e evidências).
2. **Avaliar o risco** aos titulares: tipo de dado (sensível, financeiro, de criança), volume e possibilidade de dano.
3. **Prazo**: pela Resolução CD/ANPD nº 15/2024, se o incidente puder causar risco ou dano relevante, o controlador comunica a ANPD e os titulares em **3 dias úteis** a partir de quando soube que dados pessoais foram afetados (em dobro para agentes de pequeno porte). Informações que faltarem podem ser complementadas em até 20 dias úteis.
4. Ajude a montar a linha do tempo e o rascunho técnico da comunicação. A decisão de comunicar e o envio são do controlador, com o encarregado/jurídico.

## Cuidados

- Não peça nem copie dados pessoais reais para a conversa. Trabalhe com schema, código e amostras anonimizadas.
- Não afirme que o sistema "está em conformidade com a LGPD". Diga quais controles técnicos foram verificados e quais lacunas restam.
- Legislação e regulamentos da ANPD mudam: para prazos e obrigações, confira o texto vigente no site da ANPD.

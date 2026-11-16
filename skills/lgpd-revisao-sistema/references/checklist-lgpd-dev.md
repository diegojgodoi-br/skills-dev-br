# Checklist técnico de LGPD para sistemas

Marque cada item como **OK**, **Lacuna** ou **N/A**, sempre com evidência (arquivo:linha, tabela, tela, configuração).

## 1. Inventário e finalidade (art. 6º e art. 37)

- [ ] Cada campo pessoal tem uma finalidade clara (por que coletamos?)
- [ ] Não há coleta "por via das dúvidas" (necessidade/minimização: CPF, data de nascimento, gênero só se usados)
- [ ] Existe registro das operações de tratamento (o que, para quê, onde, com quem): o art. 37 exige esse registro
- [ ] Dados sensíveis identificados à parte (art. 5º, II: origem racial ou étnica, convicção religiosa, opinião política, filiação a sindicato ou organização religiosa, filosófica ou política, saúde, vida sexual, dado genético ou biométrico)
- [ ] Dados de crianças e adolescentes identificados (art. 14: tratamento no melhor interesse; para crianças, consentimento específico de pelo menos um dos pais ou responsável, com as exceções da lei)

## 2. Coleta (formulários, APIs, integrações)

- [ ] Formulários pedem só o necessário. Campos opcionais estão marcados como opcionais
- [ ] Quando a base legal for consentimento: registro de quando, como e para quê foi dado, e opção de revogar
- [ ] Aviso de privacidade acessível no ponto de coleta
- [ ] Dados recebidos de terceiros/integrações mapeados (origem, contrato)

## 3. Armazenamento

- [ ] Senhas com `password_hash`/bcrypt/argon2. **Nunca** md5/sha1 nem texto puro
- [ ] Dados sensíveis e documentos (CPF, RG, dados de saúde) com proteção adicional: criptografia em repouso ou, no mínimo, acesso restrito por perfil
- [ ] Backups e dumps protegidos (criptografados, fora da webroot, com acesso restrito) e incluídos na política de retenção
- [ ] Nenhum dado real em repositório, fixtures, seeds, prints ou planilhas de teste. Use dados sintéticos
- [ ] Ambientes de teste/homologação sem cópia de produção. Se for inevitável, com dados anonimizados

## 4. Acesso

- [ ] Controle de acesso por perfil (quem vê CPF, salário, dados de saúde?)
- [ ] Usuário do banco da aplicação com privilégio mínimo
- [ ] Trilha de auditoria: quem consultou, alterou ou exportou dados pessoais, e quando
- [ ] Exportações (CSV/Excel) controladas e registradas
- [ ] Contas de ex-colaboradores desativadas. Credenciais compartilhadas eliminadas

## 5. Logs e observabilidade

- [ ] Logs não registram senha, token, CPF completo, cartão ou dado de saúde. Mascarar (`529.***.***-**`)
- [ ] Ferramentas de erro/APM (Sentry, New Relic etc.) com filtro de dados pessoais
- [ ] Retenção de logs definida

## 6. Retenção e descarte (art. 15 e 16)

- [ ] Prazo de guarda definido por tipo de dado (obrigação legal, contrato, finalidade)
- [ ] Rotina de descarte ou anonimização ao fim do prazo. Inclui backups e réplicas
- [ ] "Excluir conta" realmente exclui ou anonimiza (e não só marca `ativo = 0` para sempre, sem justificativa)

## 7. Compartilhamento e transferência

- [ ] Lista de operadores/terceiros que recebem dados (e-mail marketing, CRM, nuvem, BI, IA)
- [ ] Contratos com cláusulas de proteção de dados
- [ ] Transferência internacional identificada (nuvem fora do Brasil, APIs estrangeiras): exige mecanismo previsto na LGPD e nas resoluções da ANPD
- [ ] Envio a ferramentas de IA: avaliar se precisa mandar dado pessoal; anonimizar quando possível

## 8. Direitos dos titulares (art. 18)

O sistema (ou o processo) consegue atender, em prazo razoável:
- [ ] Confirmação de que há tratamento e **acesso** aos dados
- [ ] **Correção** de dados incompletos, inexatos ou desatualizados
- [ ] **Anonimização, bloqueio ou eliminação** de dados desnecessários ou excessivos
- [ ] **Portabilidade**
- [ ] **Eliminação** dos dados tratados com consentimento
- [ ] Informação sobre com quem os dados foram compartilhados
- [ ] **Revogação do consentimento**
- [ ] Canal do encarregado (DPO) publicado (art. 41)

## 9. Segurança (art. 46)

- [ ] HTTPS em tudo. Cookies de sessão `Secure`/`HttpOnly`/`SameSite`
- [ ] Proteção contra SQL Injection, XSS e IDOR (usuário A não acessa dado do usuário B trocando o ID)
- [ ] MFA para acessos administrativos
- [ ] Atualização de dependências e do servidor
- [ ] Teste de restauração de backup

## 10. Incidentes (art. 48 + Resolução CD/ANPD nº 15/2024)

- [ ] Plano de resposta escrito: quem decide, quem comunica, como conter
- [ ] Logs suficientes para saber **o que** vazou, **de quem** e **desde quando**
- [ ] Modelo de comunicação para ANPD e titulares pronto
- [ ] Prazo conhecido: **3 dias úteis** do conhecimento de que dados pessoais foram afetados (quando houver risco ou dano relevante), em dobro para agente de pequeno porte, com complementação possível em até 20 dias úteis
- [ ] Registro interno dos incidentes, inclusive os não comunicados

---

> Este checklist cobre controles técnicos. A escolha da base legal, a elaboração de políticas e a decisão de comunicar incidentes cabem ao controlador, com o encarregado e o jurídico.

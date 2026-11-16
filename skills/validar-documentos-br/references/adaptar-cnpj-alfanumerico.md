# Checklist: adaptar um sistema ao CNPJ alfanumérico

Desde julho de 2026 a Receita pode emitir CNPJs com letras nas 12 primeiras posições. Os CNPJs antigos continuam válidos e iguais. O sistema precisa aceitar os dois.

## Onde costuma quebrar (procure no código)

| Padrão | Por que quebra | Troque por |
|---|---|---|
| `\d{14}`, `[0-9]{14}`, `^\d+$` | Rejeita letras | `^[A-Z0-9]{12}[0-9]{2}$` (após normalizar) |
| `is_numeric`, `ctype_digit`, `isdigit()`, `Number.isInteger` | Rejeita letras | Validar com a regex acima |
| `intval`, `(int)`, `parseInt`, `Number(...)`, `int(...)` no CNPJ | Corta letras e zeros à esquerda | Tratar sempre como texto |
| Coluna `BIGINT`, `NUMERIC`, `DECIMAL`, `INT` | Não guarda letras | `CHAR(14)` ou `VARCHAR(14)` |
| `LPAD(cnpj, 14, '0')` / `str_pad` / `zfill` em número | Pressupõe numérico | Só se o valor já for texto de 14 posições |
| Máscara `99.999.999/9999-99` | Campo só aceita dígitos | Máscara que aceite `A-Z` nas 12 primeiras (`AA.AAA.AAA/AAAA-99`) e force maiúsculas |
| Teclado numérico no celular (`inputmode="numeric"`, `type="number"`) | Usuário não consegue digitar letra | `inputmode="text"`, `autocapitalize="characters"` |
| Ordenação ou comparação numérica (`ORDER BY cnpj + 0`) | Ordem errada / erro | Comparar como texto |
| Validador de DV antigo (`int(c)` em cada dígito) | Quebra na letra | Usar `ord(c) - 48` (veja os scripts) |

Para varrer um projeto rapidamente:

```bash
grep -rniE "cnpj" --include="*.php" --include="*.js" --include="*.ts" --include="*.py" --include="*.java" --include="*.cs" --include="*.sql" . \
  | grep -iE '\\d\{14\}|\[0-9\]\{14\}|is_numeric|ctype_digit|isdigit|parseint|intval|\(int\)|bigint|numeric\(|99\.999\.999'
```

## Por camada

- **Banco**: migre colunas numéricas para `CHAR(14)`. Revise índices, chaves estrangeiras e views que fazem cast. Teste com um CNPJ alfanumérico real de homologação.
- **Back-end/API**: normalize (remover máscara, maiúsculas) na entrada, valide com o algoritmo novo e devolva sem máscara. Revise contratos (OpenAPI, JSON Schema) que declaram `type: integer` ou `pattern` só numérico.
- **Front-end**: máscara, teclado, `maxlength` (14 sem máscara / 18 com máscara) e conversão para maiúsculas.
- **Integrações**: NF-e/NFC-e, CT-e, MDF-e, eSocial, EFD, boleto, Pix e bancos têm cronogramas próprios. Confirme a versão de leiaute de cada parceiro. Na chave de acesso de 44 posições, as letras aparecem nas posições 7 a 18.
- **Relatórios e planilhas**: o Excel converte CNPJ numérico em número e perde zeros. Exporte como texto.

## Dados de teste

- Exemplo oficial: `12.ABC.345/01DE-35`.
- Gere outros com `python3 scripts/documentos_br.py dv-cnpj <12 caracteres>`.
- A Receita oferece o **Simulador Nacional de CNPJ** para gerar números fictícios de homologação.

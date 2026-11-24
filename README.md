<div align="center">

<img src="assets/banner.svg" alt="skills-dev-br — Claude Skills para quem programa no Brasil" width="100%">

<br>

[![testes](https://github.com/diegojgodoi-br/skills-dev-br/actions/workflows/testes.yml/badge.svg)](https://github.com/diegojgodoi-br/skills-dev-br/actions/workflows/testes.yml)
[![Skills](https://img.shields.io/badge/skills-5-1fbf6b?style=for-the-badge)](#-as-skills)
[![CNPJ alfanumérico](https://img.shields.io/badge/CNPJ-alfanumérico%20pronto-f5c400?style=for-the-badge)](skills/validar-documentos-br)
[![Licença MIT](https://img.shields.io/badge/licença-MIT-555?style=for-the-badge)](LICENSE)

**As regras brasileiras que todo sistema precisa acertar, ensinadas ao Claude: CNPJ alfanumérico, Pix, boleto, NF-e e LGPD.**<br>
Cada skill vem com **código de referência testado** (Python, e também PHP e JS onde faz sentido) e conferido contra os exemplos oficiais.

[**Skills**](#-as-skills) · [**Instalar**](#-instalação) · [**Exemplos**](#-exemplos-de-pedido) · [**Como foi testado**](#-como-foi-testado) · [**Skills em português para outras profissões**](https://github.com/diegojgodoi-br/skills-ia-pt-br)

📚 **Cursos grátis de IA com certificado, 87 skills explicadas e guias em português:** [iacomousar.com.br](https://iacomousar.com.br/?utm_source=github&utm_medium=readme&utm_campaign=skills-dev-br)

</div>

---

## 🧰 As skills

| Skill | O que resolve | Código incluso |
|---|---|---|
| 🪪 [**validar-documentos-br**](skills/validar-documentos-br) | Valida CPF e CNPJ **incluindo o CNPJ alfanumérico** (com letras, desde jul/2026) e mostra o que mudar no banco, na API, na máscara e nas integrações | Python · PHP · JS |
| 💠 [**pix-copia-e-cola**](skills/pix-copia-e-cola) | Gera, lê e valida o Pix copia e cola (BR Code): campos EMV, CRC16, txid, estático x dinâmico. Diagnostica por que o banco rejeita o código | Python (+ CRC em PHP e JS) |
| 🧾 [**boleto-linha-digitavel**](skills/boleto-linha-digitavel) | Valida linha digitável (47 e 48 dígitos), converte para código de barras, extrai banco, valor e vencimento **com o reinício do fator de 2025** | Python |
| 📄 [**nfe-xml**](skills/nfe-xml) | Lê pastas de XML de NF-e/NFC-e, valida a chave de 44 posições (com CNPJ alfanumérico) e gera CSV de notas e itens para Excel/BI, já com IBS/CBS | Python |
| 🔒 [**lgpd-revisao-sistema**](skills/lgpd-revisao-sistema) | Mapeia dados pessoais e sensíveis no código e no banco, aponta lacunas técnicas da LGPD e guia a resposta a incidente no prazo da ANPD | Python + checklist |

Todos os scripts usam **só a biblioteca padrão** (sem `pip install`) e rodam localmente, sem enviar dados para lugar nenhum.

## 🚀 Instalação

<details open>
<summary><b>No claude.ai (site ou app)</b></summary>

1. Ative **Execução de código e criação de arquivos** em *Configurações › Capacidades*.
2. Baixe o `.zip` da skill (ou o `todas-as-skills-dev-br.zip`) na [página de Releases](https://github.com/diegojgodoi-br/skills-dev-br/releases/latest).
3. Vá em *Personalizar › Skills › + › Enviar uma skill* e escolha o `.zip`.

</details>

<details>
<summary><b>No Claude Code</b></summary>

```bash
git clone https://github.com/diegojgodoi-br/skills-dev-br.git
mkdir -p ~/.claude/skills
cp -r skills-dev-br/skills/*/ ~/.claude/skills/
```

No Claude Code as skills brilham dentro do seu projeto: o Claude acha os validadores de CNPJ que quebram com letras, roda a varredura de LGPD no código e processa a pasta de XMLs.

</details>

<details>
<summary><b>Só quer o código?</b></summary>

Os scripts funcionam sozinhos, sem o Claude:

```bash
python3 skills/validar-documentos-br/scripts/documentos_br.py validar 12.ABC.345/01DE-35
python3 skills/pix-copia-e-cola/scripts/pix_brcode.py ler "000201..."
python3 skills/boleto-linha-digitavel/scripts/boleto.py "34191.09008 72564.898723 32408.290008 1 10010000082831"
python3 skills/nfe-xml/scripts/nfe.py ler pasta_xmls --csv relatorio
python3 skills/lgpd-revisao-sistema/scripts/mapear_dados_pessoais.py meu_projeto --md mapa.md
```

</details>

## 💬 Exemplos de pedido

> *"Meu sistema está rejeitando o CNPJ 12.ABC.345/01DE-35. Acha onde está o problema no projeto e me mostra o que trocar."*<br>
> *"Gera um Pix copia e cola de R$ 49,90 para a chave financeiro@minhaempresa.com.br, com o txid do pedido 1234."*<br>
> *"O banco diz que esse QR Code Pix é inválido. O que está errado?"*<br>
> *"Qual o valor e o vencimento deste boleto? 34191.09008 72564.898723..."*<br>
> *"Tenho 300 XMLs de compra do mês nesta pasta. Monta uma planilha por fornecedor e CFOP."*<br>
> *"Faz um mapa de dados pessoais deste sistema e me diz o que está fora da LGPD."*

## ✅ Como foi testado

Os testes rodam no GitHub a cada alteração ([ver execuções](https://github.com/diegojgodoi-br/skills-dev-br/actions/workflows/testes.yml)) e conferem:

- **CNPJ alfanumérico** contra o exemplo oficial do Serpro/Receita (`12.ABC.345/01DE-35`). As versões Python, PHP e JS dão o mesmo resultado, e para CNPJ só com números o resultado é idêntico ao algoritmo antigo (5.000 casos).
- **Pix**: o gerador reproduz **byte a byte** o exemplo do manual do Banco Central (CRC `1D3D`). Também detecta CRC e valor adulterados.
- **Boleto** com linhas reais do Itaú e da Caixa, as datas do reinício do fator (21/02/2025 = 9999, 22/02/2025 = 1000), ida e volta entre linha digitável e código de barras, e contas de consumo nos dois módulos.
- **NF-e** com a chave de exemplo do Manual de Orientação do Contribuinte, chave com CNPJ alfanumérico e leitura de XML com grupo IBS/CBS.
- **LGPD**: a varredura encontra campos sensíveis, dados reais no repositório, dados em log e hash fraco, e **nunca repete o dado encontrado** no relatório.

```bash
python3 tests/test_tudo.py
```

## ⚠️ Avisos

- Os algoritmos seguem as especificações oficiais vigentes em **novembro de 2026** (IN RFB 2.229/2024, Manual de Padrões para Iniciação do Pix, FEBRABAN, MOC da NF-e, NT 2025.002-RTC, LGPD e Resolução CD/ANPD nº 15/2024). Normas mudam: confira a versão em vigor antes de ir para produção.
- Validar dígito verificador prova que o número está **bem formado**, não que a empresa, o boleto ou a nota são legítimos.
- A skill de LGPD faz a revisão **técnica**. Base legal, políticas e comunicação à ANPD são decisões do controlador, com o encarregado e o jurídico.

## 🤝 Contribua

Encontrou uma regra desatualizada, um banco que foge do padrão ou quer propor uma skill (eSocial? SPED? CT-e?)? [Abra uma issue](https://github.com/diegojgodoi-br/skills-dev-br/issues) ou mande um pull request com teste.

---

<div align="center">

**Se alguma skill te poupou uma tarde de manual da Receita, deixe uma ⭐**

Feito por [Diego Godoi](https://github.com/diegojgodoi-br) · [iacomousar.com.br](https://iacomousar.com.br) · Licença [MIT](LICENSE)<br>
Veja também: [auditoria-seguranca-php-mysql](https://github.com/diegojgodoi-br/auditoria-seguranca-php-mysql) · [skills-ia-pt-br](https://github.com/diegojgodoi-br/skills-ia-pt-br)

</div>

#!/usr/bin/env python3
"""Varredura inicial de dados pessoais em um projeto (código, SQL, configs, logs de exemplo).

Encontra PONTOS DE ATENÇÃO para a revisão de LGPD, não conclusões:
  1. Colunas/campos com nome de dado pessoal ou sensível (CREATE TABLE, models, DTOs)
  2. Dados pessoais reais aparentes dentro do repositório (CPF, e-mail, telefone)
  3. Dados pessoais indo para log/console/print
  4. Senha guardada com hash fraco (md5/sha1) ou sem hash
Só usa a biblioteca padrão do Python. Não envia nada para fora da máquina.

Uso:
    python3 mapear_dados_pessoais.py caminho/do/projeto [--md relatorio.md]
"""
import re
import sys
from pathlib import Path

EXTENSOES = {".php", ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cs", ".rb", ".go", ".sql",
             ".env", ".ini", ".yml", ".yaml", ".json", ".xml", ".csv", ".log", ".txt", ".vue", ".kt"}
IGNORAR_PASTAS = {"node_modules", "vendor", ".git", "dist", "build", "__pycache__", ".venv", "venv"}

# Nomes de campo. "sensivel" segue o art. 5º, II da LGPD (origem racial/étnica, religião, opinião política,
# filiação sindical/religiosa/filosófica/política, saúde, vida sexual, dado genético ou biométrico).
CAMPOS = {
    "identificacao": r"cpf|rg|cnh|passaporte|titulo_?eleitor|pis|nis|ctps|nome_?(completo|mae|pai)|nome_social|data_?nasc|nascimento",
    "contato": r"e_?mail|telefone|celular|whats(app)?|endereco|logradouro|cep|bairro",
    "financeiro": r"salario|renda|conta_?(bancaria|corrente)|agencia|cartao|score|chave_?pix",
    "localizacao": r"latitude|longitude|geoloc|ip_?(address|origem)?\b|localizacao",
    "sensivel": r"raca|cor_?pele|etnia|religiao|crenca|opiniao_?politica|partido|sindic|saude|doenca|cid\b|"
                r"deficiencia|alergia|medicamento|exame|gestante|gravidez|orientacao_?sexual|vida_?sexual|"
                r"genetic|biometri|digital_?(dedo|impressao)|face_?id|foto_?rosto",
    "credencial": r"senha|password|passwd|pwd|token|secret|api_?key",
    "crianca": r"menor|crianca|aluno|responsavel_?legal|idade",
}
RE_CAMPOS = {cat: re.compile(rf"\b\w*(?:{pad})\w*\b", re.I) for cat, pad in CAMPOS.items()}

RE_CPF = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
RE_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")
RE_TEL = re.compile(r"\(?\b\d{2}\)?\s?9\d{4}-?\d{4}\b")
RE_LOG = re.compile(r"(console\.(log|info|debug)|error_log|var_dump|print_r|logger\.\w+|log\.\w+|print\(|System\.out)", re.I)
RE_HASH_FRACO = re.compile(r"(md5|sha1)\s*\(", re.I)
RE_DEF_CAMPO = re.compile(r"(create\s+table|alter\s+table|\bcolumn\b|\$table->|models\.|@Column|\bfillable\b|:\s*(string|str|varchar))", re.I)


def _cpf_valido(cpf):
    d = re.sub(r"\D", "", cpf)
    if len(set(d)) == 1:
        return False
    for t in (9, 10):
        s = sum(int(d[i]) * (t + 1 - i) for i in range(t))
        r = s % 11
        if (0 if r < 2 else 11 - r) != int(d[t]):
            return False
    return True


def mascarar(texto: str) -> str:
    """Nunca repete o dado pessoal no relatório: só os primeiros caracteres ficam visíveis."""
    texto = RE_CPF.sub(lambda m: m.group(0)[:3] + ".***.***-**", texto)
    texto = RE_EMAIL.sub(lambda m: m.group(0)[:2] + "***@***", texto)
    return RE_TEL.sub(lambda m: m.group(0)[:4] + "*****-****", texto)


def varrer(raiz: Path):
    achados = []
    for arq in raiz.rglob("*"):
        if not arq.is_file() or arq.suffix.lower() not in EXTENSOES and arq.name != ".env":
            continue
        if any(p in IGNORAR_PASTAS for p in arq.parts):
            continue
        try:
            linhas = arq.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        rel = arq.relative_to(raiz)
        for n, linha in enumerate(linhas, 1):
            curta = mascarar(linha.strip())[:160]
            if RE_DEF_CAMPO.search(linha) or arq.suffix.lower() == ".sql":
                for cat, rx in RE_CAMPOS.items():
                    for m in rx.finditer(linha):
                        achados.append(("campo", cat, str(rel), n, m.group(0), curta))
            for m in RE_CPF.finditer(linha):
                if _cpf_valido(m.group(0)):
                    achados.append(("dado_real", "CPF válido no repositório", str(rel), n, m.group(0)[:7] + "***", curta[:80]))
            for m in RE_EMAIL.finditer(linha):
                if not re.search(r"exemplo|example|teste|test|dominio|seu@|noreply|no-reply", m.group(0), re.I):
                    achados.append(("dado_real", "e-mail no repositório", str(rel), n, m.group(0)[:3] + "***", curta[:80]))
            for m in RE_TEL.finditer(linha):
                achados.append(("dado_real", "telefone no repositório", str(rel), n, m.group(0)[:4] + "***", curta[:80]))
            if RE_LOG.search(linha):
                for cat in ("identificacao", "contato", "sensivel", "credencial", "financeiro"):
                    m = RE_CAMPOS[cat].search(linha)
                    if m:
                        achados.append(("log", f"{cat} em log/saída", str(rel), n, m.group(0), curta))
                        break
            if RE_HASH_FRACO.search(linha) and RE_CAMPOS["credencial"].search(linha):
                achados.append(("senha", "hash fraco em senha/credencial", str(rel), n, "md5/sha1", curta))
    return achados


def relatorio_md(achados, raiz) -> str:
    titulos = {
        "campo": "1. Campos com dado pessoal (inventário inicial)",
        "dado_real": "2. Dados pessoais aparentemente reais dentro do repositório",
        "log": "3. Dados pessoais indo para log ou saída",
        "senha": "4. Senhas/credenciais com hash fraco",
    }
    out = [f"# Mapa inicial de dados pessoais — `{raiz}`", "",
           "> Varredura automática: são **pontos para revisar**, não conclusões. "
           "Confirme cada um lendo o contexto.", ""]
    for tipo, titulo in titulos.items():
        itens = [a for a in achados if a[0] == tipo]
        out += [f"## {titulo} ({len(itens)})", ""]
        if not itens:
            out += ["Nada encontrado.", ""]
            continue
        out += ["| Categoria | Arquivo:linha | Termo | Trecho |", "|---|---|---|---|"]
        vistos = set()
        for _, cat, arq, n, termo, trecho in itens:
            if (arq, n, termo) in vistos:
                continue
            vistos.add((arq, n, termo))
            trecho = trecho.replace("|", "\\|")
            out.append(f"| {cat} | `{arq}:{n}` | `{termo}` | `{trecho}` |")
        out.append("")
    return "\n".join(out)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    raiz = Path(argv[1])
    md = relatorio_md(varrer(raiz), raiz)
    if "--md" in argv:
        destino = argv[argv.index("--md") + 1]
        Path(destino).write_text(md, encoding="utf-8")
        print(f"Relatório salvo em {destino}")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

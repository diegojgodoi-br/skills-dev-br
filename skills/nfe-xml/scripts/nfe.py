#!/usr/bin/env python3
"""Leitura de XML de NF-e/NFC-e (modelos 55 e 65): valida a chave de acesso e extrai notas e itens.

- Aceita arquivos soltos, pastas (busca *.xml recursivamente) e o XML autorizado (nfeProc) ou só a NFe.
- Valida a chave de 44 posições, inclusive com CNPJ alfanumérico (letras nas posições 7-18).
- Gera CSV de notas e de itens, prontos para planilha/BI, ou JSON.
Só usa a biblioteca padrão do Python.

Uso:
    python3 nfe.py chave 52060433009911002506550120000007800267301615
    python3 nfe.py ler pasta_ou_arquivo.xml [--csv saida]   (gera saida_notas.csv e saida_itens.csv)
    python3 nfe.py ler pasta --json
"""
import csv
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"n": "http://www.portalfiscal.inf.br/nfe"}

UF_CODIGOS = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE", "29": "BA",
    "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR", "42": "SC", "43": "RS",
    "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}
MODELOS = {"55": "NF-e", "65": "NFC-e", "57": "CT-e", "58": "MDF-e", "67": "CT-e OS"}


def dv_chave(chave43: str) -> int:
    """Módulo 11, pesos 2-9 da direita para a esquerda; resto 0 ou 1 -> DV 0.
    Cada caractere vale (código ASCII - 48), o que mantém o cálculo antigo para dígitos
    e cobre as letras do CNPJ alfanumérico."""
    soma, peso = 0, 2
    for c in reversed(chave43):
        soma += (ord(c) - 48) * peso
        peso = 2 if peso == 9 else peso + 1
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def analisar_chave(chave: str) -> dict:
    c = re.sub(r"\s", "", chave or "").upper()
    if c.startswith("NFE"):
        c = c[3:]
    problemas = []
    if not re.fullmatch(r"[0-9]{6}[A-Z0-9]{12}[0-9]{26}", c):
        return {"chave": c, "valida": False,
                "problemas": ["Formato inválido: esperado 44 posições, com letras só no CNPJ (posições 7 a 18)"]}
    if dv_chave(c[:43]) != int(c[43]):
        problemas.append(f"Dígito verificador inválido: informado {c[43]}, esperado {dv_chave(c[:43])}")
    uf = UF_CODIGOS.get(c[0:2])
    if not uf:
        problemas.append(f"Código de UF {c[0:2]} não existe")
    mes = int(c[4:6])
    if not 1 <= mes <= 12:
        problemas.append(f"Mês de emissão {c[4:6]} inválido")
    return {
        "chave": c, "valida": not problemas, "problemas": problemas,
        "uf": uf, "ano_mes": f"20{c[2:4]}-{c[4:6]}", "emitente": c[6:20],
        "modelo": MODELOS.get(c[20:22], c[20:22]), "serie": int(c[22:25]), "numero": int(c[25:34]),
        "tipo_emissao": c[34], "codigo_numerico": c[35:43], "dv": c[43],
    }


def _txt(el, caminho):
    if el is None:
        return None
    achado = el.find(caminho, NS)
    return achado.text.strip() if achado is not None and achado.text else None


def _num(v):
    try:
        return float(v) if v not in (None, "") else None
    except ValueError:
        return None


def _grupo_como_dict(el):
    """Converte um grupo (ex.: totais do IBS/CBS da reforma tributária) em dict plano, sem depender do leiaute exato."""
    if el is None:
        return {}
    saida = {}
    for filho in el.iter():
        tag = filho.tag.split("}")[-1]
        if filho is not el and filho.text and filho.text.strip() and len(filho) == 0:
            saida[tag] = filho.text.strip()
    return saida


def ler_xml(caminho: Path) -> dict:
    raiz = ET.parse(caminho).getroot()
    inf = raiz.find(".//n:infNFe", NS)
    if inf is None:
        raise ValueError("Não é um XML de NF-e/NFC-e (infNFe não encontrado)")
    chave = (inf.get("Id") or "").replace("NFe", "")
    ide, emit, dest = inf.find("n:ide", NS), inf.find("n:emit", NS), inf.find("n:dest", NS)
    icms_tot = inf.find("n:total/n:ICMSTot", NS)
    prot = raiz.find(".//n:protNFe/n:infProt", NS)
    total = inf.find("n:total", NS)
    ibscbs_tot = total.find("n:IBSCBSTot", NS) if total is not None else None

    nota = {
        "arquivo": str(caminho),
        "chave": chave,
        "chave_valida": analisar_chave(chave)["valida"] if chave else False,
        "modelo": _txt(ide, "n:mod"), "serie": _txt(ide, "n:serie"), "numero": _txt(ide, "n:nNF"),
        "emissao": _txt(ide, "n:dhEmi") or _txt(ide, "n:dEmi"),
        "natureza_operacao": _txt(ide, "n:natOp"),
        "tipo": {"0": "entrada", "1": "saída"}.get(_txt(ide, "n:tpNF"), _txt(ide, "n:tpNF")),
        "emitente_doc": _txt(emit, "n:CNPJ") or _txt(emit, "n:CPF"),
        "emitente_nome": _txt(emit, "n:xNome"),
        "emitente_uf": _txt(emit, "n:enderEmit/n:UF"),
        "destinatario_doc": _txt(dest, "n:CNPJ") or _txt(dest, "n:CPF") or _txt(dest, "n:idEstrangeiro"),
        "destinatario_nome": _txt(dest, "n:xNome"),
        "destinatario_uf": _txt(dest, "n:enderDest/n:UF"),
        "valor_produtos": _num(_txt(icms_tot, "n:vProd")),
        "valor_desconto": _num(_txt(icms_tot, "n:vDesc")),
        "valor_frete": _num(_txt(icms_tot, "n:vFrete")),
        "valor_icms": _num(_txt(icms_tot, "n:vICMS")),
        "valor_icms_st": _num(_txt(icms_tot, "n:vST")),
        "valor_ipi": _num(_txt(icms_tot, "n:vIPI")),
        "valor_pis": _num(_txt(icms_tot, "n:vPIS")),
        "valor_cofins": _num(_txt(icms_tot, "n:vCOFINS")),
        "valor_nota": _num(_txt(icms_tot, "n:vNF")),
        "ibs_cbs_totais": json.dumps(_grupo_como_dict(ibscbs_tot), ensure_ascii=False) if ibscbs_tot is not None else "",
        "autorizada": bool(prot is not None and _txt(prot, "n:cStat") in ("100", "150")),
        "status_sefaz": _txt(prot, "n:cStat"),
        "motivo_sefaz": _txt(prot, "n:xMotivo"),
        "protocolo": _txt(prot, "n:nProt"),
    }
    itens = []
    for det in inf.findall("n:det", NS):
        prod = det.find("n:prod", NS)
        itens.append({
            "chave": chave, "item": det.get("nItem"),
            "codigo": _txt(prod, "n:cProd"), "descricao": _txt(prod, "n:xProd"),
            "ncm": _txt(prod, "n:NCM"), "cfop": _txt(prod, "n:CFOP"), "unidade": _txt(prod, "n:uCom"),
            "quantidade": _num(_txt(prod, "n:qCom")), "valor_unitario": _num(_txt(prod, "n:vUnCom")),
            "valor_total": _num(_txt(prod, "n:vProd")),
            "tem_grupo_ibscbs": det.find("n:imposto/n:IBSCBS", NS) is not None,
        })
    return {"nota": nota, "itens": itens}


def coletar(caminhos):
    arquivos = []
    for c in caminhos:
        p = Path(c)
        arquivos += sorted(p.rglob("*.xml")) if p.is_dir() else [p]
    notas, itens, erros = [], [], []
    for a in arquivos:
        try:
            r = ler_xml(a)
            notas.append(r["nota"])
            itens += r["itens"]
        except (ET.ParseError, ValueError) as e:
            erros.append({"arquivo": str(a), "erro": str(e)})
    return notas, itens, erros


def _csv(caminho, linhas):
    if not linhas:
        return
    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:   # utf-8-sig abre certo no Excel
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()), delimiter=";")
        w.writeheader()
        for linha in linhas:
            # vírgula decimal para o Excel em português
            w.writerow({k: (f"{v:.4f}".rstrip("0").rstrip(".").replace(".", ",") if isinstance(v, float) else v)
                        for k, v in linha.items()})


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    if argv[1] == "chave":
        r = analisar_chave(argv[2])
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r["valida"] else 1
    if argv[1] == "ler":
        args = argv[2:]
        saida = None
        if "--csv" in args:
            i = args.index("--csv"); saida = args[i + 1]; args = args[:i] + args[i + 2:]
        como_json = "--json" in args
        args = [a for a in args if a != "--json"]
        notas, itens, erros = coletar(args)
        if saida:
            _csv(f"{saida}_notas.csv", notas)
            _csv(f"{saida}_itens.csv", itens)
        if como_json or not saida:
            print(json.dumps({"notas": notas, "itens": itens, "erros": erros}, ensure_ascii=False, indent=2))
        else:
            print(f"{len(notas)} notas, {len(itens)} itens, {len(erros)} arquivos com erro -> {saida}_notas.csv / {saida}_itens.csv")
            for e in erros:
                print("ERRO:", e["arquivo"], "-", e["erro"])
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))

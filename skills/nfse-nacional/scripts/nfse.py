#!/usr/bin/env python3
"""NFS-e padrão nacional: decompõe chave de acesso e Id da DPS, lê XMLs e gera CSV.

Uso:
  python3 nfse.py chave 41130022212345678000195000000000012326111234567891
  python3 nfse.py dps DPS411300221234567800019500001000000000000123
  python3 nfse.py ler pasta_xmls --csv relatorio      # gera relatorio_nfse.csv
  python3 nfse.py ler nota.xml --json

Só biblioteca padrão. Lê o XML pelo nome local das tags, então funciona com ou sem
o namespace http://www.sped.fazenda.gov.br/nfse e com as versões 1.00/1.01 do leiaute.
"""
import argparse
import csv
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

AMB_GER = {"1": "sistema próprio do município", "2": "Sefin Nacional (emissor nacional)"}
TP_INSC = {"1": "CPF", "2": "CNPJ"}
AMBIENTE = {"1": "produção", "2": "homologação/produção restrita"}
RET_ISS = {"1": "não retido", "2": "retido pelo tomador", "3": "retido pelo intermediário"}

URL_CONSULTA = "https://www.nfse.gov.br/consultapublica"

# Chave de acesso (50 posições)
CAMPOS_CHAVE = [("cod_municipio", 7), ("amb_gerador", 1), ("tp_inscricao", 1), ("inscricao", 14),
                ("numero_nfse", 13), ("ano_mes", 4), ("codigo_numerico", 9), ("dv", 1)]
# Id da DPS: "DPS" + 42 posições
CAMPOS_DPS = [("cod_municipio_emissor", 7), ("tp_inscricao", 1), ("inscricao", 14),
              ("serie", 5), ("numero_dps", 15)]


def _limpa(s):
    return re.sub(r"[\s.\-/]", "", s or "").upper()


def _fatiar(valor, campos):
    out, i = {}, 0
    for nome, tam in campos:
        out[nome] = valor[i:i + tam]
        i += tam
    return out


def _inscricao(tp, insc):
    if tp == "1":
        return insc[3:] if insc.startswith("000") else insc
    return insc


def decompor_chave(chave):
    """Separa os campos da chave. Não confere o DV: quem gera a chave é o Sistema Nacional."""
    c = _limpa(chave)
    if c.startswith("NFS"):
        c = c[3:]
    erros = []
    if len(c) != 50:
        erros.append(f"a chave tem {len(c)} posições; o padrão nacional usa 50")
    if not re.fullmatch(r"[0-9A-Z]*", c):
        erros.append("caracteres inválidos")
    d = _fatiar(c.ljust(50), CAMPOS_CHAVE)
    d = {k: v.strip() for k, v in d.items()}
    if d["amb_gerador"] and d["amb_gerador"] not in AMB_GER:
        erros.append(f"ambiente gerador desconhecido: {d['amb_gerador']}")
    if d["tp_inscricao"] and d["tp_inscricao"] not in TP_INSC:
        erros.append(f"tipo de inscrição desconhecido: {d['tp_inscricao']}")
    am = d["ano_mes"]
    if len(am) == 4 and am.isdigit() and not 1 <= int(am[2:]) <= 12:
        erros.append(f"mês inválido em AAMM: {am}")
    if d["numero_nfse"] and not d["numero_nfse"].isdigit():
        erros.append("número da NFS-e com caracteres não numéricos")
    return {
        "chave": c, "formato_ok": not erros, "erros": erros,
        "cod_municipio_ibge": d["cod_municipio"],
        "ambiente_gerador": AMB_GER.get(d["amb_gerador"], d["amb_gerador"]),
        "tipo_inscricao": TP_INSC.get(d["tp_inscricao"], d["tp_inscricao"]),
        "inscricao_emitente": _inscricao(d["tp_inscricao"], d["inscricao"]),
        "numero_nfse": d["numero_nfse"].lstrip("0") or "0",
        "emissao_aaaa_mm": f"20{am[:2]}-{am[2:]}" if len(am) == 4 else am,
        "codigo_numerico": d["codigo_numerico"], "dv": d["dv"],
        "dv_conferido": False,
        "consulta": URL_CONSULTA,
    }


def decompor_dps(id_dps):
    c = _limpa(id_dps)
    if c.startswith("DPS"):
        c = c[3:]
    erros = [] if len(c) == 42 else [f"o Id da DPS tem {len(c)} posições após 'DPS'; o padrão usa 42"]
    d = {k: v.strip() for k, v in _fatiar(c.ljust(42), CAMPOS_DPS).items()}
    return {"id": "DPS" + c, "formato_ok": not erros, "erros": erros,
            "cod_municipio_emissor": d["cod_municipio_emissor"],
            "tipo_inscricao": TP_INSC.get(d["tp_inscricao"], d["tp_inscricao"]),
            "inscricao": _inscricao(d["tp_inscricao"], d["inscricao"]),
            "serie": d["serie"].lstrip("0") or "0", "numero_dps": d["numero_dps"].lstrip("0") or "0"}


# ---------- leitura de XML ----------

def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _achar(no, *caminho):
    """Busca por nome local, descendo em qualquer profundidade a cada passo."""
    atual = [no]
    for nome in caminho:
        prox = []
        for n in atual:
            prox.extend(e for e in n.iter() if e is not n and _local(e.tag) == nome)
        if not prox:
            return None
        atual = prox[:1]
    return atual[0]


def _txt(no, *caminho):
    if no is None:
        return ""
    e = _achar(no, *caminho)
    return (e.text or "").strip() if e is not None and e.text else ""


def _doc(no):
    if no is None:
        return ""
    return _txt(no, "CNPJ") or _txt(no, "CPF") or _txt(no, "NIF")


def _num(s):
    try:
        return float(s.replace(",", ".")) if s else 0.0
    except ValueError:
        return 0.0


def ler_xml(caminho):
    raiz = ET.parse(caminho).getroot()
    inf_nfse = raiz if _local(raiz.tag) == "infNFSe" else _achar(raiz, "infNFSe")
    inf_dps = _achar(raiz, "infDPS")
    if inf_nfse is None and inf_dps is None:
        raise ValueError("não é NFS-e nem DPS do padrão nacional (sem infNFSe/infDPS)")
    chave = ""
    if inf_nfse is not None:
        chave = (inf_nfse.get("Id") or "").removeprefix("NFS")
    valores_nfse = None
    if inf_nfse is not None:
        valores_nfse = next((e for e in inf_nfse if _local(e.tag) == "valores"), None)
    emit = _achar(inf_nfse, "emit") if inf_nfse is not None else None
    prest = _achar(inf_dps, "prest") if inf_dps is not None else None
    toma = _achar(inf_dps, "toma") if inf_dps is not None else None
    serv = _achar(inf_dps, "serv") if inf_dps is not None else None
    ibscbs = _achar(inf_dps, "IBSCBS") if inf_dps is not None else None
    r = {
        "arquivo": str(caminho),
        "tipo": "NFS-e" if inf_nfse is not None else "DPS (sem autorização)",
        "chave": chave,
        "numero_nfse": _txt(inf_nfse, "nNFSe"),
        "data_processamento": _txt(inf_nfse, "dhProc"),
        "status": _txt(inf_nfse, "cStat"),
        "municipio_emissao": _txt(inf_nfse, "xLocEmi"),
        "municipio_incidencia": _txt(inf_nfse, "xLocIncid"),
        "competencia": _txt(inf_dps, "dCompet"),
        "serie_dps": _txt(inf_dps, "serie"),
        "numero_dps": _txt(inf_dps, "nDPS"),
        "prestador_doc": _doc(emit) or _doc(prest),
        "prestador_nome": _txt(emit, "xNome") or _txt(prest, "xNome"),
        "tomador_doc": _doc(toma),
        "tomador_nome": _txt(toma, "xNome"),
        "cod_trib_nacional": _txt(serv, "cTribNac"),
        "cod_nbs": _txt(serv, "cNBS"),
        "descricao": _txt(serv, "xDescServ")[:200],
        "valor_servico": _txt(inf_dps, "vServ"),
        "iss_retencao": RET_ISS.get(_txt(inf_dps, "tpRetISSQN"), _txt(inf_dps, "tpRetISSQN")),
        "aliquota_iss": _txt(valores_nfse, "pAliqAplic"),
        "valor_iss": _txt(valores_nfse, "vISSQN"),
        "valor_liquido": _txt(valores_nfse, "vLiq"),
        "tem_grupo_ibscbs": ibscbs is not None,
        "ibscbs_cst": _txt(ibscbs, "CST"),
        "ibscbs_cclasstrib": _txt(ibscbs, "cClassTrib"),
        "ibscbs_ind_operacao": _txt(ibscbs, "cIndOp"),
        "valor_ibs": _txt(inf_nfse, "vIBSTot"),
        "valor_cbs": _txt(inf_nfse, "vCBS"),
        "valor_total_nf": _txt(inf_nfse, "vTotNF"),
    }
    alertas = []
    if inf_nfse is None:
        alertas.append("arquivo é só a DPS: não prova que a NFS-e foi gerada")
    if chave and not decompor_chave(chave)["formato_ok"]:
        alertas.append("chave fora do formato de 50 posições")
    if r["valor_liquido"] and r["valor_servico"] and _num(r["valor_liquido"]) > _num(r["valor_servico"]) + 0.005:
        alertas.append("valor líquido maior que o valor do serviço")
    r["alertas"] = "; ".join(alertas)
    return r


def ler(caminhos):
    arquivos = []
    for c in caminhos:
        p = Path(c)
        arquivos += sorted(p.rglob("*.xml")) if p.is_dir() else [p]
    notas, erros, vistas = [], [], {}
    for a in arquivos:
        try:
            n = ler_xml(a)
        except (ET.ParseError, ValueError, OSError) as e:
            erros.append({"arquivo": str(a), "erro": str(e)})
            continue
        if n["chave"]:
            if n["chave"] in vistas:
                n["alertas"] = "; ".join(filter(None, [n["alertas"], f"chave duplicada de {vistas[n['chave']]}"]))
            vistas.setdefault(n["chave"], str(a))
        notas.append(n)
    return notas, erros


def salvar_csv(notas, prefixo):
    destino = Path(f"{prefixo}_nfse.csv")
    if not notas:
        return destino
    with destino.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(notas[0]), delimiter=";")
        w.writeheader()
        for n in notas:
            linha = {k: (str(v).replace(".", ",") if k.startswith(("valor_", "aliquota_")) else v)
                     for k, v in n.items()}
            w.writerow(linha)
    return destino


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("chave").add_argument("chave")
    sub.add_parser("dps").add_argument("id")
    lp = sub.add_parser("ler")
    lp.add_argument("caminhos", nargs="+")
    lp.add_argument("--csv", metavar="PREFIXO")
    lp.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "chave":
        r = decompor_chave(a.chave)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r["formato_ok"] else 1
    if a.cmd == "dps":
        r = decompor_dps(a.id)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r["formato_ok"] else 1
    notas, erros = ler(a.caminhos)
    if a.json:
        print(json.dumps({"notas": notas, "erros": erros}, ensure_ascii=False, indent=2))
    else:
        total = sum(_num(n["valor_servico"]) for n in notas)
        print(f"{len(notas)} documento(s) lido(s), {len(erros)} erro(s). Total de serviços: R$ {total:,.2f}"
              .replace(",", "X").replace(".", ",").replace("X", "."))
        for n in notas:
            if n["alertas"]:
                print(f"  ! {n['arquivo']}: {n['alertas']}")
        for e in erros:
            print(f"  x {e['arquivo']}: {e['erro']}")
    if a.csv:
        print(f"CSV: {salvar_csv(notas, a.csv)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

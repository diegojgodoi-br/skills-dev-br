#!/usr/bin/env python3
"""Reforma tributária do consumo (IBS/CBS): calendário de transição e simulações.

Uso:
  python3 reforma.py calendario
  python3 reforma.py simular 1000 --ano 2026
  python3 reforma.py simular 1000 --ano 2027 --cbs 8.8 --reducao 60
  python3 reforma.py por-dentro 1150 --cbs 8.8 --ibs 0.1
  python3 reforma.py apurar --vendas 100000 --compras 40000 --cbs 8.8 --ibs 0.1

Só biblioteca padrão. Valores em reais, alíquotas em %.
As alíquotas de referência de 2027 em diante são fixadas pelo Senado:
o script nunca inventa esse número, você precisa informar.
"""
import argparse
import json
import sys
from decimal import Decimal, ROUND_HALF_UP

D = Decimal
CENT = D("0.01")

# Fase de cada ano (EC 132/2023 e LC 214/2025). Fator ICMS/ISS = fração das alíquotas atuais.
CALENDARIO = {
    2026: {"cbs": D("0.9"), "ibs": D("0.1"), "icms_iss": D("1"), "pis_cofins": True, "ipi": "vigente",
           "obs": "Ano de teste. CBS 0,9% e IBS 0,1% destacados na nota; compensáveis com PIS/Cofins. "
                  "Quem cumpre as obrigações acessórias fica dispensado de recolher. Simples Nacional fora do teste."},
    2027: {"cbs": None, "ibs": D("0.1"), "icms_iss": D("1"), "pis_cofins": False, "ipi": "zero (exceto ZFM)",
           "obs": "CBS cheia (referência menos 0,1 p.p.). PIS e Cofins extintos. IBS de teste 0,05% UF + 0,05% município. "
                  "Começa o Imposto Seletivo."},
    2028: {"cbs": None, "ibs": D("0.1"), "icms_iss": D("1"), "pis_cofins": False, "ipi": "zero (exceto ZFM)",
           "obs": "Igual a 2027."},
    2029: {"cbs": None, "ibs": None, "icms_iss": D("0.9"), "pis_cofins": False, "ipi": "zero (exceto ZFM)",
           "obs": "ICMS e ISS a 90% das alíquotas; IBS sobe para compensar."},
    2030: {"cbs": None, "ibs": None, "icms_iss": D("0.8"), "pis_cofins": False, "ipi": "zero (exceto ZFM)",
           "obs": "ICMS e ISS a 80%."},
    2031: {"cbs": None, "ibs": None, "icms_iss": D("0.7"), "pis_cofins": False, "ipi": "zero (exceto ZFM)",
           "obs": "ICMS e ISS a 70%."},
    2032: {"cbs": None, "ibs": None, "icms_iss": D("0.6"), "pis_cofins": False, "ipi": "zero (exceto ZFM)",
           "obs": "ICMS e ISS a 60%."},
    2033: {"cbs": None, "ibs": None, "icms_iss": D("0"), "pis_cofins": False, "ipi": "zero (exceto ZFM)",
           "obs": "ICMS e ISS extintos. IBS e CBS integrais."},
}

REDUCOES = {
    "0": "regime geral",
    "30": "redução de 30% (ex.: profissões intelectuais regulamentadas)",
    "60": "redução de 60% (ex.: saúde, educação, medicamentos, alimentos fora da cesta, insumos agro)",
    "100": "alíquota zero (ex.: Cesta Básica Nacional)",
}


def dec(x):
    return D(str(x).replace(",", "."))


def pct(x):
    return format(x.normalize(), "f")


def r2(x):
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def aliquotas(ano, cbs=None, ibs=None):
    """Devolve (cbs, ibs) em %, usando o calendário quando a lei fixa o número."""
    if ano not in CALENDARIO:
        raise ValueError(f"ano fora da transição (2026 a 2033): {ano}")
    fase = CALENDARIO[ano]
    cbs = dec(cbs) if cbs is not None else fase["cbs"]
    ibs = dec(ibs) if ibs is not None else fase["ibs"]
    faltando = [n for n, v in (("--cbs", cbs), ("--ibs", ibs)) if v is None]
    if faltando:
        raise ValueError(
            f"{ano}: a alíquota de referência é fixada pelo Senado. Informe {' e '.join(faltando)} "
            "(consulte a resolução vigente; o script não chuta esse número)."
        )
    return cbs, ibs


def simular(valor, ano, cbs=None, ibs=None, reducao=0):
    """Cálculo 'por fora': o tributo é somado ao valor da operação."""
    base = dec(valor)
    red = dec(reducao)
    if not D(0) <= red <= D(100):
        raise ValueError("redução deve estar entre 0 e 100")
    p_cbs, p_ibs = aliquotas(ano, cbs, ibs)
    fator = (D(100) - red) / D(100)
    ef_cbs, ef_ibs = p_cbs * fator, p_ibs * fator
    v_cbs, v_ibs = r2(base * ef_cbs / 100), r2(base * ef_ibs / 100)
    return {
        "ano": ano, "base": str(r2(base)), "reducao_pct": str(red),
        "aliq_cbs": str(p_cbs), "aliq_ibs": str(p_ibs),
        "aliq_efetiva_cbs": pct(ef_cbs), "aliq_efetiva_ibs": pct(ef_ibs),
        "cbs": str(v_cbs), "ibs": str(v_ibs), "total_ibs_cbs": str(v_cbs + v_ibs),
        "total_com_tributo": str(r2(base) + v_cbs + v_ibs),
        "fator_icms_iss": str(CALENDARIO[ano]["icms_iss"]),
        "pis_cofins_vigente": CALENDARIO[ano]["pis_cofins"],
        "obs": CALENDARIO[ano]["obs"],
    }


def por_dentro(preco_final, cbs, ibs, reducao=0):
    """Separa a base de um preço que já embute IBS/CBS (preço final ao consumidor)."""
    fator = (D(100) - dec(reducao)) / D(100)
    aliq = (dec(cbs) + dec(ibs)) * fator / 100
    preco = dec(preco_final)
    base = r2(preco / (1 + aliq))
    return {"preco_final": str(r2(preco)), "base": str(base), "tributos": str(r2(preco - base)),
            "aliq_efetiva_total": pct(aliq * 100)}


def apurar(vendas, compras, cbs, ibs, reducao_vendas=0, reducao_compras=0):
    """Não cumulatividade: débito nas vendas menos crédito nas compras com tributo destacado."""
    out = {}
    for nome, p in (("cbs", dec(cbs)), ("ibs", dec(ibs))):
        deb = r2(dec(vendas) * p * (100 - dec(reducao_vendas)) / 10000)
        cred = r2(dec(compras) * p * (100 - dec(reducao_compras)) / 10000)
        out[nome] = {"debito": str(deb), "credito": str(cred), "saldo": str(deb - cred),
                     "situacao": "a recolher" if deb >= cred else "saldo credor"}
    return out


def _fmt(d):
    return json.dumps(d, ensure_ascii=False, indent=2)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("calendario")
    s = sub.add_parser("simular")
    s.add_argument("valor")
    s.add_argument("--ano", type=int, required=True)
    s.add_argument("--cbs")
    s.add_argument("--ibs")
    s.add_argument("--reducao", default="0", help="0, 30, 60 ou 100 (%% de redução da alíquota)")
    p = sub.add_parser("por-dentro")
    p.add_argument("preco")
    p.add_argument("--cbs", required=True)
    p.add_argument("--ibs", required=True)
    p.add_argument("--reducao", default="0")
    a = sub.add_parser("apurar")
    a.add_argument("--vendas", required=True)
    a.add_argument("--compras", required=True)
    a.add_argument("--cbs", required=True)
    a.add_argument("--ibs", required=True)
    a.add_argument("--reducao-vendas", default="0")
    a.add_argument("--reducao-compras", default="0")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "calendario":
            for ano, f in CALENDARIO.items():
                cbs = f"{f['cbs']}%" if f["cbs"] is not None else "referência (Senado)"
                ibs = f"{f['ibs']}%" if f["ibs"] is not None else "referência (Senado)"
                print(f"{ano}: CBS {cbs} | IBS {ibs} | ICMS/ISS x{f['icms_iss']} | "
                      f"PIS/Cofins {'sim' if f['pis_cofins'] else 'extinto'} | IPI {f['ipi']}\n      {f['obs']}")
        elif args.cmd == "simular":
            print(_fmt(simular(args.valor, args.ano, args.cbs, args.ibs, args.reducao)))
        elif args.cmd == "por-dentro":
            print(_fmt(por_dentro(args.preco, args.cbs, args.ibs, args.reducao)))
        else:
            print(_fmt(apurar(args.vendas, args.compras, args.cbs, args.ibs,
                              args.reducao_vendas, args.reducao_compras)))
    except ValueError as e:
        print(f"erro: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

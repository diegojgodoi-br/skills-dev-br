#!/usr/bin/env python3
"""Boletos: valida e converte linha digitável <-> código de barras, extrai banco, valor e vencimento.

Cobre:
  - Boleto bancário (ficha de compensação): linha digitável de 47 dígitos / código de barras de 44
  - Arrecadação (contas de consumo e tributos, começam com 8): linha de 48 dígitos / barras de 44
  - Fator de vencimento com o reinício da FEBRABAN (22/02/2025 = fator 1000)

Só usa a biblioteca padrão do Python.

Uso:
    python3 boleto.py "34191.09008 72564.898723 32408.290008 1 10010000082831"
"""
import json
import re
import sys
from datetime import date, timedelta

BASE_ANTIGA = date(1997, 10, 7)       # fator 1000 = 03/07/2000 ... fator 9999 = 21/02/2025
BASE_NOVA = date(2025, 2, 22)         # a partir daqui o fator recomeça em 1000

BANCOS = {
    "001": "Banco do Brasil", "033": "Santander", "104": "Caixa Econômica Federal",
    "237": "Bradesco", "341": "Itaú Unibanco", "399": "HSBC (legado)", "422": "Safra",
    "748": "Sicredi", "756": "Sicoob", "077": "Banco Inter", "260": "Nubank",
    "336": "C6 Bank", "208": "BTG Pactual", "212": "Banco Original", "041": "Banrisul",
    "070": "BRB", "004": "Banco do Nordeste", "085": "Ailos", "136": "Unicred",
}

SEGMENTOS_ARRECADACAO = {
    "1": "Prefeituras", "2": "Saneamento", "3": "Energia elétrica e gás", "4": "Telecomunicações",
    "5": "Órgãos governamentais", "6": "Carnês e assemelhados", "7": "Multas de trânsito",
    "9": "Uso exclusivo do banco",
}


def so_digitos(s: str) -> str:
    return re.sub(r"\D", "", s or "")


def mod10(num: str) -> int:
    soma, peso = 0, 2
    for d in reversed(num):
        p = int(d) * peso
        soma += p // 10 + p % 10
        peso = 1 if peso == 2 else 2
    return (10 - soma % 10) % 10


def _soma_mod11(num: str) -> int:
    soma, peso = 0, 2
    for d in reversed(num):
        soma += int(d) * peso
        peso = 2 if peso == 9 else peso + 1
    return soma


def mod11_bancario(num: str) -> int:
    """DV geral do código de barras bancário: restos que dariam 0, 10 ou 11 viram 1."""
    dv = 11 - _soma_mod11(num) % 11
    return 1 if dv in (0, 10, 11) else dv


def mod11_arrecadacao(num: str) -> int:
    resto = _soma_mod11(num) % 11
    return 0 if resto in (0, 1) else 11 - resto


def datas_do_fator(fator: int, hoje: date = None):
    """Um fator pode corresponder a duas datas (antes e depois do reinício). Escolhe a mais próxima de hoje."""
    if fator == 0:
        return None, []
    hoje = hoje or date.today()
    candidatas = [BASE_ANTIGA + timedelta(days=fator)]
    if fator >= 1000:
        candidatas.append(BASE_NOVA + timedelta(days=fator - 1000))
    escolhida = min(candidatas, key=lambda d: abs((d - hoje).days))
    return escolhida, candidatas


def fator_da_data(venc: date) -> int:
    if venc >= BASE_NOVA:
        return 1000 + (venc - BASE_NOVA).days
    return (venc - BASE_ANTIGA).days


# ---------- boleto bancário ----------

def linha_para_barras_bancario(linha: str) -> str:
    l = so_digitos(linha)
    return l[0:4] + l[32] + l[33:47] + l[4:9] + l[10:20] + l[21:31]


def barras_para_linha_bancario(barras: str) -> str:
    b = so_digitos(barras)
    c1 = b[0:4] + b[19:24]
    c2 = b[24:34]
    c3 = b[34:44]
    c1 += str(mod10(c1)); c2 += str(mod10(c2)); c3 += str(mod10(c3))
    return f"{c1[:5]}.{c1[5:]} {c2[:5]}.{c2[5:]} {c3[:5]}.{c3[5:]} {b[4]} {b[5:19]}"


def analisar_bancario(barras: str, problemas: list, hoje: date = None) -> dict:
    dv_calc = mod11_bancario(barras[:4] + barras[5:])
    if int(barras[4]) != dv_calc:
        problemas.append(f"DV geral do código de barras inválido: informado {barras[4]}, esperado {dv_calc}")
    if barras[3] != "9":
        problemas.append(f"Código da moeda {barras[3]} (esperado 9 = Real)")
    fator = int(barras[5:9])
    venc, candidatas = datas_do_fator(fator, hoje)
    return {
        "tipo": "boleto bancário",
        "banco": barras[0:3],
        "nome_banco": BANCOS.get(barras[0:3], "não mapeado"),
        "valor": f"{int(barras[9:19]) / 100:.2f}",
        "fator_vencimento": fator,
        "vencimento": venc.isoformat() if venc else None,
        "vencimento_alternativo": [d.isoformat() for d in candidatas if d != venc],
        "campo_livre": barras[19:44],
    }


# ---------- arrecadação ----------

def _mod_arrecadacao(barras: str):
    ident = barras[2]
    if ident in "67":
        return mod10, "módulo 10"
    if ident in "89":
        return mod11_arrecadacao, "módulo 11"
    return None, None


def linha_para_barras_arrecadacao(linha: str) -> str:
    l = so_digitos(linha)
    return "".join(l[i * 12:i * 12 + 11] for i in range(4))


def barras_para_linha_arrecadacao(barras: str) -> str:
    b = so_digitos(barras)
    f, _ = _mod_arrecadacao(b)
    blocos = [b[i * 11:(i + 1) * 11] for i in range(4)]
    return " ".join(f"{x}-{f(x)}" for x in blocos)


def analisar_arrecadacao(barras: str, problemas: list) -> dict:
    f, nome_mod = _mod_arrecadacao(barras)
    if f is None:
        problemas.append(f"Identificador de valor {barras[2]} inválido (esperado 6, 7, 8 ou 9)")
    else:
        dv_calc = f(barras[:3] + barras[4:])
        if int(barras[3]) != dv_calc:
            problemas.append(f"DV geral inválido ({nome_mod}): informado {barras[3]}, esperado {dv_calc}")
    efetivo = barras[2] in "68"
    return {
        "tipo": "arrecadação (conta de consumo / tributo)",
        "segmento": SEGMENTOS_ARRECADACAO.get(barras[1], f"código {barras[1]}"),
        "valor": f"{int(barras[4:15]) / 100:.2f}" if efetivo else None,
        "valor_observacao": None if efetivo else "valor de referência/quantidade de moeda: confirmar com o emissor",
        "modulo_dv": nome_mod,
        "identificacao_empresa": barras[15:19] if barras[1] != "6" else barras[15:23],
    }


def analisar(entrada: str, hoje: date = None) -> dict:
    d = so_digitos(entrada)
    problemas = []
    if len(d) == 48 and d[0] == "8":
        f, _ = _mod_arrecadacao(d[:11])
        if f:
            for i in range(4):
                bloco, dv = d[i * 12:i * 12 + 11], int(d[i * 12 + 11])
                if f(bloco) != dv:
                    problemas.append(f"DV do bloco {i + 1} inválido: informado {dv}, esperado {f(bloco)}")
        barras = linha_para_barras_arrecadacao(d)
        r = analisar_arrecadacao(barras, problemas)
        r.update(linha_digitavel=barras_para_linha_arrecadacao(barras) if f else None)
    elif len(d) == 44 and d[0] == "8":
        barras = d
        r = analisar_arrecadacao(barras, problemas)
        r.update(linha_digitavel=barras_para_linha_arrecadacao(barras) if not problemas else None)
    elif len(d) == 47:
        for i, (ini, fim, dvpos) in enumerate([(0, 9, 9), (10, 20, 20), (21, 31, 31)], start=1):
            if mod10(d[ini:fim]) != int(d[dvpos]):
                problemas.append(f"DV do campo {i} inválido: informado {d[dvpos]}, esperado {mod10(d[ini:fim])}")
        barras = linha_para_barras_bancario(d)
        r = analisar_bancario(barras, problemas, hoje)
        r.update(linha_digitavel=barras_para_linha_bancario(barras))
    elif len(d) == 44:
        barras = d
        r = analisar_bancario(barras, problemas, hoje)
        r.update(linha_digitavel=barras_para_linha_bancario(barras))
    else:
        return {"valido": False, "problemas": [f"Tamanho {len(d)} não reconhecido (esperado 44, 47 ou 48 dígitos)"]}
    r.update(codigo_barras=barras, valido=not problemas, problemas=problemas)
    return r


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    res = analisar(" ".join(sys.argv[1:]))
    print(json.dumps(res, ensure_ascii=False, indent=2))
    sys.exit(0 if res["valido"] else 1)

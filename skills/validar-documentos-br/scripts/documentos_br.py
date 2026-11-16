#!/usr/bin/env python3
"""Validação e geração de dígitos verificadores de documentos brasileiros.

Cobre CPF, CNPJ numérico e CNPJ alfanumérico (IN RFB 2.229/2024, em vigor desde jul/2026).
Só usa a biblioteca padrão do Python.

Uso:
    python3 documentos_br.py validar 12.ABC.345/01DE-35
    python3 documentos_br.py validar 529.982.247-25
    python3 documentos_br.py dv-cnpj 12ABC34501DE     -> 12ABC34501DE35
    python3 documentos_br.py dv-cpf 529982247         -> 52998224725
"""
import re
import sys

PESOS_CNPJ_DV1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
PESOS_CNPJ_DV2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]


def limpar(doc: str) -> str:
    """Remove máscara (pontos, barra, traço, espaços) e passa letras para maiúsculas."""
    return re.sub(r"[.\-/\s]", "", doc or "").upper()


def _valor_cnpj(c: str) -> int:
    # Regra oficial: valor ASCII do caractere menos 48 (0-9 -> 0-9, A -> 17 ... Z -> 42).
    return ord(c) - 48


def _mod11(soma: int) -> int:
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def dv_cnpj(base12: str) -> str:
    base12 = limpar(base12)
    if not re.fullmatch(r"[A-Z0-9]{12}", base12):
        raise ValueError("A base do CNPJ precisa ter 12 caracteres (0-9 ou A-Z)")
    dv1 = _mod11(sum(_valor_cnpj(c) * p for c, p in zip(base12, PESOS_CNPJ_DV1)))
    base13 = base12 + str(dv1)
    dv2 = _mod11(sum(_valor_cnpj(c) * p for c, p in zip(base13, PESOS_CNPJ_DV2)))
    return f"{dv1}{dv2}"


def validar_cnpj(cnpj: str) -> bool:
    c = limpar(cnpj)
    # 12 primeiros: letras maiúsculas ou números; 2 últimos (DV): sempre números.
    if not re.fullmatch(r"[A-Z0-9]{12}[0-9]{2}", c):
        return False
    if len(set(c)) == 1:  # 00000000000000, 11111111111111 ...
        return False
    return dv_cnpj(c[:12]) == c[12:]


def dv_cpf(base9: str) -> str:
    base9 = limpar(base9)
    if not re.fullmatch(r"[0-9]{9}", base9):
        raise ValueError("A base do CPF precisa ter 9 dígitos")
    nums = [int(d) for d in base9]
    dv1 = _mod11(sum(n * p for n, p in zip(nums, range(10, 1, -1))))
    nums.append(dv1)
    dv2 = _mod11(sum(n * p for n, p in zip(nums, range(11, 1, -1))))
    return f"{dv1}{dv2}"


def validar_cpf(cpf: str) -> bool:
    c = limpar(cpf)
    if not re.fullmatch(r"[0-9]{11}", c) or len(set(c)) == 1:
        return False
    return dv_cpf(c[:9]) == c[9:]


def formatar_cnpj(cnpj: str) -> str:
    c = limpar(cnpj)
    return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}"


def formatar_cpf(cpf: str) -> str:
    c = limpar(cpf)
    return f"{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}"


def identificar(doc: str) -> str:
    c = limpar(doc)
    if len(c) == 11 and c.isdigit():
        return "CPF"
    if len(c) == 14:
        return "CNPJ alfanumérico" if re.search(r"[A-Z]", c) else "CNPJ"
    return "desconhecido"


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd, valor = argv[1], argv[2]
    if cmd == "validar":
        tipo = identificar(valor)
        ok = validar_cpf(valor) if tipo == "CPF" else validar_cnpj(valor) if tipo.startswith("CNPJ") else False
        print(f"{tipo}: {'VÁLIDO' if ok else 'INVÁLIDO'}")
        return 0 if ok else 1
    if cmd == "dv-cnpj":
        print(limpar(valor) + dv_cnpj(valor))
        return 0
    if cmd == "dv-cpf":
        print(limpar(valor) + dv_cpf(valor))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))

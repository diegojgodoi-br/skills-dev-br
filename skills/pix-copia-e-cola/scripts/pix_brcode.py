#!/usr/bin/env python3
"""Pix "copia e cola" (BR Code / EMV QRCPS-MPM): gerar estático, decodificar e validar.

Baseado no Manual de Padrões para Iniciação do Pix (Banco Central) e no padrão EMV.
Só usa a biblioteca padrão do Python.

Uso:
    python3 pix_brcode.py gerar --chave email@exemplo.com --nome "LOJA EXEMPLO" --cidade LONDRINA --valor 12.50 --txid PEDIDO123
    python3 pix_brcode.py ler "00020126...6304ABCD"
"""
import argparse
import json
import re
import sys
import unicodedata

GUI_PIX = "br.gov.bcb.pix"


def crc16_ccitt(dados: str) -> str:
    """CRC16/CCITT-FALSE: polinômio 0x1021, valor inicial 0xFFFF. Retorna 4 hex maiúsculos."""
    crc = 0xFFFF
    for byte in dados.encode("utf-8"):
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if crc & 0x8000 else (crc << 1)
            crc &= 0xFFFF
    return f"{crc:04X}"


def tlv(campo: str, valor: str) -> str:
    if len(valor) > 99:
        raise ValueError(f"Campo {campo} passou de 99 caracteres")
    return f"{campo}{len(valor):02d}{valor}"


def sem_acentos(texto: str) -> str:
    """Nome e cidade devem usar caracteres simples; removemos acentos para evitar rejeição."""
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", t).strip()


def gerar_estatico(chave: str, nome: str, cidade: str, valor: float = None,
                   txid: str = "***", descricao: str = None) -> str:
    """Gera o Pix copia e cola ESTÁTICO (sem URL de cobrança)."""
    nome = sem_acentos(nome)[:25]
    cidade = sem_acentos(cidade)[:15]
    if not chave:
        raise ValueError("Informe a chave Pix")
    if txid != "***" and not re.fullmatch(r"[A-Za-z0-9]{1,25}", txid):
        raise ValueError("txid do QR estático: até 25 caracteres, só letras e números (ou *** para nenhum)")

    conta = tlv("00", GUI_PIX) + tlv("01", chave)
    if descricao:
        conta += tlv("02", descricao)
    payload = tlv("00", "01")                      # Payload Format Indicator
    payload += tlv("26", conta)                    # Merchant Account Information - Pix
    payload += tlv("52", "0000")                   # Merchant Category Code
    payload += tlv("53", "986")                    # Moeda: BRL
    if valor is not None:
        if valor <= 0:
            raise ValueError("Valor precisa ser maior que zero")
        payload += tlv("54", f"{valor:.2f}")       # ponto como separador decimal
    payload += tlv("58", "BR")
    payload += tlv("59", nome)
    payload += tlv("60", cidade)
    payload += tlv("62", tlv("05", txid))          # Additional Data Field: txid
    payload += "6304"                              # o CRC é calculado INCLUINDO "6304"
    return payload + crc16_ccitt(payload)


def _ler_tlv(texto: str) -> list:
    itens, i = [], 0
    while i < len(texto):
        if i + 4 > len(texto):
            raise ValueError(f"Estrutura TLV quebrada na posição {i}")
        campo, tam = texto[i:i + 2], texto[i + 2:i + 4]
        if not tam.isdigit():
            raise ValueError(f"Tamanho inválido no campo {campo} (posição {i})")
        tam = int(tam)
        valor = texto[i + 4:i + 4 + tam]
        if len(valor) != tam:
            raise ValueError(f"Campo {campo} declara {tam} caracteres mas o texto acabou")
        itens.append((campo, valor))
        i += 4 + tam
    return itens


def ler(codigo: str) -> dict:
    """Decodifica e valida um Pix copia e cola. Retorna dicionário com campos e problemas."""
    codigo = codigo.strip()
    problemas = []
    campos = dict(_ler_tlv(codigo))

    crc_informado = campos.get("63")
    if not crc_informado or not codigo.endswith(crc_informado) or codigo[-8:-4] != "6304":
        problemas.append("CRC (campo 63) ausente ou fora do final do código")
    else:
        esperado = crc16_ccitt(codigo[:-4])
        if esperado != crc_informado.upper():
            problemas.append(f"CRC inválido: informado {crc_informado}, esperado {esperado}")

    if campos.get("00") != "01":
        problemas.append("Campo 00 (Payload Format Indicator) deveria ser 01")

    pix = None
    for id_conta in [f"{n:02d}" for n in range(26, 52)]:
        if id_conta in campos:
            sub = dict(_ler_tlv(campos[id_conta]))
            if sub.get("00", "").lower() == GUI_PIX:
                pix = sub
                break
    if pix is None:
        problemas.append("Não encontrei o arranjo Pix (GUI br.gov.bcb.pix) nos campos 26-51")
        pix = {}

    adicionais = dict(_ler_tlv(campos["62"])) if "62" in campos else {}
    tipo = "dinâmico (URL de cobrança)" if "25" in pix else "estático"

    if campos.get("53") not in (None, "986"):
        problemas.append(f"Moeda {campos.get('53')} não é BRL (986)")
    if "54" in campos and not re.fullmatch(r"\d+(\.\d{1,2})?", campos["54"]):
        problemas.append(f"Valor (campo 54) com formato inválido: {campos['54']}")

    return {
        "valido": not problemas,
        "tipo": tipo,
        "chave": pix.get("01"),
        "url_cobranca": pix.get("25"),
        "descricao": pix.get("02"),
        "valor": campos.get("54"),
        "nome_recebedor": campos.get("59"),
        "cidade": campos.get("60"),
        "txid": adicionais.get("05"),
        "crc": crc_informado,
        "problemas": problemas,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gerar")
    g.add_argument("--chave", required=True)
    g.add_argument("--nome", required=True)
    g.add_argument("--cidade", required=True)
    g.add_argument("--valor", type=float)
    g.add_argument("--txid", default="***")
    g.add_argument("--descricao")
    l_ = sub.add_parser("ler")
    l_.add_argument("codigo")
    a = ap.parse_args()
    if a.cmd == "gerar":
        print(gerar_estatico(a.chave, a.nome, a.cidade, a.valor, a.txid, a.descricao))
        return 0
    r = ler(a.codigo)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0 if r["valido"] else 1


if __name__ == "__main__":
    sys.exit(main())

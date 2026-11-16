"""Testes de todas as skills. Rode com: python3 tests/test_tudo.py (ou pytest)."""
import random
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for s in ("validar-documentos-br", "pix-copia-e-cola", "boleto-linha-digitavel", "nfe-xml", "lgpd-revisao-sistema"):
    sys.path.insert(0, str(RAIZ / "skills" / s / "scripts"))

import documentos_br as doc  # noqa: E402
import pix_brcode as pix  # noqa: E402
import boleto  # noqa: E402
import nfe  # noqa: E402
import mapear_dados_pessoais as lgpd  # noqa: E402


def test_cnpj_exemplo_oficial():
    assert doc.dv_cnpj("12ABC34501DE") == "35"            # exemplo Serpro/RFB
    assert doc.validar_cnpj("12.ABC.345/01DE-35")
    assert not doc.validar_cnpj("12.ABC.345/01DE-36")
    assert doc.validar_cnpj("00.000.000/0001-91")
    assert not doc.validar_cnpj("11111111111111")


def test_cnpj_numerico_igual_ao_algoritmo_antigo():
    def antigo(b):
        def m(s):
            r = s % 11
            return 0 if r < 2 else 11 - r
        n = [int(x) for x in b]
        d1 = m(sum(a * p for a, p in zip(n, doc.PESOS_CNPJ_DV1)))
        n.append(d1)
        return f"{d1}{m(sum(a * p for a, p in zip(n, doc.PESOS_CNPJ_DV2)))}"
    random.seed(7)
    for _ in range(5000):
        b = "".join(random.choice("0123456789") for _ in range(12))
        assert doc.dv_cnpj(b) == antigo(b)


def test_cpf():
    assert doc.validar_cpf("529.982.247-25") and not doc.validar_cpf("529.982.247-24")
    assert not doc.validar_cpf("111.111.111-11")


def test_php_e_js_iguais_ao_python():
    pasta = RAIZ / "skills" / "validar-documentos-br" / "scripts"
    random.seed(11)
    bases = ["".join(random.choice("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(12)) for _ in range(300)]
    esperado = [doc.dv_cnpj(b) for b in bases]
    lista = ",".join(bases)
    for cmd in (
        ["php", "-r", f'require "{pasta}/documentos_br.php"; echo implode(",", array_map("cnpj_dv", explode(",", "{lista}")));'],
        ["node", "-e", f'const d=require("{pasta}/documentos_br.js"); process.stdout.write("{lista}".split(",").map(d.cnpjDV).join(","))'],
    ):
        try:
            saida = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
        except FileNotFoundError:
            continue  # linguagem não instalada nesta máquina
        assert saida.split(",") == esperado, cmd[0]


def test_pix_exemplo_bcb():
    bcb = ("00020126580014br.gov.bcb.pix0136123e4567-e12b-12d1-a456-4266554400005204000053039865802BR"
           "5913Fulano de Tal6008BRASILIA62070503***63041D3D")
    assert pix.gerar_estatico("123e4567-e12b-12d1-a456-426655440000", "Fulano de Tal", "BRASILIA") == bcb
    r = pix.ler(bcb)
    assert r["valido"] and r["tipo"] == "estático" and r["txid"] == "***"
    assert not pix.ler(bcb[:-4] + "0000")["valido"]


def test_pix_com_valor_e_acentos():
    c = pix.gerar_estatico("diego@exemplo.com", "José da Conceição", "São José dos Pinhais", 12.5, "PEDIDO123")
    r = pix.ler(c)
    assert r["valido"] and r["valor"] == "12.50" and r["nome_recebedor"] == "Jose da Conceicao"
    assert r["cidade"] == "Sao Jose dos Pi" and r["txid"] == "PEDIDO123"
    assert not pix.ler(c.replace("12.50", "99.50"))["valido"]


def test_boleto_fator():
    assert boleto.BASE_ANTIGA + timedelta(days=9999) == date(2025, 2, 21)
    assert boleto.fator_da_data(date(2025, 2, 22)) == 1000
    assert boleto.fator_da_data(date(2000, 12, 6)) == 1156


def test_boleto_linhas_reais():
    itau = "34191.09008 72564.898723 32408.290008 1 10010000082831"
    r = boleto.analisar(itau, hoje=date(2025, 3, 1))
    assert r["valido"] and r["banco"] == "341" and r["valor"] == "828.31" and r["vencimento"] == "2025-02-23"
    caixa = "10499.00127 00200.001287 70000.000128 1 10990000016000"
    assert boleto.analisar(caixa)["valido"]
    for linha in (itau, caixa):
        barras = boleto.linha_para_barras_bancario(linha)
        assert boleto.so_digitos(boleto.barras_para_linha_bancario(barras)) == boleto.so_digitos(linha)
    assert not boleto.analisar(itau.replace("90008", "90009"))["valido"]


def test_boleto_arrecadacao():
    random.seed(3)
    for ident in "6789":
        f = boleto.mod10 if ident in "67" else boleto.mod11_arrecadacao
        for _ in range(100):
            corpo = "8" + random.choice("12345") + ident
            resto = "".join(random.choice("0123456789") for _ in range(40))
            barras = corpo + str(f(corpo + resto)) + resto
            linha = boleto.barras_para_linha_arrecadacao(barras)
            r = boleto.analisar(linha)
            assert r["valido"] and r["codigo_barras"] == barras
            d = boleto.so_digitos(linha)
            assert not boleto.analisar(d[:14] + str((int(d[14]) + 1) % 10) + d[15:])["valido"]


def test_nfe_chave():
    moc = "52060433009911002506550120000007800267301615"
    r = nfe.analisar_chave(moc)
    assert r["valida"] and r["uf"] == "GO" and r["numero"] == 780
    assert not nfe.analisar_chave(moc[:-1] + "4")["valida"]
    base = "412608" + "12ABC34501DE35" + "55001" + "000000123" + "1" + "00000001"
    assert nfe.analisar_chave(base + str(nfe.dv_chave(base)))["valida"]


def test_nfe_xml():
    base = "412608" + "12ABC34501DE35" + "55001" + "000000123" + "1" + "00000001"
    k = base + str(nfe.dv_chave(base))
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00"><NFe><infNFe Id="NFe{k}" versao="4.00">
<ide><mod>55</mod><serie>1</serie><nNF>123</nNF><dhEmi>2026-08-10T10:00:00-03:00</dhEmi><tpNF>1</tpNF></ide>
<emit><CNPJ>12ABC34501DE35</CNPJ><xNome>EMPRESA EXEMPLO LTDA</xNome></emit>
<dest><CPF>52998224725</CPF><xNome>CLIENTE TESTE</xNome></dest>
<det nItem="1"><prod><cProd>001</cProd><xProd>Produto A</xProd><NCM>12019000</NCM><CFOP>5102</CFOP><qCom>10</qCom><vUnCom>150.00</vUnCom><vProd>1500.00</vProd></prod><imposto><IBSCBS><CST>000</CST></IBSCBS></imposto></det>
<det nItem="2"><prod><cProd>002</cProd><xProd>Produto B</xProd><qCom>2</qCom><vUnCom>45.50</vUnCom><vProd>91.00</vProd></prod><imposto/></det>
<total><ICMSTot><vProd>1591.00</vProd><vNF>1591.00</vNF></ICMSTot><IBSCBSTot><vBCIBSCBS>1591.00</vBCIBSCBS></IBSCBSTot></total>
</infNFe></NFe><protNFe versao="4.00"><infProt><cStat>100</cStat><nProt>141260000000001</nProt></infProt></protNFe></nfeProc>'''
    with tempfile.TemporaryDirectory() as d:
        Path(d, "nota.xml").write_text(xml, encoding="utf-8")
        Path(d, "outro.xml").write_text("<nao-e-nfe/>", encoding="utf-8")
        notas, itens, erros = nfe.coletar([d])
    n = notas[0]
    assert n["chave_valida"] and n["autorizada"] and n["valor_nota"] == 1591.0
    assert len(itens) == 2 and itens[0]["tem_grupo_ibscbs"] and not itens[1]["tem_grupo_ibscbs"]
    assert "vBCIBSCBS" in n["ibs_cbs_totais"] and len(erros) == 1


def test_lgpd_varredura_e_mascara():
    with tempfile.TemporaryDirectory() as d:
        Path(d, "schema.sql").write_text(
            "CREATE TABLE clientes (cpf CHAR(11), email VARCHAR(99), religiao VARCHAR(30), senha VARCHAR(32));")
        Path(d, "app").mkdir()
        Path(d, "app", "login.php").write_text(
            '<?php\n$h = md5($senha);\nerror_log("falhou cpf " . $cpf);\n'
            '// joao.silva@empresareal.com.br 529.982.247-25 (43) 99876-5432\n')
        Path(d, "node_modules").mkdir()
        Path(d, "node_modules", "x.js").write_text("console.log(user.email)")
        achados = lgpd.varrer(Path(d))
        md = lgpd.relatorio_md(achados, d)
    tipos = {a[0] for a in achados}
    assert {"campo", "dado_real", "log", "senha"} <= tipos
    assert {"sensivel", "credencial"} <= {a[1] for a in achados if a[0] == "campo"}
    assert not any("node_modules" in a[2] for a in achados)
    for vazamento in ("529.982.247-25", "joao.silva", "empresareal", "99876-5432"):
        assert vazamento not in md


if __name__ == "__main__":
    testes = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in testes:
        t()
        print("ok ", t.__name__)
    print(f"\n{len(testes)} testes passaram")

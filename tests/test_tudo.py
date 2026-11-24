"""Testes de todas as skills. Rode com: python3 tests/test_tudo.py (ou pytest)."""
import random
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for s in ("validar-documentos-br", "pix-copia-e-cola", "boleto-linha-digitavel", "nfe-xml", "lgpd-revisao-sistema",
          "reforma-tributaria-ibs-cbs", "nfse-nacional"):
    sys.path.insert(0, str(RAIZ / "skills" / s / "scripts"))

import documentos_br as doc  # noqa: E402
import pix_brcode as pix  # noqa: E402
import boleto  # noqa: E402
import nfe  # noqa: E402
import mapear_dados_pessoais as lgpd  # noqa: E402
import reforma  # noqa: E402
import nfse  # noqa: E402


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


def test_reforma_2026_teste():
    r = reforma.simular("1000", 2026)
    assert (r["cbs"], r["ibs"], r["total_com_tributo"]) == ("9.00", "1.00", "1010.00")
    assert r["pis_cofins_vigente"] is True


def test_reforma_nao_inventa_aliquota():
    for ano in (2027, 2029, 2033):
        try:
            reforma.simular("1000", ano)
        except ValueError as e:
            assert "Senado" in str(e)
        else:
            raise AssertionError(f"{ano} deveria exigir a alíquota de referência")
    assert reforma.simular("1000", 2027, cbs="8.8")["ibs"] == "1.00"   # IBS 2027 = 0,05% + 0,05%


def test_reforma_reducoes_e_calendario():
    assert reforma.simular("1000", 2026, reducao=60)["cbs"] == "3.60"
    assert reforma.simular("1000", 2026, reducao=100)["total_ibs_cbs"] == "0.00"
    assert reforma.simular("200", 2027, cbs="10", ibs="0.1", reducao=30)["cbs"] == "14.00"
    fatores = [str(reforma.CALENDARIO[a]["icms_iss"]) for a in range(2028, 2034)]
    assert fatores == ["1", "0.9", "0.8", "0.7", "0.6", "0"]
    assert not reforma.CALENDARIO[2027]["pis_cofins"]


def test_reforma_por_dentro_e_apuracao():
    r = reforma.por_dentro("1100", cbs="9", ibs="1")
    assert (r["base"], r["tributos"], r["aliq_efetiva_total"]) == ("1000.00", "100.00", "10")
    a = reforma.apurar("100000", "40000", cbs="9", ibs="1")
    assert a["cbs"]["saldo"] == "5400.00" and a["ibs"]["saldo"] == "600.00"
    assert reforma.apurar("100", "300", cbs="9", ibs="1")["cbs"]["situacao"] == "saldo credor"


CHAVE_NFSE = "41130022212345678000195000000000012326111234567891"


def test_nfse_chave_e_dps():
    c = nfse.decompor_chave("NFS" + CHAVE_NFSE)
    assert c["formato_ok"] and c["cod_municipio_ibge"] == "4113002"
    assert (c["tipo_inscricao"], c["inscricao_emitente"], c["numero_nfse"], c["emissao_aaaa_mm"]) == \
        ("CNPJ", "12345678000195", "123", "2026-11")
    assert c["dv_conferido"] is False                      # regra do DV não é pública
    cpf = nfse.decompor_chave(CHAVE_NFSE[:8] + "1" + "00052998224725" + CHAVE_NFSE[23:])
    assert cpf["tipo_inscricao"] == "CPF" and cpf["inscricao_emitente"] == "52998224725"
    assert not nfse.decompor_chave(CHAVE_NFSE[:-1])["formato_ok"]
    assert not nfse.decompor_chave(CHAVE_NFSE[:36] + "2613" + CHAVE_NFSE[40:])["formato_ok"]   # mês 13
    d = nfse.decompor_dps("DPS411300221234567800019500001000000000000123")
    assert d["formato_ok"] and (d["serie"], d["numero_dps"]) == ("1", "123")


def test_nfse_ler_xml_e_lote():
    xml = RAIZ / "tests" / "fixtures" / "nfse_exemplo.xml"
    n = nfse.ler_xml(xml)
    assert n["chave"] == CHAVE_NFSE and n["numero_nfse"] == "123"
    assert (n["prestador_doc"], n["tomador_doc"]) == ("12345678000195", "98765432000198")
    assert (n["valor_servico"], n["valor_iss"], n["valor_liquido"]) == ("1000.00", "20.00", "980.00")
    assert n["iss_retencao"] == "retido pelo tomador"
    assert n["tem_grupo_ibscbs"] and (n["ibscbs_cst"], n["ibscbs_cclasstrib"]) == ("000", "000001")
    with tempfile.TemporaryDirectory() as d:
        texto = xml.read_text(encoding="utf-8")
        Path(d, "a.xml").write_text(texto, encoding="utf-8")
        Path(d, "copia.xml").write_text(texto, encoding="utf-8")
        sem_ns = texto.replace(' xmlns="http://www.sped.fazenda.gov.br/nfse"', "")
        inicio = sem_ns.index("<DPS ")
        Path(d, "so_dps.xml").write_text(sem_ns[inicio:sem_ns.index("</DPS>") + 6], encoding="utf-8")
        Path(d, "lixo.xml").write_text("<nada/>", encoding="utf-8")
        notas, erros = nfse.ler([d])
        assert len(notas) == 3 and len(erros) == 1
        assert any("duplicada" in x["alertas"] for x in notas)
        dps = [x for x in notas if x["tipo"].startswith("DPS")][0]
        assert "não prova" in dps["alertas"] and dps["tomador_doc"] == "98765432000198"
        csv_ = nfse.salvar_csv(notas, str(Path(d, "rel")))
        conteudo = csv_.read_text(encoding="utf-8-sig")
        assert "1000,00" in conteudo and conteudo.count("\n") == 4


if __name__ == "__main__":
    testes = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in testes:
        t()
        print("ok ", t.__name__)
    print(f"\n{len(testes)} testes passaram")

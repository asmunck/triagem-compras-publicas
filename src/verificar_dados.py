"""Auditoria independente das saídas distribuídas. Execute python src/verificar_dados.py."""
from collections import Counter, defaultdict
import csv
from datetime import date
from decimal import Decimal
import gzip
import hashlib
import json
from pathlib import Path
import re
from statistics import mean, median, quantiles

BASE = Path(__file__).resolve().parents[1] / "dados"


def ler(nome):
    with (BASE/nome).open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f,delimiter=";"))


def chave(r):
    return (r["catmat"],r["id_compra_item"],r["fornecedor"])


def n(txt):
    return Decimal(txt.replace(",","."))


def conferir():
    cfg=json.loads((BASE.parent/"config"/"materiais.json").read_text(encoding="utf-8-sig"))
    for nome, esperado in json.loads((BASE/"hashes.json").read_bytes()).items():
        assert hashlib.sha256((BASE/nome).read_bytes()).hexdigest()==esperado, nome
    treino, universo = ler("treino_2024.csv"), ler("triagem_2025.csv")
    fila, pendencias = ler("fila_2025.csv"), ler("pendencias_2025.csv")
    res = json.loads((BASE/"resultados.json").read_bytes())
    resumo = res["resumo"]
    man = json.loads((BASE/"fonte"/"manifesto.json").read_bytes())
    total_periodo = 0
    for pg in man["paginas"]:
        b=(BASE/"fonte"/pg["arquivo"]).read_bytes()
        assert hashlib.sha256(b).hexdigest()==pg["sha256_gz"]
        registros=json.loads(gzip.decompress(b))["registros"]
        total_periodo+=len(registros)
        for r in registros:
            assert not ({"niFornecedor","nomeFornecedor","descricaoDetalhadaItem"}&r.keys())
            assert not re.search(r"[\w.+%-]+@[\w.-]+\.[a-z]{2,24}",r["objeto_compra"],re.I)
            assert not re.search(r"(?<!\d)(?:\d{3}[. ]\d{3}[. ]\d{3}[- ]\d{2}|\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{11}|\d{14})(?!\d)",r["objeto_compra"])
    assert total_periodo==len(treino)+len(universo)
    assert len(treino)==resumo["universo_2024"] and len(universo)==resumo["universo_2025"]
    assert all(r["data_resultado"].startswith("2024-") for r in treino)
    assert all(r["data_resultado"].startswith("2025-") for r in universo)
    assert len({chave(r) for r in universo})==len(universo)
    assert {chave(r) for r in pendencias}=={chave(r) for r in universo if r["status"]!="Comparável"}
    comparaveis=[r for r in universo if r["status"]=="Comparável"]
    ativos=[r for r in universo if r["prioridade"] in ("Alta","Média","Contextual")]
    assert len(fila)==len(ativos)==resumo["fila_n"]
    assert [int(x["posicao"]) for x in fila]==list(range(1,len(fila)+1))
    assert [chave(x) for x in fila]==[chave(x) for x in sorted(ativos,key=lambda r:int(r["posicao"]))]
    grupos=defaultdict(list)
    for r in treino:
        if r["status"]=="Elegível":
            grupos[(r["catmat"],r["apresentacao"])].append(r)
    ajustes={}
    for coorte, grupo in grupos.items():
        if len(grupo)<cfg["historico_minimo"]:
            continue
        # O cálculo independente da biblioteca padrão cobre as fronteiras inteiras.
        tercis=quantiles([n(x["quantidade"]) for x in grupo], n=3, method="inclusive")
        def nome_faixa(q):
            return "Baixo" if q<=tercis[0] else "Médio" if q<=tercis[1] else "Alto"
        geral=median(n(x["preco_unitario"]) for x in grupo)
        medias={}
        for nome in ("Baixo","Médio","Alto"):
            valores=[n(x["preco_unitario"]) for x in grupo if nome_faixa(n(x["quantidade"]))==nome]
            medias[nome]=(median(valores) if len(valores)>=cfg["faixa_minima"] else geral)
        ajustes[coorte]=(tercis,medias)
    for r in comparaveis:
        grupo=grupos[(r["catmat"],r["apresentacao"])]
        assert len(grupo)==int(r["n_historico"])
        limites,medianas=ajustes[(r["catmat"],r["apresentacao"])]
        qtd=n(r["quantidade"])
        f="Baixo" if qtd<=limites[0] else "Médio" if qtd<=limites[1] else "Alto"
        assert r["faixa_volume"]==f and n(r["referencia"])==medianas[f]
        assert median(n(x["preco_unitario"]) for x in grupo)==n(r["baseline"])
        assert (n(r["preco_unitario"])>n(r["limite_superior"]))==bool(int(r["r1_preco"]))
        assert n(r["desvio_unitario"])==n(r["preco_unitario"])-n(r["referencia"])
        assert n(r["diferenca_total"])==n(r["desvio_unitario"])*n(r["quantidade"])
        assert n(r["erro_modelo"])==abs(n(r["desvio_unitario"]))
    compras_treino={r["id_compra"] for g in grupos.values() if len(g)>=cfg["historico_minimo"] for r in g}
    teste=[r for r in universo if r["valida_teste"]=="1"]
    assert not compras_treino&{r["id_compra"] for r in teste}
    assert len(teste)==res["avaliacao"]["n"]
    for coluna,metrica in (("erro_modelo","mae_modelo"),("erro_baseline","mae_baseline")):
        assert abs(float(mean(n(r[coluna]) for r in teste))-res["avaliacao"][metrica])<1e-9
    historico=defaultdict(list)
    for r in treino+universo:
        historico[(r["codigo_uasg"],r["catmat"],r["fornecedor"])].append(r)
    for r in universo:
        assert (n(r["quantidade"])==1 and bool(r["expressao_lote"]))==bool(int(r["r2_lote"]))
        atual=date.fromisoformat(r["data_resultado"])
        candidatos=[x for x in historico[(r["codigo_uasg"],r["catmat"],r["fornecedor"])]
                    if x["id_compra"]!=r["id_compra"] and 1<=(atual-date.fromisoformat(x["data_resultado"])).days<=cfg["janela_recorrencia_dias"]]
        assert bool(candidatos)==bool(int(r["r3_recorrencia"]))
        if candidatos:
            assert r["data_anterior"]==max(x["data_resultado"] for x in candidatos)
            assert any(r["compra_anterior"]==x["id_compra"] and r["data_anterior"]==x["data_resultado"] for x in candidatos)
    print(f"{len(man['paginas'])} páginas, {len(teste)} testes temporais e {len(fila)} posições verificadas.")


if __name__=="__main__":
    conferir()

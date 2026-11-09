"""Produz o painel portátil offline a partir do CSV de triagem e dos modelos publicados."""
import argparse
import csv
import json
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]


def numero(v):
    return float(str(v).replace(",", ".")) if v not in (None, "") else None


def montar_painel(dados, destino):
    with (dados / "triagem_2025.csv").open(encoding="utf-8-sig", newline="") as arquivo:
        base = list(csv.DictReader(arquivo, delimiter=";"))
    resultado = json.loads((dados / "resultados.json").read_text(encoding="utf-8-sig"))
    rows = []
    for r in base:
        p, ref = numero(r["preco_unitario"]), numero(r["referencia"])
        regras = [f"R{i}" for i, chave in enumerate(("r1_preco", "r2_lote", "r3_recorrencia"), 1)
                  if r[chave] == "1"]
        pos = numero(r["posicao"])
        rows.append(dict(item=r["id_compra_item"], compra=r["id_compra"], forn=r["fornecedor"],
                         cod=r["catmat"], mat=r["material"], fam=r["familia"], unit=r["apresentacao"],
                         cohort=r["catmat"] + " | " + r["apresentacao"], data=r["data_resultado"],
                         uf=r["uf"], esf=r["esfera"], uasg=r["codigo_uasg"], nome=r["uasg"],
                         org=r["orgao"], obj=r["objeto_compra"], status=r["status"],
                         q=numero(r["quantidade"]), p=p, ref=ref, base=numero(r["baseline"]),
                         cap=numero(r["limite_superior"]), hist=numero(r["n_historico"]),
                         faixa=r["faixa_volume"], ratio=p/ref if p is not None and ref else None,
                         impact=max(0, numero(r["diferenca_total"]) or 0) if ref is not None else None,
                         flag=pos is not None and pos > 0, pos=pos, pri=r["prioridade"],
                         reason=r["motivos"], rules=regras, last=r["data_anterior"],
                         lastbuy=r["compra_anterior"], eval=r["valida_teste"] == "1",
                         err=numero(r["erro_modelo"]), errbase=numero(r["erro_baseline"]),
                         fonte=r["url_fonte"]))
    carga = {
        "rows": rows, "models": resultado["modelos_2025"],
        "regra": "A fila começa pelos casos com dois ou mais sinais, seguidos de R1 isolado e dos sinais contextuais. A exposição ajuda a ordenar itens do mesmo nível.",
        "cobertura": "Cada grupo reúne o mesmo código de catálogo (CATMAT) e a mesma apresentação comercial. A referência exige pelo menos 20 resultados de 2024."
    }
    molde = (Path(__file__).parent / "painel.html").read_text(encoding="utf-8")
    embutido = json.dumps(carga, ensure_ascii=False, allow_nan=False, separators=(",", ":")).replace("<", "\\u003c")
    destino.write_text(molde.replace("__CARGA_JSON__", embutido), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dados", type=Path, default=RAIZ / "dados")
    parser.add_argument("--saida", type=Path, default=RAIZ / "index.html")
    opcoes = parser.parse_args()
    montar_painel(opcoes.dados, opcoes.saida)


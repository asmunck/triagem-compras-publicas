"""Gera fichas sem desfecho e a chave dos estratos da avaliação humana."""
import argparse
from collections import defaultdict
import csv
from hashlib import sha256
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SEMENTE = "triagem-2025-protocolo-v1"
ESTRATOS = {"Alta": 7, "Média": 7, "Contextual": 7, "Sem sinal": 7}


def resumo(chave, contexto):
    entrada = f"{SEMENTE}|{contexto}|{chave}".encode("utf-8")
    return sha256(entrada).hexdigest()


def gravar(destino, linhas):
    with destino.open("x", encoding="utf-8-sig", newline="") as saida:
        escritor = csv.DictWriter(saida, fieldnames=list(linhas[0]), delimiter=";")
        escritor.writeheader()
        escritor.writerows(linhas)


def gerar(destino):
    fonte = RAIZ / "dados" / "triagem_2025.csv"
    grupos = defaultdict(list)
    with fonte.open(encoding="utf-8-sig", newline="") as arquivo:
        for row in csv.DictReader(arquivo, delimiter=";"):
            if row["status"] == "Comparável":
                chave = f"{row['id_compra_item']}|{row['fornecedor']}"
                grupos[row["prioridade"]].append((chave, row))
    if set(grupos) != set(ESTRATOS):
        raise ValueError("Estratos divergentes do protocolo. Verifique a versão da base.")
    fichas = []
    plano = []
    for estrato, n in ESTRATOS.items():
        total = len(grupos[estrato])
        if n > total:
            raise ValueError(f"O estrato {estrato} tem menos de {n} resultados.")
        selecionados = sorted(grupos[estrato], key=lambda par: resumo(par[0], "selecao"))[:n]
        for chave, row in selecionados:
            ficha = resumo(chave, "ficha")[:12]
            item = row["id_compra_item"]
            compra = row["id_compra"]
            campos = {"ficha": ficha, "id_compra_item": item, "fornecedor_pseudonimo": row["fornecedor"],
                      "material": row["material"], "data_pesquisa_precos": row["data_resultado"],
                      "fonte_precos": row["url_fonte"],
                      "fonte_item": "https://dadosabertos.compras.gov.br/modulo-contratacoes/"
                                    f"2.1_consultarItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={compra}&idCompraItem={item}"}
            for campo in ("revisor_codigo", "data_revisao", "unidade_confirmada", "quantidade_confirmada",
                          "preco_verificado_brl", "motivo_e_evidencia", "url_documento", "pagina_item",
                          "desfecho", "acao_ou_limite", "minutos"):
                campos[campo] = ""
            fichas.append(campos)
            plano.append({"ficha": ficha, "estrato": estrato, "N": total, "n": n,
                          "posicao_fila": row["posicao"], "data_consenso": "", "desfecho_final": "",
                          "fundamento_evidencia_final": "", "url_pagina_final": ""})
    if len({f["ficha"] for f in fichas}) != len(fichas):
        raise ValueError("Chave de ficha repetida.")
    destino.mkdir(parents=True, exist_ok=True)
    if any((destino / nome).exists() for nome in ["fichas_revisao.csv", "plano_amostral.csv"]):
        raise FileExistsError("Use uma pasta de saída nova para preservar eventuais decisões preenchidas.")
    gravar(destino / "fichas_revisao.csv", sorted(fichas, key=lambda f: f["ficha"]))
    gravar(destino / "plano_amostral.csv", sorted(plano, key=lambda f: f["ficha"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", required=True, type=Path, help="Diretório que receberá os dois CSVs.")
    gerar(parser.parse_args().saida)

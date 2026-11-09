"""Triagem de compras. Executar na raiz: python src/triagem.py --help."""
import argparse
from collections import Counter, defaultdict, deque
from datetime import date, datetime, timezone
from decimal import Decimal
import csv
import gzip
import hashlib
from itertools import groupby
import json
from pathlib import Path
import re
from statistics import mean, median
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

RAIZ = Path(__file__).resolve().parents[1]
API = "https://dadosabertos.compras.gov.br/modulo-pesquisa-preco/1_consultarMaterial"
EMAIL = re.compile(r"[\w.+%-]+@[\w.-]+\.[A-Za-z]{2,24}", re.I)
DOCUMENTO = re.compile(r"(?<!\d)(?:\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{3}[. ]\d{3}[. ]\d{3}[- ]\d{2}|\d{11}|\d{14})(?!\d)")
TEL = re.compile(r"(?<!\d)(?:\(\d{2}\)|\d{2}[- ])\s*9?\d{4}[- ]\d{4}(?!\d)")
LOTE = re.compile(r"\b(?:lotes?\s+(?:[uú]nic[oa]s?|n[º°.]?\s*\d+|\d+|[IVX]+)\b|grupos?\s+(?:[uú]nic[oa]s?|n[º°.]?\s*\d+|\d+|[IVX]+)\b|(?:por|em|dois|dos|tr[êe]s)\s+(?:lotes?|grupos?)\b|(?:lotes?|grupos?)\s+(?:de\s+itens|compostos?\b))", re.I)
VOLUMES = ("Baixo", "Médio", "Alto")
BASE = ["id_compra_item","fornecedor","id_compra","data_resultado","catmat","material","familia","apresentacao",
        "uf","esfera","codigo_uasg","uasg","orgao","objeto_compra","quantidade","preco_unitario"]
ADICIONAIS = ["status","n_historico","faixa_volume","referencia","baseline","limite_superior","desvio_unitario",
              "desvio_pct","diferenca_total","erro_modelo","erro_baseline","r1_preco","r2_lote","r3_recorrencia",
              "data_anterior","compra_anterior","motivos","prioridade","posicao","url_fonte","valida_teste",
              "expressao_lote","fallback_volume"]
D = Decimal


def hash_bytes(b):
    return hashlib.sha256(b).hexdigest()


def dump(path, obj):
    def numero(valor):
        if isinstance(valor, D):
            return float(valor)
        raise TypeError(str(type(valor)))
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=numero)+"\n", encoding="utf-8")


def url_codigo(c, pagina=1, compra=None):
    params = dict(tipo="codigoItemCatalogo", codigo=c, tamanhoPagina=500, pagina=pagina)
    if compra:
        params["idCompra"] = compra
    return API + "?" + urlencode(params)


def ler_online(c, p):
    pedido = Request(url_codigo(c,p), headers={"Accept":"application/json"})
    for i in range(4):
        try:
            with urlopen(pedido, timeout=60) as res:
                return res.read()
        except (HTTPError, URLError, TimeoutError) as erro:
            if i == 3 or (isinstance(erro, HTTPError) and erro.code < 500 and erro.code != 429):
                raise
            time.sleep(2**i)


def minimizar(r, identidades):
    if not r.get("niFornecedor"):
        token = ""
    else:
        token = "F-" + hash_bytes(r["niFornecedor"].encode())[:16]
        if identidades.setdefault(token,r["niFornecedor"]) != r["niFornecedor"]:
            raise ValueError("Colisão de pseudônimos.")
    objeto = " ".join((r.get("objetoCompra") or "").split())
    objeto = EMAIL.sub("[e-mail]", DOCUMENTO.sub("[identificação]", TEL.sub("[telefone]", objeto)))
    achado = LOTE.search(objeto)
    # Preserva evidência localizada, mesmo quando a frase ocorre no fim de um texto longo.
    trecho = objeto[:300]
    if achado and achado.end() > 300:
        trecho += " […] " + objeto[max(0,achado.start()-30):achado.end()+40]
    return {"id_compra_item":r.get("idCompraItem") or "", "fornecedor":token, "id_compra":str(r.get("idCompra") or ""),
            "data_resultado":r.get("dataResultado") or "", "catmat":str(r["codigoItemCatalogo"]),
            "uf":r.get("estado") or "", "esfera":r.get("esfera") or "", "codigo_uasg":r.get("codigoUasg") or "",
            "uasg":r.get("nomeUasg") or "", "orgao":r.get("nomeOrgao") or "", "objeto_compra":trecho,
            "quantidade":r.get("quantidade"), "preco_unitario":r.get("precoUnitario"),
            "unidade":r.get("siglaUnidadeFornecimento"), "capacidade":r.get("capacidadeUnidadeFornecimento"),
            "medida":r.get("siglaUnidadeMedida"), "expressao_lote":achado.group() if achado else ""}


def congelar(pasta, config, leitor, instante):
    pasta.mkdir(parents=True)
    lista, identidades = [], {}
    for m in config["materiais"]:
        c = m["catmat"]
        p, paginas, total, recebidos = 1, 1, None, 0
        while p <= paginas:
            b = leitor(c, p)
            env = json.loads(b)
            if p == 1:
                paginas, total = env["totalPaginas"], env["totalRegistros"]
            if (env["totalPaginas"],env["totalRegistros"]) != (paginas,total):
                raise ValueError(f"{c}: paginação alterada durante a extração")
            registros = env["resultado"]
            if any(str(r["codigoItemCatalogo"]) != c for r in registros):
                raise ValueError("A resposta contém CATMAT diferente do filtro.")
            periodo = [minimizar(r, identidades) for r in registros
                       if (r.get("dataResultado") or "")[:4] in {"2024","2025"}]
            reg = {"catmat":c,"pagina":p,"registros":periodo}
            proje = json.dumps(reg, ensure_ascii=False, separators=(",",":")).encode()
            nome = f"{c}_{p:03}.json.gz"
            gz = gzip.compress(proje,mtime=0)
            (pasta/nome).write_bytes(gz)
            lista.append({"catmat":c,"pagina":p,"arquivo":nome,"url":url_codigo(c,p),"n_original":len(registros),
                          "n_periodo":len(periodo),"sha256_original":hash_bytes(b),"sha256_gz":hash_bytes(gz)})
            recebidos += len(registros)
            p += 1
        if recebidos != total:
            raise ValueError(f"{c}: total de registros inconsistente")
    dump(pasta/"manifesto.json",{"coleta_utc":instante,"endpoint":API,"periodo_por_data_resultado":[2024,2025],
                                "paginas":lista})


def carregar(pasta,cfg):
    man = json.loads((pasta/"manifesto.json").read_bytes())
    mats = {m["catmat"]:m for m in cfg["materiais"]}
    aps = {c:{tuple(a[:3]):a[3] for a in m["apresentacoes"]} for c,m in mats.items()}
    saida = []
    for p in man["paginas"]:
        gz = (pasta/p["arquivo"]).read_bytes()
        if hash_bytes(gz) != p["sha256_gz"]:
            raise ValueError(p["arquivo"]+": hash divergente")
        env = json.loads(gzip.decompress(gz))
        if len(env["registros"]) != p["n_periodo"] or env["catmat"] != p["catmat"]:
            raise ValueError("Conteúdo incompatível com manifesto")
        for r in env["registros"]:
            c = r["catmat"]
            if c not in mats:
                continue
            m = mats[c]
            tripla = (r["unidade"],r["capacidade"],r["medida"])
            ap = aps[c].get(tripla)
            r.update(material=m["material"], familia=m["familia"], habilitada=bool(ap),
                     apresentacao=ap or f"{tripla[0] or 'sem sigla'} / {tripla[1] or 0:g} / {tripla[2] or 'sem medida'}")
            for campo in ("preco_unitario","quantidade"):
                if r[campo] is not None:
                    r[campo] = D(str(r[campo]))
            saida.append(r)
    if set(mats) != {r["catmat"] for r in saida}:
        raise ValueError("Configuração e códigos do snapshot divergem. Uma nova coleta é necessária.")
    return sorted(saida,key=lambda r:(r["data_resultado"],r["id_compra_item"],r["fornecedor"])), man


def status_inicial(r, duplicados):
    if not all(r[k] for k in ("id_compra_item","id_compra","fornecedor","data_resultado")):
        return "Chave ausente"
    if chave(r) in duplicados:
        return "Chave duplicada"
    if not r["habilitada"]:
        return "Apresentação fora do recorte"
    if (r["quantidade"] or 0)<=0 or (r["preco_unitario"] or 0)<=0:
        return "Valor ou quantidade inválida"
    return "Elegível"


def chave(r):
    return (r["catmat"], r["id_compra_item"], r["fornecedor"])


def coorte(r):
    return (r["catmat"],r["apresentacao"])


def quantil(nums, numerador, denominador):
    valores = sorted(nums)
    i, resto = divmod((len(valores) - 1) * numerador, denominador)
    if resto == 0:
        return valores[i]
    return valores[i] + (valores[i+1] - valores[i]) * resto / denominador


def faixa(q, cortes):
    if q <= cortes[0]:
        return VOLUMES[0]
    if q <= cortes[1]:
        return VOLUMES[1]
    return VOLUMES[2]


def ajustar(registros,cfg):
    grupos = defaultdict(list)
    for r in registros:
        if r["status"]=="Elegível":
            grupos[coorte(r)].append(r)
    modelos = {}
    for m in cfg["materiais"]:
        for a in m["apresentacoes"]:
            k=(m["catmat"],a[3])
            g=grupos[k]
            obj={"catmat":k[0],"familia":m["familia"],"material":m["material"],"apresentacao":k[1],
                 "n":len(g),"n_minimo":cfg["historico_minimo"],"habilitado":len(g)>=cfg["historico_minimo"],
                 "cortes_volume":[],"faixas":[],"baseline":None,"q1_preco":None,"q3_preco":None,"limite_superior":None}
            modelos[k]=obj
            if not obj["habilitado"]:
                continue
            ps=[r["preco_unitario"] for r in g]; qs=[r["quantidade"] for r in g]
            q1,q3=quantil(ps, 1, 4), quantil(ps, 3, 4)
            cortes=[quantil(qs, 1, 3), quantil(qs, 2, 3)]
            obj.update(q1_preco=q1,q3_preco=q3,limite_superior=q3+D("1.5")*(q3-q1),baseline=median(ps),
                       cortes_volume=cortes)
            for f in VOLUMES:
                v=[r["preco_unitario"] for r in g if faixa(r["quantidade"],cortes)==f]
                fallback=len(v)<cfg["faixa_minima"]
                obj["faixas"].append({"faixa":f,"n":len(v),"fallback":fallback,
                                      "referencia":obj["baseline"] if fallback else median(v)})
    return modelos


def recorrencias(registros, janela):
    historico=defaultdict(deque)
    for dia,grupo in groupby(registros,key=lambda r:r["data_resultado"]):
        dia_data=date.fromisoformat(dia)
        linhas=list(grupo)
        for r in linhas:
            k=(r["codigo_uasg"],r["catmat"],r["fornecedor"])
            r["r3_recorrencia"],r["data_anterior"],r["compra_anterior"]=0,"",""
            if not all(k) or not r["id_compra"] or r["status"] in ("Chave duplicada","Chave ausente"):
                continue
            vistos=historico[k]
            while vistos and (dia_data-vistos[0][0]).days>janela:
                vistos.popleft()
            anterior=next(((d,i) for d,i in reversed(vistos) if i!=r["id_compra"]),None)
            if anterior:
                r.update(r3_recorrencia=1,data_anterior=anterior[0].isoformat(),compra_anterior=anterior[1])
        # Nenhuma observação do mesmo dia pode ser evidência para outra.
        for r in linhas:
            k=(r["codigo_uasg"],r["catmat"],r["fornecedor"])
            if all(k) and r["id_compra"] and r["status"] not in ("Chave duplicada","Chave ausente"):
                historico[k].append((dia_data,r["id_compra"]))


def pontuar(teste, modelos, compras_treino):
    for r in teste:
        m=modelos.get(coorte(r),{})
        r.update(n_historico=m.get("n",""),r1_preco=0,r2_lote=int(r["quantidade"]==1 and bool(r["expressao_lote"])),
                 motivos="",prioridade="Pendente",posicao="",valida_teste=0,
                 url_fonte=url_codigo(r["catmat"],compra=r["id_compra"]))
        if r["status"]=="Elegível":
            r["status"]="Comparável" if m.get("habilitado") else "Histórico insuficiente"
        if r["status"]=="Comparável":
            f=faixa(r["quantidade"],m["cortes_volume"])
            ajuste=next(v for v in m["faixas"] if v["faixa"]==f)
            pred=ajuste["referencia"]
            delta=r["preco_unitario"]-pred
            r.update(faixa_volume=f,referencia=pred,baseline=m["baseline"],limite_superior=m["limite_superior"],
                     desvio_unitario=delta,desvio_pct=100*delta/pred,diferenca_total=r["quantidade"]*delta,
                     erro_modelo=abs(delta),erro_baseline=abs(r["preco_unitario"]-m["baseline"]),
                     fallback_volume=int(ajuste["fallback"]),r1_preco=int(r["preco_unitario"]>m["limite_superior"]),
                     valida_teste=int(r["id_compra"] not in compras_treino))
        motivos=[sigla for sigla,campo in (("R1","r1_preco"),("R2","r2_lote"),("R3","r3_recorrencia")) if r[campo]]
        r["motivos"]=" + ".join(motivos)
        r["n_sinais"]=len(motivos)
        if r["status"]=="Comparável":
            r["prioridade"]=("Alta" if len(motivos)>=2 else "Média" if r["r1_preco"] else
                             "Contextual" if motivos else "Sem sinal")
    nivel={"Alta":0,"Média":1,"Contextual":2}
    fila=sorted((r for r in teste if r["prioridade"] in nivel),key=lambda r:(
        nivel[r["prioridade"]],-r["n_sinais"],-max(D(0),r["diferenca_total"]),-r["r1_preco"],
        r["data_resultado"],r["catmat"],r["id_compra_item"],r["fornecedor"]))
    for pos,r in enumerate(fila,1):
        r["posicao"]=pos
    return fila


def csv_saida(destino,campos,registros):
    def formatar(valor):
        if isinstance(valor,D):
            return format(valor,"f").replace(".",",")
        return valor
    with destino.open("w",encoding="utf-8-sig",newline="") as arq:
        writer=csv.writer(arq,delimiter=";")
        writer.writerow(campos)
        for r in registros:
            writer.writerow([formatar(r.get(c,"")) for c in campos])


def metricas(g):
    if not g:
        return {"n":0}
    mae=mean(r["erro_modelo"] for r in g); mae_b=mean(r["erro_baseline"] for r in g)
    return {"n":len(g),"mae_modelo":mae,"mae_baseline":mae_b,
            "medae_modelo":median(r["erro_modelo"] for r in g),"medae_baseline":median(r["erro_baseline"] for r in g),
            "medape_modelo_pct":median(100*r["erro_modelo"]/r["preco_unitario"] for r in g),
            "medape_baseline_pct":median(100*r["erro_baseline"]/r["preco_unitario"] for r in g),
            "melhora_mae_pct":100*(1-mae/mae_b) if mae_b else None}


def executar(config,fonte,destino):
    regs,man=carregar(fonte,config)
    duplicados={k for k,v in Counter(chave(r) for r in regs).items() if v>1}
    for r in regs:
        r["status"]=status_inicial(r,duplicados)
    recorrencias(regs,config["janela_recorrencia_dias"])
    treino=[r for r in regs if r["data_resultado"][:4]=="2024"]
    teste=[r for r in regs if r["data_resultado"][:4]=="2025"]
    m24,m25=ajustar(treino,config),ajustar(teste,config)
    compras24={r["id_compra"] for r in treino if r["status"]=="Elegível" and m24[coorte(r)]["habilitado"]}
    nf=sum(r["status"]=="Elegível" and m24[coorte(r)]["habilitado"] for r in treino)
    fila=pontuar(teste,m24,compras24)
    val=[r for r in teste if r["valida_teste"]]
    comparaveis=[r for r in teste if r["status"]=="Comparável"]
    resumo={"coleta_utc":man["coleta_utc"],"n_materiais":len(config["materiais"]),
            "n_familias":len({m["familia"] for m in config["materiais"]}),
            "n_paginas":len(man["paginas"]),"n_origem":sum(x["n_original"] for x in man["paginas"]),
            "universo_2024":len(treino),"treino_com_suporte":nf,"universo_2025":len(teste),
            "comparaveis_2025":len(comparaveis),"pendentes_2025":len(teste)-len(comparaveis),
            "n_ufs":len({r["uf"] for r in teste if r["uf"]}),"fila_n":len(fila),
            "coortes_configuradas":len(m24),"coortes_com_suporte":sum(m["habilitado"] for m in m24.values()),
            "compras_na_fila":len({r["id_compra"] for r in fila}),
            "compras_sobrepostas_teste":len(compras24&{r["id_compra"] for r in comparaveis}),
            "n_excluidos_teste_sobreposicao":len(comparaveis)-len(val),
            "status":dict(Counter(r["status"] for r in teste)),
            "prioridades":dict(Counter(r["prioridade"] for r in teste)),
            "regras_na_fila":{sigla:sum(r[k] for r in fila) for sigla,k in (("R1","r1_preco"),("R2","r2_lote"),("R3","r3_recorrencia"))},
            "top20":{"n":len(fila[:20]),"materiais":len({r["catmat"] for r in fila[:20]}),
                     "compras":len({r["id_compra"] for r in fila[:20]}),
                     "alta":sum(r["prioridade"]=="Alta" for r in fila[:20])}}
    por_material=[]
    for m in config["materiais"]:
        g=[r for r in teste if r["catmat"]==m["catmat"]]
        por_material.append({**{k:m[k] for k in ("catmat","material","familia")}, "universo":len(g),
                            "comparaveis":sum(r["status"]=="Comparável" for r in g),
                            "fila":sum(bool(r["posicao"]) for r in g),"avaliacao":metricas([r for r in g if r["valida_teste"]])})
    cenario_modelo=m25[("451819","Unidade")] if ("451819","Unidade") in m25 else next(iter(m25.values()))
    cenario={}
    if cenario_modelo["habilitado"]:
        quantidade=30
        f=faixa(quantidade,cenario_modelo["cortes_volume"])
        v=next(x["referencia"] for x in cenario_modelo["faixas"] if x["faixa"]==f)
        cenario={"data_simulada":"2026-01-01","treino_ano":2025,"catmat":cenario_modelo["catmat"],
                 "material":cenario_modelo["material"],"apresentacao":cenario_modelo["apresentacao"],
                 "quantidade":quantidade,"faixa_volume":f,"referencia":v,"total":quantidade*v}
    csv_saida(destino/"treino_2024.csv",BASE+["status","expressao_lote"],treino)
    csv_saida(destino/"triagem_2025.csv",BASE+ADICIONAIS,teste)
    csv_saida(destino/"fila_2025.csv",BASE+ADICIONAIS,fila)
    csv_saida(destino/"pendencias_2025.csv",BASE+ADICIONAIS,[r for r in teste if r["status"]!="Comparável"])
    dump(destino/"resultados.json",{"resumo":resumo,"avaliacao":metricas(val),"por_material":por_material,
                                   "modelos_2024":list(m24.values()),"modelos_2025":list(m25.values()),"cenario":cenario})
    nomes=["treino_2024.csv","triagem_2025.csv","fila_2025.csv","pendencias_2025.csv","resultados.json"]
    dump(destino/"hashes.json",{n:hash_bytes((destino/n).read_bytes()) for n in nomes})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--online",action="store_true",help="Consulta a fonte oficial e congela a projeção pública.")
    parser.add_argument("--saida",type=Path,default=RAIZ/"dados")
    parser.add_argument("--config",type=Path,default=RAIZ/"config"/"materiais.json")
    args=parser.parse_args()
    destino=args.saida.resolve()
    destino.mkdir(exist_ok=True,parents=True)
    if args.online and any(destino.iterdir()):
        parser.error("Use --saida com uma pasta vazia para uma nova coleta.")
    cfg=json.loads(args.config.read_text(encoding="utf-8-sig"))
    with tempfile.TemporaryDirectory(prefix="processando_",dir=destino) as caminho:
        stage=Path(caminho)
        fonte=RAIZ/"dados"/"fonte"
        if args.online:
            fonte=stage/"fonte"
            congelar(fonte,cfg,ler_online,datetime.now(timezone.utc).isoformat())
        executar(cfg,fonte,stage)
        for p in stage.iterdir():
            p.replace(destino/p.name)
    print(destino/"resultados.json")


if __name__=="__main__":
    main()

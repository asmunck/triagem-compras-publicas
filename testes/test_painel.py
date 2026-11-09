"""Testes offline do painel e do notebook. Execute python testes/test_painel.py."""
import csv
import json
import re
import unittest
from html import unescape
from pathlib import Path
from statistics import mean


PROJETO = Path(__file__).resolve().parents[1]


class PainelCompras(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (PROJETO / "index.html").read_text(encoding="utf-8")
        bloco = re.search(r'<script type="application/json" id="dados">(.*?)</script>',
                          cls.html, flags=re.S)
        cls.dados = json.loads(bloco.group(1))
        cls.rows = cls.dados["rows"]
        with (PROJETO / "dados" / "triagem_2025.csv").open(encoding="utf-8-sig", newline="") as f:
            cls.csv = list(csv.DictReader(f, delimiter=";"))

    def test_cobertura_e_fila(self):
        self.assertEqual(len(self.rows), len(self.csv))
        self.assertEqual({(r["cod"], r["item"], r["forn"]) for r in self.rows},
                         {(r["catmat"], r["id_compra_item"], r["fornecedor"]) for r in self.csv})
        fila = [r for r in self.rows if r["flag"]]
        self.assertEqual(len(fila), sum(bool(r["posicao"]) for r in self.csv))
        self.assertEqual(len({r["compra"] for r in fila}), 235)
        self.assertEqual(sum(r["pri"] == "Alta" for r in fila), 7)
        self.assertTrue(all(r["rules"] and r["status"] == "Comparável" for r in fila))

    def test_recorte_documental(self):
        recorte = [r for r in self.rows if r["fam"] == "Saúde" and r["cod"] == "267778"
                   and r["uf"] == "RJ" and r["esf"] == "F" and "farmacológico" in r["obj"].lower()]
        fila = [r for r in recorte if r["flag"]]
        self.assertEqual(len(fila), 1)
        caso = fila[0]
        self.assertEqual((caso["item"], caso["rules"]), ("1603320600054202500043", ["R1"]))
        self.assertAlmostEqual(caso["impact"], max(0, caso["p"]-caso["ref"]) * caso["q"])
        self.assertIn(caso["compra"], caso["fonte"])

    def test_validacao_temporal(self):
        resultado = json.loads((PROJETO / "dados" / "resultados.json").read_text(encoding="utf-8"))
        validos = [r for r in self.rows if r["eval"]]
        self.assertEqual(len(validos), resultado["avaliacao"]["n"])
        self.assertAlmostEqual(mean(abs(r["p"]-r["ref"]) for r in validos), resultado["avaliacao"]["mae_modelo"])
        self.assertAlmostEqual(mean(abs(r["p"]-r["base"]) for r in validos), resultado["avaliacao"]["mae_baseline"])

    def test_notebook_executado_e_sincronizado(self):
        nb = json.loads((PROJETO / "analise_compras.ipynb").read_text(encoding="utf-8"))
        code = [c for c in nb["cells"] if c["cell_type"] == "code"]
        self.assertTrue(all(c["execution_count"] is not None for c in code))
        outputs = [o for c in code for o in c["outputs"]]
        self.assertFalse(any(o["output_type"] == "error" for o in outputs))
        self.assertEqual(sum("image/png" in o.get("data", {}) for o in outputs), 3)
        iframe = "".join(code[-1]["outputs"][-1]["data"]["text/html"])
        self.assertIn(self.html, unescape(iframe))

    def test_valores_monetarios_em_texto_literal_no_colab(self):
        nb = json.loads((PROJETO / "analise_compras.ipynb").read_text(encoding="utf-8"))
        saidas = [o for c in nb["cells"] for o in c.get("outputs", [])]
        for saida in saidas:
            markdown = "".join(saida.get("data", {}).get("text/markdown", []))
            self.assertNotIn("R$", markdown, "O Colab pode interpretar dois cifrões como fórmula.")
        texto = "\n".join("".join(o["text"]) for o in saidas if o["output_type"] == "stream")
        self.assertIn("MAE do modelo · R$ 94,41", texto)
        self.assertIn("MAE da referência · R$ 94,54", texto)
        self.assertIn("Erro percentual absoluto mediano · 17,93%", texto)
        self.assertIn("R$ 25,52 por unidade · R$ 765,60 para o lote", texto)


if __name__ == "__main__":
    unittest.main()

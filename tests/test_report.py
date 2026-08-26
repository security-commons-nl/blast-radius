import json
from pathlib import Path

from blastradius.analysis import analyze
from blastradius.cli import main
from blastradius.models import Edge, Landschap, Node
from blastradius.parsers import load
from blastradius.report import render

TESTDATA = Path(__file__).resolve().parent.parent / "testdata"


def _html():
    return render(analyze(load(TESTDATA / "landschap.json")), "testdata/landschap.json")


def test_rapport_is_self_contained():
    html = _html()
    assert html.startswith("<!doctype html>")
    # eigen inline script is toegestaan; externe bronnen niet
    for verboden in ("http://", "https://", "src=", "@import", "<img", ".woff"):
        assert verboden not in html


def test_rapport_bevat_graaf_en_data():
    html = _html()
    assert '<svg id="graph"' in html
    assert "var DATA =" in html
    assert "ci-netwerk" in html
    # elke node krijgt een klikbaar element
    assert 'data-id="ci-netwerk"' in html


def test_rapport_bevat_ranglijst_en_print():
    html = _html()
    assert "Grootste blast radius" in html
    assert "@media print" in html
    assert "Methode en grenzen" in html


def test_embedded_data_is_geldige_json():
    html = _html()
    start = html.index("var DATA =") + len("var DATA =")
    end = html.index(";\n", start)
    data = json.loads(html[start:end].strip())
    assert "edges" in data and "impacts" in data
    assert data["impacts"]["ci-netwerk"]["geraakt"]
    assert data["types"]["proc-paspoort"] == "proces"


def _embedded_data(html):
    start = html.index("var DATA =") + len("var DATA =")
    end = html.index(";\n", start)
    return json.loads(html[start:end].strip())


def test_downward_closure_uit_embedded_data_klopt():
    # Bewaakt de regressie waarbij een klik op een proces niets highlightte:
    # de reverse-closure over de embedded edges moet de dependencies opleveren.
    data = _embedded_data(_html())
    steunt_op = {}
    for e in data["edges"]:
        steunt_op.setdefault(e["t"], []).append(e["f"])

    seen, stack = set(), list(steunt_op.get("proc-paspoort", []))
    while stack:
        n = stack.pop()
        if n == "proc-paspoort" or n in seen:
            continue
        seen.add(n)
        stack.extend(steunt_op.get(n, []))

    assert seen == {
        "app-brp", "app-zaak", "ci-db-brp", "ci-app-zaak",
        "ci-db-zaak", "ci-auth", "ci-netwerk",
    }


def test_selectdown_gebruikt_de_reverse_map():
    # Directe guard tegen terugvallen op de dode 'down'-map.
    html = _html()
    assert "closure(id, steuntOp)" in html
    assert "closure(id, down)" not in html


def test_markset_wist_vorige_selectie():
    # Regressie (bevestigd in de browser): zonder wissen stapelen opeenvolgende
    # kliks hun highlight op. markSet moet eerst hit/source verwijderen.
    html = _html()
    marker = html.index("function markSet(")
    body = html[marker:marker + 400]
    assert "remove('hit','source')" in body


def test_rapport_escapet_labels():
    land = Landschap(
        nodes=[Node("x", "<script>alert(1)</script>", "ci"), Node("p", "Proc & co", "proces")],
        edges=[Edge("x", "p")],
    )
    html = render(analyze(land), "bron")
    assert "<script>alert(1)</script>" not in html.split("var DATA")[0]
    assert "&lt;script&gt;" in html or "\\u003cscript" in html
    assert "Proc &amp; co" in html


def test_waarschuwing_verschijnt_in_rapport():
    land = Landschap(nodes=[Node("a", "A", "ci")], edges=[Edge("a", "spook")])
    html = render(analyze(land), "bron")
    assert "Let op bij de invoer" in html
    assert "spook" in html


def test_cli_schrijft_rapport_en_json(tmp_path, capsys):
    out = tmp_path / "sub" / "rapport.html"
    js = tmp_path / "sub" / "analyse.json"
    code = main([str(TESTDATA / "landschap.json"), "--out", str(out), "--json", str(js)])

    assert code == 0
    assert out.is_file() and js.is_file()
    data = json.loads(js.read_text(encoding="utf-8"))
    assert "impacts" in data and "layout" in data

    uit = capsys.readouterr().out
    assert "grootste blast radius: netwerk-core" in uit


def test_cli_leest_csv(tmp_path):
    out = tmp_path / "r.html"
    assert main([str(TESTDATA / "landschap.csv"), "--out", str(out)]) == 0
    assert "blast radius" in out.read_text(encoding="utf-8").lower()


def test_cli_meldt_ontbrekend_bestand(tmp_path, capsys):
    assert main([str(tmp_path / "bestaatniet.json"), "--out", str(tmp_path / "r.html")]) == 2
    assert "niet gevonden" in capsys.readouterr().err


def test_ai_zonder_sleutel_slaat_over(monkeypatch):
    from blastradius import ai

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    tekst, melding = ai.summarize(analyze(load(TESTDATA / "landschap.json")))
    assert tekst == ""
    assert "ANTHROPIC_API_KEY" in melding

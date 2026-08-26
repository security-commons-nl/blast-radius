from pathlib import Path

from blastradius.analysis import analyze, ranglijst, single_points
from blastradius.models import Edge, Landschap, Node
from blastradius.parsers import load

TESTDATA = Path(__file__).resolve().parent.parent / "testdata"


def _land(nodes, edges):
    return Landschap(
        nodes=[Node(*n) if isinstance(n, tuple) else n for n in nodes],
        edges=[Edge(*e) if isinstance(e, tuple) else e for e in edges],
    )


def test_blast_radius_is_transitief():
    # ci -> app -> proc: uitval van ci raakt app en proc
    land = _land(
        [("ci", "CI", "ci"), ("app", "App", "app"), ("proc", "Proc", "proces")],
        [("ci", "app"), ("app", "proc")],
    )
    a = analyze(land)
    assert set(a.impacts["ci"].geraakt) == {"app", "proc"}
    assert a.impacts["ci"].processen == ["proc"]
    assert set(a.impacts["app"].geraakt) == {"proc"}
    assert a.impacts["proc"].geraakt == []


def test_kritieke_processen_worden_geteld():
    land = _land(
        [("ci", "CI", "ci"), ("p1", "P1", "proces", True), ("p2", "P2", "proces", False)],
        [("ci", "p1"), ("ci", "p2")],
    )
    imp = analyze(land).impacts["ci"]
    assert imp.processen == ["p1", "p2"]
    assert imp.kritieke_processen == ["p1"]


def test_gedeelde_onderlaag_heeft_grootste_radius():
    land = load(TESTDATA / "landschap.json")
    a = analyze(land)
    top_id, top_imp = ranglijst(a)[0]
    # netwerk-core hangt onder alles, dus grootste blast radius
    assert top_id == "ci-netwerk"
    # raakt alle andere 13 nodes
    assert len(top_imp.geraakt) == 13
    assert set(top_imp.kritieke_processen) == {"proc-paspoort", "proc-uitkering"}


def test_ranglijst_sluit_processen_uit():
    a = analyze(load(TESTDATA / "landschap.json"))
    ids = [nid for nid, _ in ranglijst(a)]
    assert all(a.landschap.node(nid).type != "proces" for nid in ids)


def test_ranglijst_sorteert_op_kritiek_dan_omvang():
    a = analyze(load(TESTDATA / "landschap.json"))
    rang = ranglijst(a)
    scores = [
        (len(imp.kritieke_processen), len(imp.processen), len(imp.geraakt))
        for _, imp in rang
    ]
    assert scores == sorted(scores, reverse=True)


def test_single_point_of_failure():
    # proc-uitkering wordt in de testdata gedragen door app-zaak en app-betaal: redundant
    # proc-paspoort door app-brp en app-zaak: redundant
    # maak een landschap met een kritiek proces op een enkele app
    land = _land(
        [("app", "App", "app"), ("p", "P", "proces", True)],
        [("app", "p")],
    )
    assert single_points(analyze(land)) == ["p"]


def test_geen_spof_bij_redundantie():
    land = _land(
        [("a1", "A1", "app"), ("a2", "A2", "app"), ("p", "P", "proces", True)],
        [("a1", "p"), ("a2", "p")],
    )
    assert single_points(analyze(land)) == []


def test_testdata_heeft_geen_spof_in_applicatielaag():
    # beide kritieke processen worden door twee apps gedragen
    a = analyze(load(TESTDATA / "landschap.json"))
    assert single_points(a) == []
    assert a.dubbele_dekking["proc-paspoort"] == 2
    assert a.dubbele_dekking["proc-uitkering"] == 2


def test_cyclus_wordt_gemeld_en_klapt_niet():
    land = _land(
        [("a", "A", "ci"), ("b", "B", "ci")],
        [("a", "b"), ("b", "a")],
    )
    a = analyze(land)
    assert any("Cyclus" in w for w in a.waarschuwingen)
    # closure blijft eindig
    assert set(a.impacts["a"].geraakt) == {"b"}


def test_onbekende_edge_wordt_gemeld():
    land = _land([("a", "A", "ci")], [("a", "spooknode")])
    a = analyze(land)
    assert any("spooknode" in w for w in a.waarschuwingen)


def test_edge_tegen_laagrichting_wordt_gemeld():
    # proces -> ci is tegen de richting in
    land = _land(
        [("p", "P", "proces"), ("c", "C", "ci")],
        [("p", "c")],
    )
    a = analyze(land)
    assert any("laagrichting" in w for w in a.waarschuwingen)


def test_layout_is_gelaagd_en_deterministisch():
    land = load(TESTDATA / "landschap.json")
    a1 = analyze(land)
    a2 = analyze(load(TESTDATA / "landschap.json"))
    assert a1.layout == a2.layout
    # processen bovenaan (kleinste y), ci onderaan (grootste y)
    y_proc = a1.layout["proc-paspoort"][1]
    y_ci = a1.layout["ci-netwerk"][1]
    assert y_proc < y_ci

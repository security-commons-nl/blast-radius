from pathlib import Path

import pytest

from blastradius.models import Node
from blastradius.parsers import from_csv, from_json, load

TESTDATA = Path(__file__).resolve().parent.parent / "testdata"


def test_from_json_leest_nodes_en_edges():
    land = from_json(
        '{"naam":"t","nodes":['
        '{"id":"a","label":"A","type":"ci"},'
        '{"id":"b","label":"B","type":"proces","kritiek":true}],'
        '"edges":[{"from":"a","to":"b"}]}'
    )
    assert land.naam == "t"
    assert {n.id for n in land.nodes} == {"a", "b"}
    assert land.node("b").kritiek is True
    assert land.edges[0].src == "a" and land.edges[0].dst == "b"
    assert land.edges[0].relatie == "ondersteunt"


def test_from_json_default_label_is_id():
    land = from_json('{"nodes":[{"id":"x","type":"app"}],"edges":[]}')
    assert land.node("x").label == "x"


def test_onbekend_type_geeft_fout():
    with pytest.raises(ValueError):
        Node(id="x", label="X", type="server")


def test_testdata_json_klopt():
    land = load(TESTDATA / "landschap.json")
    assert len(land.nodes) == 14
    assert len(land.edges) == 19
    assert land.node("ci-netwerk").type == "ci"
    assert land.node("proc-paspoort").kritiek is True


def test_from_csv_leidt_nodes_af():
    land = from_csv(
        "from,from_label,from_type,to,to_label,to_type,relatie\n"
        "ci1,Server 1,ci,app1,Applicatie 1,app,ondersteunt\n"
        "app1,Applicatie 1,app,proc1,Proces 1,proces,ondersteunt\n"
    )
    assert {n.id for n in land.nodes} == {"ci1", "app1", "proc1"}
    assert land.node("ci1").type == "ci"
    assert land.node("proc1").type == "proces"
    assert len(land.edges) == 2


def test_from_csv_dedupliceert_nodes():
    land = from_csv(
        "from,from_type,to,to_type\n"
        "ci1,ci,app1,app\n"
        "ci1,ci,app2,app\n"
    )
    assert sum(1 for n in land.nodes if n.id == "ci1") == 1
    assert len(land.edges) == 2


def test_from_csv_kritiek_kolom():
    land = from_csv(
        "from,from_type,to,to_type,to_kritiek\n"
        "app1,app,proc1,proces,ja\n"
    )
    assert land.node("proc1").kritiek is True


def test_from_csv_slaat_lege_regels_over():
    land = from_csv(
        "from,from_type,to,to_type\n"
        "ci1,ci,app1,app\n"
        ",,,\n"
        "ci2,ci,,app\n"
    )
    assert len(land.edges) == 1


def test_testdata_csv_klopt():
    land = load(TESTDATA / "landschap.csv")
    assert land.node("ci-netwerk").type == "ci"
    assert land.node("proc-paspoort").type == "proces"
    assert len(land.edges) == 6


def test_load_kiest_op_extensie(tmp_path):
    j = tmp_path / "x.json"
    j.write_text('{"nodes":[{"id":"a","type":"ci"}],"edges":[]}', encoding="utf-8")
    assert load(j).node("a") is not None

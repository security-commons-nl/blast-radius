"""Inlezen van een landschap uit JSON of CSV.

JSON is het primaire formaat (expliciete nodes en edges). CSV is de handige
export-variant: één regel per relatie, met de nodes eruit afgeleid.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from .models import Edge, Landschap, Node


def from_json(text: str) -> Landschap:
    data = json.loads(text)
    nodes = [
        Node(
            id=n["id"],
            label=n.get("label", n["id"]),
            type=n["type"],
            kritiek=bool(n.get("kritiek", False)),
        )
        for n in data.get("nodes", [])
    ]
    edges = [
        Edge(src=e["from"], dst=e["to"], relatie=e.get("relatie", "ondersteunt"))
        for e in data.get("edges", [])
    ]
    return Landschap(
        naam=data.get("naam", ""),
        toelichting=data.get("toelichting", ""),
        nodes=nodes,
        edges=edges,
    )


def from_csv(text: str) -> Landschap:
    """Leest een relatie-CSV. Elke regel draagt beide uiteinden van een edge.

    Verwachte kolommen: from, from_label, from_type, to, to_label, to_type, relatie.
    Labels en relatie zijn optioneel; kritiek kan mee via een kolom `from_kritiek`
    of `to_kritiek` (waarde ja/true/1).
    """
    reader = csv.DictReader(text.splitlines())
    if reader.fieldnames is None:
        return Landschap()

    nodes: dict[str, Node] = {}
    edges: list[Edge] = []

    def kritiek(row: dict, prefix: str) -> bool:
        val = (row.get(prefix + "_kritiek") or "").strip().lower()
        return val in ("ja", "true", "1", "yes")

    def upsert(node_id: str, label: str, type_: str, is_kritiek: bool) -> None:
        node_id = node_id.strip()
        if not node_id:
            return
        if node_id not in nodes:
            nodes[node_id] = Node(
                id=node_id, label=(label or node_id).strip(), type=type_.strip(), kritiek=is_kritiek
            )
        elif is_kritiek:
            nodes[node_id].kritiek = True

    for row in reader:
        src = (row.get("from") or "").strip()
        dst = (row.get("to") or "").strip()
        if not src or not dst:
            continue
        upsert(src, row.get("from_label", ""), row.get("from_type", "ci"), kritiek(row, "from"))
        upsert(dst, row.get("to_label", ""), row.get("to_type", "proces"), kritiek(row, "to"))
        edges.append(Edge(src=src, dst=dst, relatie=(row.get("relatie") or "ondersteunt").strip()))

    return Landschap(nodes=list(nodes.values()), edges=edges)


def load(path: Path) -> Landschap:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".csv":
        return from_csv(text)
    return from_json(text)

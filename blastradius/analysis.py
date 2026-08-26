"""Analyse van het landschap.

De centrale vraag: als component X uitvalt, wat valt er dan mee om, en raakt dat
een kritiek proces? Dat is de transitieve closure over de uitgaande edges. Daarnaast
berekenen we welke processen op maar een enkele applicatie steunen (geen redundantie)
en een deterministische layout voor de tekening.

Alles is afgeleid uit de graaf. Geen model, geen toeval: dezelfde invoer geeft
dezelfde uitkomst.
"""

from __future__ import annotations

from .models import Analyse, Impact, Landschap, NODE_TYPES


def _validate(landschap: Landschap) -> list[str]:
    waarschuwingen: list[str] = []
    ids = {n.id for n in landschap.nodes}

    for edge in landschap.edges:
        if edge.src not in ids:
            waarschuwingen.append(
                "Edge verwijst naar onbekende bron {!r}; overgeslagen.".format(edge.src)
            )
        if edge.dst not in ids:
            waarschuwingen.append(
                "Edge verwijst naar onbekend doel {!r}; overgeslagen.".format(edge.dst)
            )

    # Een edge hoort van een lagere naar een hogere laag te lopen (ci -> app -> proces).
    for edge in landschap.edges:
        src, dst = landschap.node(edge.src), landschap.node(edge.dst)
        if src and dst and src.laag > dst.laag:
            waarschuwingen.append(
                "Edge {} -> {} loopt van {} naar {}, tegen de laagrichting in.".format(
                    edge.src, edge.dst, src.type, dst.type
                )
            )
    return waarschuwingen


def _reachable(landschap: Landschap, start: str) -> tuple[set[str], bool]:
    """Alle nodes stroomopwaarts van start. Tweede waarde: of er een cyclus is geraakt."""
    seen: set[str] = set()
    cycle = False
    stack = list(landschap.uitgaand(start))
    while stack:
        node = stack.pop()
        if node == start:
            cycle = True
            continue
        if node in seen:
            continue
        seen.add(node)
        stack.extend(landschap.uitgaand(node))
    return seen, cycle


def _impacts(landschap: Landschap) -> tuple[dict[str, Impact], list[str]]:
    impacts: dict[str, Impact] = {}
    waarschuwingen: list[str] = []

    for node in landschap.nodes:
        geraakt, cycle = _reachable(landschap, node.id)
        if cycle:
            waarschuwingen.append(
                "Cyclus geraakt vanaf {!r}; de blast radius is berekend maar het "
                "landschap hoort acyclisch te zijn.".format(node.id)
            )
        processen = sorted(
            n.id for n in landschap.nodes if n.id in geraakt and n.type == "proces"
        )
        kritiek = sorted(
            n.id for n in landschap.nodes
            if n.id in geraakt and n.type == "proces" and n.kritiek
        )
        impacts[node.id] = Impact(
            node_id=node.id,
            geraakt=sorted(geraakt),
            processen=processen,
            kritieke_processen=kritiek,
        )
    return impacts, waarschuwingen


def _dekking(landschap: Landschap) -> dict[str, int]:
    """Per proces: hoeveel applicaties het direct dragen. 1 = geen redundantie."""
    dekking: dict[str, int] = {}
    for node in landschap.nodes:
        if node.type != "proces":
            continue
        dragers = [
            src for src in landschap.inkomend(node.id)
            if (landschap.node(src) and landschap.node(src).type == "app")
        ]
        dekking[node.id] = len(dragers)
    return dekking


def _layout(landschap: Landschap) -> dict[str, tuple[float, float]]:
    """Gelaagde layout: y per type, x gelijk verdeeld binnen de laag.

    Deterministisch (op node-vololgorde), zodat de tekening reproduceerbaar is en
    in een test te controleren valt.
    """
    per_laag: dict[int, list[str]] = {i: [] for i in range(len(NODE_TYPES))}
    for node in landschap.nodes:
        per_laag[node.laag].append(node.id)

    layout: dict[str, tuple[float, float]] = {}
    lagen = len(NODE_TYPES)
    for laag, ids in per_laag.items():
        # proces bovenaan (y klein), ci onderaan (y groot)
        y = (lagen - 1 - laag) / max(lagen - 1, 1)
        n = len(ids)
        for i, node_id in enumerate(ids):
            x = (i + 1) / (n + 1) if n else 0.5
            layout[node_id] = (round(x, 4), round(y, 4))
    return layout


def analyze(landschap: Landschap) -> Analyse:
    analyse = Analyse(landschap=landschap)
    analyse.waarschuwingen.extend(_validate(landschap))

    impacts, cyclus_waarschuwingen = _impacts(landschap)
    analyse.impacts = impacts
    analyse.waarschuwingen.extend(cyclus_waarschuwingen)

    analyse.dubbele_dekking = _dekking(landschap)
    analyse.layout = _layout(landschap)
    return analyse


def ranglijst(analyse: Analyse) -> list[tuple[str, Impact]]:
    """CI's en apps gesorteerd op blast radius: eerst kritieke processen, dan omvang."""
    rijen = [
        (nid, imp) for nid, imp in analyse.impacts.items()
        if analyse.landschap.node(nid) and analyse.landschap.node(nid).type != "proces"
    ]
    return sorted(
        rijen,
        key=lambda r: (-len(r[1].kritieke_processen), -len(r[1].processen), -len(r[1].geraakt), r[0]),
    )


def single_points(analyse: Analyse) -> list[str]:
    """Kritieke processen die op maar een enkele applicatie steunen."""
    result = []
    for proc_id, dekking in analyse.dubbele_dekking.items():
        node = analyse.landschap.node(proc_id)
        if node and node.kritiek and dekking <= 1:
            result.append(proc_id)
    return sorted(result)

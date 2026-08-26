"""Datamodel voor blastradius.

Een landschap is een gerichte graaf. Een edge from -> to betekent "from draagt to":
valt `from` uit, dan wordt `to` geraakt. De blast radius van een node is dus alles
wat je stroomopwaarts (via uitgaande edges) transitief kunt bereiken.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

# De drie lagen van onder naar boven. De volgorde bepaalt de tekening en de
# validatie: een edge hoort van een lagere of gelijke laag naar een hogere te lopen.
NODE_TYPES = ["ci", "app", "proces"]
TYPE_LABEL = {"ci": "Infrastructuur", "app": "Applicatie", "proces": "Bedrijfsproces"}


@dataclass
class Node:
    id: str
    label: str
    type: str
    kritiek: bool = False

    def __post_init__(self) -> None:
        if self.type not in NODE_TYPES:
            raise ValueError(
                "onbekend type {!r} voor node {!r}; kies uit {}".format(
                    self.type, self.id, ", ".join(NODE_TYPES)
                )
            )
        if not self.label:
            self.label = self.id

    @property
    def laag(self) -> int:
        return NODE_TYPES.index(self.type)


@dataclass
class Edge:
    src: str
    dst: str
    relatie: str = "ondersteunt"


@dataclass
class Impact:
    """De blast radius van een node: wat valt om als deze uitvalt."""

    node_id: str
    geraakt: list[str] = field(default_factory=list)          # alle stroomopwaartse nodes
    processen: list[str] = field(default_factory=list)        # daarvan de processen
    kritieke_processen: list[str] = field(default_factory=list)


@dataclass
class Landschap:
    naam: str = ""
    toelichting: str = ""
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)

    def node(self, node_id: str) -> Node | None:
        return next((n for n in self.nodes if n.id == node_id), None)

    def uitgaand(self, node_id: str) -> list[str]:
        """Nodes die dit component draagt (die omvallen als het uitvalt)."""
        return [e.dst for e in self.edges if e.src == node_id]

    def inkomend(self, node_id: str) -> list[str]:
        """Nodes waarop dit component steunt."""
        return [e.src for e in self.edges if e.dst == node_id]


@dataclass
class Analyse:
    landschap: Landschap
    impacts: dict[str, Impact] = field(default_factory=dict)
    dubbele_dekking: dict[str, int] = field(default_factory=dict)  # proces -> aantal dragende apps
    layout: dict[str, tuple[float, float]] = field(default_factory=dict)
    waarschuwingen: list[str] = field(default_factory=list)
    ai_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        # tuples in layout serialiseren als lijsten voor JSON
        data["layout"] = {k: list(v) for k, v in self.layout.items()}
        return data

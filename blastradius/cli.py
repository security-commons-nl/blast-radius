"""Commandline-ingang.

    python -m blastradius testdata/landschap.json --out rapport.html

Leest een CI-landschap (JSON of CSV), berekent per component de blast radius en
schrijft een interactief HTML-rapport. Met --ai komt er een duidingssectie bij.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .ai import summarize
from .analysis import analyze, ranglijst, single_points
from .parsers import load
from .report import render


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="blastradius",
        description=(
            "Leest een CI-landschap en toont wat er omvalt als een component uitvalt. "
            "Invoer: JSON (nodes + edges) of CSV (relaties per regel)."
        ),
    )
    parser.add_argument("bron", type=Path, help="landschapsbestand (.json of .csv)")
    parser.add_argument("--out", type=Path, default=Path("rapport.html"), help="pad voor het HTML-rapport")
    parser.add_argument("--json", dest="json_out", type=Path, default=None, help="schrijf de analyse ook als JSON weg")
    parser.add_argument("--ai", action="store_true", help="voeg een duidingssectie toe (vereist ANTHROPIC_API_KEY)")
    parser.add_argument("--model", default=None, help="model voor de duiding")
    parser.add_argument("--version", action="version", version="blastradius " + __version__)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not args.bron.is_file():
        print("fout: bestand niet gevonden: {}".format(args.bron), file=sys.stderr)
        return 2

    try:
        landschap = load(args.bron)
    except (ValueError, KeyError) as exc:
        print("fout bij inlezen: {}".format(exc), file=sys.stderr)
        return 2

    if not landschap.nodes:
        print("fout: geen componenten gevonden in {}".format(args.bron), file=sys.stderr)
        return 2

    analyse = analyze(landschap)

    if args.ai:
        text, note = summarize(analyse, args.model)
        analyse.ai_summary = text
        print("duiding: {}".format(note))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(analyse, str(args.bron)), encoding="utf-8")

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(analyse.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
        )

    top = ranglijst(analyse)
    print(
        "{} componenten, {} relaties".format(len(landschap.nodes), len(landschap.edges))
    )
    if top:
        nid, imp = top[0]
        print(
            "grootste blast radius: {} (raakt {}, {} processen)".format(
                landschap.node(nid).label, len(imp.geraakt), len(imp.processen)
            )
        )
    spofs = single_points(analyse)
    if spofs:
        print("kritieke processen zonder redundantie: {}".format(len(spofs)))
    if analyse.waarschuwingen:
        print("waarschuwingen bij de invoer: {}".format(len(analyse.waarschuwingen)))
    print("rapport: {}".format(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

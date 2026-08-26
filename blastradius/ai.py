"""Optionele duidingslaag.

De cijfers komen uit de graaf, niet uit een model. Dit onderdeel schrijft er een
leesbaar verhaal omheen voor een bestuurder. Zonder API-sleutel werkt de tool
gewoon; je mist dan deze sectie.
"""

from __future__ import annotations

import os

from .analysis import ranglijst, single_points
from .models import Analyse

DEFAULT_MODEL = "claude-sonnet-5"

SYSTEM = (
    "Je schrijft de duiding bij een blast-radius-analyse van een gemeentelijk IT-landschap, "
    "in het Nederlands, voor een bestuurder of directeur zonder technische achtergrond.\n\n"
    "Harde regels:\n"
    "- Gebruik uitsluitend de aangeleverde cijfers. Verzin geen componenten, oorzaken of kansen bij.\n"
    "- De analyse toont gevolg bij uitval, niet hoe waarschijnlijk uitval is. Suggereer geen kansen.\n"
    "- Weet je iets niet, zeg dan dat het uit deze analyse niet blijkt.\n"
    "- Schrijf drie korte alinea's, gescheiden door een lege regel: (1) welk component het grootste "
    "gevolg heeft bij uitval en wat er dan stilvalt, (2) welke kritieke processen kwetsbaar zijn, "
    "(3) wat dit betekent voor waar je continuiteitsmaatregelen als eerste op richt.\n"
    "- Zakelijk en direct. Geen opsommingstekens, geen kopjes, geen uitroeptekens."
)


def _facts(analyse: Analyse) -> str:
    land = analyse.landschap
    lines: list[str] = [
        "LANDSCHAP: {} ({} componenten, {} relaties)".format(
            land.naam or "naamloos", len(land.nodes), len(land.edges)
        ),
        "",
        "GROOTSTE BLAST RADIUS (component: raakt N componenten, M processen, K kritieke processen)",
    ]
    for nid, imp in ranglijst(analyse)[:8]:
        node = land.node(nid)
        lines.append(
            "- {}: raakt {}, {} processen, {} kritiek".format(
                node.label, len(imp.geraakt), len(imp.processen), len(imp.kritieke_processen)
            )
        )
    spofs = single_points(analyse)
    lines.append("")
    lines.append("KRITIEKE PROCESSEN ZONDER REDUNDANTIE IN DE APPLICATIELAAG")
    if spofs:
        for p in spofs:
            lines.append("- {}".format(land.node(p).label))
    else:
        lines.append("- geen")
    return "\n".join(lines)


def summarize(analyse: Analyse, model: str | None = None) -> tuple[str, str]:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return "", "geen ANTHROPIC_API_KEY gevonden, duiding overgeslagen"

    try:
        import anthropic  # noqa: PLC0415
    except ImportError:
        return "", "pakket anthropic niet geinstalleerd, duiding overgeslagen"

    if not analyse.impacts:
        return "", "geen componenten om te duiden"

    client = anthropic.Anthropic(api_key=api_key)
    try:
        message = client.messages.create(
            model=model or os.environ.get("BLASTRADIUS_MODEL", DEFAULT_MODEL),
            max_tokens=900,
            system=SYSTEM,
            messages=[{"role": "user", "content": _facts(analyse)}],
        )
    except Exception as exc:
        return "", "duiding mislukt: {}".format(exc)

    text = "".join(block.text for block in message.content if block.type == "text")
    return text.strip(), "duiding toegevoegd"

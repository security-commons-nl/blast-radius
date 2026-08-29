# blast-radius

Wat valt er om als dit uitvalt? De blast radius van je landschap, uit een export die je al hebt.

Status: prototype. Werkt en is te draaien, zonder belofte over volledigheid of onderhoud.

Wat valt er om als dit uitvalt? Blast radius van je CI-landschap, uit een export die je al hebt.

Bij IT-audits en continuiteitsvraagstukken is de vraag steeds dezelfde: als deze server, database of
koppeling uitvalt, welke applicaties en welke bedrijfsprocessen vallen dan mee om? Die keten zit vaak
wel in een CMDB, maar niemand rekent hem door. Deze tool leest een landschapsexport en maakt de keten
zichtbaar, met per component de blast radius en een interactieve graaf.

Status: prototype (v0.1). Werkt, wordt getest, is geen product.

## Voor wie

CISO's, ISO's en continuiteitsverantwoordelijken.

## Snel starten

```sh
python -m blastradius testdata/landschap.json --out rapport.html
python -m blastradius landschap.csv --out rapport.html --json analyse.json --ai
```

| Optie | Doet |
|-------|------|
| `--out` | pad voor het HTML-rapport (standaard `rapport.html`) |
| `--json` | schrijft de analyse ook als JSON weg |
| `--ai` | voegt een duidingssectie toe (vereist `ANTHROPIC_API_KEY`) |
| `--model` | ander model voor de duiding (standaard `claude-sonnet-5`) |

Meteen uitproberen: `python -m blastradius testdata/landschap.json --out voorbeeld.html`.

## Bijdragen

Zie de [CONTRIBUTING](https://github.com/security-commons-nl/.github/blob/main/CONTRIBUTING.md) van de organisatie: daar staat per project een formulier, ook zonder Git-ervaring.

Open source onder de EUPL v1.2 (zie `LICENSE`). Onderdeel van Security Commons NL
(github.com/security-commons-nl): gratis, regelgebaseerde tooling waarmee publieke
organisaties zichzelf kunnen toetsen. Bevindingen komen uit controleerbare regels, niet
uit een black box; waar AI wordt ingezet (de optionele duiding) staat dat er duidelijk bij.

Meedenken, een bevinding delen of voortbouwen: open een issue of een pull request.

## Licentie

EUPL-1.2, zie [LICENSE](LICENSE).

## Uitgangspunten
1. Deterministisch. De blast radius is de transitieve keten omhoog door de graaf. Dezelfde invoer
   geeft dezelfde uitkomst, elke keer.
2. AI doet de duiding, niet de cijfers. Met `--ai` komt er een sectie bij die het verhaal voor een
   bestuurder vertelt. Zonder API-sleutel werkt alles, je mist alleen die sectie.
3. Self-contained rapport. Een HTML-bestand met een interactieve graaf, zonder externe scripts of
   fonts. Klik een component en zie wat er omvalt; klik een proces en zie waar het op steunt.

## Model
Een landschap is een gerichte graaf met drie lagen:

- `ci` - infrastructuur (servers, databases, netwerk, koppelingen)
- `app` - applicaties
- `proces` - bedrijfsprocessen

Een relatie `from -> to` betekent "from draagt to": valt `from` uit, dan wordt `to` geraakt. Edges
lopen dus van onder (ci) naar boven (proces). De blast radius van een component is alles wat je
stroomopwaarts transitief kunt bereiken.

## Invoer
Twee formaten. JSON is het primaire:

```json
{
  "naam": "Mijn landschap",
  "nodes": [
    {"id": "ci-db", "label": "db01", "type": "ci"},
    {"id": "app-x", "label": "Applicatie X", "type": "app"},
    {"id": "proc-y", "label": "Proces Y", "type": "proces", "kritiek": true}
  ],
  "edges": [
    {"from": "ci-db", "to": "app-x"},
    {"from": "app-x", "to": "proc-y"}
  ]
}
```

CSV is de export-variant: een regel per relatie, de nodes worden eruit afgeleid. Kolommen:
`from, from_label, from_type, to, to_label, to_type, relatie`. Kritiek kan mee via `from_kritiek` of
`to_kritiek` (waarde ja, true of 1).

## Wat de tool laat zien
1. **Interactieve graaf.** Gelaagd (processen boven, infrastructuur onder). Klik een component om de
   blast radius omhoog te highlighten, klik een proces om de keten eronder te zien.
2. **Ranglijst blast radius.** Componenten gesorteerd op geraakte kritieke processen, dan op omvang.
   Het component dat overal onder hangt komt bovenaan.
3. **Kwetsbare processen.** Kritieke processen die op een enkele applicatie steunen, zonder
   redundantie.

## Wat de tool niet doet
- Geen kans of frequentie. De analyse toont het gevolg bij uitval, niet hoe waarschijnlijk die uitval
  is.
- Redundantie wordt alleen in de applicatielaag geteld, niet in de gedeelde infrastructuur eronder.
  Een component dat overal onder hangt zie je wel in de ranglijst.
- De uitkomst is zo goed als de relaties in de bron. Ontbrekende koppelingen geven een onvolledig
  beeld; foute koppelingen (tegen de laagrichting in, of naar onbekende nodes) komen als
  waarschuwing terug.

## Ontwikkelen
```sh
pip install -r requirements-dev.txt
python -m pytest tests -q
```

35 tests over parsers, analyse en rapport, inclusief een regressietest op de klik-op-proces-keten.

## Opbouw
```
blastradius/
  models.py     datamodel, serialiseerbaar naar JSON
  parsers.py    JSON en CSV naar een landschap
  analysis.py   blast radius, kwetsbaarheid, layout
  report.py     interactief HTML-rapport
  ai.py         optionele duiding
  cli.py        commandline
testdata/       een verzonnen gemeentelijk landschap (json en csv)
tests/          pytest
```

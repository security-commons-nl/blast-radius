# Bijdragen

Dit project hoort bij [security-commons-nl](https://github.com/security-commons-nl). De
organisatiebrede regels staan in
[CONTRIBUTING.md](https://github.com/security-commons-nl/.github/blob/main/CONTRIBUTING.md) en het
[redactiestatuut](https://github.com/security-commons-nl/.github/blob/main/REDACTIESTATUUT.md).

## Wat helpt

- **Een bevinding die niet klopt.** Meld een vals-positief of een gemiste zaak met de invoer erbij
  (geanonimiseerd), zodat we er een test van kunnen maken.
- **Een ontbrekend geval.** Een configuratievorm of exportformaat dat we nog niet lezen.
- **Documentatie.** Een zin die je twee keer moest lezen, is een bug.

Een [issue](../../issues/new/choose) of
[discussion](https://github.com/security-commons-nl/.github/discussions) is een volwaardige
bijdrage. "Maak maar een pull request" is nooit het antwoord.

## Voor wie een pull request doet

- Nederlands in code-commentaar, documentatie en commitboodschappen.
- Eén onderwerp per commit, met de map als prefix.
- Geen persoonsnamen, organisatienamen of e-mailadressen in code, tests of documentatie
  (redactiestatuut A1 tot en met A3). Gebruik fictieve namen in fixtures.
- Nieuwe regels of parsers komen met een test erbij. `pytest tests/ -v` moet groen zijn.

## Gedeelde conventies met iamscan

blast-radius en [iamscan](https://github.com/security-commons-nl/iamscan) zijn op hetzelfde skelet
gebouwd. De code is bewust niet gedeeld; de afspraken wel. Wie aan een van beide werkt, houdt zich
aan deze punten, zodat de tools voor gebruikers hetzelfde aanvoelen.

**Afspraken**

- **CLI-flags.** Beide tools kennen dezelfde kern: een verplicht bronargument, `--out` (pad voor het
  HTML-rapport, standaard `rapport.html`), `--json` (ruwe uitkomst als JSON ernaast), `--ai`
  (duidingssectie, vereist `ANTHROPIC_API_KEY`), `--model` en `--version`. Toolspecifieke flags
  (zoals `--fail-on` in iamscan) mogen erbij, maar de kern verandert niet zonder dat beide repo's
  meegaan.
- **AI doet de duiding, niet de cijfers.** Elk cijfer, elke bevinding en elke ranglijst komt uit de
  Python-analyse. Het taalmodel krijgt alleen die feiten aangeleverd en schrijft er drie alinea's
  omheen. Zonder API-sleutel of zonder het pakket `anthropic` werkt de tool gewoon; alleen de
  duidingssectie ontbreekt dan. Een mislukte aanroep laat de run nooit klappen. De duiding staat
  in het rapport altijd met de melding dat de cijfers niet uit het model komen.
- **Self-contained HTML.** Het rapport is een enkel bestand zonder externe fonts, stylesheets,
  scripts of afbeeldingen. Het gebruikt een systeem-fontstack, dezelfde kleurvariabelen (`--bg`,
  `--panel`, `--line`, `--text`, `--muted`, `--accent`), dezelfde tabelstijl en een
  `@media print`-blok voor A4. Elk rapport eindigt met een voettekst "Methode en grenzen" die
  eerlijk zegt wat de tool niet ziet. De test `test_rapport_is_self_contained` bewaakt dit.

**Waarom de code niet gedeeld is**

Een vergelijking (28-08-2026) gaf per bestand: `ai.py` circa 45 procent gelijke regels, `cli.py`
circa 45 procent, `report.py` circa 10 procent; van de CSS-regels is een vijfde identiek. Wat
overeenkomt is het skelet (foutafhandeling rond de API-aanroep, de volgorde van de CLI-stappen,
de kleurvariabelen en de tabelstijl). Wat verschilt is precies de inhoud: de systeemprompt, de
feitenopbouw voor het model, de rapportsecties en de printlayout (liggend voor de graaf, staand
voor de bevindingen). Een gedeelde module zou dus vooral parameters en haakjes delen, en daarvoor
een extra repo of pip-afhankelijkheid vragen die de installatie van twee kleine tools zwaarder
maakt. Zolang beide tools elk onder de honderd regels `ai.py` en `cli.py` blijven, wegen de
afspraken hierboven zwaarder dan gedeelde code. Groeit de overlap tot boven de 80 procent, dan is
een gedeeld bestand met een hash-test het eerste dat we proberen.

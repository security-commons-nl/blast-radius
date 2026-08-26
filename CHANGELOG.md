# Changelog

Alle noemenswaardige wijzigingen aan blast-radius. Nieuwste bovenaan. Volgt losjes
[Keep a Changelog](https://keepachangelog.com/); versies volgen semver.

## [0.1.0] - 2026-08-26

Eerste publieke versie.

### Toegevoegd
- Inlezen van een CI-landschap uit JSON (expliciete nodes en edges) of CSV (relatie per regel,
  nodes eruit afgeleid).
- Transitieve blast radius per component: wat valt er mee om als dit uitvalt, tot aan de
  bedrijfsprocessen, met markering van kritieke processen.
- Kroonjuwelen-ranglijst (componenten op geraakte kritieke processen en omvang) en detectie van
  kritieke processen die op een enkele applicatie steunen (single point of failure).
- Validatie van de invoer: onbekende of tegen de laagrichting in lopende edges en cycli worden
  gemeld in plaats van stil fout te gaan.
- Interactief, self-contained HTML-rapport (geen externe fonts of scripts, print naar A4) met een
  gelaagde graaf: klik een component en zie wat omvalt, klik een proces en zie waar het op steunt.
- Optionele AI-duiding achter `--ai` (vereist `ANTHROPIC_API_KEY`); de cijfers komen altijd uit
  de graaf, niet uit het model.
- `--json`-export en 35 tests over parsers, analyse en rapport, inclusief een regressietest op de
  klik-op-proces-keten.

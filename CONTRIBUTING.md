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

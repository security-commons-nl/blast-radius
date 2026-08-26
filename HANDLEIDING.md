# blastradius - Handleiding

Wat valt er om als dit uitvalt? De blast radius van je CI-landschap, uit een export die je al hebt.

Dit is de gebruikershandleiding. Voor de opbouw van de code en de testopzet: zie `README.md`. De
leesbare versie van dit bestand is `handleiding.html` (self-contained, print naar A4).

## Wat het doet

Als een server, database of koppeling uitvalt, welke applicaties en bedrijfsprocessen vallen dan mee
om? Die keten zit vaak wel in een CMDB, maar niemand rekent hem door. blastradius leest een
landschapsexport en maakt de keten zichtbaar: een interactieve graaf, per component de blast radius,
en de kritieke processen die op een enkele applicatie steunen.

Deterministisch: de blast radius is de transitieve keten omhoog door de graaf. Dezelfde invoer geeft
dezelfde uitkomst. De optionele AI-duiding komt er los bovenop.

## Het model

Een landschap is een graaf met drie lagen. Een relatie `from -> to` betekent "from draagt to": valt
`from` uit, dan wordt `to` geraakt.

1. Infrastructuur (`ci`): server, database, netwerk, DigiD-koppeling.
2. Applicatie (`app`): zaaksysteem, betaalengine, BRP.
3. Proces (`proces`): paspoortuitgifte, uitkeringen. Markeer kritieke processen met `kritiek`.

Edges lopen van onder (ci) naar boven (proces). De blast radius van een component is alles wat je van
daaruit stroomopwaarts kunt bereiken.

## In 2 stappen

```sh
# 1 - exporteer je landschap naar JSON of CSV
# 2 - analyseer
python -m blastradius landschap.json --out rapport.html
```

Meteen uitproberen: `python -m blastradius testdata/landschap.json --out voorbeeld.html`.

## Invoer: JSON

```json
{
  "naam": "Mijn landschap",
  "nodes": [
    {"id": "ci-db",  "label": "db01",         "type": "ci"},
    {"id": "app-x",  "label": "Applicatie X", "type": "app"},
    {"id": "proc-y", "label": "Proces Y",     "type": "proces", "kritiek": true}
  ],
  "edges": [
    {"from": "ci-db", "to": "app-x"},
    {"from": "app-x", "to": "proc-y"}
  ]
}
```

## Invoer: CSV uit een CMDB

Een regel per relatie, de nodes worden eruit afgeleid.

```
from,from_label,from_type,to,to_label,to_type,relatie
ci-netwerk,netwerk-core,ci,ci-db,db01,ci,ondersteunt
ci-db,db01,ci,app-x,Applicatie X,app,ondersteunt
app-x,Applicatie X,app,proc-y,Proces Y,proces,ondersteunt
```

Labels en `relatie` zijn optioneel. Kritieke processen markeer je met een kolom `to_kritiek` (waarde
ja, true of 1).

## Opties

| Optie | Doet |
|-------|------|
| `--out` | pad voor het HTML-rapport (standaard `rapport.html`) |
| `--json` | schrijft de analyse ook als JSON weg |
| `--ai` | voegt een duidingssectie toe (vereist `ANTHROPIC_API_KEY`) |
| `--model` | ander model voor de duiding (standaard `claude-sonnet-5`) |

## Het rapport lezen

Het HTML-bestand is self-contained: geen externe fonts of scripts. Opent in elke browser, print naar
A4.

1. Klik een component (server, database, applicatie). Alles wat erbovenop hangt licht op, en het
   paneel toont hoeveel componenten en welke processen stilvallen. Dat is de blast radius.
2. Klik een proces bovenin. De keten eronder licht op: alle infrastructuur en applicaties waar het op
   steunt. Zo zie je waar de kwetsbaarheid van een proces zit.

Onder de graaf staan twee tabellen: de ranglijst blast radius en de kwetsbare processen. Een component
dat bovenaan de ranglijst staat is meestal een gedeelde onderlaag (kernnetwerk, centrale
authenticatie); daar richt je continuiteitsmaatregelen als eerste op.

## AI-duiding en de API-key

De cijfers komen altijd uit de graaf, nooit uit een model. De vlag `--ai` voegt een sectie toe voor
een bestuurder. Zonder key werkt alles door.

### 1. Een API-key aanmaken

Maak een account op https://console.anthropic.com, ga naar API Keys en maak een nieuwe sleutel. Die
begint met `sk-ant-`. Kopieer hem meteen. Het model rekent per rapport af (grofweg een cent of enkele
centen per run). Behandel de key als een wachtwoord: nooit in een bestand of gedeelde map, alleen als
omgevingsvariabele.

### 2. De key als omgevingsvariabele zetten

blastradius leest de key uit `ANTHROPIC_API_KEY`.

Linux (bash):

```sh
export ANTHROPIC_API_KEY=sk-ant-...
echo 'export ANTHROPIC_API_KEY=sk-ant-...' >> ~/.bashrc
```

macOS (zsh):

```sh
export ANTHROPIC_API_KEY=sk-ant-...
echo 'export ANTHROPIC_API_KEY=sk-ant-...' >> ~/.zshrc
```

Windows (PowerShell):

```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."     # dit venster
setx ANTHROPIC_API_KEY "sk-ant-..."       # vast, nieuw venster daarna
```

### 3. Het pakket installeren

```sh
pip install anthropic   # of: pip install -r requirements.txt
```

Draai je `--ai` zonder key of zonder pakket, dan meldt de tool dat kort en maakt gewoon het rapport
zonder die sectie. Een netwerkfout of rate limit laat de analyse ook nooit klappen.

## Grenzen

1. Geen kans of frequentie. De analyse toont het gevolg bij uitval, niet hoe waarschijnlijk die is.
2. Redundantie wordt alleen in de applicatielaag geteld, niet in de gedeelde infrastructuur eronder.
3. De uitkomst is zo goed als de relaties in de bron. Foute koppelingen komen als waarschuwing terug.
```

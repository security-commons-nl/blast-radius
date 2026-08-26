"""Interactief HTML-rapport: self-contained, geen externe fonts of scripts.

De graaf wordt server-side gelegd (deterministische layout uit analysis) en als
inline SVG geschreven. De enige JavaScript is het highlighten bij een klik: klik
een component en zie wat er stroomopwaarts omvalt; klik een proces en zie waar het
op steunt. Alle cijfers in de tabellen komen uit de Python-analyse.
"""

from __future__ import annotations

import html
import json
from datetime import datetime

from .analysis import ranglijst, single_points
from .models import Analyse, TYPE_LABEL

W, H = 1040, 600
PAD_X, PAD_TOP, PAD_BOT = 90, 70, 60

CSS = """
:root {
  --bg:#0d1117; --panel:#161b22; --panel-2:#1c2129; --line:#2a3038;
  --text:#e6edf3; --muted:#8b949e; --accent:#00d4aa; --accent-dim:#00a888;
  --ci:#74c0fc; --app:#b197fc; --proces:#ffd43b; --hit:#ff6b6b; --kritiek:#ff8787;
}
*{box-sizing:border-box;}
body{margin:0;padding:0 1.25rem 4rem;background:var(--bg);color:var(--text);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  line-height:1.55;-webkit-font-smoothing:antialiased;}
.wrap{max-width:1120px;margin:0 auto;}
header{padding:2.5rem 0 1.25rem;border-bottom:1px solid var(--line);margin-bottom:1.5rem;}
h1{margin:0 0 .3rem;font-size:1.75rem;letter-spacing:-.02em;}
h1 .dot{color:var(--accent);}
h2{margin:2.5rem 0 .8rem;font-size:1.2rem;}
.sub{color:var(--muted);font-size:.9rem;margin:0;}
.lead{font-size:1.02rem;background:var(--panel);border-left:3px solid var(--accent);
  padding:.9rem 1.1rem;border-radius:0 6px 6px 0;margin:0 0 1.25rem;}
.board{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:1rem;margin:1rem 0;}
.legend{display:flex;flex-wrap:wrap;gap:1rem;font-size:.85rem;color:var(--muted);margin:.3rem 0 1rem;}
.legend span{display:inline-flex;align-items:center;gap:.4rem;}
.dot-l{width:.8rem;height:.8rem;border-radius:3px;display:inline-block;}
.hint{font-size:.85rem;color:var(--muted);margin:.4rem 0 0;}
svg{width:100%;height:auto;display:block;background:var(--panel-2);border-radius:8px;}
.edge{stroke:#39414d;stroke-width:1.5;}
.node rect{stroke:#0d1117;stroke-width:1.5;rx:7;cursor:pointer;transition:opacity .12s;}
.node text{font-size:12px;fill:#0d1117;font-weight:600;pointer-events:none;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;}
.node.t-ci rect{fill:var(--ci);} .node.t-app rect{fill:var(--app);} .node.t-proces rect{fill:var(--proces);}
.node.kritiek rect{stroke:var(--kritiek);stroke-width:3;}
svg.dimmed .node:not(.hit) rect{opacity:.18;}
svg.dimmed .node:not(.hit) text{opacity:.25;}
svg.dimmed .edge:not(.hit){opacity:.08;}
.node.hit rect{stroke:var(--hit);stroke-width:3;}
.node.source rect{stroke:#fff;stroke-width:3.5;}
.edge.hit{stroke:var(--hit);stroke-width:2.5;}
#panel{min-height:2.5rem;font-size:.92rem;}
#panel .empty{color:var(--muted);}
#panel .title{font-weight:600;margin-bottom:.35rem;}
#panel .row{margin:.15rem 0;color:var(--muted);}
#panel b{color:var(--text);} #panel .warn{color:var(--hit);}
table{width:100%;border-collapse:collapse;margin:.5rem 0 1rem;font-size:.9rem;}
th,td{text-align:left;padding:.5rem .65rem;border-bottom:1px solid var(--line);vertical-align:top;}
th{color:var(--muted);font-size:.78rem;text-transform:uppercase;letter-spacing:.05em;}
tbody tr:hover{background:var(--panel-2);}
.num{text-align:right;font-variant-numeric:tabular-nums;}
.tag{display:inline-block;font-size:.72rem;padding:.05rem .45rem;border-radius:999px;
  border:1px solid var(--line);color:var(--muted);}
.tag.k{color:var(--kritiek);border-color:var(--kritiek);}
.warns{background:var(--panel);border-left:3px solid var(--proces);border-radius:0 6px 6px 0;
  padding:.7rem 1rem;margin:1rem 0;font-size:.88rem;}
.ai{background:var(--panel);border:1px solid var(--accent-dim);border-radius:8px;padding:1rem 1.25rem;}
.ai h2{margin-top:0;}
footer{margin-top:3rem;padding-top:1.25rem;border-top:1px solid var(--line);color:var(--muted);font-size:.82rem;}
footer ul{margin:.5rem 0 0;padding-left:1.1rem;}
@media print{
  @page{size:A4 landscape;margin:14mm;}
  :root{--bg:#fff;--panel:#fff;--panel-2:#f6f8fa;--line:#d0d7de;--text:#14161a;--muted:#57606a;}
  body{padding:0;} svg.dimmed .node:not(.hit) rect{opacity:1;}
  svg.dimmed .node:not(.hit) text{opacity:1;} svg.dimmed .edge:not(.hit){opacity:1;}
  #controls,.hint{display:none;} .board,table,.ai{break-inside:avoid;}
}
"""

JS = """
(function(){
  var edges = DATA.edges, impacts = DATA.impacts, labels = DATA.labels, types = DATA.types;
  var svg = document.getElementById('graph');
  var panel = document.getElementById('panel');

  // 'steunt op': van een node terug naar wat hem draagt (omgekeerde edges).
  // Voor de andere richting (wat valt om) gebruiken we de voorberekende impacts.
  var steuntOp = {};
  edges.forEach(function(e){ (steuntOp[e.t] = steuntOp[e.t] || []); steuntOp[e.t].push(e.f); });

  function closure(start, adj){
    var seen = {}, stack = (adj[start]||[]).slice();
    while(stack.length){ var n = stack.pop(); if(n===start||seen[n])continue;
      seen[n]=true; (adj[n]||[]).forEach(function(x){stack.push(x);}); }
    return seen;
  }
  function clear(){
    svg.classList.remove('dimmed');
    [].forEach.call(svg.querySelectorAll('.hit,.source'), function(el){
      el.classList.remove('hit','source'); });
    panel.innerHTML = '<span class="empty">Klik een component om te zien wat er omvalt, of een proces om te zien waar het op steunt.</span>';
  }
  function markSet(set, sourceId){
    // eerst de vorige selectie wissen, anders stapelen opeenvolgende kliks
    [].forEach.call(svg.querySelectorAll('.hit,.source'), function(el){
      el.classList.remove('hit','source'); });
    svg.classList.add('dimmed');
    [].forEach.call(svg.querySelectorAll('.node'), function(g){
      var id = g.getAttribute('data-id');
      if(id===sourceId){ g.classList.add('hit','source'); }
      else if(set[id]){ g.classList.add('hit'); }
    });
    [].forEach.call(svg.querySelectorAll('.edge'), function(l){
      var f = l.getAttribute('data-f'), t = l.getAttribute('data-t');
      var fin = (f===sourceId||set[f]), tin = (t===sourceId||set[t]);
      if(fin && tin) l.classList.add('hit');
    });
  }
  function selectUp(id){
    var imp = impacts[id] || {geraakt:[],processen:[],kritieke_processen:[]};
    var set = {}; imp.geraakt.forEach(function(x){set[x]=true;});
    markSet(set, id);
    var procs = imp.processen.map(function(p){
      var kr = imp.kritieke_processen.indexOf(p)>=0;
      return '<span class="'+(kr?'warn':'')+'">'+esc(labels[p]||p)+(kr?' (kritiek)':'')+'</span>';
    });
    panel.innerHTML =
      '<div class="title">Valt <b>'+esc(labels[id]||id)+'</b> uit, dan raakt dat '+imp.geraakt.length+' component(en).</div>'+
      '<div class="row">Processen die stilvallen: '+(procs.length?procs.join(', '):'geen')+'</div>';
  }
  function selectDown(id){
    var set = closure(id, steuntOp);
    markSet(set, id);
    var deps = Object.keys(set).filter(function(x){return types[x]!=='proces';});
    panel.innerHTML =
      '<div class="title">Proces <b>'+esc(labels[id]||id)+'</b> steunt op '+deps.length+' onderliggende component(en).</div>'+
      '<div class="row">Valt een daarvan uit, dan raakt dat dit proces.</div>';
  }
  function esc(s){ return String(s).replace(/[&<>]/g,function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c];}); }

  [].forEach.call(svg.querySelectorAll('.node'), function(g){
    g.addEventListener('click', function(){
      var id = g.getAttribute('data-id');
      if(types[id]==='proces') selectDown(id); else selectUp(id);
    });
  });
  svg.addEventListener('click', function(e){ if(e.target===svg) clear(); });
  var reset = document.getElementById('reset');
  if(reset) reset.addEventListener('click', clear);
  clear();
})();
"""


def _e(v: object) -> str:
    return html.escape(str(v), quote=True)


def _pos(analyse: Analyse, node_id: str) -> tuple[float, float]:
    nx, ny = analyse.layout[node_id]
    x = PAD_X + nx * (W - 2 * PAD_X)
    y = PAD_TOP + ny * (H - PAD_TOP - PAD_BOT)
    return x, y


def _svg(analyse: Analyse) -> str:
    land = analyse.landschap
    parts = ['<svg id="graph" viewBox="0 0 {} {}" role="img">'.format(W, H)]

    # laag-labels links
    for t, laag_label in TYPE_LABEL.items():
        sample = next((n for n in land.nodes if n.type == t), None)
        if sample is None:
            continue
        _, y = _pos(analyse, sample.id)
        parts.append(
            '<text x="16" y="{:.0f}" fill="#8b949e" font-size="12" '
            'font-family="sans-serif">{}</text>'.format(y + 4, _e(laag_label))
        )

    for edge in land.edges:
        if land.node(edge.src) is None or land.node(edge.dst) is None:
            continue
        x1, y1 = _pos(analyse, edge.src)
        x2, y2 = _pos(analyse, edge.dst)
        parts.append(
            '<line class="edge" data-f="{}" data-t="{}" x1="{:.1f}" y1="{:.1f}" '
            'x2="{:.1f}" y2="{:.1f}"/>'.format(_e(edge.src), _e(edge.dst), x1, y1, x2, y2)
        )

    for node in land.nodes:
        x, y = _pos(analyse, node.id)
        label = node.label
        w = max(96, min(190, 9 + len(label) * 6.7))
        cls = "node t-{}{}".format(node.type, " kritiek" if node.kritiek else "")
        parts.append(
            '<g class="{cls}" data-id="{id}" transform="translate({x:.1f},{y:.1f})">'
            '<rect x="{rx:.1f}" y="-15" width="{w:.1f}" height="30" rx="7"/>'
            '<text x="0" y="4" text-anchor="middle">{label}</text></g>'.format(
                cls=cls, id=_e(node.id), x=x, y=y, rx=-w / 2, w=w, label=_e(_clip(label))
            )
        )
    parts.append("</svg>")
    return "".join(parts)


def _clip(label: str, n: int = 26) -> str:
    return label if len(label) <= n else label[: n - 1] + "…"


def _data_json(analyse: Analyse) -> str:
    land = analyse.landschap
    data = {
        "edges": [{"f": e.src, "t": e.dst} for e in land.edges],
        "impacts": {
            nid: {
                "geraakt": imp.geraakt,
                "processen": imp.processen,
                "kritieke_processen": imp.kritieke_processen,
            }
            for nid, imp in analyse.impacts.items()
        },
        "labels": {n.id: n.label for n in land.nodes},
        "types": {n.id: n.type for n in land.nodes},
    }
    return json.dumps(data, ensure_ascii=False)


def _ranglijst_tabel(analyse: Analyse) -> str:
    rows = []
    for nid, imp in ranglijst(analyse)[:12]:
        node = analyse.landschap.node(nid)
        kritiek = (
            '<span class="tag k">{}</span>'.format(len(imp.kritieke_processen))
            if imp.kritieke_processen else '<span class="tag">0</span>'
        )
        rows.append(
            "<tr><td>{label}</td><td>{type}</td><td class='num'>{geraakt}</td>"
            "<td class='num'>{proc}</td><td class='num'>{kr}</td></tr>".format(
                label=_e(node.label),
                type=_e(TYPE_LABEL[node.type]),
                geraakt=len(imp.geraakt),
                proc=len(imp.processen),
                kr=kritiek,
            )
        )
    if not rows:
        return "<p class='sub'>Geen infrastructuur of applicaties in dit landschap.</p>"
    return (
        "<table><thead><tr><th>component</th><th>laag</th>"
        "<th class='num'>raakt</th><th class='num'>processen</th>"
        "<th class='num'>kritiek</th></tr></thead><tbody>{}</tbody></table>"
    ).format("".join(rows))


def _spof_blok(analyse: Analyse) -> str:
    spofs = single_points(analyse)
    if not spofs:
        return (
            "<p class='sub'>Geen kritiek proces steunt op een enkele applicatie. "
            "Let op: dit kijkt alleen naar de applicatielaag, niet naar gedeelde infrastructuur eronder.</p>"
        )
    items = "".join(
        "<li><b>{}</b> steunt op maar een applicatie.</li>".format(
            _e(analyse.landschap.node(p).label)
        )
        for p in spofs
    )
    return (
        "<p class='sub'>Kritieke processen zonder redundantie in de applicatielaag:</p>"
        "<ul>{}</ul>".format(items)
    )


def _warns(analyse: Analyse) -> str:
    if not analyse.waarschuwingen:
        return ""
    items = "".join("<li>{}</li>".format(_e(w)) for w in analyse.waarschuwingen)
    return '<div class="warns"><strong>Let op bij de invoer</strong><ul>{}</ul></div>'.format(items)


def _ai_blok(analyse: Analyse) -> str:
    if not analyse.ai_summary:
        return ""
    paras = "".join(
        "<p>{}</p>".format(_e(p.strip())) for p in analyse.ai_summary.split("\n") if p.strip()
    )
    return (
        '<div class="ai"><h2>Duiding</h2>'
        "<p class='sub'>Geschreven door een taalmodel op basis van de cijfers hierboven. "
        "De cijfers zelf komen uit de graaf, niet uit het model.</p>{}</div>"
    ).format(paras)


def _lead(analyse: Analyse) -> str:
    land = analyse.landschap
    n_ci = sum(1 for n in land.nodes if n.type == "ci")
    n_app = sum(1 for n in land.nodes if n.type == "app")
    n_proc = sum(1 for n in land.nodes if n.type == "proces")
    top = ranglijst(analyse)
    zin = "{} infrastructuurcomponenten dragen {} applicaties en {} processen.".format(
        n_ci, n_app, n_proc
    )
    if top:
        nid, imp = top[0]
        zin += " Het component met de grootste blast radius is {}: uitval raakt {} andere component(en) en {} proces(sen).".format(
            land.node(nid).label, len(imp.geraakt), len(imp.processen)
        )
    return zin


def render(analyse: Analyse, source: str, generated: datetime | None = None) -> str:
    stamp = (generated or datetime.now()).strftime("%d-%m-%Y %H:%M")
    naam = analyse.landschap.naam or source
    script = "var DATA = {};\n{}".format(_data_json(analyse), JS)
    return (
        "<!doctype html>\n"
        '<html lang="nl"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>Blast radius {naam}</title><style>{css}</style></head><body><div class='wrap'>"
        "<header><h1>Wat valt er om als dit uitvalt<span class='dot'>.</span></h1>"
        "<p class='sub'>{naam} &middot; bron <code>{source}</code> &middot; {stamp} &middot; "
        "blastradius prototype</p></header>"
        "<p class='lead'>{lead}</p>"
        "{warns}"
        "<div class='board'>"
        "<div class='legend'>"
        "<span><i class='dot-l' style='background:#74c0fc'></i>Infrastructuur</span>"
        "<span><i class='dot-l' style='background:#b197fc'></i>Applicatie</span>"
        "<span><i class='dot-l' style='background:#ffd43b'></i>Proces</span>"
        "<span><i class='dot-l' style='background:#161b22;border:2px solid #ff8787'></i>kritiek</span>"
        "</div>"
        "{svg}"
        "<div id='controls' class='hint'>Klik een component of proces. "
        "<a href='#' id='reset' style='color:var(--accent)'>Selectie wissen</a></div>"
        "<div id='panel' class='board' style='margin-top:.8rem'></div>"
        "</div>"
        "<h2>Grootste blast radius</h2>"
        "<p class='sub'>Gesorteerd op geraakte kritieke processen, dan op omvang. "
        "'raakt' telt alle stroomopwaartse componenten; 'processen' alleen de processen.</p>"
        "{rang}"
        "<h2>Kwetsbare processen</h2>{spof}"
        "{ai}"
        "<footer><strong>Methode en grenzen.</strong><ul>"
        "<li>De blast radius is de transitieve keten omhoog: alles wat een component "
        "direct of indirect draagt.</li>"
        "<li>De analyse gebruikt de relaties zoals aangeleverd. Ontbrekende of foute "
        "koppelingen in de bron geven een onvolledig beeld; controleer de invoer.</li>"
        "<li>Kwetsbaarheid kijkt naar redundantie in de applicatielaag, niet naar "
        "gedeelde infrastructuur eronder. Een component dat overal onder hangt is in de "
        "tabel hierboven te zien.</li>"
        "<li>Geen kans of frequentie: dit toont gevolg bij uitval, niet hoe waarschijnlijk "
        "die uitval is.</li>"
        "</ul></footer>"
        "</div><script>{script}</script></body></html>"
    ).format(
        naam=_e(naam),
        css=CSS,
        source=_e(source),
        stamp=_e(stamp),
        lead=_e(_lead(analyse)),
        warns=_warns(analyse),
        svg=_svg(analyse),
        rang=_ranglijst_tabel(analyse),
        spof=_spof_blok(analyse),
        ai=_ai_blok(analyse),
        script=script,
    )

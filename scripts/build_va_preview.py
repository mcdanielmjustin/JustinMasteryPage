"""Build a self-contained visual aid preview HTML page."""
import json, pathlib, sys

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
DATA_FILE = SCRIPTS_DIR / "data" / "visual_aids_generated.json"
OUTPUT = pathlib.Path("C:/Users/mcdan/AppData/Local/Temp/va_preview.html")

vas = json.loads(DATA_FILE.read_text(encoding="utf-8"))
data_json = json.dumps(vas, ensure_ascii=False)

HTML_TOP = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Visual Aid Showcase — PassEPPP</title>
<style>
  :root {
    --bg-primary: #09090b; --bg-secondary: #0f0f11; --bg-tertiary: #18181b;
    --bg-card: #1c1c1f; --text-primary: #fafafa; --text-secondary: #a1a1aa;
    --text-muted: #71717a; --accent: #f59e0b; --accent-dim: rgba(245,158,11,0.15);
    --border: rgba(255,255,255,0.06); --border-light: rgba(255,255,255,0.1);
    --radius-sm: 8px; --radius-md: 12px; --radius-lg: 16px;
    --font-body: 'Inter', -apple-system, sans-serif;
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family: var(--font-body); background: var(--bg-primary); color: var(--text-primary); line-height:1.6; }
  .header { background: var(--bg-secondary); border-bottom: 1px solid var(--border); padding: 32px 40px; position: sticky; top:0; z-index:100; }
  .header h1 { font-size: 1.6rem; margin-bottom: 8px; }
  .header h1 span { color: #c084fc; }
  .stats-row { display:flex; gap:24px; flex-wrap:wrap; margin-bottom:16px; }
  .stat-chip { background: var(--bg-tertiary); border:1px solid var(--border); border-radius:20px; padding:4px 14px; font-size:0.82rem; color:var(--text-secondary); }
  .stat-chip b { color:#c084fc; }
  .filters { display:flex; gap:12px; flex-wrap:wrap; align-items:center; }
  .filter-label { font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted); margin-right:4px; }
  .pill { padding:6px 14px; border-radius:20px; border:1px solid var(--border-light); background:transparent;
    color:var(--text-secondary); font-size:0.82rem; cursor:pointer; transition:all 0.2s; font-family:inherit; }
  .pill:hover { border-color:rgba(192,132,252,0.3); color:var(--text-primary); }
  .pill.active { background:rgba(192,132,252,0.15); border-color:#c084fc; color:#c084fc; }
  .pill .count { font-size:0.72rem; opacity:0.7; margin-left:4px; }
  .sep { width:1px; height:24px; background:var(--border-light); margin:0 4px; }
  .grid { padding:32px 40px; display:flex; flex-direction:column; gap:28px; }
  .va-card { background:var(--bg-secondary); border:1px solid var(--border); border-radius:var(--radius-lg); overflow:hidden; transition: border-color 0.2s; }
  .va-card:hover { border-color: rgba(192,132,252,0.2); }
  .va-card-header { display:flex; justify-content:space-between; align-items:center; padding:16px 24px; border-bottom:1px solid var(--border); background: var(--bg-tertiary); flex-wrap:wrap; gap:8px; }
  .va-card-meta { display:flex; align-items:center; gap:10px; }
  .badge { padding:3px 10px; border-radius:12px; font-size:0.72rem; font-weight:600; letter-spacing:0.03em; }
  .badge-domain { background:rgba(245,158,11,0.15); color:#f59e0b; }
  .badge-layout { background:rgba(192,132,252,0.15); color:#c084fc; }
  .va-card-chapter { font-size:0.85rem; color:var(--text-secondary); }
  .va-card-anchor { font-size:0.78rem; color:var(--text-muted); }
  .ba-container { display:grid; grid-template-columns:1fr 1fr; }
  .ba-panel { padding:24px; }
  .ba-panel.before { background:var(--bg-primary); border-right:1px solid var(--border); position:relative; }
  .ba-panel.after { background:rgba(168,85,247,0.02); position:relative; }
  .ba-label { position:absolute; top:12px; right:16px; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.1em; padding:2px 8px; border-radius:8px; font-weight:600; }
  .ba-label.bl { color:#71717a; background:rgba(255,255,255,0.05); }
  .ba-label.al { color:#c084fc; background:rgba(192,132,252,0.1); }
  .bh { font-size:1.05rem; font-weight:600; color:var(--text-primary); margin-bottom:12px; padding-bottom:10px; border-bottom:1px solid var(--border); }
  .bp { color:var(--text-muted); font-size:0.88rem; font-style:italic; padding:16px; border:1px dashed var(--border-light); border-radius:8px; text-align:center; }
  .empty { text-align:center; padding:80px 40px; color:var(--text-muted); font-size:0.95rem; }

  /* Visual Aid layout CSS */
  .visual-aid { background:rgba(168,85,247,0.06); border:1px solid rgba(168,85,247,0.2); border-radius:var(--radius-md,12px); padding:28px 32px; margin:0; }
  .visual-aid-title { display:flex; align-items:center; gap:10px; font-size:1.05rem; font-weight:600; color:#c084fc; margin-bottom:22px; letter-spacing:-0.01em; }
  .visual-aid-title svg { width:20px; height:20px; flex-shrink:0; color:#c084fc; }
  .va-compare { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:14px; }
  .va-compare-col { background:var(--bg-tertiary); border:1px solid var(--border-light); border-radius:10px; padding:18px; }
  .va-compare-col:hover { border-color:rgba(192,132,252,0.25); }
  .va-compare-col h5 { font-size:0.88rem; font-weight:600; color:#c084fc; margin:0 0 12px; padding-bottom:10px; border-bottom:1px solid rgba(192,132,252,0.15); }
  .va-compare-col ul { list-style:none; padding:0; margin:0; }
  .va-compare-col li { font-size:0.82rem; color:var(--text-secondary); padding:5px 0; line-height:1.5; }
  .va-compare-col li::before { content:'\2022'; color:#c084fc; margin-right:8px; }
  .va-tree { padding:8px 0; }
  .va-tree-node { padding:12px 16px; margin:6px 0; background:var(--bg-tertiary); border-radius:8px; border-left:3px solid #c084fc; font-size:0.88rem; color:var(--text-primary); line-height:1.4; }
  .va-tree-node.va-root { background:rgba(168,85,247,0.12); font-weight:600; border-left-width:4px; font-size:0.92rem; }
  .va-tree-node-sub { font-size:0.78rem; color:var(--text-secondary); margin-top:3px; font-weight:400; }
  .va-tree-children { padding-left:22px; margin-left:10px; border-left:2px dashed rgba(168,85,247,0.3); }
  .va-matrix { display:grid; gap:1px; background:var(--border,rgba(255,255,255,0.06)); border-radius:10px; overflow:hidden; grid-template-columns:repeat(3,1fr); }
  .va-matrix-cell { background:var(--bg-tertiary); padding:12px 16px; font-size:0.82rem; color:var(--text-secondary); line-height:1.45; }
  .va-matrix-header { background:rgba(168,85,247,0.1); font-weight:600; color:#c084fc; font-size:0.82rem; text-align:center; }
  .va-matrix-label { background:var(--bg-card); font-weight:600; color:var(--text-primary); }
  .va-timeline { position:relative; padding-left:32px; margin:8px 0; }
  .va-timeline::before { content:''; position:absolute; left:9px; top:4px; bottom:4px; width:2px; background:linear-gradient(180deg,#c084fc 0%,rgba(168,85,247,0.2) 100%); }
  .va-timeline-item { position:relative; margin-bottom:18px; padding-left:10px; }
  .va-timeline-item:last-child { margin-bottom:0; }
  .va-timeline-item::before { content:''; position:absolute; left:-27px; top:6px; width:12px; height:12px; border-radius:50%; background:#c084fc; border:2px solid var(--bg-card,#1c1c1f); box-shadow:0 0 0 3px rgba(192,132,252,0.15); }
  .va-timeline-label { font-size:0.78rem; font-weight:600; color:#c084fc; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:4px; }
  .va-timeline-content { font-size:0.85rem; color:var(--text-secondary); line-height:1.55; }
  .va-cycle { display:flex; flex-wrap:wrap; justify-content:center; padding:8px; gap:0; }
  .va-cycle-step { flex:0 0 auto; width:150px; padding:16px; background:var(--bg-tertiary); border:1px solid var(--border-light); border-radius:10px; text-align:center; font-size:0.85rem; color:var(--text-primary); }
  .va-cycle-step-label { font-size:0.7rem; color:#c084fc; text-transform:uppercase; margin-bottom:4px; font-weight:600; }
  .va-cycle-arrow { display:flex; align-items:center; padding:0 6px; color:#c084fc; font-size:1.1rem; opacity:0.7; }
  .va-steps { position:relative; padding-left:40px; margin:8px 0; }
  .va-steps::before { content:''; position:absolute; left:15px; top:4px; bottom:4px; width:2px; background:linear-gradient(180deg,#c084fc 0%,rgba(168,85,247,0.2) 100%); }
  .va-step { position:relative; margin-bottom:18px; padding-left:14px; }
  .va-step:last-child { margin-bottom:0; }
  .va-step-num { position:absolute; left:-34px; top:2px; width:26px; height:26px; border-radius:50%; background:#c084fc; color:var(--bg-primary,#09090b); display:flex; align-items:center; justify-content:center; font-size:0.74rem; font-weight:700; }
  .va-step-title { font-size:0.88rem; font-weight:600; color:var(--text-primary); margin-bottom:3px; }
  .va-step-desc { font-size:0.8rem; color:var(--text-secondary); line-height:1.5; }
  .va-flow { display:flex; align-items:stretch; overflow-x:auto; padding:8px 0; gap:0; }
  .va-flow-step { flex:1 1 0; min-width:140px; background:var(--bg-tertiary); border:1px solid var(--border-light); border-radius:10px; padding:16px 14px; text-align:center; }
  .va-flow-step-label { font-size:0.7rem; text-transform:uppercase; letter-spacing:0.06em; color:#c084fc; margin-bottom:6px; font-weight:600; }
  .va-flow-step-content { font-size:0.88rem; color:var(--text-primary); font-weight:600; line-height:1.3; }
  .va-flow-step-sub { font-size:0.78rem; color:var(--text-secondary); margin-top:6px; }
  .va-flow-arrow { display:flex; align-items:center; padding:0 8px; color:#c084fc; font-size:1.2rem; flex-shrink:0; opacity:0.7; }
  .va-pyramid { display:flex; flex-direction:column; align-items:center; gap:5px; padding:12px 0; }
  .va-pyramid-layer { padding:12px 18px; text-align:center; border-radius:8px; background:var(--bg-tertiary); border:1px solid var(--border-light); font-size:0.85rem; color:var(--text-primary); }
  .va-pyramid-layer:first-child { width:50%; background:rgba(168,85,247,0.15); font-weight:600; color:#c084fc; border-color:rgba(192,132,252,0.3); }
  .va-pyramid-layer:nth-child(2) { width:65%; } .va-pyramid-layer:nth-child(3) { width:78%; }
  .va-pyramid-layer:nth-child(4) { width:88%; } .va-pyramid-layer:nth-child(5) { width:96%; }
  .va-pyramid-layer:last-child { width:100%; }
  .va-pyramid-layer-sub { font-size:0.75rem; color:var(--text-secondary); margin-top:3px; font-weight:400; }
  .va-split { display:grid; grid-template-columns:1fr auto 1fr; gap:0; }
  .va-split-left,.va-split-right { padding:18px; }
  .va-split-left { text-align:right; } .va-split-right { text-align:left; }
  .va-split-divider { width:2px; background:rgba(168,85,247,0.3); margin:0 18px; position:relative; }
  .va-split-divider::after { content:'vs'; position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); background:var(--bg-card,#1c1c1f); padding:6px 10px; font-size:0.72rem; font-weight:700; color:#c084fc; border-radius:6px; text-transform:uppercase; letter-spacing:0.05em; border:1px solid rgba(192,132,252,0.2); }
  .va-split h5 { font-size:0.88rem; font-weight:600; color:#c084fc; margin:0 0 10px; }
  .va-split ul { list-style:none; padding:0; margin:0; }
  .va-split li { font-size:0.82rem; color:var(--text-secondary); padding:4px 0; line-height:1.5; }
  .va-hub { display:flex; flex-wrap:wrap; justify-content:center; align-items:center; gap:16px; padding:16px; }
  .va-hub-center { flex:0 0 150px; height:150px; border-radius:50%; background:rgba(168,85,247,0.12); border:2px solid #c084fc; display:flex; align-items:center; justify-content:center; text-align:center; padding:18px; font-size:0.9rem; font-weight:700; color:#c084fc; }
  .va-hub-spoke { flex:0 0 150px; padding:16px; background:var(--bg-tertiary); border:1px solid var(--border-light); border-radius:10px; text-align:center; }
  .va-hub-spoke h5 { font-size:0.85rem; font-weight:600; color:var(--text-primary); margin:0 0 6px; }
  .va-hub-spoke p { font-size:0.78rem; color:var(--text-secondary); margin:0; line-height:1.45; }
  .va-spectrum { position:relative; padding:40px 0 24px; }
  .va-spectrum-bar { height:10px; border-radius:5px; background:linear-gradient(90deg,#c084fc 0%,#60a5fa 50%,#4ade80 100%); }
  .va-spectrum-markers { display:flex; justify-content:space-between; margin-top:14px; }
  .va-spectrum-marker { text-align:center; flex:1; }
  .va-spectrum-marker-label { font-size:0.8rem; font-weight:600; color:#c084fc; }
  .va-spectrum-marker-desc { font-size:0.75rem; color:var(--text-secondary); margin-top:3px; }
  .va-cards { display:flex; gap:14px; overflow-x:auto; padding:8px 0; }
  .va-card-item { flex:0 0 220px; padding:18px; background:var(--bg-tertiary); border:1px solid var(--border-light); border-radius:10px; }
  .va-card-item h5 { font-size:0.88rem; font-weight:600; color:#c084fc; margin:0 0 8px; }
  .va-card-item p { font-size:0.82rem; color:var(--text-secondary); line-height:1.5; margin:0; }
  .va-bridge { display:flex; align-items:stretch; gap:0; }
  .va-bridge-panel { flex:1; padding:18px; background:var(--bg-tertiary); border:1px solid var(--border-light); }
  .va-bridge-panel:first-child { border-radius:10px 0 0 10px; }
  .va-bridge-panel:last-child { border-radius:0 10px 10px 0; }
  .va-bridge-panel.va-bridge-center { background:rgba(168,85,247,0.1); border-color:rgba(168,85,247,0.25); text-align:center; }
  .va-bridge-panel h5 { font-size:0.8rem; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; margin:0 0 10px; }
  .va-bridge-panel:first-child h5 { color:#f87171; }
  .va-bridge-center h5 { color:#c084fc; }
  .va-bridge-panel:last-child h5 { color:#4ade80; }
  .va-bridge-panel ul { list-style:none; padding:0; margin:0; }
  .va-bridge-panel li { font-size:0.82rem; color:var(--text-secondary); padding:4px 0; line-height:1.45; }
  .va-bridge-arrow { display:flex; align-items:center; padding:0 6px; color:#c084fc; font-size:1.2rem; flex-shrink:0; opacity:0.7; }
  .va-checklist { padding:8px 0; }
  .va-check-item { display:flex; align-items:flex-start; gap:10px; padding:10px 14px; margin-bottom:4px; border-radius:8px; font-size:0.85rem; color:var(--text-secondary); line-height:1.5; }
  .va-check-item.check::before { content:'\2713'; color:#4ade80; font-weight:700; flex-shrink:0; }
  .va-check-item.cross::before { content:'\2717'; color:#ef4444; font-weight:700; flex-shrink:0; }
  @media (max-width:800px) { .ba-container { grid-template-columns:1fr; } .ba-panel.before { border-right:none; border-bottom:1px solid var(--border); } .header,.grid { padding:20px; } }
</style>
</head>
<body>
<div class="header">
  <h1><span>Visual Aid Showcase</span> — PassEPPP Content Enrichment</h1>
  <div class="stats-row" id="stats"></div>
  <div class="filters">
    <span class="filter-label">Domain</span>
    <div id="dp" style="display:flex;gap:6px;flex-wrap:wrap"></div>
    <div class="sep"></div>
    <span class="filter-label">Layout</span>
    <div id="lp" style="display:flex;gap:6px;flex-wrap:wrap"></div>
  </div>
</div>
<div class="grid" id="grid"></div>
<div class="empty" id="empty" style="display:none">No visual aids match the current filters.</div>
"""

HTML_BOTTOM = r"""
<script>
const DN = {PMET:"Psychometrics & Research Methods",LDEV:"Lifespan Development",
  CPAT:"Clinical Psychopathology",PTHE:"Psychotherapy & Interventions",
  SOCU:"Social & Cultural Psychology",WDEV:"Workforce Development",
  BPSY:"Biopsychology",CASS:"Clinical Assessment",PETH:"Pharmacology & Ethics"};

const DATA = window.__VA_DATA;
let aD='ALL', aL='ALL';

(function(){
  const byD={},byL={};
  DATA.forEach(v=>{byD[v.domain_code]=(byD[v.domain_code]||0)+1;byL[v.layout_type]=(byL[v.layout_type]||0)+1;});

  document.getElementById('stats').innerHTML=
    `<div class="stat-chip"><b>${DATA.length}</b> visual aids</div>`+
    `<div class="stat-chip"><b>96</b> chapters</div>`+
    `<div class="stat-chip"><b>9</b> domains</div>`+
    `<div class="stat-chip"><b>${Object.keys(byL).length}</b> layout types</div>`;

  const dp=document.getElementById('dp');
  dp.innerHTML=`<button class="pill active" data-v="ALL">All<span class="count">${DATA.length}</span></button>`+
    Object.keys(DN).map(d=>`<button class="pill" data-v="${d}">${d}<span class="count">${byD[d]||0}</span></button>`).join('');
  dp.onclick=e=>{const b=e.target.closest('.pill');if(!b)return;dp.querySelectorAll('.pill').forEach(p=>p.classList.remove('active'));b.classList.add('active');aD=b.dataset.v;render();};

  const lp=document.getElementById('lp');
  const sl=Object.entries(byL).sort((a,b)=>b[1]-a[1]);
  lp.innerHTML=`<button class="pill active" data-v="ALL">All</button>`+
    sl.map(([l,n])=>`<button class="pill" data-v="${l}">${l.replace('va-','')}<span class="count">${n}</span></button>`).join('');
  lp.onclick=e=>{const b=e.target.closest('.pill');if(!b)return;lp.querySelectorAll('.pill').forEach(p=>p.classList.remove('active'));b.classList.add('active');aL=b.dataset.v;render();};

  render();
})();

function render(){
  const f=DATA.filter(v=>(aD==='ALL'||v.domain_code===aD)&&(aL==='ALL'||v.layout_type===aL));
  const g=document.getElementById('grid'),em=document.getElementById('empty');
  if(!f.length){g.innerHTML='';em.style.display='block';return;}
  em.style.display='none';
  g.innerHTML=f.map(v=>{
    const cn=v.chapter_file.split('/').pop().replace('.html','').replace(/-/g,' ').replace(/\b\w/g,c=>c.toUpperCase());
    const ch=v.html.replace(/<!--\s*\/?visual-aid:\S+\s*-->/g,'');
    return `<div class="va-card"><div class="va-card-header"><div class="va-card-meta"><span class="badge badge-domain">${v.domain_code}</span><span class="badge badge-layout">${v.layout_type.replace('va-','')}</span><span class="va-card-chapter">${cn}</span></div><span class="va-card-anchor">${v.anchor_heading}</span></div><div class="ba-container"><div class="ba-panel before"><span class="ba-label bl">Before</span><div class="bh">${v.anchor_heading}</div><div class="bp">No graphic organizer — text-only content</div></div><div class="ba-panel after"><span class="ba-label al">After</span><div class="bh">${v.anchor_heading}</div>${ch}</div></div></div>`;
  }).join('');
}
</script>
</body></html>
"""

output = HTML_TOP + '<script>window.__VA_DATA = ' + data_json + ';</script>\n' + HTML_BOTTOM
OUTPUT.write_text(output, encoding='utf-8')
print(f'Wrote {OUTPUT.stat().st_size:,} bytes with {len(vas)} VAs embedded')

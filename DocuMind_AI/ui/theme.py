"""DocuMind design system: dark glass UI. Every text colour is set explicitly so
nothing can end up light-on-light."""
import html

CSS = """
<style>
:root{
  --bg:#070b18; --panel:rgba(18,27,54,.66); --panel-2:rgba(25,36,70,.55);
  --line:rgba(148,163,184,.18); --text:#e6edf7; --muted:#9fb0c9; --dim:#6f819d;
  --cyan:#22d3ee; --violet:#8b5cf6; --blue:#3b82f6; --good:#34d399; --warn:#fbbf24; --bad:#f87171;
  --font:"Segoe UI Variable Display","Segoe UI",-apple-system,"Helvetica Neue",Arial,sans-serif;
}
html, body, [class*="css"], .stApp {font-family:var(--font);}
.stApp{
  background:
    radial-gradient(1100px 520px at 12% -8%, rgba(34,211,238,.10), transparent 60%),
    radial-gradient(900px 500px at 95% 0%, rgba(139,92,246,.13), transparent 60%),
    linear-gradient(180deg,#070b18 0%,#080e1f 100%);
  color:var(--text);
}
[data-testid="stHeader"]{background:transparent;}
.block-container{padding-top:1.4rem; padding-bottom:3rem; max-width:1280px;}
h1,h2,h3,h4{color:var(--text); letter-spacing:-.01em;}
p, li, label, span, div{color:inherit;}
a{color:var(--cyan);}
hr{border-color:var(--line);}

/* ---------- sidebar ---------- */
[data-testid="stSidebar"]{
  background:linear-gradient(180deg,rgba(10,16,36,.97),rgba(8,12,28,.97));
  border-right:1px solid var(--line);
}
[data-testid="stSidebar"] .block-container{padding-top:1rem;}
.dm-brand{display:flex;align-items:center;gap:.65rem;margin:.2rem 0 1.1rem 0;}
.dm-logo{width:38px;height:38px;border-radius:11px;display:grid;place-items:center;
  background:linear-gradient(135deg,var(--cyan),var(--violet));
  box-shadow:0 6px 22px rgba(34,211,238,.28), inset 0 1px 0 rgba(255,255,255,.35);}
.dm-logo svg{width:20px;height:20px;stroke:#04121f;fill:none;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round;}
.dm-brand b{font-size:1.15rem;color:var(--text);letter-spacing:-.01em;}
.dm-brand small{display:block;color:var(--dim);font-size:.7rem;letter-spacing:.08em;text-transform:uppercase;}
[data-testid="stSidebar"] [data-testid="stRadioGroup"]{gap:.15rem;}
[data-testid="stSidebar"] [data-testid="stRadioOption"]{
  padding:.55rem .8rem; border-radius:10px; border:1px solid transparent; cursor:pointer;
  transition:all .18s ease; width:100%; margin:0 0 .15rem 0;}
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div:first-child{display:none;}
[data-testid="stSidebar"] [data-testid="stRadioOption"] p{color:var(--muted); font-weight:500; font-size:.95rem;}
[data-testid="stSidebar"] [data-testid="stRadioOption"]:hover{background:rgba(148,163,184,.08);}
[data-testid="stSidebar"] [data-testid="stRadioOption"]:hover p{color:var(--text);}
[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"]{
  background:linear-gradient(90deg,rgba(34,211,238,.16),rgba(139,92,246,.10));
  border-color:rgba(34,211,238,.35); box-shadow:0 4px 18px rgba(34,211,238,.10);}
[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] p{color:#fff; font-weight:650;}
.dm-side-note{color:var(--dim);font-size:.78rem;line-height:1.45;}
.dm-status{display:flex;align-items:center;gap:.5rem;font-size:.82rem;color:var(--muted);
  padding:.5rem .7rem;border:1px solid var(--line);border-radius:10px;background:var(--panel);}
.dm-dot{width:8px;height:8px;border-radius:50%;background:var(--good);box-shadow:0 0 10px var(--good);}
.dm-dot.off{background:var(--bad);box-shadow:0 0 10px var(--bad);}

/* ---------- glass cards ---------- */
.dm-card{
  position:relative; background:var(--panel); border:1px solid var(--line); border-radius:16px;
  padding:1.1rem 1.25rem; margin-bottom:.9rem; color:var(--text);
  backdrop-filter:blur(14px); -webkit-backdrop-filter:blur(14px);
  box-shadow:0 1px 0 rgba(255,255,255,.05) inset, 0 12px 30px -12px rgba(0,0,0,.6);
  transition:transform .22s ease, border-color .22s ease, box-shadow .22s ease;
  transform:perspective(1000px) translateZ(0);}
.dm-card:hover{transform:perspective(1000px) translateY(-3px) rotateX(1.2deg);
  border-color:rgba(34,211,238,.38);
  box-shadow:0 1px 0 rgba(255,255,255,.07) inset, 0 22px 42px -16px rgba(34,211,238,.20), 0 14px 30px -14px rgba(0,0,0,.7);}
.dm-card.accent-good{border-left:3px solid var(--good);}
.dm-card.accent-bad{border-left:3px solid var(--bad);}
.dm-card.accent-warn{border-left:3px solid var(--warn);}
.dm-card.accent-cyan{border-left:3px solid var(--cyan);}
.dm-label{font-size:.72rem;text-transform:uppercase;letter-spacing:.09em;color:var(--dim);margin-bottom:.35rem;font-weight:600;}
.dm-big{font-size:2rem;font-weight:750;letter-spacing:-.02em;color:#fff;line-height:1.1;}
.dm-med{font-size:1.25rem;font-weight:650;color:#fff;}
.dm-text{color:var(--text);line-height:1.55;overflow-wrap:anywhere;}
.dm-muted{color:var(--muted);font-size:.9rem;line-height:1.5;}
.dm-quote{border-left:2px solid var(--cyan);padding:.35rem .8rem;margin:.4rem 0;color:var(--text);
  background:rgba(34,211,238,.06);border-radius:0 8px 8px 0;font-size:.95rem;}
.dm-pill{display:inline-block;padding:.18rem .65rem;border-radius:999px;font-size:.72rem;font-weight:650;
  letter-spacing:.02em;margin:0 .3rem .3rem 0;border:1px solid var(--line);color:var(--text);background:rgba(148,163,184,.10);}
.dm-pill.cyan{color:#67e8f9;background:rgba(34,211,238,.12);border-color:rgba(34,211,238,.35);}
.dm-pill.violet{color:#c4b5fd;background:rgba(139,92,246,.14);border-color:rgba(139,92,246,.4);}
.dm-pill.good{color:#6ee7b7;background:rgba(52,211,153,.12);border-color:rgba(52,211,153,.35);}
.dm-pill.warn{color:#fcd34d;background:rgba(251,191,36,.12);border-color:rgba(251,191,36,.35);}
.dm-pill.bad{color:#fca5a5;background:rgba(248,113,113,.12);border-color:rgba(248,113,113,.35);}
.dm-chip{display:inline-block;padding:.22rem .7rem;margin:0 .35rem .4rem 0;border-radius:8px;
  background:rgba(148,163,184,.10);border:1px solid var(--line);color:var(--text);font-size:.84rem;}
.dm-bar{height:8px;border-radius:99px;background:rgba(148,163,184,.14);overflow:hidden;margin:.25rem 0 .7rem;}
.dm-bar > i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,var(--cyan),var(--violet));}
.dm-row{display:flex;justify-content:space-between;font-size:.85rem;color:var(--muted);}
.dm-row b{color:var(--text);}
.dm-empty{text-align:center;padding:3rem 1rem;color:var(--muted);}
.dm-empty h3{margin:.6rem 0 .3rem 0;}
.dm-empty svg{width:46px;height:46px;stroke:var(--cyan);fill:none;stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round;opacity:.85;}

/* ---------- page header ---------- */
.dm-page{display:flex;align-items:center;gap:.9rem;margin:.1rem 0 1.2rem 0;}
.dm-page .ic{width:46px;height:46px;border-radius:13px;display:grid;place-items:center;
  background:linear-gradient(135deg,rgba(34,211,238,.22),rgba(139,92,246,.22));border:1px solid rgba(34,211,238,.32);}
.dm-page .ic svg{width:22px;height:22px;stroke:#67e8f9;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;}
.dm-page h1{font-size:1.7rem;margin:0;font-weight:750;}
.dm-page p{margin:0;color:var(--muted);font-size:.95rem;}

/* ---------- hero ---------- */
.dm-hero{display:grid;grid-template-columns:1.15fr .85fr;gap:2rem;align-items:center;
  padding:1.6rem 0 1.2rem 0;}
.dm-hero h1{font-size:2.55rem;line-height:1.05;margin:0 0 .8rem 0;font-weight:800;letter-spacing:-.03em;}
.dm-grad{background:linear-gradient(90deg,#22d3ee,#8b5cf6 70%);-webkit-background-clip:text;background-clip:text;color:transparent;}
.dm-hero p{color:var(--muted);font-size:1.08rem;line-height:1.6;max-width:560px;}
.dm-eyebrow{display:inline-flex;align-items:center;gap:.5rem;font-size:.75rem;letter-spacing:.14em;
  text-transform:uppercase;color:#67e8f9;font-weight:650;margin-bottom:.9rem;}
.dm-eyebrow i{width:26px;height:1px;background:#67e8f9;display:inline-block;}
.dm-stage{perspective:1100px;height:300px;position:relative;}
.dm-sheet{position:absolute;width:240px;height:170px;left:50%;top:50%;border-radius:14px;
  border:1px solid rgba(148,163,184,.28);padding:14px;
  backdrop-filter:blur(8px);box-shadow:0 30px 50px -20px rgba(0,0,0,.8);transition:transform .5s ease;}
.dm-sheet .ln{height:7px;border-radius:4px;background:rgba(203,213,225,.32);margin-bottom:9px;}
.dm-sheet .ln.s{width:60%;} .dm-sheet .ln.m{width:80%;}
.dm-sheet .tag{font-size:.65rem;letter-spacing:.12em;text-transform:uppercase;color:#67e8f9;font-weight:700;margin-bottom:10px;}
.dm-sheet.s1{background:rgba(24,34,66,.85);transform:translate(-82%,-44%) rotateX(52deg) rotateZ(-34deg) translateZ(0);}
.dm-sheet.s2{background:rgba(32,42,82,.82);transform:translate(-62%,-56%) rotateX(52deg) rotateZ(-34deg) translateZ(40px);}
.dm-sheet.s3{background:rgba(40,46,98,.85);transform:translate(-42%,-68%) rotateX(52deg) rotateZ(-34deg) translateZ(80px);
  border-color:rgba(34,211,238,.5);box-shadow:0 30px 60px -20px rgba(34,211,238,.35);}
.dm-stage:hover .s1{transform:translate(-88%,-40%) rotateX(52deg) rotateZ(-34deg);}
.dm-stage:hover .s3{transform:translate(-36%,-74%) rotateX(52deg) rotateZ(-34deg) translateZ(100px);}
.dm-hl{display:inline-block;height:7px;border-radius:4px;background:#fb923c;width:46%;box-shadow:0 0 12px rgba(251,146,60,.7);margin-bottom:9px;}
.dm-hl.c{background:#22d3ee;box-shadow:0 0 12px rgba(34,211,238,.6);width:34%;}
.dm-steps{display:grid;grid-template-columns:repeat(4,1fr);gap:.8rem;margin:.4rem 0 1.4rem 0;}
.dm-step{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:.9rem 1rem;}
.dm-step .n{width:26px;height:26px;border-radius:8px;display:grid;place-items:center;font-weight:750;font-size:.8rem;
  color:#04121f;background:linear-gradient(135deg,var(--cyan),var(--violet));margin-bottom:.5rem;}
.dm-step b{display:block;color:#fff;font-size:.95rem;}
.dm-step span{color:var(--muted);font-size:.82rem;line-height:1.4;display:block;margin-top:.15rem;}

/* ---------- stat tiles ---------- */
.dm-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.8rem;margin-bottom:1rem;}
.dm-stat{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:.85rem 1rem;
  transition:transform .2s ease,border-color .2s ease;}
.dm-stat:hover{transform:translateY(-2px);border-color:rgba(34,211,238,.38);}
.dm-stat .v{font-size:1.55rem;font-weight:750;color:#fff;letter-spacing:-.02em;}
.dm-stat .k{font-size:.72rem;text-transform:uppercase;letter-spacing:.09em;color:var(--dim);font-weight:600;}
.dm-stat .s{font-size:.78rem;color:var(--muted);margin-top:.1rem;}
.dm-ring{width:128px;height:128px;border-radius:50%;display:grid;place-items:center;margin:0 auto .4rem;}
.dm-ring > div{width:98px;height:98px;border-radius:50%;background:#0b1226;display:grid;place-items:center;
  font-size:1.9rem;font-weight:800;color:#fff;}

/* ---------- timeline / diff ---------- */
.dm-tl{position:relative;margin-left:.6rem;padding-left:1.4rem;border-left:2px solid rgba(34,211,238,.35);}
.dm-tl .it{position:relative;margin-bottom:1rem;}
.dm-tl .it:before{content:"";position:absolute;left:-1.85rem;top:.35rem;width:12px;height:12px;border-radius:50%;
  background:var(--bg);border:2px solid var(--cyan);box-shadow:0 0 10px rgba(34,211,238,.6);}
.dm-tl .d{font-weight:700;color:#fff;} .dm-tl .e{color:var(--muted);font-size:.9rem;}
.df-del{background:rgba(248,113,113,.22);color:#fecaca;border-radius:4px;padding:0 3px;text-decoration:line-through;}
.df-add{background:rgba(52,211,153,.22);color:#a7f3d0;border-radius:4px;padding:0 3px;}

/* ---------- streamlit widgets ---------- */
.stButton > button, .stDownloadButton > button{
  background:rgba(148,163,184,.10); color:var(--text); border:1px solid var(--line); border-radius:10px;
  font-weight:600; transition:all .18s ease;}
.stButton > button:hover, .stDownloadButton > button:hover{
  border-color:rgba(34,211,238,.6); color:#fff; background:rgba(34,211,238,.12);
  transform:translateY(-1px); box-shadow:0 8px 20px -10px rgba(34,211,238,.5);}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primaryFormSubmit"], .stFormSubmitButton > button{
  background:linear-gradient(135deg,#0ea5c6,#7c5cf0); color:#fff; border:0;}
[data-testid="stFileUploaderDropzone"]{background:var(--panel);border:1.5px dashed rgba(34,211,238,.45);border-radius:16px;padding:1.4rem;}
[data-testid="stFileUploaderDropzone"] *{color:var(--muted);}
[data-testid="stFileUploaderDropzone"] button{color:var(--text);}
.stTextInput input, .stTextArea textarea, [data-baseweb="select"] > div{
  background:rgba(9,14,32,.85)!important; color:var(--text)!important; border:1px solid var(--line)!important; border-radius:10px!important;}
.stTextInput input:focus, .stTextArea textarea:focus{border-color:var(--cyan)!important;box-shadow:0 0 0 3px rgba(34,211,238,.18)!important;}
[data-testid="stExpander"]{background:var(--panel);border:1px solid var(--line);border-radius:14px;}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary *{color:var(--text);}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:12px;overflow:hidden;}
[data-testid="stMetric"]{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:.7rem 1rem;}
[data-testid="stImage"] img{border-radius:12px;border:1px solid var(--line);box-shadow:0 18px 40px -18px rgba(0,0,0,.8);}
[data-testid="stCaptionContainer"]{color:var(--muted);}
.stAlert{border-radius:12px;}
@media (max-width: 900px){
  .dm-hero{grid-template-columns:1fr;} .dm-stage{display:none;} .dm-steps{grid-template-columns:1fr 1fr;}
  .dm-hero h1{font-size:2.2rem;}
}
</style>
"""

ICONS = {
 "logo": '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/><path d="M19 17v4M17 19h4"/>',
 "home": '<path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/>',
 "upload": '<path d="M12 16V4"/><path d="m7 9 5-5 5 5"/><path d="M5 20h14"/>',
 "eye": '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/>',
 "spark": '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/>',
 "chat": '<path d="M21 15a2 2 0 0 1-2 2H8l-5 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
 "shield": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="m9 12 2 2 4-4"/>',
 "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
 "columns": '<rect x="3" y="4" width="7" height="16" rx="1.5"/><rect x="14" y="4" width="7" height="16" rx="1.5"/>',
 "download": '<path d="M12 4v12"/><path d="m7 11 5 5 5-5"/><path d="M5 20h14"/>',
 "doc": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M9 13h6M9 17h6"/>',
}


def icon(name):
    return (f'<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">{ICONS[name]}</svg>')


def esc(t):
    return html.escape(str(t))


def page_header(ic, title, subtitle):
    return (f'<div class="dm-page"><div class="ic">{icon(ic)}</div>'
            f'<div><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div></div>')


def card(inner, accent="", label=None):
    lab = f'<div class="dm-label">{esc(label)}</div>' if label else ""
    return f'<div class="dm-card {accent}">{lab}{inner}</div>'


def pill(text, kind=""):
    return f'<span class="dm-pill {kind}">{esc(text)}</span>'


def chip(text):
    return f'<span class="dm-chip">{esc(text)}</span>'


def stat(key, value, sub=""):
    s = f'<div class="s">{esc(sub)}</div>' if sub else ""
    return f'<div class="dm-stat"><div class="k">{esc(key)}</div><div class="v">{esc(value)}</div>{s}</div>'


def stats(items):
    return '<div class="dm-stats">' + "".join(stat(*i) for i in items) + "</div>"


def empty_state(ic, title, text):
    return (f'<div class="dm-card"><div class="dm-empty">{icon(ic)}<h3>{esc(title)}</h3>'
            f'<div>{esc(text)}</div></div></div>')


def bar(label, value, maxv, suffix=""):
    pct = 0 if maxv <= 0 else min(100, round(100 * value / maxv))
    return (f'<div class="dm-row"><span>{esc(label)}</span><b>{esc(value)}{suffix}</b></div>'
            f'<div class="dm-bar"><i style="width:{pct}%"></i></div>')


def ring(score, label):
    color = "#34d399" if score >= 85 else "#fbbf24" if score >= 70 else "#f87171"
    return (f'<div class="dm-ring" style="background:conic-gradient({color} {score * 3.6}deg,'
            f'rgba(148,163,184,.18) 0deg)"><div>{round(score)}</div></div>'
            f'<div style="text-align:center">{pill(label, "good" if score >= 85 else "warn" if score >= 70 else "bad")}</div>')


HERO = f"""
<div class="dm-hero">
  <div>
    <div class="dm-eyebrow"><i></i>Document intelligence with evidence</div>
    <h1>Understand any document.<br><span class="dm-grad">Verify every answer.</span></h1>
    <p>DocuMind AI reads a scanned document, extracts what matters, classifies it, and answers your
       questions only from what is actually written, pointing to the exact words on the page.</p>
  </div>
  <div class="dm-stage">
    <div class="dm-sheet s1"><div class="tag">Scan</div><div class="ln"></div><div class="ln m"></div><div class="ln"></div><div class="ln s"></div></div>
    <div class="dm-sheet s2"><div class="tag">Extract</div><div class="ln m"></div><div class="dm-hl c"></div><div class="ln"></div><div class="ln s"></div></div>
    <div class="dm-sheet s3"><div class="tag">Verify</div><div class="ln"></div><div class="dm-hl"></div><div class="ln m"></div><div class="ln s"></div></div>
  </div>
</div>
<div class="dm-steps">
  <div class="dm-step"><div class="n">1</div><b>Upload</b><span>Image or PDF, up to 8 pages</span></div>
  <div class="dm-step"><div class="n">2</div><b>Read</b><span>OpenCV cleanup, Tesseract word-level OCR</span></div>
  <div class="dm-step"><div class="n">3</div><b>Understand</b><span>Facts, category, keywords, privacy scan</span></div>
  <div class="dm-step"><div class="n">4</div><b>Verify</b><span>Ask questions, see the evidence highlighted</span></div>
</div>
"""

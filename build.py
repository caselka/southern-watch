"""Render every data/*.json brief into the static site in docs/.

Each JSON file is one edition. The file name (without .json) is the edition id, e.g.
2026-11-09 or 2026-11-09-updated. An optional "edition" field labels it (e.g. "Updated sources").
"""
import html
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"

CSS = """
/* Navy masthead with the logo, then a plain document: white page, black Times New Roman, double-spaced */
:root{--navy:#0f1b2d;--gold:#f5b81c;--cream:#f3eee6;--lens:#8b0000;color-scheme:light}
*{box-sizing:border-box}
html,body{background:#ffffff;color:#000000}
body{margin:0;font-family:"Times New Roman",Times,serif;font-size:18px;line-height:2}
a{color:#000000;text-decoration:underline}
a:focus-visible{outline:2px solid #000;outline-offset:2px}
.mast{background:var(--navy);color:var(--cream)}
.mast-in{max-width:44rem;margin:0 auto;padding-block:1.25rem 1.25rem;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:grid;justify-items:center;gap:.4rem;text-align:center;line-height:1.5}
.mast img{width:min(220px,60vw);height:auto;display:block}
.mast nav{display:flex;flex-wrap:wrap;justify-content:center;gap:.2rem 1.4rem;font-size:.95rem}
.mast nav a{color:var(--cream)}
.mast nav a:hover{color:var(--gold)}
.dateline{font-style:italic;font-size:.95rem;color:var(--cream)}
.byline{font-size:.85rem;letter-spacing:.06em;color:var(--gold)}
.find{width:100%;max-width:30rem;text-align:left;font-size:.95rem}
.find summary{cursor:pointer;color:var(--gold);text-align:center;list-style:none;font-weight:bold}
.find summary::-webkit-details-marker{display:none}
.find summary::after{content:" ▾"}
.find[open] summary::after{content:" ▴"}
.find-in{display:grid;gap:.5rem;margin-top:.5rem;background:#fff;color:#000;border-radius:6px;padding:.7rem}
.find-date{display:grid;grid-template-columns:1fr 1.3fr 1.3fr auto;gap:.4rem;align-items:end}
.find-date label{display:grid;font-size:.75rem;line-height:1.3}
.find select,.find input,.find button{font:inherit;font-size:16px;padding:.3rem .4rem;border:1px solid #000;border-radius:4px;background:#fff;color:#000;min-width:0;width:100%}
.find button{background:var(--navy);color:var(--gold);border-color:var(--navy);font-weight:bold;cursor:pointer}
#fres ul{list-style:none;margin:0;padding:0;max-height:55vh;overflow-y:auto}
#fres li{padding:.4rem 0;border-top:1px solid #ccc;line-height:1.45;display:grid}
#fres a{font-weight:bold}
.find-d,.find-n{font-size:.8rem;font-style:italic}
.find-s{font-size:.85rem}
#fres mark{background:var(--gold);color:#000}
@media (max-width:420px){.find-date{grid-template-columns:1fr 1fr}}
.views{font-size:.9rem;color:var(--cream);opacity:.85}
.views[hidden]{display:none}
.edition{display:inline-block;background:var(--gold);color:var(--navy);font-weight:bold;font-size:.8rem;letter-spacing:.08em;text-transform:uppercase;padding:0 .5rem;border-radius:2px}
.wrap{max-width:44rem;margin:0 auto;padding-block:1.5rem 4rem;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
h2{font-size:1.4rem;font-weight:bold;margin:0;line-height:1.4;text-wrap:balance}
.label{display:block;font-size:1.05rem;font-weight:bold;font-style:italic;line-height:1.4;margin-top:.6rem}
.bluf{border-bottom:1px solid #000;padding-bottom:1rem}
.bluf .label{font-size:1.4rem;font-style:normal;margin-top:0}
.bluf ol{margin:0;padding-left:1.4rem}
.story{padding-block:1.5rem;border-bottom:1px solid #000}
.meta{font-size:.9rem;font-style:italic}
.tag+.tag::before{content:" · "}
.tag.hi{font-weight:bold;font-style:normal}
.story p{margin:0}
.block ul{margin:0;padding-left:1.4rem}
.lens .label{color:var(--lens)}
.src{font-size:.9rem;display:flex;flex-wrap:wrap;gap:0 1rem}
.tablewrap{overflow-x:auto}
.cal{width:100%;border-collapse:collapse}
.cal td{padding:0 .6rem 0 0;vertical-align:top}
.cal td:first-child{font-weight:bold;white-space:nowrap}
.note{font-size:.9rem;font-style:italic}
.archive{list-style:none;margin:0;padding:0}
.archive li{padding-block:.6rem;border-bottom:1px solid #000}
.archive a{font-weight:bold}
.archive .edition{margin-left:.6rem}
.archive .note{display:block}
#xbtn{position:fixed;z-index:20}
#xbtn button{font:bold .9rem/1 "Times New Roman",Times,serif;background:var(--navy);color:var(--gold);border:0;border-radius:999px;padding:.55rem 1rem;box-shadow:0 2px 8px rgba(0,0,0,.3);cursor:pointer}
#xpanel{position:fixed;z-index:21;left:50%;transform:translateX(-50%);bottom:max(12px,env(safe-area-inset-bottom,0px));width:min(44rem,calc(100% - 24px));max-height:min(70vh,36rem);display:flex;flex-direction:column;background:#fff;border:2px solid var(--navy);border-radius:10px;box-shadow:0 8px 30px rgba(0,0,0,.35);line-height:1.6;font-size:17px}
#xpanel[hidden],#xbtn[hidden]{display:none}
.xhead{display:flex;justify-content:space-between;align-items:center;gap:1rem;background:var(--navy);color:var(--cream);padding:.5rem .9rem;border-radius:7px 7px 0 0;font-weight:bold}
.xhead button{background:none;border:0;color:var(--cream);font-size:1.6rem;line-height:1;cursor:pointer;padding:0 .2rem}
#xbody{overflow-y:auto;padding:.4rem .9rem}
#xbody p{margin:.5rem 0}
#xbody ul{margin:.3rem 0;padding-left:1.3rem}
.xwait{font-style:italic}
.xfoot{display:flex;justify-content:space-between;align-items:center;gap:.6rem;flex-wrap:wrap;border-top:1px solid #000;padding:.45rem .9rem;font-size:.8rem;font-style:italic}
.xfoot button{font:inherit;font-style:normal;font-weight:bold;background:var(--gold);color:var(--navy);border:0;border-radius:4px;padding:.3rem .6rem;cursor:pointer}
.xfoot button[hidden]{display:none}
"""

EXPLAIN_JS = r"""<div id="xbtn" hidden><button type="button">Explain</button></div>
<div id="xpanel" hidden role="dialog" aria-modal="false" aria-labelledby="xtitle">
<div class="xhead"><span id="xtitle"></span><button type="button" id="xclose" aria-label="Close">×</button></div>
<div id="xbody" aria-live="polite"></div>
<div class="xfoot"><button type="button" id="xdeep">Search the web for the latest</button><span>Claude, via your Pi</span></div>
</div>
<script>
(() => {
  // Highlight-to-explain. Only works on the owner's devices (Tailscale); for everyone else nothing appears.
  const API = "https://raspberrypi.tail52911d.ts.net";
  const $ = id => document.getElementById(id);
  const btn = $("xbtn"), panel = $("xpanel"), body = $("xbody");
  let avail = null, sel = "", ctx = "", timer;
  const esc = s => s.replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
  function md(t){
    const inl = s => esc(s).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
      .replace(/(^|[\s(])(https?:\/\/[^\s<)]+)/g, '$1<a href="$2" target="_blank" rel="noopener">link</a>');
    let out = "", list = [];
    for (const raw of t.split("\n")) {
      const l = raw.trim();
      if (/^[-*] /.test(l)) { list.push("<li>" + inl(l.slice(2)) + "</li>"); continue; }
      if (list.length) { out += "<ul>" + list.join("") + "</ul>"; list = []; }
      if (l) out += "<p>" + inl(l.replace(/^#+\s*/, "")) + "</p>";
    }
    return out + (list.length ? "<ul>" + list.join("") + "</ul>" : "");
  }
  async function available(){
    if (avail !== null) return avail;
    try {
      const c = new AbortController(); setTimeout(() => c.abort(), 4000);
      const r = await fetch(API + "/explain/ping", {signal: c.signal});
      avail = r.ok && (await r.json()).ok;
    } catch (e) { avail = false; }
    return avail;
  }
  function place(range){
    const r = range.getBoundingClientRect();
    btn.hidden = false;
    const w = btn.offsetWidth, h = btn.offsetHeight;
    let top = r.bottom + 10; if (top + h > innerHeight - 8) top = Math.max(8, r.top - h - 10);
    btn.style.top = top + "px";
    btn.style.left = Math.min(innerWidth - w - 8, Math.max(8, r.left + r.width / 2 - w / 2)) + "px";
  }
  document.addEventListener("selectionchange", () => {
    clearTimeout(timer);
    timer = setTimeout(async () => {
      const s = getSelection(), t = s ? s.toString().replace(/\s+/g, " ").trim() : "";
      if (!t || t.length < 2 || t.length > 300 || !s.rangeCount) { btn.hidden = true; return; }
      const node = s.anchorNode && (s.anchorNode.nodeType === 1 ? s.anchorNode : s.anchorNode.parentElement);
      if (!node || !node.closest("main") || node.closest("#xpanel")) { btn.hidden = true; return; }
      if (!(await available())) return;
      sel = t;
      const box = node.closest(".story, .bluf") || node.closest("main");
      ctx = (box.innerText || "").slice(0, 3500);
      place(s.getRangeAt(0));
    }, 350);
  });
  addEventListener("scroll", () => { btn.hidden = true; }, {passive: true});
  async function ask(deep){
    panel.hidden = false; btn.hidden = true;
    $("xtitle").textContent = sel.length > 60 ? sel.slice(0, 57) + "…" : sel;
    $("xdeep").hidden = true;
    body.innerHTML = '<p class="xwait">' + (deep ? "Searching the web… (up to a minute)" : "Thinking… (about 10 seconds)") + "</p>";
    try {
      const r = await fetch(API + "/explain", {method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({text: sel, context: ctx, deep, date: (document.querySelector(".dateline") || {}).textContent || ""})});
      const d = await r.json();
      body.innerHTML = d.answer ? md(d.answer) : '<p class="xwait">' + esc(d.error || "No answer") + "</p>";
      $("xdeep").hidden = !!deep || !d.answer;
    } catch (e) { body.innerHTML = '<p class="xwait">Couldn\'t reach the Pi. Is Tailscale on?</p>'; }
  }
  for (const ev of ["mousedown", "touchstart"]) btn.addEventListener(ev, e => e.preventDefault(), {passive: false});
  btn.querySelector("button").addEventListener("click", () => ask(false));
  $("xdeep").addEventListener("click", () => ask(true));
  $("xclose").addEventListener("click", () => { panel.hidden = true; });
  addEventListener("keydown", e => { if (e.key === "Escape") panel.hidden = true; });
})();
</script>"""

FIND_HTML = r"""<details class="find" data-prefix="{prefix}"><summary>Find a brief</summary>
<div class="find-in">
<form class="find-date" onsubmit="return false">
<label><span>Year</span><select id="fy" aria-label="Year"></select></label>
<label><span>Month</span><select id="fm" aria-label="Month"></select></label>
<label><span>Day</span><select id="fd" aria-label="Day"></select></label>
<button type="button" id="fgo">Open</button>
</form>
<form class="find-q" role="search" onsubmit="return false">
<input id="fq" type="search" placeholder="Search all briefs, e.g. Solomon Islands" aria-label="Search all briefs" autocomplete="off" enterkeyhint="search">
</form>
<div id="fres" aria-live="polite"></div>
</div></details>
<script>
(() => {
  const box = document.querySelector("details.find"), P = box.dataset.prefix;
  const $ = id => document.getElementById(id);
  const MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"];
  let eds = null;
  const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
  const url = e => P + "archive/" + e.id + ".html";
  function opts(sel, items, keep){
    sel.innerHTML = items.map(([v, t]) => `<option value="${esc(v)}">${esc(t)}</option>`).join("");
    if (keep && items.some(([v]) => v === keep)) sel.value = keep;
  }
  function fillMonths(){
    const y = $("fy").value, ms = [...new Set(eds.filter(e => e.date.startsWith(y)).map(e => e.date.slice(5, 7)))].sort().reverse();
    opts($("fm"), ms.map(m => [m, MONTHS[+m - 1]]), $("fm").value); fillDays();
  }
  function fillDays(){
    const pre = $("fy").value + "-" + $("fm").value;
    const ds = eds.filter(e => e.date.startsWith(pre)).sort((a, b) => b.id.localeCompare(a.id));
    opts($("fd"), ds.map(e => [e.id, new Date(e.date + "T12:00").toLocaleDateString("en-AU", {weekday: "short", day: "numeric"}) + (e.edition ? " · " + e.edition : "")]));
  }
  async function load(){
    if (eds) return;
    try { eds = await (await fetch(P + "editions.json")).json(); } catch (e) { $("fres").textContent = "Couldn't load the list of briefs."; return; }
    const ys = [...new Set(eds.map(e => e.date.slice(0, 4)))].sort().reverse();
    opts($("fy"), ys.map(y => [y, y])); fillMonths();
  }
  box.addEventListener("toggle", () => { if (box.open) load(); });
  $("fy").addEventListener("change", fillMonths);
  $("fm").addEventListener("change", fillDays);
  $("fgo").addEventListener("click", () => { const e = eds && eds.find(x => x.id === $("fd").value); if (e) location.href = url(e); });
  let t;
  $("fq").addEventListener("input", () => { clearTimeout(t); t = setTimeout(search, 250); });
  async function search(){
    await load(); if (!eds) return;
    const q = $("fq").value.trim().toLowerCase(), words = q.split(/\s+/).filter(w => w.length > 1);
    if (!words.length) { $("fres").innerHTML = ""; return; }
    const hits = [];
    for (const e of eds) for (const s of e.stories) {
      const hay = (s.t + " " + s.x).toLowerCase();
      if (!words.every(w => hay.includes(w))) continue;
      const score = words.filter(w => s.t.toLowerCase().includes(w)).length * 3 + (hay.includes(q) ? 2 : 0);
      hits.push({e, s, score});
    }
    hits.sort((a, b) => b.score - a.score || b.e.id.localeCompare(a.e.id));
    const mark = txt => { let h = esc(txt); for (const w of words) h = h.replace(new RegExp("(" + w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "gi"), "<mark>$1</mark>"); return h; };
    const snip = x => { const i = x.toLowerCase().indexOf(words[0]); const a = Math.max(0, i - 70); return (a ? "…" : "") + x.slice(a, a + 200) + "…"; };
    $("fres").innerHTML = hits.length
      ? `<p class="find-n">${hits.length} result${hits.length === 1 ? "" : "s"}</p><ul>` + hits.slice(0, 40).map(h =>
          `<li><a href="${url(h.e)}">${mark(h.s.t)}</a><span class="find-d">${esc(new Date(h.e.date + "T12:00").toLocaleDateString("en-AU", {day: "numeric", month: "short", year: "numeric"}))}${h.e.edition ? " · " + esc(h.e.edition) : ""}</span><span class="find-s">${mark(snip(h.s.x))}</span></li>`).join("") + "</ul>"
      : '<p class="find-n">No briefs mention that yet.</p>';
  }
})();
</script>"""

FONTS = ""  # Times New Roman is a system font: nothing to load

NOTE = ("State media (Global Times, Xinhua, TASS, Tehran Times, IRNA, KCNA) show each government's "
        "official position and the messages it wants to spread. They are not independent evidence of what happened.")


def esc(s):
    return html.escape(str(s), quote=True)


def inline(s):
    """Escape text, then allow **bold**."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc(s))


def prose(s):
    """Paragraphs, with '- ' lines turned into a bullet list."""
    out, bullets = [], []
    for line in str(s).splitlines():
        line = line.strip()
        if line.startswith("- "):
            bullets.append(f"<li>{inline(line[2:])}</li>")
            continue
        if bullets:
            out.append("<ul>" + "".join(bullets) + "</ul>")
            bullets = []
        if line:
            out.append(f"<p>{inline(line)}</p>")
    if bullets:
        out.append("<ul>" + "".join(bullets) + "</ul>")
    return "".join(out)


def safe_url(u):
    return esc(u) if str(u).startswith(("https://", "http://")) else "#"


def dateline(d: date):
    return f"{d:%A} {d.day} {d:%B %Y} · Sydney"


def page(title, mast_extra, body, prefix):
    return f"""<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0f1b2d">
<title>{esc(title)}</title>
<link rel="icon" href="{prefix}assets/icon-64.png" type="image/png">
<link rel="apple-touch-icon" href="{prefix}assets/icon-180.png">
{FONTS}
<style>{CSS}</style>
</head>
<body>
<header class="mast"><div class="mast-in">
<a href="{prefix}index.html" aria-label="Southern Watch home"><img src="{prefix}assets/logo.png" alt="Southern Watch: geopolitics from Australia's angle" width="640" height="591"></a>
<span class="byline">Created by Caselka</span>
{mast_extra}
{FIND_HTML.replace("{prefix}", prefix)}
</div></header>
<main class="wrap">
{body}
</main>
{EXPLAIN_JS}
</body>
</html>
"""


COUNTER_NS = "caselka-southern-watch"


def views(eid):
    """'Viewed by N readers' - counts each browser once per edition (abacus.jasoncameron.dev, no cookies)."""
    return f"""<span class="views" id="views" hidden></span>
<script>
(function(){{
  var key = "{eid}", el = document.getElementById("views"), seen = false;
  try {{ seen = localStorage.getItem("sw-seen-" + key) === "1"; }} catch (e) {{}}
  var url = "https://abacus.jasoncameron.dev/" + (seen ? "get" : "hit") + "/{COUNTER_NS}/" + key;
  fetch(url).then(function(r){{ return r.json(); }}).then(function(d){{
    if (typeof d.value !== "number") return;
    try {{ localStorage.setItem("sw-seen-" + key, "1"); }} catch (e) {{}}
    el.textContent = "Viewed by " + d.value.toLocaleString("en-AU") + (d.value === 1 ? " reader" : " readers");
    el.hidden = false;
  }}).catch(function(){{}});
}})();
</script>"""


def nav(prefix, prev_id, next_id):
    links = [f'<a href="{prefix}index.html">Latest</a>', f'<a href="{prefix}archive/index.html">Archive</a>']
    if prev_id:
        links.append(f'<a href="{prefix}archive/{prev_id}.html">← Previous</a>')
    if next_id:
        links.append(f'<a href="{prefix}archive/{next_id}.html">Next →</a>')
    return f"<nav>{''.join(links)}</nav>"


def render_brief(b, eid, prev_id, next_id, prefix):
    d = date.fromisoformat(b["date"])
    edition = f'<span class="edition">{esc(b["edition"])}</span>' if b.get("edition") else ""
    mast = f'<span class="dateline">{esc(dateline(d))}</span>{edition}{views(eid)}{nav(prefix, prev_id, next_id)}'

    parts = ['<section class="bluf"><span class="label">Bottom line up front</span><ol>'
             + "".join(f"<li>{inline(x)}</li>" for x in b["bluf"]) + "</ol></section>"]
    for s in b["stories"]:
        tags = (['<span class="tag hi">Priority</span>'] if s.get("priority") else []) + [
            f'<span class="tag">{esc(s["region"]).title()}</span>',
            f'<span class="tag">Confidence: {esc(s["confidence"]).lower()}</span>']
        srcs = "".join(f'<a href="{safe_url(x["url"])}" rel="noopener">{esc(x["label"])}</a>' for x in s["sources"])
        parts.append(f"""<article class="story">
<div class="meta">{''.join(tags)}</div>
<h2>{inline(s['title'])}</h2>
<div class="block"><span class="label">What happened</span>{prose(s['what_happened'])}</div>
<div class="block"><span class="label">Why it matters for Australia</span>{prose(s['why_australia'])}</div>
<div class="lens"><span class="label">State media framing · {esc(s['lens_actor'])}</span>{prose(s.get('state_media_framing') or s.get('adversary_lens', ''))}</div>
<div class="angle"><span class="label">Angle to build</span>{prose(s['angle'])}</div>
<div class="src">{srcs}</div>
</article>""")
    rows = "".join(f"<tr><td>{esc(w['when'])}</td><td>{inline(w['what'])}</td></tr>" for w in b["watch_list"])
    parts.append(f'<section class="story"><span class="label">Watch list</span>'
                 f'<div class="tablewrap"><table class="cal">{rows}</table></div>'
                 f'<p class="note">{NOTE}</p></section>')
    title = f"Southern Watch · {d.day} {d:%b %Y}" + (f" · {b['edition']}" if b.get("edition") else "")
    return page(title, mast, "\n".join(parts), prefix)


def render_archive(editions):
    items = []
    for eid, b in reversed(editions):
        d = date.fromisoformat(b["date"])
        badge = f'<span class="edition">{esc(b["edition"])}</span>' if b.get("edition") else ""
        first = b["bluf"][0] if b["bluf"] else ""
        items.append(f'<li><a href="{eid}.html">{d:%A} {d.day} {d:%B %Y}</a>{badge}'
                     f'<span class="note">{inline(first)}</span></li>')
    mast = '<span class="dateline">All briefs</span><nav><a href="../index.html">Latest</a></nav>'
    return page("Southern Watch Archive", mast, f'<ul class="archive">{"".join(items)}</ul>', "../")


def search_index(editions):
    """Small list of every edition for the header's date picker and search (text trimmed to keep it light)."""
    plain = lambda t: re.sub(r"\s+", " ", re.sub(r"\*\*|^- ", "", str(t), flags=re.M)).strip()
    out = []
    for eid, b in editions:
        stories = [{"t": plain(st["title"]),
                    "x": plain(" ".join([st.get("region", ""), st.get("lens_actor", ""), st.get("what_happened", ""),
                                         st.get("why_australia", "")]))[:900]} for st in b["stories"]]
        stories.append({"t": "Bottom line up front", "x": plain(" ".join(b["bluf"]))[:900]})
        out.append({"id": eid, "date": b["date"], "edition": b.get("edition", ""), "stories": stories})
    return out


def main():
    files = sorted(DATA.glob("*.json"), key=lambda f: f.stem)
    editions = [(f.stem, json.loads(f.read_text(encoding="utf-8"))) for f in files]
    if not editions:
        raise SystemExit("No briefs in data/")
    (DOCS / "archive").mkdir(parents=True, exist_ok=True)
    ids = [e for e, _ in editions]
    for i, (eid, b) in enumerate(editions):
        prev_id = ids[i - 1] if i > 0 else None
        next_id = ids[i + 1] if i + 1 < len(ids) else None
        (DOCS / "archive" / f"{eid}.html").write_text(render_brief(b, eid, prev_id, next_id, "../"), encoding="utf-8")
    latest_id, latest = editions[-1]
    (DOCS / "index.html").write_text(render_brief(latest, latest_id, ids[-2] if len(ids) > 1 else None, None, ""), encoding="utf-8")
    (DOCS / "archive" / "index.html").write_text(render_archive(editions), encoding="utf-8")
    (DOCS / "editions.json").write_text(json.dumps(search_index(editions), ensure_ascii=False, separators=(",", ":")),
                                        encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    old_favicon = DOCS / "favicon.svg"
    if old_favicon.exists():
        old_favicon.unlink()
    print(f"Built {len(editions)} edition(s); latest {latest_id}")


if __name__ == "__main__":
    main()

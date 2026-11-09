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
/* Layout: navy masthead carrying the logo, then one calm reading column */
:root{
  --navy:#0f1b2d; --navy-2:#16263d; --gold:#f5b81c; --cream:#f3eee6;
  --bg:#fbfaf7; --surface:#ffffff; --ink:#1a1f29; --muted:#5d6573; --rule:#e4e1da;
  --lens:#9a2f2f; --lens-bg:#f8eeec; --angle-bg:#fbf4df;
  --head:"Montserrat","Arial",sans-serif;
  --body:"Source Serif 4",Georgia,serif;
  --mono:"JetBrains Mono",ui-monospace,Consolas,monospace;
  color-scheme:light;
}
@media (prefers-color-scheme: dark){:root{
  --bg:#0c1522; --surface:#122033; --ink:#e7ebf0; --muted:#97a3b3; --rule:#22344c;
  --lens:#ef9a8f; --lens-bg:#2a1c22; --angle-bg:#2a2615; color-scheme:dark}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--body);font-size:17.5px;line-height:1.65}
a{color:inherit;text-decoration-color:var(--gold);text-decoration-thickness:2px;text-underline-offset:3px}
a:focus-visible{outline:2px solid var(--gold);outline-offset:2px}
.mast{background:var(--navy);color:var(--cream)}
.mast-in{max-width:46rem;margin:0 auto;padding-block:1.25rem 1.5rem;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:grid;justify-items:center;gap:.75rem;text-align:center}
.mast img{width:min(230px,62vw);height:auto;display:block}
.mast nav{display:flex;flex-wrap:wrap;justify-content:center;gap:.3rem 1.4rem;font:500 .74rem var(--mono);letter-spacing:.06em;text-transform:uppercase}
.mast nav a{color:var(--cream);text-decoration:none;opacity:.8}
.mast nav a:hover{opacity:1;color:var(--gold)}
.dateline{font:500 .78rem var(--mono);letter-spacing:.08em;color:var(--cream);opacity:.85;text-transform:uppercase}
.edition{display:inline-block;background:var(--gold);color:var(--navy);font:700 .7rem var(--head);letter-spacing:.12em;text-transform:uppercase;padding:.25rem .6rem;border-radius:3px}
.wrap{max-width:46rem;margin:0 auto;padding-block:2rem 4rem;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
h2{font:700 1.45rem/1.2 var(--head);margin:0;text-wrap:balance;letter-spacing:-.01em}
.label{font:700 .72rem var(--head);letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.bluf{display:grid;gap:.6rem;padding-bottom:1.6rem;border-bottom:3px solid var(--gold)}
.bluf .label{color:var(--ink)}
.bluf ol{margin:0;padding-left:1.25rem;display:grid;gap:.55rem}
.story{display:grid;gap:.85rem;padding-block:1.9rem;border-bottom:1px solid var(--rule)}
.meta{display:flex;flex-wrap:wrap;gap:.45rem}
.tag{font:500 .68rem var(--mono);letter-spacing:.05em;color:var(--muted);border:1px solid var(--rule);padding:.12rem .45rem;border-radius:3px}
.tag.hi{color:var(--navy);background:var(--gold);border-color:var(--gold);font-weight:700}
.story p{margin:0}
.block{display:grid;gap:.3rem}
.block ul{margin:0;padding-left:1.15rem;display:grid;gap:.3rem}
.lens,.angle{padding:.9rem 1.1rem;border-radius:6px;display:grid;gap:.3rem}
.lens{background:var(--lens-bg)} .lens .label{color:var(--lens)}
.angle{background:var(--angle-bg)} .angle .label{color:var(--ink)}
.src{font:.72rem var(--mono);color:var(--muted);display:flex;flex-wrap:wrap;gap:.3rem 1rem}
.src a{text-decoration-thickness:1px}
.tablewrap{overflow-x:auto}
.cal{width:100%;border-collapse:collapse}
.cal td{padding:.5rem .4rem;border-bottom:1px solid var(--rule);vertical-align:top}
.cal td:first-child{font:600 .78rem var(--mono);white-space:nowrap;font-variant-numeric:tabular-nums}
.note{font-size:.86rem;color:var(--muted)}
.archive{list-style:none;margin:0;padding:0}
.archive li{display:grid;gap:.25rem;padding-block:1rem;border-bottom:1px solid var(--rule)}
.archive a{font:700 1.1rem var(--head);text-decoration:none}
.archive .edition{justify-self:start}
"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Montserrat:wght@500;700'
         '&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=JetBrains+Mono:wght@500;600&display=swap">')

NOTE = ("Adversary state media (Global Times, Xinhua, TASS, Tehran Times, IRNA, KCNA) shows each government's "
        "official position and the messages it wants spread. It is not independent evidence of what happened.")


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
{mast_extra}
</div></header>
<main class="wrap">
{body}
</main>
</body>
</html>
"""


def nav(prefix, prev_id, next_id):
    links = [f'<a href="{prefix}index.html">Latest</a>', f'<a href="{prefix}archive/index.html">Archive</a>']
    if prev_id:
        links.append(f'<a href="{prefix}archive/{prev_id}.html">← Previous</a>')
    if next_id:
        links.append(f'<a href="{prefix}archive/{next_id}.html">Next →</a>')
    return f"<nav>{''.join(links)}</nav>"


def render_brief(b, prev_id, next_id, prefix):
    d = date.fromisoformat(b["date"])
    edition = f'<span class="edition">{esc(b["edition"])}</span>' if b.get("edition") else ""
    mast = f'<span class="dateline">{esc(dateline(d))}</span>{edition}{nav(prefix, prev_id, next_id)}'

    parts = ['<section class="bluf"><span class="label">Bottom line up front</span><ol>'
             + "".join(f"<li>{inline(x)}</li>" for x in b["bluf"]) + "</ol></section>"]
    for s in b["stories"]:
        tags = (['<span class="tag hi">Priority</span>'] if s.get("priority") else []) + [
            f'<span class="tag">{esc(s["region"]).upper()}</span>',
            f'<span class="tag">Confidence: {esc(s["confidence"]).title()}</span>']
        srcs = "".join(f'<a href="{safe_url(x["url"])}" rel="noopener">{esc(x["label"])}</a>' for x in s["sources"])
        parts.append(f"""<article class="story">
<div class="meta">{''.join(tags)}</div>
<h2>{inline(s['title'])}</h2>
<div class="block"><span class="label">What happened</span>{prose(s['what_happened'])}</div>
<div class="block"><span class="label">Why it matters for Australia</span>{prose(s['why_australia'])}</div>
<div class="lens"><span class="label">Adversary lens · {esc(s['lens_actor'])}</span>{prose(s['adversary_lens'])}</div>
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


def main():
    files = sorted(DATA.glob("*.json"))
    editions = [(f.stem, json.loads(f.read_text(encoding="utf-8"))) for f in files]
    if not editions:
        raise SystemExit("No briefs in data/")
    (DOCS / "archive").mkdir(parents=True, exist_ok=True)
    ids = [e for e, _ in editions]
    for i, (eid, b) in enumerate(editions):
        prev_id = ids[i - 1] if i > 0 else None
        next_id = ids[i + 1] if i + 1 < len(ids) else None
        (DOCS / "archive" / f"{eid}.html").write_text(render_brief(b, prev_id, next_id, "../"), encoding="utf-8")
    latest_id, latest = editions[-1]
    (DOCS / "index.html").write_text(render_brief(latest, ids[-2] if len(ids) > 1 else None, None, ""), encoding="utf-8")
    (DOCS / "archive" / "index.html").write_text(render_archive(editions), encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    old_favicon = DOCS / "favicon.svg"
    if old_favicon.exists():
        old_favicon.unlink()
    print(f"Built {len(editions)} edition(s); latest {latest_id}")


if __name__ == "__main__":
    main()

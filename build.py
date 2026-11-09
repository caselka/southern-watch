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
"""

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

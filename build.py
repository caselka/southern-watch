"""Render every data/YYYY-MM-DD.json brief into the static site in docs/."""
import html
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"

CSS = """
:root{
  --bg:#f3f5f6; --surface:#ffffff; --fg:#17212b; --muted:#5b6873; --rule:#d5dce1;
  --accent:#0d5c63; --accent-soft:#e1efef; --red:#9b2c2c; --red-soft:#f6e6e4;
  --display:"Barlow Condensed","Arial Narrow",sans-serif;
  --body:"Source Serif 4",Georgia,serif;
  --mono:"JetBrains Mono",ui-monospace,Consolas,monospace;
  color-scheme:light;
}
@media (prefers-color-scheme: dark){:root{
  --bg:#10171d; --surface:#172129; --fg:#e3e9ed; --muted:#93a1ab; --rule:#2b3843;
  --accent:#5fbcc3; --accent-soft:#163338; --red:#e58a80; --red-soft:#3a2120; color-scheme:dark}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--body);font-size:17px;line-height:1.6}
.wrap{max-width:46rem;margin:0 auto;padding-block:2rem 4rem;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
nav{display:flex;flex-wrap:wrap;gap:.4rem 1.2rem;font-family:var(--mono);font-size:.75rem;margin-bottom:1.2rem}
header{display:grid;gap:.4rem;border-bottom:3px solid var(--fg);padding-bottom:1rem;margin-bottom:1.5rem}
.dtg{font-family:var(--mono);font-size:.78rem;color:var(--muted);letter-spacing:.04em}
h1{font-family:var(--display);font-weight:700;font-size:clamp(2.2rem,7vw,3.2rem);line-height:1;margin:0;text-transform:uppercase;letter-spacing:.01em}
.sub{color:var(--muted);margin:0;font-size:.95rem}
h2{font-family:var(--display);text-wrap:balance;margin:0}
.label{font-family:var(--display);font-weight:600;font-size:.85rem;letter-spacing:.12em;text-transform:uppercase;color:var(--accent)}
.bluf{background:var(--surface);border:1px solid var(--rule);padding:1.1rem 1.25rem;display:grid;gap:.6rem;margin-bottom:2rem}
.bluf ol{margin:0;padding-left:1.2rem;display:grid;gap:.45rem}
.story{display:grid;gap:.8rem;padding-block:1.6rem;border-top:1px solid var(--rule)}
.story h2{font-size:1.75rem;font-weight:600;line-height:1.1}
.meta{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center}
.tag{font-family:var(--mono);font-size:.72rem;padding:.15rem .5rem;border:1px solid var(--rule);color:var(--muted)}
.tag.hi{border-color:var(--red);color:var(--red)}
.story p{margin:0}
.block{display:grid;gap:.35rem}
.block ul{margin:0;padding-left:1.1rem;display:grid;gap:.35rem}
.lens{background:var(--red-soft);padding:.8rem 1rem;display:grid;gap:.3rem}
.lens .label{color:var(--red)}
.angle{background:var(--accent-soft);padding:.8rem 1rem;display:grid;gap:.3rem}
.src{font-family:var(--mono);font-size:.72rem;color:var(--muted);display:flex;flex-wrap:wrap;gap:.3rem .9rem}
a{color:var(--accent)}
a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.tablewrap{overflow-x:auto}
.cal{width:100%;border-collapse:collapse;font-size:.95rem}
.cal td{padding:.45rem .4rem;border-bottom:1px solid var(--rule);vertical-align:top}
.cal td:first-child{font-family:var(--mono);font-size:.8rem;white-space:nowrap;color:var(--accent);font-variant-numeric:tabular-nums}
.note{font-size:.88rem;color:var(--muted)}
.archive{list-style:none;margin:0;padding:0;display:grid}
.archive li{display:grid;gap:.2rem;padding-block:.9rem;border-top:1px solid var(--rule)}
.archive a{font-family:var(--display);font-size:1.3rem;font-weight:600;text-decoration:none}
"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700'
         '&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=JetBrains+Mono:wght@400;600&display=swap">')

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


def dtg(d: date):
    return f"{d.day:02d}0700K {d:%b}".upper() + f" {d:%y} · {d:%A} {d.day} {d:%B %Y}".upper() + " · AEDT"


def page(title, body, prefix):
    return f"""<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(title)}</title>
<link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml">
{FONTS}
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
{body}
</div>
</body>
</html>
"""


def render_brief(b, prev_d, next_d, prefix):
    d = date.fromisoformat(b["date"])
    nav = [f'<a href="{prefix}index.html">Latest</a>', f'<a href="{prefix}archive/index.html">Archive</a>']
    if prev_d:
        nav.append(f'<a href="{prefix}archive/{prev_d}.html">← {prev_d}</a>')
    if next_d:
        nav.append(f'<a href="{prefix}archive/{next_d}.html">{next_d} →</a>')

    parts = [f"<nav>{''.join(nav)}</nav>",
             f'<header><span class="dtg">{esc(dtg(d))}</span><h1>Southern Watch</h1>'
             '<p class="sub">Foreign and security brief from an Australian vantage point. Each story pairs the '
             'reporting with how Beijing, Moscow, Tehran or Pyongyang tell it.</p></header>',
             '<section class="bluf"><span class="label">Bottom line up front</span><ol>'
             + "".join(f"<li>{inline(x)}</li>" for x in b["bluf"]) + "</ol></section>"]

    for s in b["stories"]:
        tags = (['<span class="tag hi">PRIORITY</span>'] if s.get("priority") else []) + [
            f'<span class="tag">{esc(s["region"]).upper()}</span>',
            f'<span class="tag">CONFIDENCE: {esc(s["confidence"])}</span>']
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
    return page(f"Southern Watch · {d.day} {d:%b %Y}", "\n".join(parts), prefix)


def render_archive(briefs):
    items = []
    for b in reversed(briefs):
        d = date.fromisoformat(b["date"])
        first = b["bluf"][0] if b["bluf"] else ""
        items.append(f'<li><a href="{b["date"]}.html">{d:%A} {d.day} {d:%B %Y}</a>'
                     f'<span class="note">{inline(first)}</span></li>')
    body = ('<nav><a href="../index.html">Latest</a></nav>'
            '<header><span class="dtg">ALL BRIEFS</span><h1>Archive</h1></header>'
            f'<ul class="archive">{"".join(items)}</ul>')
    return page("Southern Watch Archive", body, "../")


FAVICON = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="6" fill="#0d5c63"/>'
           '<text x="16" y="23" font-family="Arial Narrow,Arial,sans-serif" font-weight="700" font-size="18" '
           'text-anchor="middle" fill="#fff">SW</text></svg>')


def main():
    files = sorted(DATA.glob("*.json"))
    briefs = [json.loads(f.read_text(encoding="utf-8")) for f in files]
    if not briefs:
        raise SystemExit("No briefs in data/")
    (DOCS / "archive").mkdir(parents=True, exist_ok=True)
    dates = [b["date"] for b in briefs]
    for i, b in enumerate(briefs):
        prev_d = dates[i - 1] if i > 0 else None
        next_d = dates[i + 1] if i + 1 < len(dates) else None
        (DOCS / "archive" / f"{b['date']}.html").write_text(render_brief(b, prev_d, next_d, "../"), encoding="utf-8")
    latest = briefs[-1]
    (DOCS / "index.html").write_text(render_brief(latest, dates[-2] if len(dates) > 1 else None, None, ""), encoding="utf-8")
    (DOCS / "archive" / "index.html").write_text(render_archive(briefs), encoding="utf-8")
    (DOCS / "favicon.svg").write_text(FAVICON, encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Built {len(briefs)} brief(s); latest {latest['date']}")


if __name__ == "__main__":
    main()

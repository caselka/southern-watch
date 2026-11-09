"""Check a brief JSON file has the shape build.py expects. Exit 1 with a reason if not."""
import json
import sys

STORY_KEYS = {"title", "region", "priority", "confidence", "what_happened", "why_australia",
              "lens_actor", "adversary_lens", "angle", "sources"}


def fail(msg):
    sys.exit(f"invalid brief: {msg}")


path, date = sys.argv[1], sys.argv[2]
try:
    b = json.load(open(path, encoding="utf-8"))
except Exception as e:
    fail(f"not JSON ({e})")
if b.get("date") != date:
    fail(f"date is {b.get('date')!r}, expected {date}")
if not isinstance(b.get("bluf"), list) or not b["bluf"]:
    fail("bluf missing")
if not isinstance(b.get("stories"), list) or not 3 <= len(b["stories"]) <= 8:
    fail("stories missing or wrong count")
for i, s in enumerate(b["stories"]):
    missing = STORY_KEYS - set(s)
    if missing:
        fail(f"story {i} missing {sorted(missing)}")
    if not all(str(x.get("url", "")).startswith("http") for x in s["sources"]):
        fail(f"story {i} has a bad source url")
if not isinstance(b.get("watch_list"), list):
    fail("watch_list missing")
print(f"ok: {len(b['stories'])} stories")

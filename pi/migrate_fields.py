"""Rename the old 'adversary_lens' field to 'state_media_framing' in every brief in data/ (safe to re-run)."""
import json
from pathlib import Path

changed = 0
for f in sorted((Path(__file__).parent.parent / "data").glob("*.json")):
    b = json.loads(f.read_text(encoding="utf-8"))
    touched = False
    for s in b.get("stories", []):
        if "adversary_lens" in s:
            s["state_media_framing"] = s.pop("adversary_lens")
            touched = True
    if touched:
        f.write_text(json.dumps(b, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        changed += 1
print(f"migrated {changed} brief(s)")

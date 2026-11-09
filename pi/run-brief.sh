#!/bin/bash
# Daily Southern Watch run on the Raspberry Pi (called by cron).
# Claude Code (logged in to the owner's Claude subscription) researches and writes
# data/YYYY-MM-DD.json; this script validates it, rebuilds docs/ and pushes to GitHub Pages.
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
cd "$HOME/southern-watch"

# Optional extra edition: run-brief.sh <id-suffix> "<label>", e.g. run-brief.sh updated "Updated sources"
SUFFIX="${1:-}"
LABEL="${2:-}"
DATE=$(TZ=Australia/Sydney date +%F)
DATE_LONG=$(TZ=Australia/Sydney date '+%A %-d %B %Y')
OUT="data/$DATE${SUFFIX:+-$SUFFIX}.json"
LOG_DIR="$HOME/brief-logs"
mkdir -p "$LOG_DIR"
exec >>"$LOG_DIR/$DATE.log" 2>&1
echo "=== start $(date)"

# Push a phone alert if any step fails (needs /usr/local/bin/notify; skipped if absent)
trap 'command -v notify >/dev/null && notify "Southern Watch failed" "Brief for $DATE did not publish. See ~/brief-logs/$DATE.log on the Pi." 4 warning' ERR

git pull -q --rebase

if [ -f "$OUT" ]; then
  echo "brief $OUT already exists, nothing to do"
  exit 0
fi

PROMPT=$(sed -e "s#data/{{DATE}}.json#$OUT#g" -e "s/{{DATE}}/$DATE/g" -e "s/{{DATE_LONG}}/$DATE_LONG/g" pi/prompt.md)

# Private Source Digests from the last 24h (written on the Pi, never committed)
DIGESTS=""
HIST="$HOME/osint/digest/work/history"
if [ -d "$HIST" ]; then
  for f in $(find "$HIST" -name '*.md' -mmin -1500 | sort | tail -3); do
    DIGESTS+=$'\n\n'"### Digest $(basename "$f" .md)"$'\n'"$(cat "$f")"
  done
fi
[ -n "$DIGESTS" ] || DIGESTS="(No Source Digest available today. Rely on web research.)"
echo "digests used: $(find "$HIST" -name '*.md' -mmin -1500 2>/dev/null | wc -l)"
PROMPT="${PROMPT//\{\{DIGESTS\}\}/$DIGESTS}"

timeout 40m claude -p "$PROMPT" \
  --allowedTools "WebSearch" "WebFetch" "Edit(data/**)" \
  --max-turns 80 \
  --output-format text </dev/null | tail -20

python3 pi/validate.py "$OUT" "$DATE"
if [ -n "$LABEL" ]; then
  python3 -c "import json,sys;p=sys.argv[1];b=json.load(open(p));b['edition']=sys.argv[2];json.dump(b,open(p,'w'),indent=2,ensure_ascii=False)" "$OUT" "$LABEL"
fi
python3 build.py

git add data docs
git commit -q -m "Brief for $DATE${LABEL:+ ($LABEL)}"
git push -q
echo "=== published $(date)"
if command -v notify >/dev/null; then
  BLUF=$(python3 -c "import json,re;b=json.load(open('$OUT'));print(re.sub(r'\*\*','',b['bluf'][0]))")
  curl -fsS -H "Title: Southern Watch $DATE${LABEL:+ · $LABEL}" -H "Tags: newspaper" \
    -H "Click: https://caselka.github.io/southern-watch/" \
    -d "$BLUF" "https://ntfy.sh/$(cat /etc/ntfy-topic)" >/dev/null || true
fi

# Keep 60 days of logs
find "$LOG_DIR" -name '*.log' -mtime +60 -delete

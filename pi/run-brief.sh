#!/bin/bash
# Daily Southern Watch run on the Raspberry Pi (called by cron).
# Claude Code (logged in to the owner's Claude subscription) researches and writes
# data/YYYY-MM-DD.json; this script validates it, rebuilds docs/ and pushes to GitHub Pages.
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
cd "$HOME/southern-watch"

DATE=$(TZ=Australia/Sydney date +%F)
DATE_LONG=$(TZ=Australia/Sydney date '+%A %-d %B %Y')
OUT="data/$DATE.json"
LOG_DIR="$HOME/brief-logs"
mkdir -p "$LOG_DIR"
exec >>"$LOG_DIR/$DATE.log" 2>&1
echo "=== start $(date)"

git pull -q --rebase

if [ -f "$OUT" ]; then
  echo "brief for $DATE already exists, nothing to do"
  exit 0
fi

PROMPT=$(sed -e "s/{{DATE}}/$DATE/g" -e "s/{{DATE_LONG}}/$DATE_LONG/g" pi/prompt.md)

timeout 40m claude -p "$PROMPT" \
  --allowedTools "WebSearch" "WebFetch" "Edit(data/**)" \
  --max-turns 80 \
  --output-format text </dev/null | tail -20

python3 pi/validate.py "$OUT" "$DATE"
python3 build.py

git add data docs
git commit -q -m "Brief for $DATE"
git push -q
echo "=== published $(date)"

# Keep 60 days of logs
find "$LOG_DIR" -name '*.log' -mtime +60 -delete

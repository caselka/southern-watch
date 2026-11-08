# Southern Watch

A daily foreign and security brief from an Australian angle. Each story pairs the reporting with how Beijing, Moscow, Tehran or Pyongyang frame it.

**Read it:** https://caselka.github.io/southern-watch/

## How it works

- Every morning (6:40am AEDT) the **Daily brief** GitHub Action runs `generate.py`.
- `generate.py` asks Claude (via the Anthropic API, with web search) to research the last day's news and return the brief as JSON in `data/YYYY-MM-DD.json`.
- `build.py` turns every JSON file into the static site in `docs/` (latest brief, plus an archive). GitHub Pages serves `docs/`.

## Setup

1. Add an Anthropic API key as a repository secret named `ANTHROPIC_API_KEY`
   (Settings → Secrets and variables → Actions → New repository secret).
2. To run it now: Actions → Daily brief → Run workflow.

## Settings

Optional repository variables / env: `SW_MODEL` (default `claude-opus-5-5`), `SW_EFFORT` (default `high`; `medium` is cheaper).

Rebuild the site locally without calling the API: `python build.py`.

# Cloudflare Pages Migration Plan

Tracking issue: https://github.com/bdimech/ParkRun/issues/16  
Branch: `feature/cloudflare-hosting`

## Overview

Migrate the ParkRun dashboard from a local Flask server to a fully static site hosted on Cloudflare Pages. The Python scraper continues to run locally — updated data files are committed and pushed, triggering an automatic Cloudflare Pages redeploy.

## Git Strategy

One commit per step with a clear message. At any point:
- `git log --oneline` to see progress
- `git diff <step~1> <step>` to see exactly what changed
- `git revert` or reset to a previous step if something breaks

---

## Steps

### Step 1 — Data: CSV → JSON converter
**Commit:** `data: add CSV → JSON export script`

- Write `scripts/export_json.py` to read the three CSVs and write `data/*.json`
- No other files change in this step

**Testing:**
- Run the script and validate the JSON structure
- `pytest` unit tests for the converter function

---

### Step 2 — Static HTML shell
**Commit:** `static: add bare HTML shell`

- Create `index.html` at the project root
- Copy structure from the current rendered output — no Flask, no Jinja2, just static placeholders
- `static/style.css` unchanged

**Testing:**
- Open `index.html` directly in a browser — should look correct

---

### Step 3 — Wire up data with JavaScript
**Commit:** `static: load athlete data from JSON via JS`

- Add `static/app.js`
- Fetch the JSON files and populate the athlete list and stats
- Athlete switching via URL params (`?athlete_id=...`)

**Testing:**
- Serve locally: `python -m http.server`
- Verify athlete switching works correctly

---

### Step 4 — Plotly.js charts
**Commit:** `static: render charts client-side with Plotly.js`

- Replace server-rendered Plotly HTML with Plotly.js in `app.js`
- Results chart and location map both rendered in the browser

**Testing:**
- Verify charts render correctly for each athlete via `python -m http.server`

---

### Step 5 — Remove Flask server code
**Commit:** `cleanup: remove Flask server, scraper-only Python remains`

- Delete `app.py`
- Delete `dashboard/routes.py`
- Delete `dashboard/__init__.py`
- Delete `dashboard/charts.py`
- Update `requirements.txt` to scraper-only dependencies

**Testing:**
- Confirm static site still works
- Confirm scraper script still runs independently

---

### Step 6 — Cloudflare Pages config + deploy
**Commit:** `deploy: add Cloudflare Pages config`

- Connect `bdimech/ParkRun` repo to a Cloudflare Pages project
- Set publish directory to project root (no build step required)
- Verify CI/CD deploys automatically on push to `feature/cloudflare-hosting` or `master`

**Testing:**
- Live URL works
- Athlete switching works
- Charts render correctly

---

## Files Affected

| File | Action |
|------|--------|
| `templates/index.html` | Replaced by root `index.html` |
| `static/style.css` | Unchanged |
| `static/app.js` | New — client-side JS |
| `scripts/export_json.py` | New — CSV → JSON converter |
| `data/*.csv` | Converted to `data/*.json` |
| `dashboard/charts.py` | Removed |
| `dashboard/routes.py` | Removed |
| `dashboard/__init__.py` | Removed |
| `app.py` | Removed |
| `requirements.txt` | Trimmed to scraper-only deps |

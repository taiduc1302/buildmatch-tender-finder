# TENDER_FINDER raw development-application sweep — connector pack

Two files do the work:

- **`tenderfinder_dev_app_endpoints.csv`** — the connector registry (16 sources). Edit this, not the script, to add/disable sources or paste verified URLs.
- **`tenderfinder_raw_sweep.py`** — the collector. Reads the registry, pulls **raw** records, writes one Excel + one CSV + per-connector raw JSON, and prints a run log telling you which connectors are live.

This is the **COLLECT** layer only. It does not score, filter, or judge TENDER_FINDER-fit — that is the next (prompt) layer. Raw stays raw so it can be re-scored any time. Access is sanctioned open-data APIs only (ArcGIS REST, Opendatasoft); no scraping.

---

## Run it

```bash
pip install openpyxl          # requests is optional but recommended
pip install requests

# 1) Fast check — resolve every endpoint, pull NO data. Run this first.
python tenderfinder_raw_sweep.py --probe

# 2) Full sweep of everything enabled
python tenderfinder_raw_sweep.py

# 3) Just the confirmed flagships
python tenderfinder_raw_sweep.py --only twp_langley_devactivity,maple_ridge_devapps,van_building_permits,van_city_projects

# Output lands in ./tenderfinder_raw_out/<date>/  (tenderfinder_raw_sweep.xlsx, .csv, raw_json/, run_log.json)
```

`--probe` is the important one. It shows, per connector, the exact REST/ODS layer URL it resolved — so you can see what is live and what needs a manual endpoint before you commit to a full pull.

---

## Connector status — confirmed vs to-verify (honest disclosure)

These were checked against the live public portals. "Confirmed" = hub/REST root verified and (where noted) the exact dataset verified. "To-verify" = root is real but the script resolves the exact dev-application layer at runtime; first run tells you if it found one.

**Confirmed dataset/endpoint (should return rows on first run):**
- `twp_langley_devactivity` — Township of Langley Development Activity Status (itemId + layer pinned)
- `maple_ridge_devapps` — Maple Ridge Development Applications (itemId + layer pinned)
- `van_building_permits` — Vancouver Issued Building Permits (slug pinned)
- `van_city_projects` — Vancouver City Projects (slug pinned)
- `abbotsford_devapps` — Abbotsford Development Application Areas (slug confirmed)
- `new_west_currentdev` — New Westminster Current Developments + building permits (confirmed)
- `port_coquitlam_landdev` — Port Coquitlam "Lands and Development" MapServer (REST confirmed)

**Root confirmed, exact layer resolved at runtime (verify what comes back):**
- `surrey_devapps` — Surrey public hub `data.surrey.ca` (this is the open hub, separate from the **blocked internal** `gisservices.surrey.ca`). COSMOS-fed; the script finds the dataset via the hub's DCAT feed.
- `city_langley_devapps`, `burnaby_devapps`, `coquitlam_devapps`, `delta_devapps` — hub roots confirmed; dev-application layer matched by keyword at runtime. Burnaby and Delta in particular publish thinner per-application detail, and Delta's portal is brand new (launched Dec 2025) — check the matched layer's columns.
- `dnv_devapps` — District of North Vancouver GEOweb MapServer confirmed live, but it is mostly infra/hazard layers; a clean dev-application layer may not exist. Low priority (secondary geography).

**Gated — do not enable yet:**
- `surrey_futureworks` — Surrey FutureWorks capital/servicing layers. **Blocked pending the TENDER_FINDER office-network access test** (the critical gate from the plan). Once the office machine confirms reach, paste the verified MapServer URL into the `endpoint` column and change `DISABLED_PENDING_OFFICE_NETWORK`.

---

## What the output is for

`tenderfinder_raw_sweep.xlsx` is the normalized raw pile: one row per application, with convenience columns (`address`, `native_id`, `app_type_or_stage`) plus the full original record in `raw_json`. This file is the **input to Prompt P1** (the universal scope-scoring prompt). You collect wide and cheap here; P1 turns it into a scored TENDER_FINDER lead list, and P5 dedupes across municipalities and writes Example Reviewer's digest.

---

## Two time-sensitive reminders carried over from the plan

1. **BC Major Projects Inventory goes offline ~June 30, 2026.** It is not one of these API connectors (it's a capital-plan source), but if the Q3 2025 XLS has not been downloaded yet, grab it now — it's the final issue.
2. **Surrey FutureWorks stays disabled** until the office-network test passes. Everything else here works from any network.

Nothing here replaces Example Coordinator's manual tracking yet. Per the discipline: run this in parallel, prove ≥3 useful leads/month per source and three consecutive weeks of full capture, then automate the sources that earn it.

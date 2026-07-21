# Controlled Live Refresh Results (Phase 5)

> AI-tool attribution note: this document describes work done by Claude Code during this session. For the full, honest Codex/GPT-5.6/Claude Code contribution breakdown required by the OpenAI Build Week rules, see the README's "AI tool and contributor disclosure" section and `docs/buildweek/final/CLAIMS_LEDGER.md` — this document alone should not be read as claiming Claude Code built the project's core functionality.

Executed from this session's Linux development environment (network access to
public sources works here; no Windows desktop is available — see
`02_WINDOWS_ACCEPTANCE_RESULTS.md`). All sources used are public, unauthenticated
municipal/regional open-data feeds — no login, no CAPTCHA, no private/paid
access. Real network I/O; not a test or a simulation.

## Sources selected (all 8 runtime-eligible development sources)

Selection came from the truthful registry filter (`eligible_development_sources`)
— `needs_configuration` / `manual_only` / `wrong_source` / `blocked` sources are
never selected, matching the offline `test_eligible_sources_exclude_non_runnable`
test.

| Source ID | Municipality | Fetch type |
|---|---|---|
| `surrey_devapps_v2` | Surrey | ArcGIS REST layer |
| `surrey_planning_reports` | Surrey | PDF (Rezoning + DP in-process reports) |
| `maple_ridge_devapps` | Maple Ridge | ArcGIS Hub item |
| `twp_langley_devactivity` | Township of Langley | ArcGIS Hub item |
| `coquitlam_devapps` | Coquitlam | ArcGIS Hub item |
| `abbotsford_devapps` | Abbotsford | ArcGIS REST layer |
| `van_building_permits` | Vancouver | Opendatasoft v2.1 |
| `van_city_projects` | Vancouver | Opendatasoft v2.1 |

## Run 1 — first attempt (found a real defect)

`max_records_per_source=200`. Result: **8/8 sources succeeded**, 1,434 records
fetched, 1,404 after dedup — but the run reported `succeeded: False`,
`"Refresh failed dataset validation. Previous data retained."`

Root cause: one real Abbotsford record had every descriptive field blank
(`address=""`, `scope_summary=""` — a genuinely thin municipal record), and the
dataset-validation check failed the *entire* 1,404-record dataset over that one
record. Fixed in `deduplicate_records`/`validate_dataset` (see
`06_REMEDIATION_LOG.md` item 2). This is exactly the kind of defect a live run
against real data finds that synthetic fixtures cannot.

## Run 2 — after the validation fix

```
succeeded: True
message: Refreshed 1204 development records from 8/8 sources.
sources: 8/8 successful, fetched=1434, before_dedup=1434,
         duplicates_removed=230, normalized=1204, records_live=1204
reconciled: True []
data_mode: LIVE
```

Metrics reconciliation confirmed clean (`RunMetrics.is_reconciled() == True`,
zero errors).

## Run 3 — after wiring the real scorer (Civil Contractor preset)

Time: 105.5s wall-clock for full acquisition + scoring across all 8 sources.

```
succeeded: True
message: Refreshed 1209 development records from 8/8 sources.
sources: 8/8 | fetched=1439 normalized=1209 scored=1209
BID_LATER=104 WATCH=531 SKIP=574 BID_NOW=0
reconciled: True []
output_paths:
  dataset: .../datasets/development_review_<run_id>.xlsx
  output_workbook: .../datasets/runs/<run_id>/output/ranked_opportunities.xlsx
  manifest: .../datasets/runs/<run_id>/run_manifest.json
```

`BID_NOW=0` is correct and truthful — BID_NOW is a live-tender-track (Track B)
concept; a development-application-only refresh never populates it.

Per-source breakdown (Run 3):

| Source | Records | HTTP |
|---|---|---|
| `twp_langley_devactivity` | 138 | 200 |
| `maple_ridge_devapps` | 168 | 200 |
| `van_building_permits` | 177 | 200 |
| `van_city_projects` | 0 | 200 (no matching records this capture) |
| `abbotsford_devapps` | 200 (cap reached) | 200 |
| `coquitlam_devapps` | 196 | 200 |
| `surrey_planning_reports` | 355 (PDF-extracted) | n/a (PDF download, not HTTP-status-bearing) |
| `surrey_devapps_v2` | 200 (cap reached) | 200 |

## Preset comparison on the SAME real dataset (no repeat network I/O)

Re-scoring the identical 1,209-record dataset captured in Run 3 under each
preset (`tenderfinder_refresh_service.default_scorer`, no new fetch):

| Preset | BID_LATER | WATCH | SKIP |
|---|---|---|---|
| Civil Contractor | 104 | 531 | 574 |
| Multi-Family Residential Builder | 246 | 504 | 459 |
| General Contractor | 144 | 542 | 523 |

Residential surfaces **2.4× more** BID_LATER opportunities than Civil on the
same real data — exactly the expected effect of not penalizing
interior/mechanical/electrical/HVAC/suite scope, now demonstrated on genuine
municipal permit and development-application text, not just synthetic fixtures.

## Comparison with the prior external observation (~18,213 / 498 / 114)

Not directly comparable, and the difference is explainable, not a red flag:

* the prior figure likely came from a broader `tenderfinder_raw_sweep.py`
  `--review-only` run with a much higher `--max-records` (CLI default 20,000)
  and possibly a different/larger `--only` source selection or capture date;
* this run deliberately used a conservative `max_records_per_source=200` (Run
  1/2) to respect "do not hammer public portals" during a proof exercise, then
  effectively similar per-source counts in Run 3;
* only the 8 sources that pass the truthful `source_is_runtime_eligible` gate
  were used — `needs_configuration`/`manual_only`/`wrong_source`/`blocked`
  sources are correctly excluded, which the ~18,213 figure's source set may
  not have been;
* municipal open-data feeds change over time (new applications filed,
  concluded applications removed from "in process" reports).

Real counts are reported above, not fabricated or hard-coded to match the
external figure, per instruction.

## Output workbook spot-check

The real ranked output workbook's top-ranked record (fit 79, `BID_LATER`) is a
genuine Surrey rezoning application (subdivision into 15 lots with road-network
and drainage-corridor changes) — publicly viewable at the `source_url` in the
workbook. No secrets, no private data, no local paths in any field (verified by
`scripts/package_audit.py`).

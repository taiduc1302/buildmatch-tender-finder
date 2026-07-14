# RUN_ALL_SOURCES_SAFE.md

## 1. Purpose

This file is the safe operating runbook for the TENDER_FINDER Tender Intelligence controlled runner.

It defines what can be run now, what must not be run yet, the required order of operations, expected outputs, stop conditions, and the final checklist before any workbook write is allowed.

This file applies to the controlled runner patch attempt only. It is not approval to run production automation.

Reference packages:

- Base project: `0623 v4 Tender Finder Final.zip`
- Current patched code attempt: `TENDER_FINDER_controlled_runner_patch_attempt_1_hotfix.zip`
- Folder rules: `TENDER_FINDER_Final_Folder_Guide.docx`

Expected location:

```text
01 Code / CONNECTOR_SWEEP / RUN_ALL_SOURCES_SAFE.md
```

---

## 2. Current hotfix status

The current accepted hotfix is a patch attempt, not production-ready automation.

Accepted status:

- `tenderfinder_raw_sweep.py` compiles.
- `tenderfinder_guards.py` compiles.
- `tenderfinder_master_io.py` compiles.
- `tenderfinder_source_registry.py` compiles.
- `tenderfinder_guards.py` self-check passed.
- `--sync-registry` works.
- Township of Langley and Maple Ridge pinned endpoints are fixed.
- Sources marked `manual_p3_only` now short-circuit before any network call.
- Sources marked `access_test_required` now short-circuit before any network call.
- Duplicate `TWP-LANGLEY-RO100158` now keeps `COUNCIL 3RD READING - PENDING` as the live stage.

Important: this status only confirms the limited hotfix checks above. It does not confirm that a full live sweep or master write is safe.

---

## 3. Hard safety rules

Do not run a live all-source sweep yet.

Do not run any all-source `--write-master` command yet.

Do not run Tier 1 or Tier 2 `--write-master` yet.

Do not overwrite this workbook:

```text
00 Master / TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx
```

Any workbook write must happen only on a copied v7 workbook:

```text
00 Master / TENDER_FINDER_Tender_Intelligence_Working_Master_v7.xlsx
```

Before any write is considered, the v7 workbook must be a copied working file created from v6. The v6 workbook is the protected source file and must remain unchanged.

Do not scrape login-only portals.

Do not use paid sources unless access is configured.

Do not silently fall back to similar datasets.

Do not treat building permits as Future Projects.

Do not mix Active Tenders with Future Projects.

Do not treat uncertain AI extraction as verified. Any uncertain AI extraction must be marked:

```text
Needs Review
```

Keep raw outputs and run logs for QA.

---

## 4. Folder rules

Use active folders only:

```text
00 Master
01 Code
02 Runbooks And Plans
03 Active and QA Runbooks
04 RESEARCH REFERENCE
05_PROMPTS
```

Do not work from `_ss`. The `_ss` folder is snapshot/archive only.

Folder usage:

| Folder | Use |
|---|---|
| `00 Master` | Current master workbook only. Keep v6 protected. Use copied v7 only for write testing. |
| `01 Code` | Executable scripts, connector registries, and technical instructions. |
| `01 Code / CONNECTOR_SWEEP` | Controlled runner, connector registry, helper modules, run logs, and this safe runbook. |
| `02 Runbooks And Plans` | Operating instructions, plans, process notes, and next-step documents. |
| `03 Active and QA Runbooks` | Active tender setup and quality-control workbooks. |
| `04 RESEARCH REFERENCE` | Research, evidence, source background, and proof-of-value reports. |
| `05_PROMPTS` | Reusable AI prompts and prompt review materials. |
| `_ss` | Snapshot/archive only. Do not run from here. |

---

## 5. Commands safe to run now

All commands below assume the hotfix files have been applied into the active connector folder and the command prompt is opened from the project root.

First move into the active runner folder:

```bash
cd "01 Code/CONNECTOR_SWEEP"
```

### 5.1 List connectors

Safe because it reads the connector CSV and prints the connector table. It does not call the network and does not write to the workbook.

```bash
python tenderfinder_raw_sweep.py --list
```

Expected output:

- A connector table with columns similar to:
  - `SOURCE_ID`
  - `TIER`
  - `FETCH TYPE`
  - `ACCESS STATUS`
  - `ROUTE`
- Expected current count: `16 connectors.`
- No workbook changes.
- No live sweep.
- No master write.

---

### 5.2 Sync registry report

Safe because it compares the workbook Source Register / Run Queue against the connector CSV and writes a sync report. It must not modify the registry CSV or the workbook.

Use v6 only as a read-only source for this report:

```bash
python tenderfinder_raw_sweep.py --sync-registry --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx" --out sync_report.csv
```

Expected output:

- Console line similar to:

```text
Sync report -> sync_report.csv  (... sources)
```

- Current hotfix check previously reconciled `71 sources`.
- A `sync_report.csv` report is created in the runner folder.
- No registry CSV changes.
- No workbook changes.
- No network calls.
- No master write.

Review the sync report before moving to probe commands.

---

### 5.3 Township of Langley / Maple Ridge probe

Safe as a targeted probe. This checks the pinned endpoint resolution only and does not pull records for loading.

```bash
python tenderfinder_raw_sweep.py --only twp_langley_devactivity,maple_ridge_devapps --probe --out tol_maple_ridge_probe.xlsx
```

Expected output:

- Console header:

```text
TENDER_FINDER controlled runner - PROBE
```

- Two selected connectors:
  - `twp_langley_devactivity`
  - `maple_ridge_devapps`
- Each source should show a resolved pinned endpoint.
- Probe summary should show:

```text
PROBE SUMMARY: resolved OK 2/2
```

- `tol_maple_ridge_probe.xlsx` is created.
- `raw_runs/<date>/logs/run_log.json` is created.
- No master write.

Stop if either source does not resolve to the expected pinned development-application endpoint.

---

### 5.4 Manual / P3 short-circuit dry-run

Safe because these sources should short-circuit before any network call.

```bash
python tenderfinder_raw_sweep.py --only city_langley_devapps,burnaby_devapps,abbotsford_devapps,surrey_futureworks --dry-run --max-records 1
```

Expected output:

- `city_langley_devapps` should return `p3_extract_required` and route to `Run_Queue`.
- `burnaby_devapps` should return `p3_extract_required` and route to `Run_Queue`.
- `abbotsford_devapps` should return `p3_extract_required` and route to `Run_Queue`.
- `surrey_futureworks` should return `access_test_required` and route to `Run_Queue`.
- Pulled records should be `0` for these short-circuit sources.
- No network calls to the manual/P3 or access-test sources.
- `raw_runs/<date>/logs/run_log.json` is created.
- No master write.

Stop if any manual/P3 or access-test source attempts a network call.

---

### 5.5 Tier 1 dry-run only

Safe only as a dry-run after list, sync-registry, targeted probe, and manual/P3 short-circuit checks have passed.

Do not add `--write-master`.

```bash
python tenderfinder_raw_sweep.py --tier 1 --dry-run --max-records 500
```

Expected output:

- Console header:

```text
TENDER_FINDER controlled runner - DRY-RUN
```

- Run summary showing:
  - dev/capital leads routed for `Future_Projects`
  - quarantined rows routed for `Rejected_Archive`
  - P3/manual/queue sources routed for `Run_Queue`
- Raw outputs saved under:

```text
01 Code / CONNECTOR_SWEEP / raw_runs / <date>
```

- Expected raw subfolders may include:
  - `json`
  - `csv`
  - `logs`
- Console should state:

```text
DRY-RUN: no master write. Classified leads/rejects above.
```

- No workbook changes.
- No master write.

Review all logs and raw outputs before any writer test is considered.

---

## 6. Commands not allowed yet

The following commands are not allowed at this stage.

### 6.1 Any all-source write-master

Do not run:

```bash
python tenderfinder_raw_sweep.py --write-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7.xlsx"
```

Reason: no full live sweep has been verified, and all-source writing has not been QA-approved.

---

### 6.2 Tier 1 write-master

Do not run:

```bash
python tenderfinder_raw_sweep.py --tier 1 --write-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7.xlsx"
```

Reason: Tier 1 dry-run logs must be reviewed first, and writer testing must happen only on a copied v7 workbook.

---

### 6.3 Tier 2 write-master

Do not run:

```bash
python tenderfinder_raw_sweep.py --tier 2 --write-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7.xlsx"
```

Reason: Tier 2 includes sources with known unresolved or rejected conditions, including Vancouver ODS slug verification needs, wrong-layer sources, trailing/context sources, and manual/P3 routes.

---

### 6.4 Live full sweep without prior probe

Do not run any broad live pull before source-specific probes and log review.

Do not run:

```bash
python tenderfinder_raw_sweep.py --dry-run
```

Do not run:

```bash
python tenderfinder_raw_sweep.py
```

Reason: unfiltered commands can select too many sources and create uncontrolled live pulls or confusing QA outputs.

---

### 6.5 Any write to v6

Never run:

```bash
python tenderfinder_raw_sweep.py --write-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx"
```

Reason: v6 is protected and must not be overwritten.

---

## 7. Required order of operations

Follow this order exactly.

1. List connectors.
2. Run sync-registry report.
3. Probe targeted sources.
4. Run dry-run only.
5. Review logs and raw outputs.
6. Only then test the writer on a copied v7 workbook.

Do not skip steps.

Do not move to a workbook write if any stop condition is triggered.

---

## 8. Exact example command sequence

Run from the project root:

```bash
cd "01 Code/CONNECTOR_SWEEP"
```

Step 1 - list:

```bash
python tenderfinder_raw_sweep.py --list
```

Step 2 - sync registry report:

```bash
python tenderfinder_raw_sweep.py --sync-registry --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx" --out sync_report.csv
```

Step 3 - targeted probe for Township of Langley and Maple Ridge:

```bash
python tenderfinder_raw_sweep.py --only twp_langley_devactivity,maple_ridge_devapps --probe --out tol_maple_ridge_probe.xlsx
```

Step 4 - manual/P3 and access-test short-circuit dry-run:

```bash
python tenderfinder_raw_sweep.py --only city_langley_devapps,burnaby_devapps,abbotsford_devapps,surrey_futureworks --dry-run --max-records 1
```

Step 5 - Tier 1 dry-run only:

```bash
python tenderfinder_raw_sweep.py --tier 1 --dry-run --max-records 500
```

Step 6 - review outputs:

```text
01 Code / CONNECTOR_SWEEP / sync_report.csv
01 Code / CONNECTOR_SWEEP / tol_maple_ridge_probe.xlsx
01 Code / CONNECTOR_SWEEP / raw_runs / <date> / logs / run_log.json
01 Code / CONNECTOR_SWEEP / raw_runs / <date> / json
01 Code / CONNECTOR_SWEEP / raw_runs / <date> / csv
```

No writer command is included in the safe sequence.

---

## 9. Expected outputs by command

| Command | Expected output | Must not happen |
|---|---|---|
| `--list` | Prints connector table; expected `16 connectors.` | No network call; no workbook write. |
| `--sync-registry` | Creates `sync_report.csv`; prints summary counts; previous hotfix check reconciled `71 sources`. | Must not edit connector CSV or workbook. |
| TOL / Maple Ridge `--probe` | Resolves `twp_langley_devactivity` and `maple_ridge_devapps`; expected `resolved OK 2/2`; creates probe workbook and run log. | Must not pull records for loading; must not write workbook. |
| manual/P3 short-circuit dry-run | Returns `p3_extract_required` or `access_test_required`; pulled records should be `0`; creates run log. | Must not call manual/P3/access-test endpoints. |
| Tier 1 dry-run | Pulls/classifies allowed Tier 1 dry-run records; creates raw outputs and run log; prints `DRY-RUN: no master write.` | Must not write workbook; must not include `--write-master`. |

---

## 10. Stop conditions

Stop immediately if any of the following occurs.

### Wrong layer

Stop if a source resolves to or pulls a layer that is not a real development-application or relevant capital/future-project source.

Examples of rejected/wrong-layer history to preserve:

- Surrey API previously pulled the wrong `Subdivision Markers` layer.
- Coquitlam previous pull was neighbourhood-plan polygons.
- District of North Vancouver hazard/DPA polygons are rejected/quarantined.
- Port Coquitlam ALR polygons are rejected/quarantined.

Action: quarantine/reject. Do not load to `Future_Projects`.

---

### Schema too thin

Stop if the layer does not provide enough useful fields to support lead review.

Action: classify as too thin, keep raw output for QA, and do not write to the master.

---

### Access blocked

Stop if a source requires login, paid access, office-network access, or any gated access that is not configured.

Action: route to `Run_Queue` for access testing. Do not scrape.

Current access-test example:

```text
surrey_futureworks
```

---

### Slug not found

Stop if an Opendatasoft slug is not found.

Action: verify the exact dataset manually. Do not silently fall back to a similar dataset.

Current Vancouver ODS slugs requiring manual verification:

```text
van_rezoning
van_devpermits
```

---

### manual_p3_only

Stop automated fetching if the source is marked:

```text
manual_p3_only
```

Action: route to `Run_Queue`. Do not fetch until a proper P3/manual extractor exists and is approved.

Current examples:

```text
city_langley_devapps
burnaby_devapps
abbotsford_devapps
```

---

### Duplicate risk

Stop before writing if duplicates or stage conflicts are detected.

Known duplicate/stage issue to preserve:

```text
TWP-LANGLEY-RO100158
```

Current accepted live stage:

```text
COUNCIL 3RD READING - PENDING
```

Action: confirm the pending live milestone is retained and prior stages are preserved in Notes as much as the current writer supports.

---

## 11. Master workbook protection rule

The following workbook must not be overwritten:

```text
00 Master / TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx
```

This file is the protected operational source workbook.

Do not pass the v6 path to `--write-master`.

Do not save over v6 manually.

Do not use v6 for writer testing.

---

## 12. v7-only workbook write rule

Any workbook write must happen only on a copied v7 workbook:

```text
00 Master / TENDER_FINDER_Tender_Intelligence_Working_Master_v7.xlsx
```

The v7 workbook must be a copied working file based on v6.

The first writer test must be limited and reversible.

The first writer test must not be all-source.

The first writer test must only happen after list, sync, probe, dry-run, and log review are complete.

---

## 13. Current known limitations

Known limitations that remain open:

- No full live sweep has been verified.
- Active_Tenders writer is placeholder / append-only.
- P3 extractor is not implemented.
- ODS slugs for Vancouver rezoning and development permits need manual verification.
- Conditional formatting may not extend beyond row 201.
- Full preservation of all prior duplicate stages in Notes may still need improvement.

Additional caution:

- Surrey public development applications endpoint is still not fully re-pinned and verified.
- Surrey FutureWorks remains access-test-required.
- City of Langley and Burnaby are manual/P3 routes, not API failures.
- Delta and New Westminster permit-style sources are trailing/context unless verified otherwise.

---

## 14. Final checklist before allowing any --write-master

Do not allow any `--write-master` command unless every item below is complete.

```text
[ ] Confirm work is happening from 01 Code / CONNECTOR_SWEEP, not _ss.
[ ] Confirm v6 exists and is protected from overwrite.
[ ] Create a copied workbook named TENDER_FINDER_Tender_Intelligence_Working_Master_v7.xlsx.
[ ] Confirm --list passes and shows the expected connector table.
[ ] Confirm --sync-registry passes and the sync report has been reviewed.
[ ] Confirm Township of Langley / Maple Ridge probe resolves OK 2/2.
[ ] Confirm manual_p3_only sources short-circuit with no network calls.
[ ] Confirm access_test_required sources short-circuit with no network calls.
[ ] Run Tier 1 dry-run only, with no --write-master.
[ ] Review raw_runs/<date>/logs/run_log.json.
[ ] Review raw JSON/CSV outputs for wrong layer, thin schema, and trailing/context data.
[ ] Confirm no Vancouver ODS slug_not_found source is included in a write set.
[ ] Confirm no wrong-layer source is included in a write set.
[ ] Confirm no building-permit-only source is routed to Future_Projects.
[ ] Confirm duplicate risks are reviewed, including TWP-LANGLEY-RO100158.
[ ] Confirm COUNCIL 3RD READING - PENDING remains the live stage for TWP-LANGLEY-RO100158.
[ ] Confirm all uncertain AI-extracted rows are marked Needs Review, not Verified.
[ ] Confirm the first writer test is limited, reversible, and on copied v7 only.
[ ] Confirm a backup exists before any workbook save.
[ ] Confirm Active_Tenders append-only limitation is understood and not treated as complete automation.
```

If any checklist item fails, do not run `--write-master`.

---

## Final operating rule

Run list, sync, probe, and dry-run first. Review outputs and stop conditions. Only after that, test the writer on a copied v7 workbook. Never overwrite v6.

---

## Patch 4 link preflight gate

Patch Attempt 4 adds the accepted `TENDER_FINDER_Link_Checker_v2.1.0` as a preflight/source-health gate inside the controlled runner.

The preflight must run through `tenderfinder_raw_sweep.py`, not only as a standalone checker.

Safe preflight command from `01 Code / CONNECTOR_SWEEP`:

```bash
python tenderfinder_raw_sweep.py \
  --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx" \
  --preflight-links \
  --preflight-no-search \
  --preflight-output-dir "./link_audit_out" \
  --preflight-timeout 20 \
  --preflight-retries 2 \
  --preflight-workers 6
```

Sandbox / no-network validation command:

```bash
python tenderfinder_raw_sweep.py \
  --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx" \
  --preflight-links \
  --preflight-no-search \
  --preflight-output-dir "./link_audit_out_dry" \
  --preflight-timeout 20 \
  --preflight-retries 2 \
  --preflight-workers 6 \
  --dry-run
```

Required preflight output files:

- `TENDER_FINDER_Source_Register_URL_Live_Audit.csv`
- `TENDER_FINDER_Source_Register_URL_Live_Audit.xlsx`
- `TENDER_FINDER_Source_Register_Fix_Queue.csv`
- `TENDER_FINDER_Source_Register_Replacement_Candidates.csv`
- `TENDER_FINDER_Source_Register_Cleaned_For_Script.csv`
- `TENDER_FINDER_Link_Check_Run_Log.txt`
- `TENDER_FINDER_Link_Check_Debug_Log.txt`

The master workbook uses the Source Register URL header `URL / Portal`. Patch 4 supports this header as a valid URL column alias.

Preflight routing rules:

- Exclude from simple scraping unless `--include-broken-sources` is provided:
  - `BROKEN_DNS`
  - `BROKEN_SSL`
  - `BROKEN_404`
  - `BROKEN_OTHER`
  - `FIX_URL_FIRST`
  - `NO_REPLACEMENT_FOUND`
- Do not automatically delete or treat these as broken:
  - `FORBIDDEN_BUT_LIKELY_VALID` = review / connector-safe
  - `NEEDS_CONNECTOR_NOT_SIMPLE_SCRAPE` = connector workflow
  - `LOGIN_OR_MANUAL` = manual workflow / Run Queue
  - `TIMEOUT_RETRY_NEEDED` = retry / review

Safety notes:

- Preflight reads the master workbook but does not save it.
- Preflight does not delete Source Register rows.
- Preflight does not silently replace original URLs.
- Original URL, normalized URL, final redirect URL, error details, classification reason, retry count, safe-to-scrape, and manual-review flags are preserved in output files.
- `TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx` remains protected and must not be overwritten.

---

## Tavily replacement-search preflight

Patch 4.1 defaults replacement search to Tavily. The key is read from `TAVILY_API_KEY` or local `.env.tenderfinder.local` in this folder.

Run without replacement search:

```bash
python tenderfinder_raw_sweep.py \
  --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx" \
  --preflight-links \
  --preflight-no-search \
  --preflight-output-dir "./link_audit_out"
```

Run with Tavily replacement search:

```bash
python tenderfinder_raw_sweep.py \
  --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx" \
  --preflight-links \
  --preflight-search-provider tavily \
  --preflight-output-dir "./link_audit_out"
```

If the key is missing, invalid, exhausted, or rate-limited, the checker will mark that as a search API/key/quota issue such as `SEARCH_API_QUOTA_OR_RATE_LIMIT`, not as proof that the source URL is good or bad.

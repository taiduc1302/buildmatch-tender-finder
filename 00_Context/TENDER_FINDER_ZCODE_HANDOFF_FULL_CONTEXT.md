# TENDER_FINDER Tender Finder - ZCode Handoff Full Context

**Current date/context:** after Patch 5.3 Live Hardened package-level verification.  
**Latest package to start from:** `TENDER_FINDER_Patch_5_3_Live_Hardened (1).zip`  
**Project:** Example Civil Contractor tender / future-project intelligence system for civil / earthworks opportunities in Lower Mainland, BC.

---

## 1. What this project is trying to build

TENDER_FINDER needs a practical tender/future-project intelligence workflow that finds civil / earthwork opportunities before or when they become bid opportunities.

TENDER_FINDER fit profile:

- civil / earthworks contractor,
- excavation,
- site servicing,
- underground utilities,
- roadworks,
- subdivision development,
- storm / sanitary / water infrastructure,
- industrial / institutional / multifamily projects only when there is a clear civil scope.

The system is not meant to collect every construction record. It must separate:

- strong TENDER_FINDER-fit future projects,
- watchlist projects,
- noisy bulk permit records,
- trailing/context-only records,
- active tenders / portal opportunities,
- manual / login / paid sources,
- rejected or wrong-layer sources.

Main workbook routes / logical buckets:

- `Future_Projects`
- `Active_Tenders`
- `Bulk_Intake_Raw`
- `Run_Queue`
- `Rejected_Archive`
- `Paid_Intelligence`
- `Manual_Portal_Workflow`

Important principle: **do not treat raw records as sales leads until they are filtered, scored, routed, and reviewed.**

---

## 2. Latest version and current status

Latest accepted package-level build:

```text
TENDER_FINDER_Patch_5_3_Live_Hardened (1).zip
```

Status:

```text
Package-level / regression-level: ACCEPTED
Live-production proof: PARTIAL / still requires Windows live runs
Production master write: NOT YET DONE except copied-master tests and show-intermediate master
```

Patch 5.3 fixed the main package/regression issues:

- shipped `test_outputs_p53/`,
- `tests/run_regression.py --all` passes 24/24 from fresh unzip,
- `--verify-outputs --output-dir "..\..\test_outputs_p53"` passes 7/7,
- offline fixture mode no longer hangs by trying live fetch first,
- Surrey parser unit tests pass 16/16 on synthetic PDFs,
- Vancouver routing/gate unit tests pass 21/21,
- Windows console Unicode crash was addressed at code/package level,
- package has no real `.env.tenderfinder.local`; only `.env.tenderfinder.local.example`.

But ZCode must understand the difference:

- Regression/offline fixture tests prove code paths, output generation, promotion, dedupe, and packaging.
- They do **not** prove current live municipal websites still parse correctly.
- Live proof must be run on the Windows/TENDER_FINDER machine against real endpoints.

---

## 3. Development history already completed

### Phase A - Manual-first strategy and source model

Originally the project was planned around manual validation before full automation. The goal was to avoid building code around bad/noisy data.

Initial target was Surrey development applications and civil-signal sources, then expand to other municipalities and active tender sources.

Core design decisions:

- keep a master workbook,
- route candidates into meaningful sheets,
- preserve rejected/held items with reasons,
- do not silently overwrite master,
- always prove outputs with row counts and logs.

### Phase B - Source Register expansion

Source Register was expanded significantly.

Important numbers from the source expansion stage:

```text
Source_Register rows expanded: 68 -> 159
Added rows: 91
Dirty URLs cleaned/moved to notes: 47
Blank URL rows retained: 12
Dirty URL strings remaining in URL/Portal fields: 0
```

Routing summary from the expanded Source Register:

```text
Active_Tenders: 51
Future_Projects: 72
Run_Queue: 13
Bulk_Intake_Raw: 14
Paid_Intelligence: 9
```

Important distinction:

```text
159 Source_Register rows != 159 coded connectors
live URL != harvestable source
raw record != TENDER_FINDER lead
```

### Phase C - Link preflight / URL checker

A live link checker/preflight was built to classify URLs and generate audit outputs.

Expected preflight files:

```text
TENDER_FINDER_Source_Register_URL_Live_Audit.csv
TENDER_FINDER_Source_Register_URL_Live_Audit.xlsx
TENDER_FINDER_Source_Register_Fix_Queue.csv
TENDER_FINDER_Source_Register_Replacement_Candidates.csv
TENDER_FINDER_Source_Register_Cleaned_For_Script.csv
TENDER_FINDER_Link_Check_Run_Log.txt
TENDER_FINDER_Link_Check_Debug_Log.txt
```

The preflight system can classify URLs as OK, redirected, needs connector, manual/login, forbidden likely valid, broken, etc.

Patch 5.3 also addressed a Windows console/logging problem where Unicode arrows like `→` caused `UnicodeEncodeError` under PowerShell/cp1252.

### Phase D - Connector sweep and first real connector set

A controlled connector runner was created around:

```text
tenderfinder_raw_sweep.py
```

The runner supports:

- connector listing,
- selected connector runs with `--only`,
- review-only mode,
- source summary output,
- review workbooks,
- demo workbook generation,
- dry-run / preflight modes,
- copied-master promotion with audit/dedupe.

The package currently lists 17 coded connector entries, but not all are real working connectors. Some are honest status stubs such as `needs_exact_url`, `p3_extract_required`, or `disabled_wrong_layer`.

### Phase E - Patch 5.0 stabilization

Patch 5.0 focused on reproducibility, not adding more sources.

Patch 5.0 goals:

- restore/prove Surrey workflow,
- protect Township Langley and Maple Ridge,
- add regression tests,
- add source-level summary,
- fix long path output writing,
- add `review_decision`,
- add `--promote-reviewed`,
- prove dedupe,
- prevent Vancouver permit noise from dominating demo outputs,
- prevent false success reports.

Patch 5.0 verified package showed:

```text
Surrey fixture rows: 20
Township Langley rows: 778
Maple Ridge rows: 879
Source summary rows: 3
Demo workbook sheets: 8
Promote first run: 3 rows appended
Promote second run: 3 duplicates skipped
```

### Phase F - Show-ready intermediate master

A show-ready intermediate master was built for presentation purposes:

```text
TENDER_FINDER_Tender_Intelligence_Working_Master_PATCH5_SHOW_INTERMEDIATE.xlsx
```

It integrated Patch 5.0 candidates as `Needs Review - Patch 5.0 intermediate`, without overwriting the protected original master.

Integrated counts:

```text
Total integrated Future_Project candidates: 1,677
Surrey Planning Reports: 20
Township Langley: 778
Maple Ridge: 879
```

This file is useful for showing progress, but it is not a final production master write.

### Phase G - Full live capability run

A full live `--review-only` run across all 17 coded connectors was executed on Windows.

Observed live run summary:

```text
Connectors selected: 17
records_pulled: 25,995
records_normalized: 17,906
records_eligible: 17,906   <-- misleading before Patch 5.3 routing fix
records_written: 0
records_rejected: 5
P3/manual/queue sources: 9
Future_Projects eligible leads: 17,906   <-- inflated by Vancouver permits before fix
```

Important live source results:

```text
Township Langley:
  pulled=780
  dedupe skipped=322
  normalized/eligible around 458
  route=Future_Projects
  status=loaded

Maple Ridge:
  pulled=909
  dedupe skipped=327
  normalized/eligible around 582
  route=Future_Projects
  status=loaded

Vancouver Building Permits:
  pulled=20,000
  strong=3,144
  watchlist=1,261
  bulk=5,870
  noisy=9,725
  status=loaded
  before Patch 5.3: clean eligible count was inflated

Vancouver City Projects:
  pulled=936
  route=Rejected_Archive
  status=context_only

New Westminster Current Developments:
  pulled=1,346
  route=Rejected_Archive
  status=trailing_permit

Delta Development Applications:
  pulled=2,024
  route=Rejected_Archive
  status=trailing_permit

Surrey Planning Reports:
  PDFs downloaded successfully
  RezoningInProcess downloaded ~157,720 bytes
  DP-IN-PROCESS downloaded ~224,072 bytes
  extracted 0 rows before Patch 5.3 parser rewrite
  status=no_records_extracted
```

### Phase H - Patch 5.3 Live Hardened

Patch 5.3 addressed the main issues found in the live run and packaging review.

Main Patch 5.3 fixes:

1. **Surrey PDF parser rewritten/hardened**
   - multiple extraction strategies,
   - ruled table,
   - text table,
   - ID-anchored lines,
   - word-cluster strategy,
   - better support for numbered streets,
   - synthetic tests prove IDs like `25-0366` and `7926-0157-00`.

2. **Vancouver permit routing / gate fixed**
   - prevents bulk/noisy/watchlist rows from being counted as clean Future_Project eligible rows,
   - per-connector routing is respected,
   - gates can tighten but not loosen the route.

3. **Windows Unicode logging bug addressed**
   - avoids console crashes from non-ASCII symbols.

4. **Source summary made more honest**
   - should separate clean / watchlist / bulk / rejected / manual / failed categories.

5. **Regression harness fixed**
   - `TENDER_FINDER_OFFLINE_FIXTURES` skips network entirely for fixture-backed tests,
   - avoids post-Maple-Ridge hang,
   - offline tests become deterministic and fast.

6. **Packaging fixed**
   - `test_outputs_p53/` is included,
   - fresh-unzip `--all` passes,
   - fresh-unzip `--verify-outputs` passes.

---

## 4. What the current code can do

### 4.1 List and run connector inventory

Command:

```powershell
python tenderfinder_raw_sweep.py --list
```

Expected: 17 connector entries.

Known minor cosmetic issue: `surrey_planning_reportsready_for_load` may appear without a space. This is not functional but should be cleaned later.

### 4.2 Run review-only extraction without touching master

Examples:

```powershell
python tenderfinder_raw_sweep.py --only twp_langley_devactivity --review-only --out "C:\tenderfinder_out\tol_review.xlsx"

python tenderfinder_raw_sweep.py --only maple_ridge_devapps --review-only --out "C:\tenderfinder_out\maple_ridge_review.xlsx"

python tenderfinder_raw_sweep.py --review-only --out "C:\tenderfinder_out\all17_live_review.xlsx"
```

Review-only mode does not open, back up, or save master.

### 4.3 Pull live Township Langley development activity

Live proven:

```text
pulled=780
batching works
within-run dedupe works
deduped 322 duplicate app_no/address rows
produces Future_Projects review candidates
```

This is one of the strongest current connectors.

### 4.4 Pull live Maple Ridge development applications

Live proven:

```text
pulled=909
batching works
no unrecovered 504 during latest live run
deduped 327 duplicate app_no/address rows
produces Future_Projects review candidates
```

This is another strong connector.

### 4.5 Pull Vancouver building permits and tier them

Live proven pull:

```text
pulled=20,000
strong=3,144
watchlist=1,261
bulk=5,870
noisy=9,725
```

Patch 5.3 fixed the dangerous gate problem where too many Vancouver permit rows were counted as clean eligible Future_Project rows.

However, live validation after Patch 5.3 still needs to confirm:

- clean eligible count is not inflated,
- bulk/noisy rows are not presented as clean leads,
- summary columns are honest and readable.

### 4.6 Pull context/trailing sources and route them away from clean leads

Currently working as context/trailing/archive:

```text
van_city_projects -> context_only -> Rejected_Archive
new_west_currentdev -> building_permit_trailing -> Rejected_Archive
delta_devapps -> building_permit_trailing -> Rejected_Archive
```

This is good behavior: these records are preserved but not treated as high-quality TENDER_FINDER leads.

### 4.7 Surrey Planning Reports parser exists, but needs live proof

Patch 5.3 parser tests pass on synthetic fixtures.

Still required:

```powershell
python tenderfinder_raw_sweep.py --only surrey_planning_reports --review-only --out "C:\tenderfinder_out\patch5_3_live\surrey_live_review.xlsx"
```

Acceptance:

```text
rows > 0
status != no_records_extracted
no fixture fallback
source/evidence URLs present
debug artifact only if failure occurs
```

### 4.8 Run Source Register live preflight

Command pattern:

```powershell
python tenderfinder_raw_sweep.py --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7_1_cleaned_urls.xlsx" --preflight-links --preflight-no-search --preflight-output-dir "C:\tenderfinder_out\patch5_3_live\preflight_159_live" --preflight-timeout 20 --preflight-retries 2 --preflight-workers 6
```

Purpose:

- classify all 159 Source Register rows,
- produce fix queue,
- prove output writer works,
- identify broken/replaced/manual/connector-needed sources.

### 4.9 Generate review workbooks and source summaries

Current outputs include:

- review workbook `.xlsx`,
- `TENDER_FINDER_Run_Source_Summary.csv`,
- demo workbook,
- logs.

Patch 5.3 should make summary more honest by showing separated categories instead of one misleading eligible total.

### 4.10 Promote reviewed rows into a copied master

The code supports:

```powershell
python tenderfinder_raw_sweep.py --promote-reviewed "C:\tenderfinder_out\review_marked.xlsx" --write-master "C:\tenderfinder_out\TENDER_FINDER_Master_WRITE_TEST.xlsx"
```

Proven behavior:

- writes only `ACCEPT` rows,
- writes to copied workbook only,
- creates backup/log,
- second run skips duplicates.

Important: do not use protected original master for testing.

---

## 5. Current connector status by group

### Working live / high value

```text
twp_langley_devactivity
maple_ridge_devapps
```

These are the best current clean development-application sources.

### Working live but noisy / needs strong routing

```text
van_building_permits
```

Use only strong/watchlist after routing. Bulk/noisy must not contaminate clean leads.

### Working as context/trailing/rejected

```text
van_city_projects
new_west_currentdev
delta_devapps
```

Keep them for context, not clean leads.

### Parser exists but live proof pending

```text
surrey_planning_reports
```

Priority live test. If it still returns zero, use debug artifact to tune parser.

### Coded status but not working as real extractors yet

```text
surrey_devapps -> needs_exact_url
surrey_futureworks -> access_test_required
city_langley_devapps -> p3_extract_required
van_rezoning -> needs_exact_url
van_devpermits -> needs_exact_url
abbotsford_devapps -> p3_extract_required
burnaby_devapps -> p3_extract_required
coquitlam_devapps -> needs_exact_url
```

### Wrong layer / disabled

```text
dnv_devapps -> disabled_wrong_layer
port_coquitlam_landdev -> disabled_wrong_layer
```

Do not pretend these are working. Either find correct layers later or keep disabled.

---

## 6. Known weaknesses and risks

### 6.1 Live Surrey remains the biggest immediate unknown

Surrey PDFs are accessible. Before Patch 5.3, they downloaded but extracted zero rows. Patch 5.3 fixed parser logic in tests, but real live PDF proof is still required.

ZCode should run the live command and inspect result.

If live Surrey still extracts zero:

- do not mark it as working,
- inspect the generated debug artifact,
- tune parser to actual live text/table layout,
- rerun until rows > 0 or produce honest reason.

### 6.2 Vancouver permits can overwhelm the system

Vancouver permits produce 20,000 raw rows. They are useful, but dangerous.

Do not treat all Vancouver permit rows as TENDER_FINDER leads.

Required behavior:

```text
strong -> clean Future_Project review
watchlist -> watchlist / needs review
bulk -> Bulk_Intake_Raw
noisy -> Rejected_Archive or noisy archive
```

### 6.3 Many connector entries are not true connectors yet

The system has 17 entries, but several are honest placeholders/status entries. This is acceptable if reported clearly, but not acceptable if counted as working automation.

### 6.4 Active tenders are still underdeveloped

The current strongest work is Future_Projects / development applications.

Active tender sources such as BC Bid, bidsandtenders, Bonfire, MERX, BidCentral often require:

- connector-style scraping,
- portal/API handling,
- login/manual workflow,
- paid intelligence workflow.

This is likely a later phase.

### 6.5 Production master write is not fully operationalized

The code can promote accepted rows to a copied master, but the workflow for review decisions still needs a controlled operational process.

Do not write all review rows into the master.

Correct process:

1. run review-only,
2. manually or programmatically mark `review_decision=ACCEPT`,
3. promote only accepted rows to copied master,
4. inspect backup/audit/dedupe,
5. only then consider protected master handling.

### 6.6 Offline regression fixtures must not be confused with live proof

Patch 5.3 added `TENDER_FINDER_OFFLINE_FIXTURES` so tests do not hang. This is good.

But ZCode must preserve this rule:

```text
Offline fixture mode is only for regression harness.
Production/live runs must never silently replace failed live sources with fixtures.
```

### 6.7 Source Register has more sources than coded connectors

There are 159 Source Register rows, but far fewer working extractors.

ZCode must not claim all sources are automated.

---

## 7. Commands ZCode should run immediately

From fresh unzip:

```powershell
cd "TENDER_FINDER_Patch_5_0\01 Code\CONNECTOR_SWEEP"

python -m py_compile tenderfinder_raw_sweep.py tenderfinder_live_link_checker.py tenderfinder_surrey_inprocess.py tenderfinder_source_registry.py tenderfinder_master_io.py tenderfinder_guards.py tenderfinder_bulk_io.py tenderfinder_link_preflight.py

python tenderfinder_raw_sweep.py --list

python tests\run_regression.py --all

python tests\run_regression.py --verify-outputs --output-dir "..\..\test_outputs_p53"
```

Expected package-level result:

```text
--all: 24/24 PASS
--verify-outputs: 7/7 PASS
```

Then run live acceptance tests on Windows/TENDER_FINDER network without offline fixtures:

```powershell
mkdir C:\tenderfinder_out\patch5_3_live -Force

python tenderfinder_raw_sweep.py --only surrey_planning_reports --review-only --out "C:\tenderfinder_out\patch5_3_live\surrey_live_review.xlsx"

python tenderfinder_raw_sweep.py --only van_building_permits --review-only --out "C:\tenderfinder_out\patch5_3_live\van_permits_live_review.xlsx"

python tenderfinder_raw_sweep.py --only twp_langley_devactivity,maple_ridge_devapps --review-only --out "C:\tenderfinder_out\patch5_3_live\core_live_review.xlsx"

python tenderfinder_raw_sweep.py --review-only --out "C:\tenderfinder_out\patch5_3_live\all17_live_review.xlsx"
```

Run live preflight:

```powershell
python tenderfinder_raw_sweep.py --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7_1_cleaned_urls.xlsx" --preflight-links --preflight-no-search --preflight-output-dir "C:\tenderfinder_out\patch5_3_live\preflight_159_live" --preflight-timeout 20 --preflight-retries 2 --preflight-workers 6
```

---

## 8. What ZCode should do next

### Step 1 - Verify package state

- Confirm fresh unzip works.
- Confirm 24/24 regression.
- Confirm 7/7 verify outputs.
- Confirm no secrets.
- Confirm no nested stale package.

### Step 2 - Run live proof

Run real live commands on Windows/TENDER_FINDER network.

Produce a live proof report with:

- exact command,
- timestamp,
- source rows pulled,
- normalized rows,
- clean candidates,
- watchlist,
- bulk/noisy,
- rejected/context,
- manual/P3,
- failed extraction,
- duplicate rows skipped,
- output paths.

### Step 3 - Fix live Surrey if needed

If Surrey returns rows > 0, mark as live-proven.

If Surrey returns 0:

- use debug artifact,
- inspect current PDF layout,
- tune parser,
- add real live fixture sample if allowed,
- rerun until current PDFs parse.

### Step 4 - Confirm Vancouver routing live

Check `van_permits_live_review.xlsx` and `TENDER_FINDER_Run_Source_Summary.csv`.

Acceptance:

```text
clean eligible != 20,000
bulk/noisy excluded from clean Future_Project count
strong/watchlist/bulk/noisy counts visible
routing_reason present
```

### Step 5 - Build operational master update workflow

Use copied master only.

Suggested flow:

1. Generate live review workbook.
2. Create review decision columns or use existing `review_decision`.
3. Mark a small controlled ACCEPT set.
4. Copy v7_1 master to `C:\tenderfinder_out\TENDER_FINDER_Master_PATCH5_4_WRITE_TEST.xlsx`.
5. Promote accepted rows.
6. Run promote again to prove dedupe.
7. Produce audit log and row-count diff.

### Step 6 - Improve connector backlog

Priority order:

```text
1. van_rezoning
2. van_devpermits
3. coquitlam_devapps
4. city_langley_devapps
5. burnaby_devapps
6. abbotsford_devapps
7. surrey_devapps
8. surrey_futureworks
```

For each:

- find exact endpoint or API,
- prove row count,
- or keep status honest with next action.

Do not add broad new sources before current coded backlog is cleaned.

### Step 7 - Improve output/dashboard quality

Create a showable workbook/report that separates:

- clean TENDER_FINDER candidates,
- watchlist,
- Vancouver permit bulk/noisy,
- rejected/trailing/context,
- manual/P3 backlog,
- connector status.

The business user must be able to answer:

```text
What did we find?
Where did it come from?
Why is it relevant?
What was rejected and why?
Which sources are working?
Which sources need manual/P3 work?
What is safe to promote to master?
```

---

## 9. Non-negotiable rules for ZCode

Do not violate these:

```text
1. Do not overwrite protected original master workbook.
2. Do not silently overwrite any workbook.
3. Do not call Source Register rows coded connectors.
4. Do not call URL-alive harvestable source.
5. Do not treat Vancouver bulk/noisy permit rows as clean leads.
6. Do not hide failed connectors by routing everything to manual.
7. Do not use offline fixtures as live proof.
8. Do not claim live success unless live command output proves rows > 0 without fixture fallback.
9. Do not write to master unless review_decision=ACCEPT and target workbook is a copied test master.
10. Do not remove rejected/held rows; preserve them with reason.
11. Do not add new broad sources until current coded backlog is stabilized.
12. Do not produce audit-only reports; make code/output changes and prove them.
```

---

## 10. Desired next deliverable from ZCode

Recommended next package name:

```text
TENDER_FINDER_Patch_5_4_Live_Production_Candidate.zip
```

Required deliverables:

```text
PATCH_5_4_LIVE_PROOF_REPORT.md
PATCH_5_4_CHANGELOG.md
PATCH_5_4_CONNECTOR_STATUS_MATRIX.csv
REGRESSION_TEST_REPORT_PATCH_5_4.md
test_outputs_p54/
live_outputs_p54/
TENDER_FINDER_Master_PATCH5_4_WRITE_TEST.xlsx
promote_audit_*.json
```

Required live outputs:

```text
surrey_live_review.xlsx
van_permits_live_review.xlsx
core_live_review.xlsx
all17_live_review.xlsx
TENDER_FINDER_Run_Source_Summary_live.csv
preflight_159_live/*
```

Required acceptance:

```text
[ ] Fresh unzip regression passes.
[ ] Fresh unzip verify outputs passes.
[ ] Surrey live PDFs extract rows > 0 or produce debug artifact and honest failure.
[ ] Township Langley live still pulls rows > 0.
[ ] Maple Ridge live still pulls rows > 0.
[ ] Vancouver permits route strong/watchlist/bulk/noisy correctly live.
[ ] Clean eligible count is not inflated.
[ ] all17 review-only completes without master write.
[ ] 159-source live preflight creates all required files.
[ ] Source summary is business-readable and honest.
[ ] Copied-master promote works with ACCEPT only.
[ ] Second promote skips duplicates.
[ ] No protected master overwritten.
[ ] Final reports match actual outputs.
```

---

## 11. One-paragraph executive summary

TENDER_FINDER Tender Finder has moved from planning into a real working Python package. It now has a 159-row Source Register, a controlled runner, 17 connector entries, review-only extraction, source summaries, live preflight, regression tests, fixture-based offline tests, copied-master promotion with dedupe, and showable intermediate master output. Live runs proved Township Langley and Maple Ridge development-application connectors work well, and Vancouver permits pull large volumes but require strict routing. Patch 5.3 fixed package-level regression, output verification, offline fixture hang, Surrey parser logic tests, Vancouver eligible-count inflation tests, and Windows logging issues. The remaining work is to convert this into a production-live build: prove Surrey against real PDFs, confirm Vancouver routing on live data, run all17/preflight live, improve connector backlog endpoints, and promote only reviewed ACCEPT rows into a copied master.

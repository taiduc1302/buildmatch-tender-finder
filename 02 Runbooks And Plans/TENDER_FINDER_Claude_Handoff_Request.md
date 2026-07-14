# TENDER_FINDER Tender Intelligence — Claude Handoff Request

I am uploading the current TENDER_FINDER project package:

`0623 v4 Tender Finder Final.zip`

Please do not rename, reorganize, or rebuild the project from scratch.

This ZIP is the current project package. Treat it as the current source of truth. The original custom instructions are no longer available, so this handoff request is intended to preserve the current project logic, known issues, and next technical direction.

## 1. Important folder rule

Use the active folders only:

* `00 Master`
* `01 Code`
* `02 Runbooks And Plans`
* `03 Active and QA Runbooks`
* `04 RESEARCH REFERENCE`
* `05_PROMPTS`

Do not work from `_ss`.

`_ss` is snapshot/archive only. Use it only for backup comparison if absolutely needed, not for active development.

## 2. Main files to read first

Please read these first, in this order:

1. `TENDER_FINDER_Final_Folder_Guide.docx`
2. `structure.txt`
3. `00 Master / TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx`
4. `01 Code / CONNECTOR_SWEEP / tenderfinder_raw_sweep.py`
5. `01 Code / CONNECTOR_SWEEP / tenderfinder_dev_app_endpoints.csv`
6. `01 Code / tenderfinder_agent2.py`
7. `02 Runbooks And Plans / TENDER_FINDER_Run_Results_Review_and_Next_Steps.md`
8. `02 Runbooks And Plans / TENDER_FINDER_Municipal_Run_Packs.md`
9. `02 Runbooks And Plans / TENDER_FINDER_Project_Plan_Role_Goal_Tasks_Instructions.md`
10. `02 Runbooks And Plans / TENDER_FINDER_Project_Plan_Supplement_v2.md`
11. `05_PROMPTS / TENDER_FINDER_Prompt_Pack_v2.md`
12. `03 Active and QA Runbooks / TENDER_FINDER_Task_D_Active_Tenders_Phase0.xlsx`
13. `03 Active and QA Runbooks / TENDER_FINDER_Task_G_Quality_Controls.xlsx`

## 3. Current project state

The TENDER_FINDER system already has the organizational structure. Do not build a new one.

The system already includes:

* Operational master workbook.
* Source_Register.
* Run_Queue.
* Future_Projects.
* Active_Tenders.
* Rejected_Archive / Cleanup / QA structure.
* Prompt Pack v2.
* Active Tenders Phase 0 workbook.
* Quality Control workbook.
* Connector sweep package.
* Municipal runbooks.
* Research/reference files.
* Current code prototype.

The missing piece is not another plan. The missing piece is a controlled executable bridge between the existing pieces.

The target architecture is:

`Source_Register / Run_Queue`
→ `technical endpoint registry`
→ `safe probe / sweep dispatcher`
→ `classification + scoring`
→ `dedup / update`
→ `Future_Projects / Active_Tenders / Rejected_Archive / QA log`

## 4. Main objective

Patch the existing project into a safe controlled all-source probe/load runner.

Do not run all sources directly into production.

The safe rollout should be:

1. All-source probe only, no loading.
2. Tier 1 structured load only.
3. QA review.
4. Tier 2 structured load.
5. P3/manual queue for web/PDF/council sources.
6. Active Tender parser later.
7. Scheduled automation only for proven sources.

## 5. Known important issue from previous raw sweep

The previous raw sweep mechanically worked, but the quality was mixed.

Some sources were excellent and already loaded:

* Township of Langley.
* Maple Ridge.
* Surrey manual lead screen.

But several sources returned wrong-layer, trailing, context-only, or useless data.

Known examples:

* Surrey API previously pulled `Subdivision Markers`, not development applications.
* Coquitlam pulled neighbourhood plan polygons, not applications.
* District of North Vancouver pulled hazard/DPA polygons.
* Port Coquitlam pulled ALR polygons.
* Delta and New Westminster pulled building/plumbing permits, which are trailing signals, not future development applications.
* Vancouver rezoning/dev-permits suffered from wrong ODS fallback behavior.
* Some sources are web/PDF/council-only and should not be treated as failed just because they do not have an API.

The main lesson:

Do not allow discovery/fallback to load data unless the layer and attributes prove the source is actually useful.

## 6. What already exists and should be reused

### 6.1 Master workbook

Use:

`00 Master / TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx`

This is the current operating workbook.

Before writing any new data, create a new version:

`TENDER_FINDER_Tender_Intelligence_Working_Master_v7.xlsx`

Do not overwrite v6 directly.

### 6.2 Code

Use and patch:

`01 Code / CONNECTOR_SWEEP / tenderfinder_raw_sweep.py`

Use as technical connector registry:

`01 Code / CONNECTOR_SWEEP / tenderfinder_dev_app_endpoints.csv`

Use as reference for known working guards/pins:

`01 Code / tenderfinder_agent2.py`

Important: `tenderfinder_agent2.py` already includes some useful concepts such as pinned endpoints, denylist, attribute richness gate, aliases, and Claude/offline scoring. Reuse the logic where appropriate, but do not turn `tenderfinder_agent2.py` into the main all-source runner unless that is clearly the better path.

The main patch target should be `tenderfinder_raw_sweep.py`.

### 6.3 Prompt Pack

Use:

`05_PROMPTS / TENDER_FINDER_Prompt_Pack_v2.md`

Do not invent new prompt logic from scratch unless required. Use existing prompt pack logic and assign stable prompt IDs if needed:

* `PROMPT_DEV_APP_SCORING`
* `PROMPT_COUNCIL_CAPITAL`
* `PROMPT_ACTIVE_TENDER_PARSE`
* `PROMPT_WEB_PDF_EXTRACT`
* `PROMPT_WEEKLY_QA`

### 6.4 Active and QA workbooks

Use:

`03 Active and QA Runbooks / TENDER_FINDER_Task_D_Active_Tenders_Phase0.xlsx`

for Active Tender setup logic.

Use:

`03 Active and QA Runbooks / TENDER_FINDER_Task_G_Quality_Controls.xlsx`

for quality control, false positives, duplicate issues, automation readiness, Example Reviewer/estimator feedback, and source performance.

## 7. Required technical work

## 7.1 Patch `tenderfinder_raw_sweep.py`

Add or improve these command-line options:

* `--from-master`
* `--tier`
* `--category`
* `--probe`
* `--write-master`
* `--dry-run`
* `--max-records`
* `--only`
* `--skip-paid`
* `--skip-login`
* `--sync-registry`
* `--out`

Expected commands should look like:

```bash
python tenderfinder_raw_sweep.py --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7.xlsx" --probe --out "../../00 Master/probe_results_2026-06-23.xlsx"
```

```bash
python tenderfinder_raw_sweep.py --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7.xlsx" --tier 1 --max-records 500 --write-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7.xlsx"
```

```bash
python tenderfinder_raw_sweep.py --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7.xlsx" --tier 2 --max-records 500 --write-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7.xlsx"
```

## 7.2 Add no-silent-fallback behavior

Do not silently fall back to a different dataset if the requested source/slug/layer is not found.

Bad behavior to prevent:

* `van_rezoning` resolving to issued building permits.
* `van_devpermits` resolving to business licences.
* A “similar” dataset being used just because the requested dataset failed.

Correct behavior:

* Mark the source as `slug_not_found`, `endpoint_not_found`, or `layer_not_confirmed`.
* Do not load records.
* Save the error in run log.
* Set `Next Action = verify endpoint manually`.

## 7.3 Add ArcGIS layer denylist

During discovery/ranking, reject layers whose names indicate they are not development applications or useful capital/tender signals.

Denylist examples:

* `hazard`
* `dpa`
* `development permit area`
* `permit area`
* `marker`
* `subdivision marker`
* `watering`
* `lawn`
* `alr`
* `agricultural land reserve`
* `reserve`
* `neighbourhood plan`
* `np_`
* `asset`
* `facility`
* `watercourse`
* `flood`
* `slope`
* `creek`
* `wildfire`
* `streamside`
* `zoning`
* geometry-only overlays

Important: denylist should be applied before loading, not after pollution already enters the workbook.

## 7.4 Add positive layer scoring

Prefer layers whose names or metadata include useful terms:

* `development application`
* `development applications`
* `active development applications`
* `development activity`
* `planning application`
* `rezoning`
* `subdivision`
* `development permit`
* `current applications`
* `permit application`
* `project`
* `capital project`

But positive name match alone is not enough. It must pass attribute richness sampling.

## 7.5 Add attribute-richness sampling

Do not check only one record.

Sample the first 10–20 records where possible.

A layer/source should pass only if records contain meaningful non-geometry fields.

Useful fields include:

* application number
* file number
* folder number
* project number
* application type
* subtype
* status
* stage
* address
* location
* applicant
* owner
* developer
* description
* proposal
* work proposed
* project name
* dates
* milestone
* source URL or per-record link

Reject or quarantine if records contain mostly:

* OBJECTID
* FID
* GlobalID
* Shape
* Shape_Area
* Shape_Length
* geometry only
* polygon metadata only
* no useful application/project fields

Minimum rule:

A sample should have at least 3 useful non-geometry fields and at least one key application/project indicator.

If not, set:

`status = schema_too_thin`

and route to:

`Rejected_Archive` or run log, not Future_Projects.

## 7.6 Add wrong-layer quarantine

Wrong-layer data should not crash the run and should not enter Future_Projects.

Classify bad or irrelevant returns as:

* `wrong_layer`
* `schema_too_thin`
* `trailing_permit`
* `context_only`
* `manual_review_needed`
* `access_blocked`
* `missing_connector`
* `needs_exact_url`
* `paid_or_login_skip`

Each source should receive a run result and next action.

## 7.7 Always save raw outputs

Even if the source is rejected, save raw output for QA/debugging.

Suggested raw folders:

* `01 Code / CONNECTOR_SWEEP / raw_runs / <date> / json`
* `01 Code / CONNECTOR_SWEEP / raw_runs / <date> / csv`
* `01 Code / CONNECTOR_SWEEP / raw_runs / <date> / logs`

Do not discard raw records silently.

## 8. Source_Register / Run_Queue integration

The master workbook has business source data. The connector CSV has technical endpoints. These need to be bridged.

Add logic to compare:

`Source_Register`

against:

`tenderfinder_dev_app_endpoints.csv`

For each source, assign one of these statuses:

* `ready_for_probe`
* `ready_for_load`
* `missing_connector`
* `needs_exact_url`
* `manual_p3_only`
* `paid_or_login_skip`
* `access_test_required`
* `disabled_wrong_layer`
* `endpoint_stale`
* `blocked`
* `not_automation_ready`

If a source exists in Source_Register but not in endpoint CSV, do not ignore it. Add it to a sync report with a clear status.

Expected sync report columns:

* `source_id`
* `source_name`
* `category`
* `priority_tier`
* `source_register_status`
* `connector_registry_status`
* `fetch_type`
* `endpoint`
* `layer`
* `automation_feasibility`
* `access_status`
* `output_route`
* `prompt_type`
* `next_action`
* `notes`

## 9. Suggested connector CSV schema

If needed, migrate or expand `tenderfinder_dev_app_endpoints.csv` to include:

* `source_id`
* `source_name`
* `municipality`
* `category`
* `fetch_type`
* `endpoint`
* `layer`
* `priority_tier`
* `access_status`
* `automation_feasibility`
* `output_route`
* `prompt_type`
* `last_probe_status`
* `last_good_endpoint`
* `notes`

Do not remove useful existing fields unless clearly replaced.

## 10. Fetch type dispatcher

Do not treat all sources as the same type.

Add a dispatcher based on `fetch_type`, `category`, or source metadata.

Suggested routes:

* `arcgis_feature_service` → ArcGIS REST query
* `arcgis_hub_discover` → discovery + denylist + richness gate + query
* `arcgis_mapserver` → mapserver layer query with same gates
* `ods_api` → exact ODS dataset only, no silent fallback
* `rss` → active tender/news parser
* `web_page` → P3/manual extractor queue
* `pdf` → P3/manual extractor queue
* `council_agenda` → P3/manual extractor queue
* `capital_plan` → council/capital prompt route
* `email_gc_invite` → active tender parser later
* `paid_login` → skip unless access configured
* `manual_only` → Run_Queue only

## 11. Output router

Do not write all results to one place.

Route by classification:

* `dev_application_lead` → `Future_Projects`
* `capital_project` → `Future_Projects` or `Capital_Context`
* `active_tender` → `Active_Tenders`
* `building_permit_trailing` → `Rejected_Archive` or `Context`
* `wrong_layer` → `Rejected_Archive`
* `schema_too_thin` → `Rejected_Archive`
* `context_only` → `Rejected_Archive` or `Context`
* `web_page` → `P3_Manual_Extract_Queue` / `Run_Queue`
* `pdf` → `P3_Manual_Extract_Queue` / `Run_Queue`
* `council_agenda` → `P3_Manual_Extract_Queue` / `Run_Queue`
* `paid_login` → `Run_Queue` only, no scraping

Do not mix Active Tenders with Future Projects.

Do not treat building permits as future development applications unless there is a clear reason and they are explicitly marked as trailing/context.

## 12. Master workbook writer

Add a safe writer for:

`00 Master / TENDER_FINDER_Tender_Intelligence_Working_Master_v7.xlsx`

Do not write to a separate 14-column output as the final workflow.

The current prototype output is useful as reference, but the production workflow must write into the existing master workbook schema.

Future_Projects uses this 21-column schema:

* `Project ID`
* `Date Found`
* `Source`
* `Source URL`
* `Project Title`
* `Owner/Developer`
* `Municipality`
* `Application No`
* `Application Type/Stage`
* `Scope Summary`
* `Expected Civil Component`
* `Fit Score`
* `Fit Class`
* `Verification Status`
* `Est. Civil Timeline/Horizon`
* `Est. Value`
* `Next Milestone`
* `Linked Active Tender ID`
* `Assigned To`
* `Notes`
* `Last Updated`

Requirements:

* Preserve formulas.
* Preserve `Fit Class` formula.
* Preserve formatting.
* Preserve dropdowns.
* Preserve workbook tabs.
* Do not overwrite existing rows unless update logic identifies the same project.
* Support append/update/enrich.
* Update Run_Queue and QA log.
* Save a backup before write.

Suggested behavior:

* If new project → append.
* If same project, new stage → update existing row.
* If same project, new owner/applicant/source URL → enrich existing row.
* If future project becomes active tender → link Future to Active.

## 13. Dedup and update logic

Do not dedup only by `project_id`.

Use multiple keys:

* municipality + application number
* municipality + normalized address
* source URL
* owner + address
* project title similarity
* application number aliases
* source-specific ID if available

Normalize:

* whitespace
* punctuation
* case
* address abbreviations where reasonable
* application/file number formatting
* municipality names

Known issue to fix:

There is/was a duplicate future project:

`TWP-LANGLEY-RO100158`

It appeared multiple times with different stages. The correct behavior should be one live row with current stage, and prior stage history in Notes.

## 14. P3/manual extraction handling

Do not mark `web_page`, `PDF`, `council`, or `manual` sources as failed just because there is no API.

Instead:

* Add them to P3/manual queue.
* Set `status = p3_extract_required`.
* Set `next_action = run P3 extractor`.
* Use Prompt Pack v2 for web/PDF/council extraction.

Possible later script:

```bash
python tenderfinder_p3_extract.py --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7.xlsx" --queue p3
```

Sources like City of Langley, Burnaby, Pitt Meadows, Richmond, and council/capital sources may need this route.

## 15. Active Tender handling

Active Tenders are a separate track.

Do not process Active Tender sources through the dev-application pipeline.

Use the Active Tender Phase 0 workbook for:

* shared inbox
* BC Bid alerts
* bids&tenders alerts
* CivicInfo RSS
* BidCentral if access approved
* GC invite forwarding

Later, add parser for:

* RSS tender notices
* email alerts
* GC invitations
* portal notifications

Route to:

`Active_Tenders`

not:

`Future_Projects`

## 16. QA and source performance

Use the QA workbook or add/update a QA log with:

* source_id
* source_name
* records_pulled
* records_loaded
* records_rejected
* wrong_layer_count
* schema_too_thin_count
* duplicate_count
* false_positive_reason
* useful_leads_count
* manual_review_count
* Example Reviewer feedback
* estimator feedback
* automation readiness
* next action

Important metrics:

* useful leads per source
* false positive rate
* duplicate rate
* wrong-layer rate
* future lead → real tender conversion
* manual review hours saved
* automation readiness

## 17. Known source decisions to preserve

Preserve the current run-review logic:

Good / loaded:

* Surrey manual lead screen.
* Township of Langley.
* Maple Ridge.

Needs re-pin / retest:

* Surrey public development applications.
* Surrey FutureWorks from TENDER_FINDER office network.
* Coquitlam development application source.

P3/manual route:

* City of Langley.
* Burnaby.
* Pitt Meadows.
* Council agenda / PDF sources.
* Some current development pages.

Trailing/context:

* building permits
* plumbing permits
* business licences
* permits-only datasets
* Vancouver issued building permits
* Delta/New Westminster permits unless clearly useful as context

Reject/quarantine:

* DNV hazard/DPA polygons.
* Port Coquitlam ALR polygons.
* Coquitlam neighbourhood plan polygons.
* Surrey Subdivision Markers.
* any geometry-only layers.

## 18. Commands to document

Create a new markdown file:

`RUN_ALL_SOURCES_SAFE.md`

It should include exact commands for:

### Probe only

```bash
python tenderfinder_raw_sweep.py --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7.xlsx" --probe --out "../../00 Master/probe_results_YYYY-MM-DD.xlsx"
```

### Tier 1 load

```bash
python tenderfinder_raw_sweep.py --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7.xlsx" --tier 1 --max-records 500 --write-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7.xlsx"
```

### Tier 2 load

```bash
python tenderfinder_raw_sweep.py --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7.xlsx" --tier 2 --max-records 500 --write-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7.xlsx"
```

### Dry run

```bash
python tenderfinder_raw_sweep.py --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7.xlsx" --tier 1 --dry-run --max-records 100
```

### Only specific sources

```bash
python tenderfinder_raw_sweep.py --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7.xlsx" --only langley_tol,maple_ridge --probe
```

### P3 queue

```bash
python tenderfinder_p3_extract.py --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7.xlsx" --queue p3
```

If `tenderfinder_p3_extract.py` is not implemented yet, document it as a planned next script and make sure `tenderfinder_raw_sweep.py` correctly queues those sources.

## 19. Expected deliverables

Please return:

1. Patched `tenderfinder_raw_sweep.py`.
2. If needed, helper module such as `tenderfinder_master_io.py`.
3. If needed, helper module such as `tenderfinder_source_registry.py`.
4. Updated or migrated `tenderfinder_dev_app_endpoints.csv`.
5. `RUN_ALL_SOURCES_SAFE.md`.
6. List of workbook tabs the script writes to.
7. List of sources that are:

   * ready for structured probe
   * ready for structured load
   * manual/P3 only
   * paid/login skip
   * access-test required
   * wrong-layer disabled
   * needs exact URL
8. Summary of changed logic.
9. Known limitations.
10. No secrets committed.

## 20. Important constraints

Do not violate these constraints:

* Do not scrape login-only portals.
* Do not use paid sources unless access is configured.
* Do not commit API keys or credentials.
* Do not silently fall back to similar datasets.
* Do not treat building permits as future development applications.
* Do not mix Active Tenders with Future Projects.
* Do not work from `_ss`.
* Do not overwrite v6 directly.
* Create v7 before writing changes.
* Keep raw outputs and run logs for QA.
* Preserve workbook formulas, dropdowns, formatting, and existing tabs.
* Automate only proven sources.
* Any uncertain AI extraction must be marked `Needs Review`, not `Verified`.

## 21. Recommended implementation sequence

Please implement in this order:

### Step 1 — Inspect and confirm

* Inspect ZIP structure.
* Confirm active folders.
* Confirm master workbook tabs.
* Confirm connector CSV schema.
* Confirm existing CLI options in `tenderfinder_raw_sweep.py`.
* Confirm current output behavior.

### Step 2 — Add guards

Patch:

* no silent fallback
* denylist
* positive layer scoring
* attribute-richness sampling
* wrong-layer quarantine
* raw output preservation

### Step 3 — Add registry bridge

Patch:

* Source_Register / Run_Queue reader
* endpoint CSV comparison
* source status classification
* sync report

### Step 4 — Add dispatcher

Patch:

* fetch_type routes
* output routes
* prompt_type route placeholder

### Step 5 — Add master writer

Patch:

* v6 → v7 copy
* Future_Projects writer
* Active_Tenders writer placeholder if not fully implemented
* Rejected_Archive writer
* Run_Queue update
* QA/run log update

### Step 6 — Add dedup/update

Patch:

* multi-key dedup
* update existing row
* enrich existing row
* duplicate log

### Step 7 — Add docs

Create:

* `RUN_ALL_SOURCES_SAFE.md`
* notes on connector CSV migration
* list of manual/P3/blocked/paid sources

### Step 8 — Test safely

Run in this order:

1. `--probe`
2. `--dry-run`
3. `--only langley_tol,maple_ridge --probe`
4. `--tier 1 --dry-run`
5. write to copied v7 only

Do not perform all-source production load without probe + QA.

## 22. Final expected outcome

The final system should not be “all sources dumped into Future_Projects.”

The final system should be a controlled runner that:

* reads the current master workbook
* understands the technical endpoint registry
* safely probes sources
* rejects wrong layers
* queues manual sources
* separates Future Projects from Active Tenders
* writes only useful structured leads into the correct workbook tabs
* keeps raw outputs and logs
* supports QA and future automation decisions

Do not optimize for maximum row count.

Optimize for source quality, traceability, deduplication, and safe automation.

# TENDER_FINDER Tender Intelligence — Technical / Business Context Brief for Code and Source Expansion

1. What this program is

This is the TENDER_FINDER Tender Intelligence controlled runner.

It is a Python-based data acquisition and workbook-writing system for Example Civil Contractor Ltd. Its purpose is to collect public-source data that may indicate active tenders or future civil/earthworks opportunities, normalize that data, classify it, and write it into controlled Excel workbook tabs for review.

The current program is not a fully autonomous tender agent. It is a controlled runner with safety gates, source classification, raw evidence capture, run logs, and workbook-write protection.

The current active version is Patch 3 / Bulk Harvest mode, built on top of Patch 2 production-safety protections.

---

2. Who it is for

The system is for Example Civil Contractor Ltd.

TENDER_FINDER is a civil / earthworks contractor in the Lower Mainland / Fraser Valley, British Columbia.

The system is intended to support estimating, business development, and tender-intelligence workflows by finding opportunities earlier and more consistently than manual searching alone.

The intended users are:

* TENDER_FINDER estimating / business development team
* Example Operator running source sweeps
* Example Reviewer / human reviewer for high-value leads
* future AI / automation agents that help parse, score, summarize, and prioritize opportunities

---

3. TENDER_FINDER opportunity scope

Relevant opportunities include:

* subdivision servicing
* site servicing
* land servicing
* excavation
* grading
* earthworks
* underground utilities
* water main
* storm sewer
* sanitary sewer
* drainage
* manholes
* roadworks
* curbs
* sidewalks
* paving
* bridges
* site concrete
* structural/site concrete
* municipal civil works
* airport civil works
* port / industrial civil
* utility infrastructure
* development applications that indicate future civil work
* capital plans and procurement pipelines that signal future civil projects

Not relevant:

* vertical-only building construction
* interior renovations
* tenant improvements
* HVAC-only / electrical-only / roofing-only work
* general building construction without civil scope
* sources that require unauthorized scraping
* login-only or paid portals unless TENDER_FINDER has authorized access and the source is handled as a manual/email/paid workflow

Priority geography:

* Surrey
* Township of Langley
* City of Langley
* Maple Ridge
* Pitt Meadows
* Metro Vancouver
* Fraser Valley
* broader BC only where it includes relevant civil/infrastructure work

Known important clients / owners / targets (EXAMPLE PLACEHOLDER LIST — configure per deployment):

* Example municipal owners (the municipalities and regional bodies whose public
  procurement portals and development-application feeds the connectors monitor —
  e.g. City of Surrey, Township of Langley, Maple Ridge, Metro Vancouver in the
  reference BC configuration)
* Example provincial / crown infrastructure owners (transportation ministry,
  transit authority, airport authority, port authority, utilities)
* Example Developer A (private land developer)
* Example Developer B (private land developer)
* Example General Contractor A
* Example General Contractor B
* Example Materials / Heavy-Civil Partner

Note: the original internal version of this brief listed the operating company's
real client and target organizations. That list was replaced with placeholders
during sanitization. Populate this section for your own deployment.

---

4. What problem the code is solving

Before this runner, the project had a broad business source map, prompt pack, and workbook structure, but not enough safe automation.

The code solves these problems:

1. Pull data from selected public sources.
2. Avoid silently using wrong layers or bad datasets.
3. Separate raw source data from scored/reviewed leads.
4. Protect the master workbook from accidental overwrite.
5. Preserve formulas and deduplicate known project rows when writing to Future_Projects.
6. Keep logs and QA evidence for every run.
7. Allow broader data acquisition through Bulk_Intake_Raw without polluting Future_Projects.
8. Support future expansion into active tenders, infrastructure sources, paid/manual sources, and GC invite workflows.

---

5. Important distinction: business sources vs technical connectors

There are two different source lists.

A. Source_Register

This is the business source universe.

It lives in the master workbook.

It contains the strategic list of potential sources, including:

* active tender portals
* municipal development applications
* council agendas
* capital plans
* paid intelligence sources
* GC/developer invitation sources
* news / early-signal sources

The current Source_Register has 68 source concepts grouped into categories A-G.

This is the correct place to expand the overall market map.

B. tenderfinder_dev_app_endpoints.csv

This is the technical connector registry.

It lives in:
01 Code / CONNECTOR_SWEEP / tenderfinder_dev_app_endpoints.csv

It currently contains 16 technical connectors, mostly municipal open-data / ArcGIS / Opendatasoft sources.

This is what the Python runner actually runs right now.

Do not confuse these two:

* Source_Register = business universe
* tenderfinder_dev_app_endpoints.csv = executable connector list

---

6. Current technical connectors

The current runner has 16 connectors:

1. surrey_devapps
2. surrey_futureworks
3. twp_langley_devactivity
4. maple_ridge_devapps
5. city_langley_devapps
6. van_building_permits
7. van_rezoning
8. van_devpermits
9. van_city_projects
10. abbotsford_devapps
11. new_west_currentdev
12. burnaby_devapps
13. coquitlam_devapps
14. delta_devapps
15. dnv_devapps
16. port_coquitlam_landdev

Current status summary:

* Township of Langley and Maple Ridge are confirmed high-quality development application sources.
* Vancouver building permits, New Westminster, and Delta are mostly trailing/context permit sources, not future leads.
* Vancouver city projects are context/capital project source.
* Surrey devapps needs exact URL / endpoint verification.
* Surrey FutureWorks requires access test.
* City Langley, Burnaby, Abbotsford are manual/P3-style sources right now.
* DNV and Port Coquitlam current layers are wrong-layer / disabled candidates.
* Coquitlam and some Vancouver ODS sources need exact URL / correct layer repair.

---

6a. P3 extraction — definition

P3 extraction (also written "P3-style" or "Phase 3") is a workflow classification, not a code module or library.

It refers to sources that cannot be accessed via direct API, ArcGIS REST, RSS, or Opendatasoft. These sources require one of the following:

* Manual human review and data entry — the operator reads the source and enters records by hand
* PDF parsing — council agendas, capital plans, tender award notices, or IFB documents that exist only as PDFs
* Authenticated / login access that TENDER_FINDER holds but the runner cannot use automatically
* Email-forwarded content — GC invitation emails, subscription alerts, or manual feed workflows

How the runner handles P3 sources:

The runner detects P3 sources at load time and short-circuits them without making a network request. It records a stub row in Bulk_Intake_Raw with:

* classification = p3_extract_required
* status = manual_required
* notes = human action or future module needed
* records_pulled = 0

The stub is then routed to Run_Queue so a human operator or future dedicated extraction module can process it.

The runner must never attempt to scrape, parse, or guess at P3 source content. The correct output for a P3 source is always a stub row with a clear manual action note.

Future Patch 4+ work may introduce a dedicated P3 extraction module for council agenda PDFs and capital plan documents. Until then, P3 sources are human-handled.

---

7. Main files and modules

7.1 tenderfinder_raw_sweep.py

Main runner script.

Responsibilities:

* parse command-line options
* load connector CSV
* select connectors by tier, category, or source id
* resolve endpoints
* pull records from supported public APIs
* save raw JSON outputs
* classify source returns
* normalize records into lead-like rows
* apply write gates
* write review-only files
* write probe files
* write run logs
* write to master workbook when explicitly allowed
* run Patch 3 bulk intake mode

Supported source technologies currently include:

* ArcGIS Hub item
* ArcGIS Hub discovery
* ArcGIS MapServer discovery
* Opendatasoft v2.1 datasets

On connector errors, see section 10a for required behavior.

7.2 tenderfinder_guards.py

Safety and classification module.

Responsibilities:

* denylist bad ArcGIS layers
* score/rank possible layers by title
* reject obvious wrong layers
* sample record richness
* classify records/source returns into controlled classes
* route classifications to workbook tabs
* normalize municipalities, application numbers, addresses
* generate dedup keys
* estimate civil fit score from text heuristics

See section 20 for the full fit score algorithm.

Important classifications:

* dev_application_lead
* capital_project
* active_tender
* building_permit_trailing
* wrong_layer
* schema_too_thin
* context_only
* p3_extract_required
* manual_review_needed
* fetch_error
* access_denied
* empty_response

Important routing:

* dev_application_lead -> Future_Projects
* capital_project -> Future_Projects
* active_tender -> Active_Tenders
* building_permit_trailing -> Rejected_Archive
* wrong_layer -> Rejected_Archive
* schema_too_thin -> Rejected_Archive
* context_only -> Rejected_Archive
* p3_extract_required -> Run_Queue
* manual_review_needed -> Run_Queue
* fetch_error -> Bulk_Intake_Raw (stub, error field populated)
* access_denied -> Bulk_Intake_Raw (stub, error field populated)
* empty_response -> Bulk_Intake_Raw (stub, records_pulled = 0)

7.3 tenderfinder_master_io.py

Excel master workbook writer.

Responsibilities:

* copy v6 to v7/test workbook if needed
* create mandatory backup before save
* fail closed if backup fails
* protect v6 from writes
* write/merge Future_Projects
* append Active_Tenders
* append Rejected_Archive
* create/update Run_Log
* create/update Source_QA
* preserve Fit Class formulas
* deduplicate Future_Projects rows
* collapse multiple records for same project into one best row
* prefer current/pending advanced stage over older/completed stage where appropriate

See section 21 for workbook tab schemas.
See section 22 for stage hierarchy used in collapse/dedup logic.

Important workbook tabs:

* Future_Projects
* Active_Tenders
* Rejected_Archive
* Run_Log
* Source_QA
* Bulk_Intake_Raw

7.4 tenderfinder_source_registry.py

Source_Register bridge.

Responsibilities:

* read Source_Register from the master workbook
* read connector CSV
* match business source names to technical connector ids
* emit sync report
* classify sources into ready/missing/manual/paid/login/etc.
* help identify which business sources do not yet have technical connectors

This is important for Source Expansion Patch 4 because the project already has a broad source register, and new sources should not be added blindly.

7.5 tenderfinder_bulk_io.py

Patch 3 bulk intake writer.

Responsibilities:

* create Bulk_Intake_Raw sheet if missing
* append broad raw/normalized source rows
* does not write to Future_Projects
* does not write to Rejected_Archive
* keeps raw acquisition separate from curated leads

Bulk_Intake_Raw columns:

* run_id
* run_timestamp
* source_id
* source_name
* tier
* municipality
* access_status
* fetch_type
* resolved_endpoint
* records_pulled
* record_index
* classification
* output_route
* status
* richness
* project_id
* application_no
* address
* owner_applicant
* application_type_stage
* scope_summary
* fit_score
* source_url
* raw_json
* raw_file_path
* error
* notes

---

8. Main workflow modes

8.1 List connectors

Command:
python tenderfinder_raw_sweep.py --list

Purpose:
Shows the current 16 executable connectors.

No network.
No workbook write.

8.2 Sync registry

Command:
python tenderfinder_raw_sweep.py --sync-registry --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx" --out sync_report.csv

Purpose:
Compares Source_Register with connector CSV.

Useful for finding:

* sources in Source_Register but not in connector CSV
* connectors not represented in Source_Register
* sources that need exact URL
* manual-only sources
* paid/login sources
* automation-ready sources

No master workbook write.

8.3 Probe

Command example:
python tenderfinder_raw_sweep.py --only twp_langley_devactivity,maple_ridge_devapps --probe --out tol_maple_ridge_probe.xlsx

Purpose:
Resolve/check endpoints without full pull.

Used to confirm:

* endpoint is correct
* layer resolves
* source can be reached
* no bad fallback happened

8.4 Dry-run pull

Command example:
python tenderfinder_raw_sweep.py --tier 1 --dry-run --max-records 100

Purpose:
Pull and classify records without writing the master workbook.

Used to check:

* source works
* records pulled
* classification
* richness
* errors
* run log

8.5 Review-only mode

Command example:
python tenderfinder_raw_sweep.py --tier 1 --review-only --max-records 50 --out tier1_review.xlsx

Purpose:
Creates an Excel review file without opening, backing up, or saving the master workbook.

Important:
Review-only is safer than write-master.
It is useful for human review before writing to Future_Projects.

8.6 Controlled Future_Projects write

Command example:
python tenderfinder_raw_sweep.py --only twp_langley_devactivity,maple_ridge_devapps --max-records 50 --max-write-per-source 10 --write-master "../../00 Master/v7_TEST.xlsx"

Purpose:
Writes only eligible records to Future_Projects in a copied v7/test workbook.

Important:
This should not be used on v6.
This should not be run all-source unless explicitly approved.
This is not a raw dump mode.

8.7 Bulk intake mode

Command example:
python tenderfinder_raw_sweep.py --bulk-intake --include-tier2 --include-tier3 --include-trailing-context --include-wrong-layer --max-records-per-source 100 --write-master "../../00 Master/v8_BULK_INTAKE_ALL_TEST.xlsx"

Purpose:
Broad acquisition mode.

It pulls as much as allowed from selected sources and writes raw/normalized records into Bulk_Intake_Raw.

Default behavior:

* writes to Bulk_Intake_Raw
* does not write to Future_Projects
* does not write to Rejected_Archive
* includes manual/error/access-test sources as stub rows
* useful for debugging and source universe expansion

This is the preferred mode for "collect first, clean later."

---

9. Important command-line parameters

--config
Path to connector CSV.
Default: tenderfinder_dev_app_endpoints.csv

--from-master
Read Source_Register / Run_Queue from a master workbook for sync reporting.

--write-master
Target workbook to write to.
Must be copied v7/test/bulk workbook.
Never use production v6.

--v6
Source v6 workbook used to create v7/test workbook if target is missing.

--tier
Filter connectors by tier.

--category
Filter connectors by category prefix, e.g. B.

--only
Run specific source ids.

--out
Output path for review/probe or raw output directory.

--max-records
Max records per connector for normal mode.

--probe
Resolve endpoints only; no data pull.

--dry-run
Pull/classify but do not write master.

--min-fit-score
Only write records above score threshold.
Current scoring is heuristic and not calibrated enough to use high thresholds blindly.

--max-write-per-source
Cap the number of records eligible for Future_Projects write from each source.

--review-only
Create review output; do not open/save/backup master workbook.

--bulk-intake
Patch 3 raw acquisition mode; writes to Bulk_Intake_Raw by default.

--promote-to-future-projects
In bulk mode, also promote eligible dev/capital leads to Future_Projects.
Do not use until classification is cleaned up.

--also-write-rejected
In bulk mode, also append rejected/thin/wrong-layer summaries to Rejected_Archive.
Do not use during raw source expansion unless explicitly needed.

--include-tier2
In bulk mode, include Tier 2 sources.

--include-tier3
In bulk mode, include Tier 3 sources.

--include-trailing-context
In bulk mode, include trailing/context sources like permits.

--include-wrong-layer
In bulk mode, include wrong-layer/disabled sources as stubs or rejected candidates for debugging.

--max-records-per-source
In bulk mode, per-source record limit. Overrides --max-records when set.

--skip-paid
Skip paid sources.

--skip-login
Skip login-required sources.

--sync-registry
Emit Source_Register to connector CSV sync report.

--list
Print technical connector registry.

---

10. Safety rules

Hard rules:

* Never write to TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx.
* Never overwrite v6.
* Always write only to copied v7/test/bulk workbook.
* Backup must succeed before workbook write.
* If backup fails, stop before load/write/save.
* Do not scrape login-only portals.
* Do not bypass paid portals.
* Do not silently fall back to "similar" datasets.
* Do not treat building permits as Future_Projects by default.
* Do not mix Active_Tenders and Future_Projects.
* Uncertain AI extraction must be marked Needs Review.
* Raw outputs and run logs must be kept for QA.
* Do not run from _ss snapshot/archive folder.

Patch 3 adds safer raw intake:

* Bulk_Intake_Raw can contain messy raw records.
* Future_Projects should remain curated / reviewed.
* Bulk mode should not promote to Future_Projects unless explicitly requested.

---

10a. Connector error behavior

This section defines the required fail path for any connector that cannot be fetched successfully. All cases below apply whether the runner is in dry-run, review-only, or write-master mode.

Error types and required handling:

* connection_error (network unreachable, DNS failure, timeout):
  - Log immediately to Run_Log with: connector id, error type, timestamp, error message.
  - Write stub row to Bulk_Intake_Raw: classification = fetch_error, status = error, records_pulled = 0, error field = full exception message.
  - Continue to next connector. Do not abort the run.

* http_error (4xx or 5xx response):
  - Log to Run_Log with HTTP status code.
  - Write stub to Bulk_Intake_Raw: classification = fetch_error or access_denied (401/403), status = error, records_pulled = 0, error = HTTP status + response snippet.
  - Continue to next connector.

* schema_error (endpoint reachable but returned unexpected structure):
  - Log to Run_Log.
  - Write stub to Bulk_Intake_Raw: classification = wrong_layer or schema_too_thin as appropriate, status = error, records_pulled = 0, error = schema mismatch description.
  - Continue to next connector.

* empty_response (reachable, valid schema, zero records returned):
  - This is not an error. Log to Run_Log.
  - Write stub to Bulk_Intake_Raw: classification = context_only or the resolved classification, status = ok, records_pulled = 0.
  - Continue.

General rules:

* Never abort an entire run because a single connector fails.
* Never silently skip a connector. Every attempted connector must have at minimum one row in Run_Log and one stub in Bulk_Intake_Raw.
* Do not retry automatically within the same run. Retries must be explicit on the next run or via manual probe.
* The error field in Bulk_Intake_Raw must always contain a human-readable description, not just an exception class name.

A developer adding a new Patch 4 connector must ensure the connector raises a typed exception (connection_error, http_error, schema_error) that the runner can classify. Generic bare exceptions that fall outside the classifier produce unknown_error stubs and must be avoided.

---

11. What the program has already proven

The runner has passed these types of tests:

* compile check
* connector list
* Source_Register sync
* endpoint probe
* manual/P3 short-circuit
* v6 write refusal
* backup hardening
* limited write to copied v7/test workbook
* formula preservation
* duplicate Project ID preservation
* RO100158 stage collapse logic
* Patch 3 bulk intake to Bulk_Intake_Raw
* all-source bulk intake test into copied v8 workbook

Known good source behavior:

* Township of Langley development activity pulls real development application records.
* Maple Ridge development applications pulls real development application records.
* Vancouver building permits can pull lots of records but should be treated as trailing/context.
* Vancouver city projects can pull capital/context records.
* New Westminster/Delta can pull records but mostly permits/trailing context.
* Some other sources currently need exact endpoint repair or manual/P3 workflow.

---

12. What the program does not do yet

It does not yet:

* fully automate all 68 Source_Register sources
* scrape paid/login portals
* parse GC invitation emails automatically
* parse PDFs/council agendas with P3 extraction
* reliably extract owner/applicant/civil consultant from every source
* reliably know tender timing from development applications
* calibrate final TENDER_FINDER fit scores enough for automated production gates
* convert all active tender portals into technical connectors
* maintain a production-grade scheduler
* perform Deep Research source discovery
* deduplicate Bulk_Intake_Raw into project-level opportunities automatically
* distinguish every permit source from future project source perfectly

---

13. Current strategic gap

The project already has a broad 68-source Source_Register, but the runner only has 16 technical connectors.

The next big step is not just cleaning the 610-row bulk output.

The next big step is source expansion:

Source_Register 68 sources
-> map to technical connector/workflow
-> identify duplicates
-> identify missing source candidates
-> add only real non-duplicate sources
-> create connectors or manual workflows by source type

---

14. How to add new sources correctly

Do not blindly add source rows.

For each potential source, decide:

* Is this already in Source_Register under another name?
* Is it an active tender source?
* Is it a future project / capital plan source?
* Is it a municipal dev application source?
* Is it a council/agenda/PDF source?
* Is it paid/login-only?
* Is it email-forwarded / GC invite workflow?
* Is it public API/RSS/HTML/PDF?
* Is it automatable now?
* Is it useful to TENDER_FINDER's civil/earthworks scope?
* Should it route to Active_Tenders, Future_Projects, Bulk_Intake_Raw, Run_Queue, or Paid_Intelligence?

Suggested fields for every new source:

* source_id
* source_name
* category
* tier
* owner / organization
* geography
* platform
* fetch_type
* official_url
* endpoint_url
* access_status
* automation_feasibility
* output_route
* prompt_type
* status
* notes
* duplicate_check
* recommended_next_action

---

15. Categories to use for source expansion

Existing A-G categories:
A_active_tender
B_dev_applications
C_council_agendas
D_capital_future_infrastructure
E_paid_intelligence
F_gc_developer_invites
G_news_early_signal

Possible new expanded categories:
H_utilities_crown_port_airport
I_first_nations_indigenous_infrastructure
J_institutional_public_sector
K_private_developer_pipeline

---

16. Best next sources to expand into

High priority non-municipal / broader sources:

* BC Bid
* CivicInfo BC Bids & Tenders
* CivicInfo Construction RSS
* bids&tenders municipal portals
* Metro Vancouver Procurement
* Metro Vancouver Current & Upcoming Projects
* TransLink Procurement / Ariba
* BC Hydro bid opportunities / BC Bid filter
* FortisBC contractor/vendor sources
* YVR supplier opportunities
* Port of Vancouver procurement
* Infrastructure BC projects
* BC MoTI highway/bridge construction opportunities
* CanadaBuys BC construction searches
* BidCentral
* BuildingConnected GC invitations
* Procore GC bid invitations
* SmartBid / iSqFt / TradeTapp
* estimator inbox auto-forward workflow
* First Nations infrastructure / procurement sources
* school district / university / health authority capital procurement
* private developer project pipelines
* GC subcontractor prequalification pages

---

17. What another chat should not do

Do not:

* modify Excel workbooks unless explicitly asked
* write to v6
* run production writes
* scrape login-only portals
* bypass paid portals
* invent endpoints
* silently use wrong layers
* duplicate Source_Register entries
* treat raw bulk records as verified leads
* route building permits directly to Future_Projects
* mix Active_Tenders and Future_Projects
* remove safety gates
* remove Run_Log / Source_QA / raw JSON outputs
* remove backup requirements
* work from _ss archive snapshot
* change fit score weights without documenting the reason
* change stage rank hierarchy without documenting the reason
* silently skip failed connectors

---

18. Recommended next task for a Deep Research chat

The best next research task is:

Expand TENDER_FINDER's source universe beyond the existing 68 Source_Register concepts without duplicating existing sources.

The Deep Research chat should:

1. Take the current 68-source baseline as "do not duplicate."
2. Search for additional real source candidates.
3. Classify each source by category and source type.
4. Mark whether it is API/RSS/HTML/PDF/email/paid/manual.
5. Identify which ones are automatable now.
6. Identify top 20 highest-value additions.
7. Produce a CSV-ready table.
8. Produce a "do not add / duplicate" list.
9. Recommend the next 10 technical connectors to build.

---

19. Recommended next task for a coding chat

Before adding Patch 4 connectors, create a Source Expansion Audit.

The coding chat should:

1. Read Source_Register from master workbook.
2. Read tenderfinder_dev_app_endpoints.csv.
3. Read Run_Queue, Automation_Plan, Paid_Intelligence if available.
4. Produce source_expansion_mapping.csv.
5. Identify source concepts with no connector.
6. Identify connectors with no Source_Register mapping.
7. Identify duplicates.
8. Recommend which sources become API/RSS/HTML/PDF/email/paid/manual workflows.
9. Do not modify master workbook.
10. Do not run write-master.

Only after that should it create Patch 4 connectors.

---

20. Fit score algorithm

The fit_score column appears in Bulk_Intake_Raw, Future_Projects, and classification routing. This section defines the current heuristic scoring logic so it can be understood, reproduced, and improved.

The score is an integer from 0 to 100. It is heuristic, not calibrated for production gates. Do not use high thresholds (e.g., min-fit-score > 50) for automated promotion without manual review.

Scoring components:

A. Geography match — up to 30 points

Check the municipality / address field against the priority geography list from section 3.

* Surrey, Township of Langley, City of Langley, Maple Ridge, Pitt Meadows: 30 points
* Metro Vancouver or Fraser Valley (other municipalities): 20 points
* Broader BC with relevant civil context: 10 points
* Outside geography or unknown: 0 points

B. Scope keyword match — up to 40 points

Scan scope_summary, application_type_stage, and application_no fields for civil keywords.
Award 5 points per keyword match, up to a maximum of 40 points.

Core keywords (5 points each):
excavation, grading, earthworks, watermain, water main, storm sewer, sanitary sewer,
drainage, roadworks, paving, subdivision servicing, site servicing, land servicing,
utilities, pipe, manhole, curb, sidewalk, bridge, retaining wall, dike, pump station,
trench, ESC, erosion, site preparation, clearing, demolition

C. Known client / owner match — up to 20 points

Check owner_applicant field against the known important clients / owners / targets list from section 3.

* Exact or partial match to a known target: 20 points
* No match or unknown: 0 points

D. Stage indicator — up to 10 points

Check application_type_stage for signals that the project is active or upcoming, not completed.

* Keywords suggesting active/current/pending work: 10 points
  (active, current, in progress, pending, conditional, applied, submitted, received, under review, approved)
* Keywords suggesting completed or closed work: 0 points
  (complete, completed, closed, withdrawn, cancelled, expired, refused)
* Stage unknown or missing: 5 points (neutral)

Total maximum: 100 points.

Routing thresholds (indicative, not hard gates):

* 60 and above: eligible for Future_Projects consideration after human review
* 30 to 59: write to Bulk_Intake_Raw; flag for manual review
* Below 30: likely Rejected_Archive; still write to Bulk_Intake_Raw in bulk mode

The fit_score must always be written to the record even if it is 0. A missing score is not the same as a zero score.

When modifying the scoring weights or keyword list, document the change in the run log and in a comment in tenderfinder_guards.py. Do not silently change weights.

---

21. Workbook tab schemas

This section defines the expected column structure for the key workbook tabs. Bulk_Intake_Raw columns are already defined in section 7.5. The tabs below have not previously been specified.

21.1 Future_Projects columns

* project_id — unique dedup key (generated from municipality + application_no or address hash)
* application_no — source application number
* address — civic address or project location
* municipality — normalized municipality name
* owner_applicant — name of applicant / owner / developer
* application_type_stage — application type and current stage as returned by source
* stage_rank — integer rank used for collapse logic (see section 22); not visible to reviewer
* scope_summary — normalized text description of project scope
* fit_score — integer 0–100 from scoring algorithm (see section 20)
* fit_class — formula-preserved column; do not overwrite with Python
* source_id — connector id that produced the record
* source_name — human-readable source name
* source_url — direct link to source record if available
* first_seen_date — date the record first appeared in the workbook
* last_updated_date — date the record was most recently updated by a run
* status — active / needs_review / archived
* notes — operator or run notes

Rules:
- fit_class column must never be overwritten by the writer; it is Excel-formula-driven.
- project_id must be stable across runs. Do not regenerate it on re-import.
- first_seen_date must not be updated on re-import of an existing project_id.

21.2 Active_Tenders columns

* tender_id — unique key (source id + tender number or hash)
* tender_name — project or contract name as published
* owner — issuing authority or owner
* municipality — normalized municipality
* scope_summary — description of scope
* fit_score — integer 0–100
* source_id — connector id
* source_name — human-readable source name
* tender_type — public / invited / negotiated / unknown
* issue_date — date tender was issued
* closing_date — bid closing date
* estimated_value — published estimated contract value if available
* source_url — direct link to tender notice
* first_seen_date — date first captured
* status — open / closed / awarded / unknown
* notes — operator notes

Rules:
- Active_Tenders must never be mixed with Future_Projects.
- Closing dates must be preserved exactly as published; do not normalize to a date type if the source provides a string.
- Closed/awarded tenders should be moved to Rejected_Archive after Example Reviewer review, not deleted in place.

21.3 Run_Log columns

* run_id — unique run identifier (timestamp-based)
* run_timestamp — ISO datetime of run start
* run_mode — dry_run / review_only / write_master / bulk_intake / probe / list / sync_registry
* connectors_attempted — count of connectors selected for this run
* connectors_succeeded — count of connectors that returned records without error
* connectors_failed — count of connectors that produced any error type
* records_pulled_total — total raw records fetched across all connectors
* records_classified_lead — count classified as dev_application_lead or capital_project
* records_classified_tender — count classified as active_tender
* records_classified_rejected — count classified as rejected/trailing/wrong-layer
* records_written_future_projects — count written to Future_Projects tab
* records_written_active_tenders — count written to Active_Tenders tab
* records_written_bulk_intake — count written to Bulk_Intake_Raw tab
* errors_summary — comma-separated list of connector ids that errored, with error type
* operator_notes — any notes added by the operator at run time
* duration_seconds — total elapsed time for the run

Rules:
- Every run must produce at least one Run_Log row, even if zero records were pulled.
- errors_summary must never be empty if connectors_failed > 0.

---

22. Stage hierarchy for Future_Projects collapse and dedup

When multiple records share the same project_id (same project seen across multiple sources or multiple runs), the writer must collapse them into a single best row rather than duplicating.

The collapse rule: keep the record with the highest stage_rank. If two records have equal stage_rank, keep the one with the most recent last_updated_date.

Stage rank values (higher = preferred):

* Rank 5 — active, current, in progress, under construction, open
* Rank 4 — pending, conditional, in review, advanced, authorized
* Rank 3 — applied, submitted, received, approved (pre-construction)
* Rank 2 — on hold, deferred, referred
* Rank 1 — complete, completed, closed, withdrawn, cancelled, expired, refused

Assignment rules:

* Stage rank is assigned by matching application_type_stage text against the keyword lists above (case-insensitive, partial match is acceptable).
* If the stage text contains no matching keyword, assign rank 3 as a neutral default and flag status = needs_review.
* Rank assignment must be logged in notes for any record where the match was ambiguous.
* A Rank 5 or Rank 4 record must never be replaced by a Rank 1 record, even if the Rank 1 record is more recent. A project appearing as "completed" in a later run should not overwrite a record that was previously marked "in progress" without human confirmation.
* Source ids from all collapsed records must be preserved as a comma-separated list in a sources field rather than discarding any.

The stage_rank value must be written to the Future_Projects tab as a hidden column so the collapse logic can be audited without reading the raw JSON.

---

23. Reserved for future additions

This section is intentionally left open for Patch 4 specifications.

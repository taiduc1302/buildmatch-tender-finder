# PROJECT STRUCTURE — Tender Finder

**In plain English:** this is a map of the folder. If you just want to run the
demo, you don't need this file — see `README.md`. If you're a developer about
to make changes, the two things worth knowing are: (1) almost all the actual
program logic lives in one folder, `01 Code\CONNECTOR_SWEEP\`, and (2) one
file in there, `tenderfinder_demo_three_buckets.py`, is the main program that
does the actual work — everything else supports it (tests, docs, sample data).

```
Tender_Finder_Generic_Portable_Package_YYYYMMDD_HHMMSS\
│
├── README.md / INSTALL.md / RUNBOOK.md          ← start here
├── PROJECT_STRUCTURE.md / FUTURE_WEB_APP_PLAN.md
├── SANITIZATION_REPORT.md / PORTABLE_PACKAGE_AUDIT.md
├── README_QUICKSTART.md / README_INSTALL.md / README_START_HERE.txt
│       (original quickstart docs, sanitized — kept because verify_package.bat
│        requires them and they document the original UX)
├── Email_Setup_Guide.md / MANUAL_PORTAL_WORKFLOW.md / SOURCE_STATUS_EXPLANATION.md
├── KNOWN_LIMITATIONS.md / PATCH_NOTES.md / PACKAGE_MANIFEST.md
├── TENDER_FINDER_FINAL_PRODUCT_HANDOFF.md       ← original product handoff (sanitized)
├── TENDER_FINDER_Connector_Coverage_Map.csv     ← which sources are coded vs manual
│
├── *.bat                                        ← launchers (see "Entry points")
│
├── 00 Master\                                   ← master tracker workbook TEMPLATE
├── 00_Context\                                  ← product/technical context briefs (sanitized)
├── 01 Code\
│   ├── tenderfinder_agent2.py                   ← older standalone agent (kept for reference)
│   └── CONNECTOR_SWEEP\                         ← THE ENGINE (see below)
├── 02 Runbooks And Plans\                       ← project plans, run packs, handoff request docs
├── 03 Active and QA Runbooks\                   ← Task D / Task G workbook templates (checklists)
├── 04 RESEARCH REFERENCE\                       ← source research, agent build plan, register expansion
├── 05_PROMPTS\                                  ← LLM prompt pack (scoring/screening prompts)
├── 06 QA\                                       ← QA review CSV for replacement source candidates
├── docs\                                        ← engine docs + docs\history\ (patch/QA reports)
├── inputs\all_live_review.xlsx                  ← SYNTHETIC demo review workbook
├── demo_data\email_alerts\*.eml                 ← SYNTHETIC alert emails
├── latest_verified_output\demo_synthetic_sample\ ← sample output built from synthetic data
├── user_data\email_alerts\                      ← your inbox/logs for email intake (starts empty)
└── packaging\macos\                             ← macOS launcher equivalents
```

## The engine: `01 Code\CONNECTOR_SWEEP\`

| File | Role |
|---|---|
| **`tenderfinder_demo_three_buckets.py`** | **Main entry point.** Reads the review workbook (Track A leads), optionally sweeps live public tender pages (Track B), runs email alert intake, scores/routes rows, writes the three-bucket demo workbook + talk track + build report, then builds the slim "user master" with a production anti-fixture guard. ~8k lines; CLI: `--review-xlsx --out-dir [--no-fetch] [--email-intake] [--email-import-path]` |
| `tenderfinder_launcher_gui.py` | Tkinter GUI wrapper around the demo builder + email import folder UX |
| `tenderfinder_email_intake.py` | Provider-neutral `.eml` parsing → tender rows (no credentials) |
| `tenderfinder_email_guidance.py` | Email setup state detection + user guidance sheets |
| `tenderfinder_raw_sweep.py` | Bulk source harvester driven by the master workbook source register |
| `tenderfinder_source_registry.py` | Coded source registry (endpoints, access methods) |
| `tenderfinder_source_backlog.py` | Source-universe backlog sheets (growth roadmap) |
| `tenderfinder_live_link_checker.py` | Link preflight / URL audit with safe long-path fallback writer |
| `tenderfinder_link_preflight.py` | Preflight integration for source URLs |
| `tenderfinder_master_io.py` | Controlled read/write of the master tracker workbook (backups, write gates) |
| `tenderfinder_review_workbook.py` | Review-workbook discovery chain shared by GUI + .bat launchers |
| `tenderfinder_package_paths.py` | Package-root detection, user_data folder management |
| `tenderfinder_guards.py` | Write-protection / safety gates |
| `tenderfinder_bulk_io.py` | Bulk CSV/JSON I/O helpers |
| `tenderfinder_surrey_inprocess.py` | Surrey in-process PDF lead parser |
| `tenderfinder_dev_app_endpoints.csv` | Development-application endpoint register |
| `data\` | Source-universe backlog workbook + candidate source CSV (public sources) |
| `tests\` | 23 standalone test scripts + fixtures (run each with python; see RUNBOOK) |
| `requirements.txt` / `requirements-dev.txt` | Runtime / test dependencies |
| `.env.tenderfinder.local.example` | Optional search-API key env file format |

## Entry points (batch launchers)

| Launcher | What it does |
|---|---|
| `setup_venv.bat` → `setup_tenderfinder_environment.bat` | Create `.venv`, install deps, optional desktop shortcut |
| `run_demo_synthetic.bat` | **Added in this package** — fully offline demo on synthetic data |
| `run_tenderfinder_demo_fast.bat` | Demo without live fetch (package inputs + email inbox) |
| `run_tenderfinder_demo.bat` | Full demo incl. live public-site sweep |
| `Launch_TENDER_FINDER_GUI.bat` | GUI |
| `verify_package.bat` | Packaged self-checks (expected: `VERIFY_PACKAGE: PASS`) |
| `01_SETUP_AND_RUN_LIVE.bat` / `02_RUN_FAST_TEST_NO_FETCH.bat` | Combined setup+run conveniences |
| `scripts\package_audit.py` | Sanitization re-scan of the whole package |

## Data flow

```
public sources ──(live sweep / Track B)──┐
review workbook (Track A leads) ─────────┤
.eml alert files ──(email intake)────────┼──► score + route ──► three-bucket workbook
                                         │        │                    │
source registers (00 Master, data\) ─────┘        └── run log, guard ──► slim user master
```

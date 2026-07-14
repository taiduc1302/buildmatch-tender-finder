# BuildMatch Tender Finder

Python-based tender and construction-opportunity intelligence engine. It reads
public-source and approved local inputs, normalizes records, scores civil and
earthworks relevance, and produces reviewable Excel workbooks for active
tenders, future projects, watchlists, and audit trails.

This repository is a clean Git-ready copy of the sanitized portable package.
It contains no local virtual environment, user mailbox state, `.eml` files,
database files, local API-key files, or runtime history.

## Version

This snapshot corresponds to `PATCH_VERSION = "5.23"` in
`01 Code/CONNECTOR_SWEEP/tenderfinder_demo_three_buckets.py`. The live-link
checker has its own component version, `2.1.0`. Pre-Git development history is
available only through the checked-in patch reports and historical documents.

## Setup

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The repository-level `requirements.txt` includes all third-party packages
found in runtime code and repository tests. `tkinter`, `email`, `urllib`, and
the other unlisted imports are part of Python's standard library.

## Offline validation

The packaged no-fetch entry point is:

```bat
02_RUN_FAST_TEST_NO_FETCH.bat
```

Equivalent direct command after the environment is installed:

```powershell
.\.venv\Scripts\python.exe "01 Code\CONNECTOR_SWEEP\tenderfinder_demo_three_buckets.py" `
  --review-xlsx "inputs\all_live_review.xlsx" `
  --out-dir "C:\tenderfinder_out\demo_fast_test" `
  --email-intake --no-fetch
```

This mode does not fetch any external site. Outputs are written beneath
`C:\tenderfinder_out`; package-local user state and history are ignored by Git.

## Project structure

```text
buildmatch-tender-finder/
|-- 00 Master/                    Excel master template
|-- 00_Context/                   historical project context
|-- 01 Code/
|   |-- tenderfinder_agent2.py    legacy standalone future-project pipeline
|   `-- CONNECTOR_SWEEP/
|       |-- tenderfinder_guards.py
|       |-- tenderfinder_raw_sweep.py
|       |-- tenderfinder_demo_three_buckets.py
|       |-- tenderfinder_email_intake.py
|       |-- tenderfinder_launcher_gui.py
|       |-- tenderfinder_live_link_checker.py
|       |-- tenderfinder_master_io.py
|       |-- tenderfinder_source_registry.py
|       |-- tenderfinder_surrey_inprocess.py
|       |-- tenderfinder_dev_app_endpoints.csv
|       |-- data/                 source backlog data
|       `-- tests/                offline tests and non-email fixtures
|-- 02 Runbooks And Plans/
|-- 03 Active and QA Runbooks/
|-- 04 RESEARCH REFERENCE/
|-- 05_PROMPTS/
|-- 06 QA/
|-- demo_data/                    documentation only; `.eml` files excluded
|-- docs/                         current and historical reports
|-- inputs/                       packaged synthetic review workbook
|-- latest_verified_output/       packaged synthetic reference output
|-- packaging/macos/              macOS launch scripts and documentation
|-- scripts/package_audit.py      package content/secrets audit
|-- requirements.txt              combined runtime/test dependencies
|-- .gitignore
|-- 01_SETUP_AND_RUN_LIVE.bat
|-- 02_RUN_FAST_TEST_NO_FETCH.bat
|-- Launch_TENDER_FINDER_GUI.bat
`-- verify_package.bat
```

The root also contains the original runbooks, package audits, changelogs, and
Windows launch scripts required by the portable workflow.

## Scoring entry points

- `tenderfinder_guards.py` contains the primary deterministic fit scoring and
  source/layer guards.
- `tenderfinder_raw_sweep.py` collects, normalizes, routes, and applies source-
  specific filters.
- `tenderfinder_demo_three_buckets.py` builds active/future/watch outputs and
  contains tender/civil matching rules.
- `tenderfinder_agent2.py` is an older standalone scorer that optionally reads
  `ANTHROPIC_API_KEY` from the process environment.

Keyword externalization is intentionally not part of this repository-prep
change; current scoring behavior is preserved exactly.

## Known issues

Two pre-existing Patch 5.23 validation failures are intentionally documented
and not fixed in this repository-prep task:

1. Fixture/synthetic future-project rows can reach `Outreach_Tracker` because
   `select_user_future_projects_rows()` does not apply
   `_is_fixture_or_example_row()` before returning selected rows. See
   `01 Code/CONNECTOR_SWEEP/tenderfinder_demo_three_buckets.py:6761` and the
   downstream outreach construction at line 6853. The final guard reports
   `No fixture/synthetic/example rows in Outreach_Tracker: FAIL`.
2. Dashboard `future_full` is populated from raw `future_total` at
   `tenderfinder_demo_three_buckets.py:7146`, while verification recounts the
   demo sheet with fixture rows excluded at lines 7285-7296. This produces the
   known Dashboard counter mismatch.

These are real consistency defects in the user-master output path. Do not
weaken the validation checks to hide them.

## Credentials and generated data

No credential file is committed. Optional search and Claude integrations read
keys from environment variables or an ignored local env file. Runtime-created
`.venv/`, `user_data/`, `demo_history/`, logs, email messages, databases, and
ZIP archives are ignored.

Live fetching, scoring changes, BuildMatch/Neon integration, Git remotes, and
publishing are outside the scope of this snapshot preparation.

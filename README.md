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
|       |-- tenderfinder_keywords_config.py
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
|-- config/                       company profile + editable keyword workbooks
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

- `tenderfinder_keywords_config.py` strictly loads and validates the shared
  company profile and active rules in `config/keywords.xlsx`.
- `tenderfinder_guards.py` applies the configured deterministic fit scoring and
  source/layer guards.
- `tenderfinder_raw_sweep.py` collects, normalizes, routes, and applies source-
  specific filters, including configured Vancouver signal word lists.
- `tenderfinder_demo_three_buckets.py` builds active/future/watch outputs and
  applies the configured tender/civil matching rules.
- `tenderfinder_agent2.py` is an older standalone scorer that optionally reads
  `ANTHROPIC_API_KEY` from the process environment. It is frozen legacy code:
  it keeps its own built-in keyword lists and does not read `keywords.xlsx`.

Scores, tiers, gates, and labels always reflect current `keywords.xlsx`.
Editing rules changes **all records'** evaluation on the next run, including
previously collected records. Stored review-workbook `fit_score` values are
audit inputs only: the main pipeline recomputes current score, signal quality,
and score-based routing before it builds any output. Records that no longer
meet the Future Projects gate remain visible in the run log/build report and
previously tracked Outreach rows keep their user-owned follow-up fields.

Historical packaged values such as 74, 81, and 65 were snapshot-era scores
copied by the old replay stage. They are intentionally superseded by the
current workbook on every run; they are not a compatibility target.

Documented limits are narrow. `tenderfinder_agent2.py` remains static. A
replayed Vancouver permit can refresh its score and labels, but its special
permit tier remains stored if the old review workbook lacks the raw permit
attributes that tier requires. Tender candidates that were never persisted
cannot be retroactively rescored; newly parsed tender rows always use the
current configuration.

## Configuring for your company

1. Keep `config/keywords_template.xlsx` unchanged as the clean handoff copy.
2. Copy it to `config/keywords.xlsx` and fill in `Company_Profile`: company
   name, regions, preferred work types, and known clients (one value per row).
3. Optionally tune the `Keywords` sheet. Its dropdowns show the allowed match
   types, categories, and Y/N active state; the `Instructions` sheet includes
   worked examples. `exact` means trimmed, case-insensitive equality against
   any preserved business field (for example, the full title), not equality
   against one concatenated record blob.
4. In the launcher, click **Validate keywords**. A bad or missing workbook
   stops the run with a row-specific message; there is no hidden fallback.
5. Run TENDER_FINDER normally after validation passes.

Profile values create sensible defaults: regions become geography/+8 rules,
work types become positive/+9 rules, and known clients become client/+6 rules.
If the same normalized `(keyword, category)` is also present in `Keywords`,
that explicit row wins, including when it is set to `active = N`.

The pre-filled live workbook reproduces the original Tybo behavior: base score
35, +9 per positive hit, -12 per negative hit, one +8 geography bonus, one +6
known-client bonus, and the same 0-100 cap, civil gates, and Vancouver routing
thresholds. Only the Vancouver word lists are editable; their thresholds stay
in code.

## Known issues

No open data-integrity issue is currently documented for the slim user-master
anti-fixture path. Broader product and live-connector limitations remain
documented in `KNOWN_LIMITATIONS.md` and `DEMO_LIMITATIONS.md`.

## Fixed

- 2026-07-14: `_is_fixture_or_example_row()` now excludes fixture rows before slim `Future_Projects`/`Outreach_Tracker` selection, and `future_total_live` keeps Dashboard `future_full` aligned with the validator's non-fixture recount.

## Credentials and generated data

No credential file is committed. Optional search and Claude integrations read
keys from environment variables or an ignored local env file. Runtime-created
`.venv/`, `user_data/`, `demo_history/`, logs, email messages, databases, and
ZIP archives are ignored.

Live connector changes, BuildMatch/Neon integration, Git remotes, and publishing
are outside the scope of this configuration change.

comand in termainal:  
git add .
   git commit -m "Fix fixture leak in Outreach_Tracker + dashboard count mismatch"
   git push

# Tender Finder — Internal Weekly Beta

Tender Finder is a clickable Windows/Python application for collecting approved
public tender and development-project signals, normalizing them, scoring their
fit, and producing reviewable Excel workbooks. It is intended for an internal
weekly operator workflow. It is not production-ready, a hosted service, or a
self-contained executable.

The normal entry point is `Launch_TENDER_FINDER_GUI.bat`. Core orchestration is
implemented separately from Tkinter in
`01 Code/CONNECTOR_SWEEP/tenderfinder_engine.py`, so a future BuildMatch service
can call the engine without automating the desktop GUI. That integration does
not exist yet.

## BuildMatch Tender Finder — AI Opportunity Copilot (Build Week)

The Run tab adds a contractor-profile-driven copilot workflow:

`Contractor profile → public opportunities → deterministic filtering & scoring →
ranked results → OpenAI analysis of a selected opportunity → evidence-based
recommendation → estimator review/export`

- A **persistent data-mode banner** always states the origin and age of the
  loaded data (synthetic / public snapshot / live / cached-live / mixed / unknown).
- **Contractor profiles** — Civil Contractor, Multi-Family Residential Builder,
  General Contractor — selectable in the GUI; the residential/general profiles do
  not penalize interior/mechanical/electrical/HVAC/suite scope.
- **Refresh Development Data** pulls approved public development-application
  records without command-line work, scores them, promotes them as the active
  dataset, and shows truthful current-run statistics. A failed refresh keeps the
  last known-good data and labels it cached/stale.
- **Analyze Selected Opportunity with AI** runs an OpenAI (Responses API) analysis
  with strict structured output, shown separately from — and never overriding —
  the deterministic fit score and routing bucket. Set `OPENAI_API_KEY` (and
  optionally `OPENAI_MODEL`); without a key, deterministic features still work.
- A stable, offline **Public Snapshot** demo (`demo_data/public_snapshot`) powers
  the three-minute presentation.

Details are in `docs/buildweek/` (architecture, live refresh & rollback, data
modes & metrics, presets, OpenAI integration, test results, demo script, Windows
acceptance, known limitations, change index). AI output is advisory and
evidence-referenced; it does not determine eligibility or replace estimator
judgment. There is no hosted SaaS, 24/7 harvesting, or native HeavyBid/Bluebeam
integration.

## Requirements and first launch

- Windows 10 or 11.
- Python 3.11 or newer available through `py`, `python`, or `python3`.
- Internet access during first-run dependency and Playwright Chromium setup.
- Excel or another `.xlsx` viewer/editor for the operator workbooks.

Double-click `Launch_TENDER_FINDER_GUI.bat`. If `.venv` is missing or broken,
the launcher runs `setup_tenderfinder_environment.bat`, reports failures with a
non-zero exit, and opens the GUI only after the environment imports correctly.
The repository-relative launcher remains canonical; setup never rewrites it to
contain a machine-specific path. A Desktop shortcut, when created, points to
that launcher.

The clean release ZIP never contains a copied virtual environment. First-run
installation is therefore expected and can take several minutes.

## Safe weekly workflow

1. Double-click `Launch_TENDER_FINDER_GUI.bat`.
2. Open the **Keywords** tab and click **Validate Keywords**.
3. Click **Run Self-Test** and require `PASS` with zero failed and zero
   `not tested (no fixture)` checks.
4. Run **Offline/Test Run** first when checking local inputs or configuration.
5. Use **Live Run** only when contacting enabled public sources is intended.
6. Review `Keyword_Change_Audit`, then work the slim user master.
7. Use **Open Workbook** or **Open Output Folder** from the GUI.

Self-Test is strictly offline. A process-wide DNS/socket deny guard makes any
network attempt fail and records it in the run manifest. The GUI and
`verify_package.bat` call the same authoritative runner and report passed,
failed, skipped, intentionally excluded, and unavailable-fixture totals
separately.

## Run modes

**Offline/Test Run** uses `inputs/all_live_review.xlsx`, approved local email
files, and local fixtures. It passes `--no-fetch` and does not contact tender
sites.

**Live Run** contacts only enabled, runtime-eligible public sources from
`config/sources.csv`. It does not store portal credentials, log in, bypass a
browser check, or solve a CAPTCHA. A public site can still block automation or
change its structure; one successful source does not establish that all
configured sources work.

**Self-Test** creates unique output and state roots, runs focused security,
configuration, scoring, preservation, launcher, engine, CI, and packaging
tests, then performs a real offline pipeline run. It protects and re-hashes the
canonical keywords workbook, source registry, launcher, and frozen Agent2.

## Editable keywords and scoring

`config/keywords.xlsx` is the canonical operator-maintained scoring workbook.
Its `Keywords` rows expose `keyword`, `match_type`, `weight`, `category`,
`explanation`, and `active`; the implementation also retains the minimal
structured `param` field used by collision/title gates. Supported match types
are `contains`, `exact`, and bounded `regex`.

From the **Keywords** tab an operator can:

- open the workbook or its folder;
- validate row types, duplicates, regex safety, and required sheets;
- force a reload after saving an edit;
- see requested/effective paths, source kind, timestamps, active/inactive
  counts, categories, validation errors, and last-known-good status;
- open workbook instructions.

Editable regex is constrained by pattern length, input length, prohibited
construct checks, and an execution timeout. An invalid row receives a
sheet/row-specific error instead of silently becoming a hardcoded rule.

A valid canonical workbook is atomically snapshotted outside the repository at
`C:\tenderfinder_out\state\user\settings\keywords_last_known_good.xlsx` with
SHA-256 metadata. If the normal canonical workbook later becomes missing or
invalid, Tender Finder may use only that verified snapshot and shows a visible
warning plus the effective path in the GUI and run manifest. A custom
`TENDER_FINDER_KEYWORDS_CONFIG` path does not silently borrow the canonical
snapshot. Repair the canonical workbook before routine operation.

One process/run uses one cached ruleset. **Validate Keywords**, **Reload
Keywords**, a new CLI process, or a new run forces a fresh load; an Excel save
mid-run cannot mix rule versions.

### RESCORE_ALWAYS

Every main-pipeline run recomputes keyword-derived score, signal tier, labels,
gates, and bucket routing from the effective workbook. Stored scores are prior
audit values, not authoritative current values. `Keyword_Change_Audit` records
stable ID, old/new score, tier, route/bucket, rule attribution, and any explicit
legacy exception. A record that falls below the current gate remains visible in
the audit/moved-record path instead of silently disappearing.

The explicit limits are:

- historical Vancouver permit rows without their raw scoring snapshot retain
  the source-specific legacy permit tier, visibly marked as an exception;
- tender candidates that were never persisted cannot be retroactively
  rescored, while every newly parsed candidate uses current rules;
- `01 Code/tenderfinder_agent2.py` is frozen legacy code with its own lists and
  is not part of the GUI/engine path.

## Manual review preservation

Across weekly runs, stable IDs carry forward user-owned `Status`, `Notes`,
`Assigned To`, and `Weekly Review Log` values. Rescoring cannot erase those
fields. If the current rules move a record below an ordinary output gate, its
prior manual information remains available through the preserved/audit path.

## Source Manager and truthful status

`config/sources.csv` is the single configurable registry used by both tender
and development tracks. The GUI reads its counts live; configured, enabled,
runtime-eligible, fixture-tested, and live-verified are different facts.

The **Source Checks** tab supports adding a disabled draft, editing it,
enabling/disabling it, and three deliberately separate operations:

- **Validate Configuration** checks schema, supported adapter, duplicate
  runnable endpoints, and public HTTP(S) syntax. It uses no parser and no
  network, and it never labels a source live-verified.
- **Offline Parser Test** runs the real adapter parser/normalizer against a
  sanitized local fixture. An adapter with no applicable fixture is reported
  `NOT TESTED — NO APPLICABLE OFFLINE FIXTURE`, never PASS.
- **Live Source Test** is an explicit one-source action. It validates every DNS
  destination and redirect as public, uses conservative timeouts, records HTTP
  and parser counts, and is the only action that can assign `verified_live`.

Operational statuses are `verified_live`, `ready_for_live_test`,
`config_valid_only`, `manual_only`, `needs_configuration`, `blocked`,
`wrong_source`, and `deprecated`. Historical `LIVE` text is retained as
history but is not promoted to current `verified_live` without a structured
controlled test.

Source-registry writes use a temp file, flush/fsync, external timestamped
backup, and atomic replacement. Unknown columns are preserved. Unsafe private,
loopback, link-local, credential-bearing, malformed, or duplicate runnable
URLs are rejected before network use; every redirect is revalidated.

## Outputs and mutable state

Normal generated content is external to the program folder:

- selected output workbooks/logs/manifests: beneath `C:\tenderfinder_out` or
  the user-selected output root;
- persistent operator settings and registry backups:
  `C:\tenderfinder_out\state\user\settings`;
- mode-specific history/latest master: beneath
  `C:\tenderfinder_out\state\<mode>`;
- Self-Test state and artifacts: unique folders beneath
  `C:\tenderfinder_out\state\self_test` and the selected Self-Test output root.

Runtime state, source downloads, email content/state, browser profiles,
screenshots, caches, and temporary workbook copies must not be committed.
`config/keywords.xlsx` and `config/sources.csv` are intentional editable source
configuration, so keep ordinary backups of them.

## Engine boundary

`tenderfinder_engine.py` owns JSON-serializable run requests/plans/results,
preflight, source selection, isolated state, manifests, source operations, and
Self-Test. It imports no Tkinter. The GUI calls this contract rather than
duplicating scoring or source-test logic. A future BuildMatch adapter could map
normalized records to BuildMatch's `sourceName + externalId` key, but no web,
Neon, or importer synchronization is included today.

## Offline CI and verification

GitHub workflow `.github/workflows/offline-ci.yml` runs on Windows/Python 3.12,
installs the offline-test dependencies, performs syntax/import checks under a
network deny guard, and runs the authoritative Self-Test. It downloads no
browser and requires no secrets.

Local equivalent:

```powershell
.\.venv\Scripts\python.exe scripts\offline_ci_check.py
.\.venv\Scripts\python.exe "01 Code\CONNECTOR_SWEEP\tenderfinder_self_test.py" --root .
```

Or double-click `verify_package.bat`.

For the complete developer suite, install the test-only requirements and run
pytest from the connector directory:

```powershell
.\.venv\Scripts\python.exe -m pip install -r "01 Code\CONNECTOR_SWEEP\requirements-dev.txt"
Push-Location "01 Code\CONNECTOR_SWEEP"
..\..\.venv\Scripts\python.exe -m pytest tests\ -q
Pop-Location
```

The live OpenAI smoke test is opt-in and is skipped by default. All other
tests are offline and must not contact tender portals.

## Offline Public Snapshot demo

Promote the checked-in, sanitized snapshot without contacting a live source:

```powershell
.\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, r'01 Code\CONNECTOR_SWEEP'); import tenderfinder_snapshot as s; print(s.promote_snapshot(root='.'))"
```

Then launch `Launch_TENDER_FINDER_GUI.bat`, open **Ranked Opportunities**, and
click **Load / Refresh Ranked List**. Select a row before using the optional AI
action. Configure AI only in the current process environment:

```powershell
$env:OPENAI_API_KEY = "<your key>"
$env:OPENAI_MODEL = "gpt-5.6"  # optional; this is the default
```

Never save the key in repository files, workbooks, manifests, or logs.

## Clean source release

Build the deterministic allowlist ZIP outside the repository:

```powershell
.\.venv\Scripts\python.exe scripts\build_clean_release.py --output-dir C:\tenderfinder_out\release --require-clean
```

The builder records release version, source commit SHA, included-file hashes,
excluded categories, and ZIP SHA-256. It excludes `.git`, `.venv`,
`.codex_tmp`, caches, runtime outputs, user/email/browser data, downloaded
pages, temporary files, local env files, credentials, and historical generated
output. `scripts/verify_clean_release.py` verifies paths, duplicate entries,
CRC, per-file hashes, and an optional clean extraction.

## Known limitations

See `KNOWN_LIMITATIONS.md`. In particular, public sites can change, many
configured sources remain unverified, Email Alert Intake is local `.eml`
import rather than mailbox OAuth/IMAP, Agent2 is frozen, and BuildMatch
integration is only a future engine boundary. Do not describe this release as
production-ready or as a self-contained executable.

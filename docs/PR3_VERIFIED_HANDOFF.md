# PR #3 Verified Handoff

Verified on 2026-07-19 in a Windows checkout of this repository. This document
records what was checked in that checkout; it does not treat prior chat logs or
commit messages as proof of live-source or live-API results.

## Repository and pull request

- Starting branch: `claude/buildmatch-tender-finder-completion-03pg2w`.
- Starting commit: `c0d840b1b848b5e4a464e61a91b39754f38ac7b5`.
- Upstream: `origin/claude/buildmatch-tender-finder-completion-03pg2w` at the
  same starting commit.
- Remote: `https://github.com/taiduc1302/buildmatch-tender-finder.git`.
- Draft PR: [#3](https://github.com/taiduc1302/buildmatch-tender-finder/pull/3),
  base `main`, head `claude/buildmatch-tender-finder-completion-03pg2w`.
- At the starting commit GitHub reported the PR open, draft, mergeable/clean,
  with no reviews, conversation comments, or review threads. Its one Windows
  Python 3.12 offline-verification check was successful.
- The local handoff file `BUILDMatch_Tender_Finder_Codex_Handoff.md` was the
  only untracked file at the start. It is local background evidence and is
  deliberately excluded from commits and release artifacts.
- `AGENTS.md` is present; `CLAUDE.md` is absent.

## Product boundary and architecture

The implemented product flow is:

`contractor profile -> approved public opportunities -> deterministic filtering/scoring -> ranked results -> optional AI analysis of a selected opportunity -> estimator review/export`

The deterministic engine remains authoritative. `config/keywords.xlsx` is the
business-rule source, scoring stops on invalid or unavailable configuration,
and `01 Code/tenderfinder_agent2.py` remains frozen legacy code. The optional
OpenAI layer receives approved public fields plus a copy of deterministic
evidence, returns a separate advisory view, and cannot mutate the score,
matches, bucket, or manual estimator fields.

Key boundaries:

- `tenderfinder_engine.py`: GUI-independent run contract, preflight, offline
  Self-Test, deterministic pipeline, and manifests.
- `tenderfinder_refresh_service.py`: eligible-source acquisition,
  normalization/deduplication, validation, candidate scoring, atomic active
  dataset promotion, failure fallback, ranked workbook, and run manifest.
- `tenderfinder_data_modes.py` and `tenderfinder_runtime.py`: provenance,
  current-run metrics, external state, atomic JSON pointers/manifests, and
  last-known-good recovery.
- `tenderfinder_presets.py` plus `config/presets/`: versioned Civil,
  Multi-Family Residential, and General Contractor configurations.
- `tenderfinder_ai_analysis.py` and `tenderfinder_ai_controller.py`: optional
  Responses API structured output, safe caching, error handling, and export.
- `tenderfinder_launcher_gui.py`: Windows operator UI wired to the headless
  refresh, ranking, selected-opportunity, and AI controllers.

## Confirmed implementation

Direct source inspection and offline tests confirmed:

- source eligibility guards exclude blocked, manual-only,
  needs-configuration, wrong-source, deprecated, unsafe, and duplicate
  runnable endpoints;
- normalization, deduplication, validation, timestamped external datasets,
  active-dataset promotion, cached/stale fallback, and reconciled current-run
  metrics are present;
- production refresh uses the full connector sweep, while the small preview is
  diagnostic-only;
- deterministic scoring creates ranked output and keeps BID NOW at zero for
  development-only records;
- formula-prefixed public values are neutralized before Excel output;
- all three contractor presets validate, and residential/general presets do
  not apply the Civil preset's ordinary residential-scope penalties;
- the GUI requires a real ranked-row selection for the primary AI action and
  does not silently substitute the top-ranked record;
- the OpenAI request uses the Responses API `text.format` JSON Schema form with
  `strict: true`, matching the current official API reference; missing keys,
  refusals, schema errors, API errors, caching, and disagreement display have
  offline coverage;
- the checked-in Public Snapshot has 82 records, a manifest capture timestamp,
  a matching content hash, source-provenance fields, and passing sanitization
  and scoring acceptance checks;
- release creation is allowlist-based and excludes runtime state, credentials,
  caches, browser/email data, and the local handoff file.

This completion pass fixed three additional verified defects:

1. deterministic scoring now finishes before active-dataset promotion, so a
   scoring exception returns a failure manifest and retains the prior active
   dataset instead of partially committing the refresh;
2. atomic JSON writes use unique same-directory temporary files plus an
   in-process lock, flush/fsync, close, and replace, preventing concurrent GUI
   workers from colliding or producing Windows `WinError 5`;
3. an AI response with the wrong `record_id` is rejected as a schema mismatch
   instead of being silently relabelled for the selected opportunity.

## Claims corrected or still unverified

- Commit `cc03740abc72217d72f98f0279ca5ff9b4e68c76` does not exist in the
  fetched local refs. The claimed final commit `b54fc3d` exists, but it is not
  the branch tip; multiple commits follow it.
- Historical counts such as 194/8, 216/8, and Self-Test 106/198/199 are not
  current acceptance results.
- The committed snapshot is internally consistent and sanitized, but this
  offline pass did not contact its cited municipal sources and therefore did
  not independently reproduce the claimed capture.
- Prior claims of an 8-source live sweep with 1,439 fetched and 1,209 normalized
  records remain historical evidence only; portal access was intentionally not
  used during this verification.
- A real OpenAI response remains unverified because `OPENAI_API_KEY` was absent.
- The GUI code and headless/widget tests are verified, but human interactive
  acceptance (layout, dialogs, workbook opening, and full operator flow) was
  not performed in this pass.
- The official OpenAI Build Week page confirms a Codex-built project challenge,
  a July 21 submission deadline, and judging that values thoughtful GPT-5.6 and
  Codex use. Devpost remains the authority for full rules, eligibility, tracks,
  and submission requirements. The repository must not claim more than those
  checked sources establish.

Official references:

- [OpenAI Build Week](https://openai.com/build-week/)
- [Responses API structured JSON Schema format](https://platform.openai.com/docs/api-reference/responses-streaming/response/output_item?lang=python)

## Installation and operation

Normal Windows setup:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
```

Launch `Launch_TENDER_FINDER_GUI.bat`. Runtime outputs belong beneath
`C:\tenderfinder_out`, never inside the repository.

For the complete developer suite:

```powershell
.\.venv\Scripts\python.exe -m pip install -r "01 Code\CONNECTOR_SWEEP\requirements-dev.txt"
.\.venv\Scripts\python.exe scripts\offline_ci_check.py
Push-Location "01 Code\CONNECTOR_SWEEP"
..\..\.venv\Scripts\python.exe -m pytest tests\ -q
Pop-Location
.\.venv\Scripts\python.exe "01 Code\CONNECTOR_SWEEP\tenderfinder_self_test.py" --root . --output-root C:\tenderfinder_out\self_test
```

Offline Public Snapshot demo:

```powershell
.\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, r'01 Code\CONNECTOR_SWEEP'); import tenderfinder_snapshot as s; print(s.promote_snapshot(root='.'))"
```

Then open the GUI, load Ranked Opportunities, and select a row. AI remains
optional. For a live AI check, set `OPENAI_API_KEY` only in the process
environment; optionally set `OPENAI_MODEL` (default `gpt-5.6`). Never save the
key in repository files, workbooks, logs, manifests, or cache keys.

## Verification results

Executed with the repository-local Python 3.14.6 `.venv` on Windows:

- `python scripts/offline_ci_check.py`: PASS; 82 Python files syntax-checked,
  13 core imports, zero network attempts.
- `python -m pytest tests\ -q`: 226 passed, 1 skipped, 0 failed; three existing
  pytest return-value warnings.
- focused security, engine-contract, Build Week, and packaging suites before
  the final regression additions: 109 passed, 1 skipped, 0 failed.
- authoritative Self-Test: PASS; 209 passed, 0 failed, 3 skipped,
  3 intentionally excluded, 0 missing-fixture tests; zero network attempts.
- `python scripts/package_audit.py --mode repo .`: PASS after the final code and
  documentation edits; 257 text files and 11 workbooks scanned.

The opt-in live OpenAI test, live portal acquisition, and human interactive GUI
acceptance were not run and must not be described as passing.

## Recommended next task

First complete the owner-only acceptance gate on a normal Windows desktop: run
`scripts/windows_acceptance.ps1`, exercise the documented GUI checklist, and
perform one selected-opportunity live OpenAI smoke test with an owner-provided
key. If those pass, update this document and PR #3 with the exact evidence and
decide whether to mark the draft ready for public review. Do not merge solely
from the offline evidence in this handoff.

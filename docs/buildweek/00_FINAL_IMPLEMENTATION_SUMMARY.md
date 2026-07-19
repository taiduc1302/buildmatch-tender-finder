# BuildMatch Tender Finder — Build Week Final Implementation Summary

This document summarizes the Build Week completion work delivered on branch
`claude/buildmatch-tender-finder-completion-03pg2w`.

## What a Windows user can now do

1. Launch the GUI (`Launch_TENDER_FINDER_GUI.bat`).
2. See a **persistent data-mode banner** stating exactly what kind and age of
   data is loaded (synthetic demo, public snapshot, live, cached-live, mixed, or
   unknown).
3. Choose a **contractor profile** — Civil Contractor, Multi-Family Residential
   Builder, or General Contractor — from the Run tab.
4. Click **Refresh Development Data** to pull approved public development-application
   records without any command-line work. The refresh scores the records, promotes
   them as the active dataset, and shows truthful current-run statistics.
5. Review the ranked opportunities and click **Analyze Selected Opportunity with
   AI** to get an OpenAI evidence-based second opinion, shown separately from the
   deterministic score/bucket.
6. Export or save the estimator-review result.

If refresh fails, the previous known-good dataset is retained and clearly labelled
as cached/stale — the packaged synthetic input is never presented as live and is
never overwritten.

## New service/controller layer (all GUI-independent, JSON-serializable)

| Module | Responsibility |
|---|---|
| `tenderfinder_data_modes.py` | Data-mode enum, `DatasetProvenance`, self-reconciling `RunMetrics`, persistent-banner text, atomic external active-dataset pointer with validate-before-promote and corrupt/missing-pointer recovery. |
| `tenderfinder_presets.py` | Civil / Multi-Family Residential / General Contractor presets as alternate validated keyword workbooks; identify/load/apply-to-copy; manifest fields. |
| `tenderfinder_refresh_service.py` | Headless development-data refresh: eligible-source selection, per-source outcomes, dedup, validation, timestamped dataset, atomic promotion, scoring, manifest, metrics, last-known-good rollback. |
| `tenderfinder_ai_analysis.py` | OpenAI Responses API analysis with strict JSON-schema structured output, caching, prompt-injection protection, bounded retries, missing-key handling. |
| `tenderfinder_ai_controller.py` | Renders deterministic vs AI conclusions separately; JSON/Markdown export. |
| `tenderfinder_snapshot.py` | Loads/validates/promotes the sanitized PUBLIC_SNAPSHOT demo dataset. |

The GUI (`tenderfinder_launcher_gui.py`) calls these through thin, display-agnostic
helpers so no business logic is duplicated in the widget layer.

## Deterministic authority

The deterministic engine keeps sole authority over the fit score, matched keyword
terms, the routing bucket, and every manual field. AI output is strictly
advisory: when it disagrees with the deterministic bucket, the disagreement is
surfaced for human review and nothing is silently rerouted.

## Test status

- Full offline pytest suite: **194 passed, 8 justified skips, 0 failures, 0 errors**
  (deterministic across repeated runs).
- Authoritative offline Self-Test: **PASS**.
- Offline CI check, package audit, clean-release build + verify: **PASS**.
- 8 skips = 7 Tk-display widget tests (headless CI has no tkinter/display; verified
  on Windows) + 1 opt-in live-OpenAI smoke test.

See `06_TEST_AND_ACCEPTANCE_RESULTS.md` for the full breakdown and the external
checks that still require an interactive Windows GUI, live public network, or a
user-owned OpenAI key.

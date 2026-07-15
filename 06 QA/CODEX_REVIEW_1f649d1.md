# Codex targeted review — commit `1f649d1`

Date: 2026-07-14 (America/Vancouver)
Reviewer: Codex
Scope: editable regex safety, `RESCORE_ALWAYS`, manual `Status`/`Notes`, cache
isolation, Vancouver tier consistency, `tenderfinder_agent2.py` isolation,
runtime-state isolation, and the configurable source registry.

## Final outcome

**PASS — Codex targeted review completed and all blocking/high findings
resolved.** No blocking or high-severity finding remains open. External Claude
review is an optional future audit and is not a release gate.

Commit `1f649d1f275a91e42ce36cbdf9b8c7997c1e8926` established the editable
keyword configuration. The review initially found four HIGH findings and one
MEDIUM source-registry gap; final Self-Test then exposed one additional HIGH
package-local email-state write. All are resolved below.

## Findings and resolutions

### [RESOLVED HIGH] Editable regex rules could run without a bound

- The live matcher now caps a pattern at 256 characters, input at 100,000
  characters, and execution at 0.02 seconds; it rejects backreferences,
  lookarounds, conditional groups, and nested unbounded quantifiers before a
  run (`01 Code/CONNECTOR_SWEEP/tenderfinder_keywords_config.py:77-93`,
  `:134-160`, `:269-298`).
- Missing bounded-regex support or a runtime timeout raises a clear hard error;
  no standard-library unbounded fallback exists (`tenderfinder_keywords_config.py:140-159`).
- Regression coverage exercises oversized, nested, backreference, and forced
  timeout cases (`01 Code/CONNECTOR_SWEEP/tests/test_standalone_weekly_release.py:72-99`).

### [RESOLVED HIGH] Runtime output/state could contaminate the repository

- State-root resolution rejects every path beneath the package and defines
  separate history, latest-master, and settings paths
  (`01 Code/CONNECTOR_SWEEP/tenderfinder_runtime.py:49-67`, `:98-115`).
- Engine preflight selects an external state root, passes it explicitly to the
  pipeline, and records config hashes/state/output in a run manifest
  (`01 Code/CONNECTOR_SWEEP/tenderfinder_engine.py:138-194`, `:309-378`).
- Persistent email inboxes, logs, duplicate state, and user settings now route
  to the external settings root. Old package-local settings and `.eml` inboxes
  are read only as migration sources and are never moved or deleted
  (`01 Code/CONNECTOR_SWEEP/tenderfinder_runtime.py:70-87`,
  `tenderfinder_package_paths.py:45-92`, `:115-176`).
- Isolation and no-data-loss migration are covered in
  `tests/test_standalone_weekly_release.py:202-271`. The final Self-Test log
  shows its email inbox below its unique external self-test state root, not
  below the repository.

### [RESOLVED HIGH] Manual triage could be lost after keyword-driven moves

- Prior `Future_Projects`, `Outreach_Tracker`, and `Keyword_Change_Audit` rows
  are indexed by stable ID; audit rows also repopulate manual `Assigned To`,
  `Status`, and `Notes` when a lead leaves the visible Future set
  (`tenderfinder_demo_three_buckets.py:6535-6575`, `:6775-6825`).
- The slim audit's row-1 schema is detected separately from the technical
  audit's row-2 schema, closing the E2E-discovered readback ambiguity
  (`tenderfinder_demo_three_buckets.py:5557-5575`).
- `Weekly_Review_Log` is cloned from the previous user master instead of reset
  from the static template (`tenderfinder_demo_three_buckets.py:6579-6590`,
  `:7235-7237`).
- Focused coverage is in
  `tests/test_standalone_weekly_release.py:302-379`. The persisted E2E proof
  shows `53/Future_Projects -> 44/Run_Queue -> 53/Future_Projects`, one audit
  row per run, and unchanged founder-owned fields.

### [RESOLVED HIGH] Vancouver replay contradicted `RESCORE_ALWAYS`

- New development rows persist bounded `keyword_scoring_text`
  (`01 Code/CONNECTOR_SWEEP/tenderfinder_raw_sweep.py:729-740`, `:1958-2029`).
- The unified replay stage recomputes score for every record and recomputes the
  Vancouver tier/route when that snapshot exists. A historical row without
  the needed raw snapshot keeps its stored special tier and receives the
  explicit `legacy_vancouver_scoring_text_unavailable` audit exception; no
  tier is fabricated (`tenderfinder_demo_three_buckets.py:1169-1210`,
  `:1222-1320`).
- Coverage proves both branches in
  `tests/test_standalone_weekly_release.py:272-301`.

### [PASS] Cache behavior is isolated and explicit

- A normal same-process load is stable; `force_reload=True` evicts exactly the
  selected workbook entry before reloading
  (`tenderfinder_keywords_config.py:492-508`).
- Engine preflight and GUI validation force reload at run/validation boundaries
  (`tenderfinder_engine.py:146-150`; `tenderfinder_launcher_gui.py:1741-1747`).
- Unit and black-box cache proofs passed; a temporary workbook edit was picked
  up by a fresh process and GUI validation without altering the canonical file.

### [PASS] Frozen legacy `tenderfinder_agent2.py` remains isolated

- The legacy file identifies its independent built-in lists and prints a
  startup warning (`01 Code/tenderfinder_agent2.py:32-37`, `:708-714`).
- Neither the engine nor GUI imports it, and it does not import the active
  keyword loader. Static assertions are in
  `tests/test_standalone_weekly_release.py:380-399`.
- Therefore edits to `keywords.xlsx` do not affect `tenderfinder_agent2.py`.

### [RESOLVED MEDIUM] Runtime source configuration was split/hardcoded

- `config/sources.csv` is now the single validated registry for tender and
  development tracks (`tenderfinder_source_registry.py:3-12`, `:100-220`).
- Active tender sources are loaded through that registry in
  `tenderfinder_demo_three_buckets.py:229-238` and refreshed after CLI override
  at `:7513-7537`; active development connectors are loaded in
  `tenderfinder_raw_sweep.py:1520-1545`.
- Registry writes are atomic; add/edit/toggle use `upsert_source()` and
  `set_source_active()` (`tenderfinder_source_registry.py:230-280`). Disabled
  drafts may be incomplete, but an active row must use a supported adapter and
  a public URL (`:100-176`).
- GUI controls for Add/Edit/Enable/Disable/Validate/Offline Test/Live Test are
  at `tenderfinder_launcher_gui.py:881-927`, with an explicit live-request
  confirmation at `:1104-1131`. Offline fixture and one-source live testing
  use the display-independent engine seam
  (`tenderfinder_engine.py:574-660`).

## Verification evidence

- Final shared Self-Test: **PASS**, return code 0, `7 passed / 0 failed / 0
  skipped / 4 intentionally excluded`.
- Manifest:
  `C:\tenderfinder_out\standalone_release_final_selftest_v2\self_test\self_test_20260714_222301_d747fb93\run_manifest.json`.
- Manifest hashes: `keywords.xlsx =
  ea7e98097552d099f719b5a54b131386ed37a6202df3b904e07744aa11df429a`;
  `sources.csv =
  5e7d251013f6a0256bc06bcdb17785d473a289bba4777d3268c0af2ce0b85108`.
- FINAL USER MASTER CHECK: overall PASS, nine visible tabs, no fixture leakage,
  Dashboard recounts match, Outreach traceability PASS, Weekly Review Log
  present, original master untouched.
- Focused suites: regex/config `12/12`; standalone safeguards `6/6`; routing
  `21/21`; launcher GUI logic PASS; Outreach persistence PASS; workbook quality
  `5/5`.
- Controlled live evidence (release gate, not Self-Test): one Surrey public
  listing request returned HTTP 200 and 25 normalized candidates; no login,
  credentials, retry, or CAPTCHA bypass was used. Proof:
  `C:\tenderfinder_out\standalone_release_proof\surrey_live_proof.json`.
- Source extension proof: add/edit/enable/offline fixture parse/disable and exact
  canonical restoration:
  `C:\tenderfinder_out\standalone_release_proof\source_extension_proof.json`.
- Real-record keyword proof and persisted manual-field proof:
  `C:\tenderfinder_out\standalone_release_proof\real_record_keyword_proof.json`
  and
  `C:\tenderfinder_out\standalone_release_proof\persisted_rescore_manual_proof.json`.

## Remaining non-blocking limitations

- A disabled `custom` source draft needs a code adapter before it can be
  enabled; the GUI reports this honestly.
- Historical Vancouver rows with no scoring-text snapshot retain only their
  stored source-specific tier, visibly audited as the documented exception.
- Optional legacy `.eml` fixture tests cannot run in the sanitized repository
  because those payloads are intentionally absent; Self-Test lists them under
  `intentionally_excluded`, never as a PASS.

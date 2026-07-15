# TENDER_FINDER stabilization review

Baseline reviewed: `1780ad6a112dd7ca398d705b1f8ffb348e7aaf6a`

Branch: `stabilize/internal-weekly-beta`

Review date: 2026-07-15 (America/Vancouver)
Review policy: focused offline reproduction before application-code changes

Final review status (2026-07-15): **all BLOCKING and HIGH findings are
resolved**. The observations below preserve the original baseline
reproductions; each `Final disposition` records the post-fix result. The full
targeted review is in `CODEX_REVIEW_1f649d1.md`.

## Baseline controls

- Local `main` and `origin/main` were both `1780ad6a112dd7ca398d705b1f8ffb348e7aaf6a` before stabilization.
- Remote annotated baseline tag: `internal-beta-pre-stabilization-1780ad6`.
- Canonical workbook SHA-256: `ea7e98097552d099f719b5a54b131386ed37a6202df3b904e07744aa11df429a`.
- Canonical source registry SHA-256: `5e7d251013f6a0256bc06bcdb17785d473a289bba4777d3268c0af2ce0b85108`.
- Frozen Agent2 SHA-256: `5042fae15f64ce3acf822f538749f67f2b2569e16c13e6b251c8434be9d97137`; its Git blob matches `HEAD` (`2fd896b7e4ecdbd9a1059630aa57e432c0973aab`).
- Baseline shared offline Self-Test returned exit 0 and reported `7 passed / 0 failed / 0 skipped / 4 intentionally excluded`. Manifest: `C:\tenderfinder_out\stabilization_review\baseline_selftest\self_test\self_test_20260715_012422_5fed1aa3\run_manifest.json`.
- The focused trusted-behaviour suite returned `6/6 PASS` before stabilization. This is useful evidence, but it does not cover the security, source-truthfulness, packaging, launcher, or GUI requirements below.

## Findings

### TF-STAB-001 — HIGH — Untrusted Excel text can become a formula

- Affected files: `01 Code/CONNECTOR_SWEEP/tenderfinder_demo_three_buckets.py` (`write_rows`); `tenderfinder_raw_sweep.py` (`_excel_safe_text`); other workbook writers that assign imported/source values directly.
- Reproduction: wrote the required hostile values through `write_rows` to `C:\tenderfinder_out\stabilization_review\baseline_formula_injection.xlsx`, reloaded with openpyxl, and inspected each cell with `data_only=False`.
- Observed: `=HYPERLINK("https://example.com","click")` reloaded with `data_type == "f"`. The `+`, `-`, `@`, and leading-space variants remained unneutralized strings and therefore were not stored using the required explicit literal-text policy. Numeric and date values retained their proper types.
- Expected: every externally sourced/imported dangerous string is stored as literal text, while application formulas, numeric values, and dates retain their intended types.
- Planned correction: add one centralized untrusted-cell sanitizer/writer and apply it at all external/imported workbook boundaries; retain direct assignment for intentional application formulas.
- Final disposition: **RESOLVED** — centralized untrusted-cell protection is applied at workbook/CSV output boundaries; security regression PASS.

### TF-STAB-002 — BLOCKING — Editable network fields permit private destinations

- Affected files: `01 Code/CONNECTOR_SWEEP/tenderfinder_source_registry.py`; development and tender fetch paths in `tenderfinder_raw_sweep.py`, `tenderfinder_demo_three_buckets.py`, `tenderfinder_surrey_inprocess.py`, and source live tests in `tenderfinder_engine.py`.
- Reproduction: constructed an enabled `arcgis_rest_layer` row with `endpoint=http://10.0.0.1/rest/services/x` and called `source_readiness_errors` without making a request.
- Observed: the result was `[]`; the private development endpoint was accepted. `_is_public_url("https://name-that-does-not-resolve.invalid/data")` also returned `True` because hostnames are not resolved.
- Expected: every editable network field must be restricted to resolvable public HTTP(S) destinations and must fail closed.
- Planned correction: centralize URL validation with DNS resolution, public-address classification, supported-scheme checks, and explicit validation for `url`, `rss`, variants, `endpoint`, `last_good_endpoint`, and adapter-specific URLs.
- Final disposition: **RESOLVED** — centralized fail-closed URL/DNS validation rejects local, private, reserved, malformed, and unresolved destinations before transport.

### TF-STAB-003 — BLOCKING — Redirect destinations are not safety-validated

- Affected files: `01 Code/CONNECTOR_SWEEP/tenderfinder_demo_three_buckets.py` (`fetch_url`, `http_fetch_with_headers`); `tenderfinder_raw_sweep.py` (`http_get`); `tenderfinder_surrey_inprocess.py`; `tenderfinder_live_link_checker.py`.
- Reproduction: replaced `urllib.request.urlopen` with an offline fake response whose final URL was `http://127.0.0.1/private` and called `fetch_url("https://public.example.org/start", retries=0)`.
- Observed: the function returned HTTP 200 and the private final URL without rejection. Existing urllib paths automatically follow redirects; the link checker explicitly uses `allow_redirects=True`.
- Expected: automatic redirect following is disabled or every hop is validated before following; a private/reserved redirect is rejected before a second request.
- Planned correction: add safe request helpers with manual bounded redirects and revalidation of every destination; adapt all runtime fetch seams.
- Final disposition: **RESOLVED** — requests and urllib fetchers validate every redirect hop; Playwright blocks unsafe page and subresource destinations.

### TF-STAB-004 — HIGH — Configured, enabled, valid, and operational sources are conflated

- Affected files: `config/sources.csv`; `01 Code/CONNECTOR_SWEEP/tenderfinder_source_registry.py`; GUI and engine source-selection paths.
- Reproduction: loaded all 39 rows and grouped the historic `access_status`/`status` values.
- Observed: all 39 rows are `active=Y`, even though enabled rows include `needs_exact_url`, `manual_p3_only`, `disabled_wrong_layer`, `GATED_OFFICE_NETWORK`, and `DISABLED_PENDING_OFFICE_NETWORK`. There is no formal operational-status column or structured test metadata.
- Expected: enabled remains founder-controlled, while a separate documented status expresses configuration-only, fixture-tested, live-verified, manual, blocked, wrong-source, and deprecated states; non-runnable rows are skipped with visible reasons.
- Planned correction: add backward-compatible operational metadata, status derivation/validation, runtime eligibility, and exact status counts.
- Final disposition: **RESOLVED** — founder-controlled enablement is separate from the documented operational-status vocabulary and runtime eligibility.

### TF-STAB-005 — HIGH — GUI reports a misleading “39 active sources” summary

- Affected files: `01 Code/CONNECTOR_SWEEP/tenderfinder_launcher_gui.py` (`_refresh_source_registry`, `_on_validate_sources`); `tenderfinder_source_registry.py` (`registry_summary`).
- Reproduction: opened the summary code and called `registry_summary` on the canonical registry.
- Observed: the result is only `{total: 39, active: 39, tender: 21, development: 18}`; GUI text presents this as `VALID — 39 sources (39 active...)` with no operational breakdown.
- Expected: separate truthful counts for configured, enabled, live-verified, ready-for-test, fixture-pass, config-only, needs-configuration, manual, blocked, wrong-source, and deprecated.
- Planned correction: expand the summary model and Source Manager columns/status copy.
- Final disposition: **RESOLVED** — GUI and manifests show configured, enabled, runtime-eligible, and every operational-status count separately.

### TF-STAB-006 — HIGH — Configuration-only validation is presented as an offline source test

- Affected files: `01 Code/CONNECTOR_SWEEP/tenderfinder_engine.py` (`test_source_definition`); `tenderfinder_launcher_gui.py` (`Test Selected Offline`).
- Reproduction: called `test_source_definition("surrey_bids_public", allow_network=False)` without a fixture.
- Observed: it returned `passed=True`, `status=PASS_CONFIG_ONLY`, while the GUI labels the action `Test Selected Offline`. No adapter, extraction, or normalization ran.
- Expected: Configuration Validation, Offline Parser Test, and Live Source Test are distinct. Missing fixtures return `NOT TESTED — NO APPLICABLE OFFLINE FIXTURE`, never PASS.
- Planned correction: separate engine operations, add maintained adapter fixtures, and make GUI wording/results explicit.
- Final disposition: **RESOLVED** — configuration validation, offline parser testing, and explicit live testing are distinct operations; missing fixture is never PASS.

### TF-STAB-007 — HIGH — Clean-install and moved-repository launcher portability are unproven

- Affected files: `Launch_TENDER_FINDER_GUI.bat`; `setup_tenderfinder_environment.bat`; Desktop shortcut creation.
- Reproduction: inspected launcher/setup behavior and the Desktop shortcut target.
- Observed: the canonical launcher is currently repository-relative, but setup creates a Desktop shortcut targeting the current absolute `pythonw.exe` and GUI script. No deterministic clean-extract/move acceptance exists, and setup always attempts a large optional Chromium installation.
- Expected: first-run setup is testable, failures are visible/non-zero, moving the repository does not permanently break the canonical path, and shortcuts point to the canonical batch launcher.
- Planned correction: keep the relative launcher immutable, target it from shortcuts, add noninteractive test controls without weakening founder defaults, and prove clean install/move behavior from an extracted release.
- Final disposition: **RESOLVED** — a clean extracted package was installed, moved, relaunched through its shortcut, and exercised through the GUI.

### TF-STAB-008 — HIGH — Setup overwrites the canonical launcher with absolute paths

- Affected file: `setup_tenderfinder_environment.bat`, Step 5a.
- Reproduction: inspected commands writing `%ROOT_LAUNCHER%`.
- Observed: setup truncates and recreates `Launch_TENDER_FINDER_GUI.bat` with absolute paths to `%VENV_PYW%` and `%GUI_SCRIPT%`, replacing the portable checked-in launcher.
- Expected: setup never rewrites the canonical repository-relative launcher.
- Planned correction: remove the rewrite, validate that the launcher exists, and make shortcuts invoke it.
- Final disposition: **RESOLVED** — setup preserves the checked-in relative launcher and shortcuts target that launcher.

### TF-STAB-009 — MEDIUM — A mutable keyword validation report exists inside the repository

- Affected files: ignored `config/keywords_validation_last.txt`; `tenderfinder_keywords_config.py` (`_validation_report_path`).
- Reproduction: inspected ignored files and the existing report.
- Observed: `config/keywords_validation_last.txt` is an ignored runtime report generated while validating `config/keywords_template.xlsx`. Canonical validation routes externally, but validation of another package-local workbook writes beside that workbook.
- Expected: mutable validation/state files live below the external runtime root; legacy generated state is inventoried and preserved before removal/migration.
- Planned correction: route every package-local validation report externally, preserve the existing report in an external migration backup, and add worktree-clean regression coverage.
- Final disposition: **RESOLVED** — package-local validation/state routes to the external runtime settings root; migration sources are read-only and preserved.

### TF-STAB-010 — HIGH — No deterministic clean Windows release builder exists

- Affected files: `scripts/package_audit.py`; `packaging/`; missing release-builder and extraction acceptance.
- Reproduction: inventoried `scripts`, `packaging`, and tracked files.
- Observed: only a historical audit script and macOS helpers exist. There is no deterministic Windows release ZIP builder that emits a manifest, exclusion summary, version/SHA, checksum, and extracted-copy test.
- Expected: reproducible clean source ZIP excludes Git/venv/runtime/user/cache/secret payloads and passes extracted first-run checks.
- Planned correction: add a deterministic packaging script, package audit, checksum, and extraction/launcher acceptance outside the repository.
- Final disposition: **RESOLVED** — deterministic allowlist ZIP builder, manifest/checksum, CRC/extraction verifier, and package audit are implemented and tested.

### TF-STAB-011 — VERIFIED NOT AN ISSUE — Manual fields survive rescoring and moves

- Affected files reviewed: `tenderfinder_demo_three_buckets.py`; `tests/test_standalone_weekly_release.py`; `tests/test_outreach_persistence.py`.
- Reproduction: ran focused preservation tests before stabilization.
- Observed: `Status`, `Notes`, and `Assigned To` were repopulated into `Keyword_Change_Audit` after a `Future_Projects -> Run_Queue` move; `Weekly_Review_Log` was restored. Outreach persistence also passed.
- Expected: founder fields and review history survive every run and remain visible when a row moves below a gate.
- Planned correction: preserve this behavior and add final multi-run E2E evidence using temporary workbooks.
- Final disposition: **VERIFIED NOT AN ISSUE** — final multi-run preservation and Outreach tests PASS.

### TF-STAB-012 — VERIFIED NOT AN ISSUE — Keyword change audit is implemented and visible in the workbook model

- Affected files reviewed: `tenderfinder_demo_three_buckets.py`; `tests/test_standalone_weekly_release.py`.
- Reproduction: constructed a technical RESCORE_ALWAYS event and rebuilt user audit rows.
- Observed: score delta, old/new bucket, manual fields, and one visible audit row were preserved.
- Expected: every recomputed score/tier/bucket change is visible, including below-gate moves and explicit exceptions.
- Planned correction: do not alter semantics; add canonical-byte restoration and deterministic temporary-keyword E2E proof.
- Final disposition: **VERIFIED NOT AN ISSUE** — final temporary-workbook RESCORE_ALWAYS E2E and visible audit test PASS; canonical workbook restored byte-for-byte.

### TF-STAB-013 — VERIFIED NOT AN ISSUE — Vancouver replay is consistent when evidence exists and explicit when it does not

- Affected files reviewed: `tenderfinder_demo_three_buckets.py`; `tenderfinder_raw_sweep.py`; `tests/test_standalone_weekly_release.py`.
- Reproduction: replayed one Vancouver record with persisted `keyword_scoring_text` and one legacy record without it.
- Observed: the replayable row recomputed `noisy -> strong` and `Rejected_Archive -> Future_Projects`; the legacy row retained its stored classification with `legacy_vancouver_scoring_text_unavailable`.
- Expected: recompute from sufficient stored text; never fabricate an unavailable historical score; show the exception.
- Planned correction: preserve and document this behavior; include it in final Self-Test/evidence.
- Final disposition: **VERIFIED NOT AN ISSUE**.

### TF-STAB-014 — MEDIUM — GUI/engine separation exists, but the engine contract is incomplete

- Affected files: `tenderfinder_engine.py`; `tenderfinder_launcher_gui.py`.
- Reproduction: static import checks plus focused engine test.
- Observed: engine imports no Tkinter and GUI calls engine functions. However `RunRequest` lacks explicit source selection/output-root/offline/self-test fields, and `EngineRunResult` lacks timing, source/record/score summaries, warnings/errors/test totals and a direct JSON-safe representation.
- Expected: stable structured, JSON-serializable request/result contract for GUI, CLI, and a future web seam.
- Planned correction: expand dataclasses compatibly, add `to_dict`, populate manifests/summaries, and test that the GUI depends on this seam.
- Final disposition: **RESOLVED** — structured JSON-safe request/result models cover source selection, paths, modes, summaries, warnings/errors, tests, and manifests; engine imports no Tkinter.

### TF-STAB-015 — HIGH — Self-Test can report PASS while required categories and safeguards are untested

- Affected files: `tenderfinder_engine.py` (`SELF_TEST_SCRIPTS`, exclusions, `run_self_test`); `verify_package.bat`; GUI Self-Test.
- Reproduction: ran the authoritative baseline Self-Test.
- Observed: exit 0 with `7 passed / 0 failed / 0 skipped / 4 intentionally excluded`; `not tested because fixture unavailable` is absent and hardcoded to no separate count. Missing `.eml` fixtures are classified as a legacy exclusion. Formula injection, DNS/private redirect safety, source-status truthfulness, launcher, package, and clean-worktree checks are not authoritative gates.
- Expected: one offline runner reports separate passed/failed/skipped/excluded/no-fixture totals and includes every required stabilization safeguard.
- Planned correction: add focused stabilization suites, explicit result categories, zero-network enforcement, canonical restoration, and clean-worktree verification; keep controlled live proof separate.
- Final disposition: **RESOLVED** — the shared process-wide zero-network Self-Test reports pass/fail/skip/excluded/no-fixture separately and runs the real offline pipeline.

### TF-STAB-016 — VERIFIED NOT AN ISSUE — `tenderfinder_agent2.py` remains frozen and isolated

- Affected files reviewed: `01 Code/tenderfinder_agent2.py`; engine and GUI imports.
- Reproduction: compared Git blob/hash to `HEAD` and ran static isolation assertions.
- Observed: file hash and Git blob match baseline; neither engine nor GUI imports Agent2, and Agent2 does not import the active keyword loader.
- Expected: frozen legacy program remains unaffected by editable keywords and stabilization work.
- Planned correction: add immutable hash/blob checks to final gates and never edit this file.
- Final disposition: **VERIFIED NOT AN ISSUE**.

### TF-STAB-017 — VERIFIED NOT AN ISSUE — Future Git identity was corrected without rewriting history

- Affected configuration: repository-local `.git/config` only.
- Reproduction: inspected current config and prior same-author history.
- Observed: baseline commit retains its placeholder metadata, as required. Repository-local future author is now `taiduc1302 <38831891+taiduc1302@users.noreply.github.com>`, an existing same-author GitHub noreply identity found in repository history.
- Expected: valid future identity; no guessed address and no history rewrite.
- Planned correction: none beyond final commit verification.
- Final disposition: **VERIFIED NOT AN ISSUE**.

### TF-STAB-018 — HIGH — Permanent sanitized stabilization evidence is missing

- Affected path: missing `06 QA/RELEASE_EVIDENCE_INTERNAL_BETA_V1/`; missing `06 QA/STABILIZATION_RELEASE_REPORT.md`.
- Reproduction: filesystem inventory.
- Observed: only the prior standalone review/report exist; no permanent evidence set for this stabilization goal.
- Expected: sanitized release evidence covers baseline, security, tests, source status, launcher, package, GUI, controlled live proof, keywords, manual fields, runtime isolation, and final Git SHA.
- Planned correction: create the required evidence directory progressively from authoritative outputs, excluding live pages, user data, secrets, and large binaries.
- Final disposition: **RESOLVED** — sanitized review, security, GUI, live, runtime, package, and release evidence is maintained under `06 QA/RELEASE_EVIDENCE_INTERNAL_BETA_V1/` and in the release report.

### TF-STAB-019 — MEDIUM — Keywords workflow lacks the required dedicated GUI area

- Affected file: `tenderfinder_launcher_gui.py`.
- Reproduction: inspected notebook construction and keyword controls.
- Observed: tabs are Run, Email Alerts, Source Checks, Results/Logs, and Settings/Advanced. Run has only `Open keywords folder` and `Validate keywords`; no dedicated Keywords tab, workbook-open/reload/instructions controls, counts, timestamps, category breakdown, error display, or last-known-good/canonical status.
- Expected: founder-friendly dedicated Keywords tab/panel with the required status and controls while Excel remains the editor.
- Planned correction: add a dedicated tab backed by headless keyword-status functions; preserve all 227 approved rules unchanged and state truthfully that invalid canonical config is a hard stop (no silent partial fallback).
- Final disposition: **RESOLVED** — the dedicated Keywords tab exposes the canonical path, validation/LKG state, counts, categories, errors, scoring semantics, and required workbook actions.

### TF-STAB-020 — HIGH — Source registry edits can lose data and lack durable backups

- Affected file: `tenderfinder_source_registry.py` (`_normalized_source_row`, `load_source_rows`, `write_source_rows`, upsert/toggle paths).
- Reproduction: added an unknown `founder_history_note` column to a temporary canonical copy, loaded and rewrote it through current APIs.
- Observed: `UNKNOWN_COLUMN_PRESERVED=False`; the unknown column was discarded. The write uses a same-directory temporary plus `os.replace`, but does not flush/fsync or create a timestamped backup outside Git runtime state.
- Expected: full-registry validation, temporary write, flush/close/fsync, timestamped external backup, atomic replace, and preservation of unknown columns/historical notes.
- Planned correction: retain original field order plus unknown columns, add external backup routing and durable write semantics, and cover failed-write/restoration paths using temporary registries.
- Final disposition: **RESOLVED** — full-registry validation, unknown-column preservation, external timestamped backup, fsync, and atomic replacement are covered by failure-path tests.

### TF-STAB-021 — HIGH — Master-template discovery could cross installation boundaries

- Affected file: `01 Code/CONNECTOR_SWEEP/tenderfinder_demo_three_buckets.py` (`find_latest_master_workbook`).
- Reproduction: the full checkout Self-Test ran while a newer clean-install candidate existed under `C:\tenderfinder_out`; its log selected that other installation's copied template.
- Observed: a valid package-local template lost to an unrelated copy solely because the foreign copy had a newer extraction timestamp.
- Expected: the current package's valid template is authoritative; external locations are fallback only when the package has no candidate.
- Correction: package-local candidate selection now precedes every external/parent/output fallback.
- Final disposition: **RESOLVED** — focused regression PASS and repeated full Self-Test selected the checkout's own `00 Master` template.

### TF-STAB-022 — MEDIUM — Clean-release bytes depended on checkout line endings

- Affected paths: `scripts/build_clean_release.py`, `.gitattributes`, and Windows launcher files.
- Reproduction: the same launcher Git blob produced LF bytes on the stabilization branch and CRLF bytes after a clean Windows checkout with `core.autocrlf=true`; the resulting clean ZIP SHA changed despite equivalent source content.
- Observed: fixed ZIP metadata was deterministic only within one worktree, not across clean checkouts with different line-ending policies.
- Expected: identical source content produces identical release-entry bytes on Windows, macOS, and Linux.
- Correction: release text is canonicalized to LF, with `.bat`/`.cmd` canonicalized to CRLF; Git attributes make Windows launcher checkout bytes explicit.
- Final disposition: **RESOLVED** — LF/CRLF equivalence regression and repeated clean-release verification PASS.

## Final review decision

The baseline was not eligible for release, but the current stabilization code
has resolved every reproduced BLOCKING and HIGH finding while preserving the
trusted scoring, manual-field, review-history, and frozen-Agent2 behavior.
Codex targeted review is complete. The final package, clean commit, GitHub CI,
normal integration, and tag gates are documented in
`STABILIZATION_RELEASE_REPORT.md`.

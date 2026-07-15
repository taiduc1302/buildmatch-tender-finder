# Tender Finder stabilization release report

Report date: 2026-07-15 (America/Vancouver)

Release scope: trustworthy internal weekly beta; portable Windows source
application, not a production SaaS product and not a self-contained `.exe`.

## 1. Baseline protection

- Starting local `main` SHA:
  `1780ad6a112dd7ca398d705b1f8ffb348e7aaf6a`.
- Starting `origin/main` SHA:
  `1780ad6a112dd7ca398d705b1f8ffb348e7aaf6a`.
- GitHub already contained `1780ad6`; no pre-stabilization push was required.
- Local and remote history were not divergent, so no backup branch was needed.
- Remote annotated baseline tag:
  `internal-beta-pre-stabilization-1780ad6`.
- Stabilization branch: `stabilize/internal-weekly-beta`.
- Main stabilization commit:
  `340e88ba8145a2fd7c30e842d4c1172d60aeaca2`.
- Windows CI portability follow-up:
  `60dbdd6aa9aa3f6571ac112fd4291bdf0151bdd7`.
- Primary PR merge commit:
  `d38de2306a40b7ce6ab6c1b022ab1756de6b45eb`.
- Release reproducibility follow-up:
  `d8c8dd83af08760aa1dc1c98e1f6947546e853af`.
- Follow-up PR merge commit and final artifact source:
  `5805d467aee539985376a3464c98ee7a6e121eb3`.
- Repository-local author:
  `taiduc1302 <38831891+taiduc1302@users.noreply.github.com>`.
- No force push, destructive reset, shared-history rewrite, or rebase was used.

## 2. Findings and fixes

The baseline reproduction details are preserved in
`06 QA/STABILIZATION_REVIEW.md`; this table records each final disposition.

| ID | Severity | Reproduction | Fix | Test | Result |
| --- | --- | --- | --- | --- | --- |
| TF-STAB-001 | HIGH | Hostile `=`, `+`, `-`, `@` values were written through workbook output and reloaded with openpyxl. | Central literal-text guard at external Excel/CSV boundaries. | Formula/type regression in security suite. | RESOLVED; PASS. |
| TF-STAB-002 | BLOCKING | Enabled private endpoint passed readiness validation. | Fail-closed public HTTP(S), DNS, and address classification for every editable network field. | Private/malformed/DNS tests. | RESOLVED; PASS. |
| TF-STAB-003 | BLOCKING | Fake public URL redirected to `127.0.0.1`. | Manual bounded redirects with every hop revalidated; unsafe browser subrequests blocked. | requests, urllib, Playwright redirect tests. | RESOLVED; PASS. |
| TF-STAB-004 | HIGH | All 39 rows were enabled despite incompatible historical states. | Separate founder enable flag, operational vocabulary, and runtime eligibility. | Canonical status classification/skip tests. | RESOLVED; PASS. |
| TF-STAB-005 | HIGH | GUI summary exposed only total/active. | Separate configured/enabled/runtime and all operational-status counts. | Registry and GUI headless tests. | RESOLVED; PASS. |
| TF-STAB-006 | HIGH | Config-only check was labeled offline source PASS. | Distinct Validate Configuration, Offline Parser Test, and Live Source Test operations. | Fixture/no-fixture/operation tests. | RESOLVED; PASS. |
| TF-STAB-007 | HIGH | Clean-install/move behavior had no acceptance proof. | Relative launcher, stable shortcut target, clean extract/setup/move acceptance. | Launcher suite and Windows black-box. | RESOLVED; PASS. |
| TF-STAB-008 | HIGH | Setup rewrote the canonical launcher with absolute paths. | Setup only validates/preserves launcher and points shortcut to it. | Static hash and launcher tests. | RESOLVED; PASS. |
| TF-STAB-009 | MEDIUM | Keyword report could be written beside a package-local workbook. | Validation/LKG state moved to external runtime settings. | Runtime/LKG tests. | RESOLVED; PASS. |
| TF-STAB-010 | HIGH | No deterministic clean Windows release builder existed. | Allowlist ZIP, fixed metadata, manifest, checksum, CRC/extraction verifier, audits. | Packaging suite and final extraction. | RESOLVED; PASS. |
| TF-STAB-011 | VERIFIED NOT AN ISSUE | Multi-run manual-field replay was exercised. | Preserved stable-ID behavior and added final E2E coverage. | Manual triage and Outreach tests. | VERIFIED; PASS. |
| TF-STAB-012 | VERIFIED NOT AN ISSUE | Technical audit rows were rebuilt and reloaded. | Preserved visible RESCORE_ALWAYS audit and added canonical restoration proof. | Temporary-workbook E2E. | VERIFIED; PASS. |
| TF-STAB-013 | VERIFIED NOT AN ISSUE | Vancouver rows with/without scoring snapshots were replayed. | Recompute when evidence exists; explicit legacy exception otherwise. | Vancouver safeguard. | VERIFIED; PASS. |
| TF-STAB-014 | MEDIUM | Engine models lacked required request/result fields. | JSON-safe structured request/result API with no Tkinter import. | Engine contract suite. | RESOLVED; PASS. |
| TF-STAB-015 | HIGH | Baseline Self-Test omitted stabilization safeguards and result classes. | Shared process-wide zero-network runner with separate totals and real offline pipeline. | Clean-checkout and extracted-package Self-Tests. | RESOLVED; PASS. |
| TF-STAB-016 | VERIFIED NOT AN ISSUE | Agent2 imports/hash were compared. | File remained frozen and isolated. | Static isolation and protected hash. | VERIFIED; PASS. |
| TF-STAB-017 | VERIFIED NOT AN ISSUE | Local identity/history inspected. | Correct future GitHub noreply identity configured without rewriting history. | Commit author inspection. | VERIFIED; PASS. |
| TF-STAB-018 | HIGH | Required permanent evidence directory/report were absent. | Sanitized review, screenshots, live, package, runtime, and final report evidence. | Repo/package audits and inventory. | RESOLVED; PASS. |
| TF-STAB-019 | MEDIUM | No dedicated founder Keywords area existed. | Dedicated Keywords tab with path/status/counts/categories/LKG/errors/actions. | GUI headless and Windows visual checks. | RESOLVED; PASS. |
| TF-STAB-020 | HIGH | Unknown source columns were lost; no durable external backup. | Full validation, unknown-column retention, external timestamped backup, fsync, atomic replace. | Success/failure-path registry test. | RESOLVED; PASS. |
| TF-STAB-021 | HIGH | Checkout Self-Test selected a newer template from another installation. | Current package template now wins before external fallbacks. | Foreign-newer/local-older isolation regression plus full Self-Test. | RESOLVED; PASS. |
| TF-STAB-022 | MEDIUM | Equivalent Git content produced different release bytes under LF versus CRLF checkout policies. | Canonical release text bytes: LF except Windows `.bat`/`.cmd` CRLF; explicit Git attributes. | LF/CRLF equivalence and repeated release builds. | RESOLVED; PASS. |

Codex targeted review completed and all blocking/high findings resolved.
External Claude review is an optional future additional audit, not a gate.

## 3. Keyword status

- Workbook: `config/keywords.xlsx`.
- Validation: VALID; effective source is canonical.
- Active: 227; inactive: 0.
- Categories (12): client 19, gate collision 2, gate exclude 28, gate include
  51, gate weak 3, geography 4, civil label 16, negative 15, positive 30,
  tender match 18, Vancouver primary 26, Vancouver secondary 15.
- Last-known-good: verified external snapshot ready; an invalid custom path
  never silently falls back.
- RESCORE_ALWAYS proof: temporary rule disable changed score `52 -> 43`, tier
  `MEDIUM -> LOW`, and bucket `Future_Projects -> Run_Queue`, with matching
  visible audit values. Canonical workbook restored byte-for-byte.
- Manual preservation: `Status`, `Notes`, `Assigned To`, Outreach state, and
  `Weekly_Review_Log` survive rescoring and moves by stable ID.
- Canonical SHA-256:
  `ea7e98097552d099f719b5a54b131386ed37a6202df3b904e07744aa11df429a`.

## 4. Source status

| Source state | Count |
| --- | ---: |
| Total configured | 39 |
| Enabled | 39 |
| Runtime eligible | 27 |
| Verified live | 1 |
| Ready for live testing | 26 |
| Adapter fixture passed | 0 |
| Config valid only | 0 |
| Needs configuration | 3 |
| Manual only | 4 |
| Blocked | 1 |
| Wrong source | 4 |
| Deprecated | 0 |

The categories are not merged. Enabled does not mean parser-tested,
live-verified, or operational. Canonical source SHA-256:
`1901c7cc73e8e240d74d8e534924c7b814f5ad32b68ee442faa52138f40f0306`.

## 5. Tests

Authoritative clean-checkout Self-Test
`self_test_20260715_101135_2ad06d9f`:

- passed: 113;
- failed: 0;
- skipped: 1;
- intentionally excluded: 3;
- not tested due to missing fixtures: 0;
- network attempts: 0;
- exit code: 0;
- clean worktree before/after: PASS.

The single skip is the display-dependent GUI worker E2E in the headless runner.
The three explicit exclusions are controlled live proof, visual GUI
black-box, and frozen Agent2 live execution; each has a separate release gate
or static proof and is not counted as PASS.

The exact GitHub CI environment was then replayed locally after the portability
follow-up. Self-Test `self_test_20260715_102813_ad5b276b` returned `112 passed /
0 failed / 2 skipped / 3 intentionally excluded / 0 no-fixture`, zero network
attempts, and exit 0. The second skip is the clean-worktree assertion while the
two test files were intentionally modified but not yet committed.

Extracted final-package Self-Test
`self_test_20260715_110434_b78f713e`: `112 passed / 0 failed / 1 skipped / 4
intentionally excluded / 0 no-fixture`, zero network attempts, exit 0. The
fourth exclusion records that a source ZIP has no Git checkout metadata.

The same final extracted package was then installed and its Self-Test was run
from the GUI. Run `self_test_20260715_111646_29605475` visibly reported PASS
with the same `112 / 0 / 1 / 4 / 0` totals, zero network attempts, and exit 0.

Focused results include: syntax/import/network guard PASS; security 11/11;
source registry 11/11; keyword configuration 13/13; RESCORE E2E 1/1;
standalone safeguards 7/7; engine 2/2; launcher 5/5; offline CI 2/2; packaging
3/3; routing 21/21; Outreach, review discovery, and tender routing PASS.

## 6. Live evidence

Exactly two public BC development sources were preview-tested with a five-row
limit and no credentials or broad crawl:

- `surrey_devapps_v2`: HTTP 200; parser used; 5 raw, 5 normalized, 0 rejected;
  four meaningful HIGH/MEDIUM records. Result `PASS_LIVE_SOURCE`; persisted as
  the only `verified_live` source with external backup.
- `abbotsford_devapps`: HTTP 200; parser used; 5 raw, 5 normalized, 0 rejected;
  all thin/LOW. Result `LIVE_SOURCE_REVIEW_REQUIRED`; not promoted.

The other 37 configured sources were not live-tested. No claim is made that
they work. Proof paths are recorded in
`RELEASE_EVIDENCE_INTERNAL_BETA_V1/source_status_and_controlled_live.md`.

## 7. GUI acceptance

- Launch methods: canonical relative batch and Desktop `.lnk` pointing to it.
- Final extracted package setup created a fresh local `.venv`, installed the
  full requirements and Chromium, preserved the launcher, and created a valid
  shortcut. Missing supported Python produced clear actionable nonzero output.
- Tested: Live Run presence, Offline/Test Run execution, selected-mode run,
  Self-Test, Keywords validation/reload/status, Source Manager add/edit/toggle,
  configuration validation, offline parser test, explicit live-test control,
  results/logs, and advanced settings visibility.
- Offline/Test Run produced workbook/report/summary outside the package.
- Moved-package GUI Self-Test: PASS with honest aggregate totals.
- The final `5805d467` release shortcut was launched after fresh setup. It
  opened the expected GUI, showed the exact extracted keyword/source paths,
  canonical VALID 227-rule status, all run/source controls, and a visible
  Self-Test PASS dialog with `112 / 0 / 1 / 4 / 0` totals.
- Sanitized screenshots:
  `06 QA/RELEASE_EVIDENCE_INTERNAL_BETA_V1/screenshots/`.

## 8. Engine contract

- `RunRequest` accepts review/output/config/state paths, mode, source IDs,
  offline/live intent, self-test flag, run ID, and Python executable.
- `EngineRunResult` returns run/timing/status, source/record/score summaries,
  output paths, warnings, errors, test totals, artifacts, and manifest path.
- Both models are JSON-serializable through `to_dict()`.
- `tenderfinder_engine.py` imports no Tkinter; GUI presentation calls this
  engine seam instead of requiring callers to parse widget text.
- This is a future BuildMatch/web-service boundary only. No BuildMatch API,
  deployment, database sync, or importer integration is claimed.

## 9. Release artifact

- ZIP:
  `C:\tenderfinder_out\release_internal_weekly_beta_v1\Tender_Finder_internal-weekly-beta-v1.zip`.
- Source commit:
  `5805d467aee539985376a3464c98ee7a6e121eb3`.
- Source worktree dirty: false.
- File count: 97 archive entries (94 source files plus three generated release
  metadata files).
- Size: 675,632 bytes.
- SHA-256:
  `912538cf10b8fc716656f0e00b0bd4ae8e55218f64cbd74b76a127e4fb84002a`.
- Extracted test path:
  `C:\tenderfinder_out\release_internal_weekly_beta_v1_5805d46_extracted\Tender_Finder_Internal_Weekly_Beta_v1`.
- CRC, manifest, exclusion, syntax/import, zero-network import, package secret
  scan, extracted Self-Test, setup, shortcut, and final GUI launch: PASS.
- A second clean build from the same commit produced the identical ZIP SHA;
  text-entry policy is LF except Windows `.bat`/`.cmd` CRLF.
- ZIP contains no `.git`, `.venv`, `.codex_tmp`, caches, logs, user data,
  browser state, email content, secrets, or generated tender outputs.

## 10. GitHub result

- Stabilization commit:
  `340e88ba8145a2fd7c30e842d4c1172d60aeaca2`.
- Branch: `stabilize/internal-weekly-beta` (pushed normally).
- Pull request: #1,
  `https://github.com/taiduc1302/buildmatch-tender-finder/pull/1`.
- First PR CI run `29436216670` correctly failed two environment-sensitive test
  assertions (Windows 8.3 path spelling and inherited no-open policy). Runtime
  behavior did not fail. Commit `60dbdd6` made both assertions semantic and
  environment-isolated.
- Required PR CI: run `29436672628` (`Tender Finder Offline CI` run #6),
  completed `success` on Windows/Python 3.12.
- PR #1 merged normally, without rebase or force, as merge commit
  `d38de2306a40b7ce6ab6c1b022ab1756de6b45eb`.
- Reproducibility follow-up: PR #2,
  `https://github.com/taiduc1302/buildmatch-tender-finder/pull/2`.
- Follow-up CI: run `29438859006` (`Tender Finder Offline CI` run #8),
  completed `success` on Windows/Python 3.12.
- PR #2 merged normally, without rebase or force, as merge commit
  `5805d467aee539985376a3464c98ee7a6e121eb3`.
- Release tag: annotated `internal-weekly-beta-v1`, targeting the final
  report-only commit on `main`.
- Local `main`, `origin/main`, and the peeled release tag target were verified
  equal with a clean worktree after publication. The exact final SHA is also
  printed in the final delivery response because a commit cannot contain its
  own hash.

## 11. Remaining limitations

- Only Surrey is currently live-verified; Abbotsford needs adapter/source
  review and the other 37 sources were not live-tested.
- Adapter-level fixtures do not prove every source-specific website shape.
- Historical Vancouver rows without persisted scoring text retain their stored
  tier with the visible legacy exception.
- Python 3.11+ is a prerequisite. First run creates a local virtual environment
  and installs dependencies/Playwright Chromium, requiring network access and
  time. Stale Python launcher registrations may require installing Python or
  correcting PATH as the setup instructions explain.
- Manual email alert import exists; Gmail/Microsoft OAuth and IMAP are not
  implemented.
- BuildMatch integration is a future engine boundary, not a completed
  integration.
- The release is a portable source ZIP, not a fully self-contained `.exe`.
- This is an internal weekly beta, not production-ready software.

## 12. Final classification

`STABILIZATION RELEASE: PASS — INTERNAL WEEKLY BETA`

All code, security, data-preservation, source-truthfulness, GUI, package,
controlled-live, GitHub Actions, normal integration, and release-publication
gates pass within the internal-weekly-beta scope and stated limitations.

## Acceptance checklist

- [x] Original GitHub baseline recoverable by remote annotated tag.
- [x] Codex targeted review completed and all blocking/high findings resolved.
- [x] Formula injection and private/redirect network requests prevented.
- [x] RESCORE_ALWAYS audit and manual founder fields preserved.
- [x] Source registry/test reporting is truthful and atomic.
- [x] Self-Test is zero-network, truthful, and PASS.
- [x] Windows setup, shortcut, GUI, Offline/Test Run, and package extraction
  acceptance passed.
- [x] Clean ZIP contains no secrets, runtime state, or user data.
- [x] GitHub Actions, normal merge, final tag, and local/remote equality.

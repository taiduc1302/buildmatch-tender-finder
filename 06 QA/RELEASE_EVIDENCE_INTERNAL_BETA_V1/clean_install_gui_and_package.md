# Clean install, moved GUI, and package evidence

## Clean install and move

A deterministic pre-commit source ZIP was extracted outside the repository.
On Windows, setup:

- found supported Python 3.12;
- created a fresh `.venv` (no copied environment);
- installed the full pinned requirements and Playwright Chromium;
- preserved `Launch_TENDER_FINDER_GUI.bat` byte-for-byte;
- discovered the real OneDrive Desktop;
- created `TENDER_FINDER Tender Intelligence.lnk` targeting the canonical
  launcher;
- returned exit code 0 without the prior spurious path errors.

The installed folder was moved to
`C:\tenderfinder_out\moved_release_candidate_0907\Tender_Finder_Internal_Weekly_Beta_v1`.
Setup was rerun there, reused the moved environment, and recreated a shortcut
whose target existed at the moved path. The launcher hash still matched the
canonical source launcher.

## Windows GUI black-box

The moved package was launched through the Desktop shortcut. Verified actions:

- main window opened from the canonical launcher;
- Offline/Test Run completed and produced workbook/report/summary externally;
- Keywords tab showed VALID canonical rules, 227 active, 0 inactive, category
  counts, LKG status, validation state, and scoring semantics;
- Source Manager exposed Add, Edit, Enable/Disable, Validate Configuration,
  Offline Parser Test, and explicit Live Source Test;
- offline parser dialog reported `Parser used: YES` with parser identity and
  fixture counts;
- Add Source opened a disabled-by-default, validated source form;
- GUI Self-Test honestly reported PASS with `110 passed / 0 failed / 1 skipped
  / 4 intentionally excluded / 0 no-fixture`, exit 0.

Moved-package GUI Self-Test manifest:
`C:\tenderfinder_out\self_test\self_test_20260715_095133_2f19a6b4\run_manifest.json`.

Sanitized screenshots are in `screenshots/`.

## Pre-commit package proof

The latest pre-commit candidate was deterministic and passed CRC, manifest,
extraction, forbidden-payload, and secret scans:

- ZIP:
  `C:\tenderfinder_out\release_candidate_precommit_v2\Tender_Finder_internal-weekly-beta-v1-precommit2.zip`.
- Size: 675,102 bytes.
- Entries: 97.
- SHA-256:
  `671c26c28630a7223a27df30a8fbbc29ddf5699bc40991e97bbb4abe0b602528`.

This is explicitly pre-commit evidence, not the final release artifact. The
final ZIP must be rebuilt from a clean committed checkout with
`--require-clean` and recorded in `STABILIZATION_RELEASE_REPORT.md`.

## Final clean release

- Source commit: `5805d467aee539985376a3464c98ee7a6e121eb3`.
- Source worktree dirty: false.
- ZIP:
  `C:\tenderfinder_out\release_internal_weekly_beta_v1\Tender_Finder_internal-weekly-beta-v1.zip`.
- Size: 675,632 bytes.
- Entries: 97 (94 source files plus three generated release records).
- SHA-256:
  `912538cf10b8fc716656f0e00b0bd4ae8e55218f64cbd74b76a127e4fb84002a`.
- Extracted root:
  `C:\tenderfinder_out\release_internal_weekly_beta_v1_5805d46_extracted\Tender_Finder_Internal_Weekly_Beta_v1`.
- CRC/manifest/exclusion verification: PASS.
- Extracted syntax/import/zero-network import guard: PASS.
- Extracted package secret audit: PASS.
- Extracted Self-Test: PASS, `112 / 0 / 1 / 4 / 0`, zero network attempts,
  exit 0; manifest:
  `C:\tenderfinder_out\release_internal_weekly_beta_v1_5805d46_selftest\self_test\self_test_20260715_110434_b78f713e\run_manifest.json`.
- Repeated clean build SHA equality: PASS. Release text policy is LF except
  `.bat`/`.cmd` CRLF, independent of checkout line endings.

The first unattended setup attempt on this Windows profile correctly returned
nonzero with actionable instructions because no supported system Python was
on PATH (only stale Python 3.10/3.13 registrations). With an available local
Python 3.12 placed on PATH, the same final extracted package created a new
`.venv`, installed all requirements and Chromium, preserved the canonical
launcher, and created a Desktop shortcut targeting the final extracted path.
Launching that exact shortcut opened the `5805d467` extracted GUI with Live
Run, Offline/Test Run, Self-Test, Keywords, and Source Checks visible. Keywords
showed VALID, 227 active rules, canonical/LKG state, and the exact extracted
path. Source Manager showed 39 configured, 27 runtime-eligible, one
verified-live, and all CRUD/test controls. GUI Self-Test visibly passed with
`112 / 0 / 1 / 4 / 0`, zero network attempts, and exit 0; manifest:
`C:\tenderfinder_out\self_test\self_test_20260715_111646_29605475\run_manifest.json`.
This remains a Python source application; Python/first-run dependency
installation is a prerequisite.

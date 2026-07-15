# Internal weekly beta v1 — sanitized evidence index

This directory contains permanent, sanitized evidence for the Tender Finder
internal weekly beta stabilization. It intentionally excludes fetched pages,
credentials, cookies, email content, user tender data, virtual environments,
and generated tender workbooks.

Evidence files:

- `baseline_and_protected_hashes.md` — recoverable Git baseline and immutable
  release inputs.
- `security_runtime_and_self_test.md` — formula/network protections, external
  runtime state, and authoritative offline Self-Test.
- `keywords_rescore_and_manual_fields.md` — editable workbook validation,
  RESCORE_ALWAYS, cache behavior, visible audit, and founder-field retention.
- `source_status_and_controlled_live.md` — registry counts and bounded live
  proof without overstating untested sources.
- `clean_install_gui_and_package.md` — clean extract/setup/move, Windows GUI
  black-box acceptance, and pre-commit package proof.
- `screenshots/` — sanitized Windows GUI screenshots.

The detailed finding-by-finding record is in `../STABILIZATION_REVIEW.md`; the
required targeted review is in `../CODEX_REVIEW_1f649d1.md`; the final release
result is in `../STABILIZATION_RELEASE_REPORT.md`.

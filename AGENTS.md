# Standing rules for this repository

These rules apply to future agent work in `C:\Projects\buildmatch-tender-finder`.

- Work only in this repository. Never use the original iCloud package as a source or destination.
- Do not run Git commands. The founder reviews and commits changes manually.
- Tests and validation are offline only: use `--no-fetch`, checked-in fixtures, or local synthetic records. Never contact tender portals during agent verification.
- Write run outputs beneath `C:\tenderfinder_out`, not inside the repository.
- `config/keywords.xlsx` is the live business-rule source. Profile `regions`, `work_types`, and `known_clients` generate geography/+8, positive/+9, and client/+6 defaults. An explicit `Keywords` row with the same normalized `(keyword, category)` wins, including `active = N`.
- Invalid or missing keyword configuration must stop scoring. Do not add a hardcoded or partial fallback.
- `01 Code/tenderfinder_agent2.py` is frozen legacy code. It intentionally retains independent built-in lists and must not be migrated without explicit founder approval.
- Keep Vancouver tier thresholds/routing in code; only its two signal word lists are configurable in this version.
- Do not retune Meridian weights, gates, matching semantics, or the 0–100 cap while performing maintenance unless the founder explicitly requests a business-logic change.

Known legacy test failures are not permission to alter unrelated behavior. Do not “fix” these without explicit sign-off:

- `test_launcher_gui.py`: stale BID LATER expectation.
- `test_surrey_tender_status.py`: stale hardcoded date.
- `test_launcher_review_xlsx_consistency.py`: removed legacy fallback expectation.
- Preflight test expecting `requests` in the offline runtime.
- Promotion test expecting a missing legacy master workbook.
- `.eml`-dependent checks in `test_patch_523_output_consistency.py`.

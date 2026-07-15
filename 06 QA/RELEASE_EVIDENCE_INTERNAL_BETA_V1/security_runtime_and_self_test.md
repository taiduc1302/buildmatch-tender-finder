# Security, runtime isolation, and Self-Test evidence

## Security controls

- Untrusted Excel text whose first non-whitespace character is `=`, `+`, `-`,
  or `@` receives an Excel literal marker. Real numbers and date/time values
  retain native types; intentional application formulas remain direct writes
  (`01 Code/CONNECTOR_SWEEP/tenderfinder_excel_safety.py:18-80`).
- Editable URLs accept only public HTTP(S). DNS resolution fails closed; any
  local, private, link-local, reserved, multicast, or otherwise non-global
  result is rejected before transport. Redirects are manual and every hop is
  revalidated. Playwright page and subresource requests use the same policy
  (`tenderfinder_url_safety.py:27-310`).
- `--no-fetch` address enrichment was explicitly regression-tested so the
  address adapter cannot create a hidden network call.

Focused security result: `11 passed / 0 failed`.

## Runtime isolation

Normal run outputs, histories, logs, manifests, keyword LKG state, email state,
registry backups, source-test artifacts, GUI state, and Self-Test artifacts are
under `C:\tenderfinder_out` (or an explicit external user-selected root), never
under the package. Legacy package-local state is treated only as a read-only
migration source. The runtime-isolation test verifies no state root may resolve
inside the package.

## Authoritative checkout Self-Test

- Run ID: `self_test_20260715_101135_2ad06d9f`.
- Result: **PASS**, exit code 0.
- Passed: 113.
- Failed: 0.
- Skipped: 1.
- Intentionally excluded: 3.
- Not tested due to missing fixture: 0.
- Network attempts: 0 (process-wide DNS/socket deny guard plus real pipeline
  `--no-fetch`).
- Real offline pipeline result: PASS.
- Protected keywords/source/Agent2/launcher hashes: unchanged.
- Manifest:
  `C:\tenderfinder_out\self_test\self_test_20260715_101135_2ad06d9f\run_manifest.json`.

This run also proved the final workbook builder selected the checkout's own
`00 Master\TENDER_FINDER_Tender_Intelligence_Working_Master_TEMPLATE_v1.xlsx`,
not the newer template copy in another test installation.

Both `git_worktree_unchanged_by_self_test` and
`clean_git_worktree_after_self_test` passed from a clean committed checkout.

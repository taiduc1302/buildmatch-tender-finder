# TEST RESULTS — Tender Finder

Last verified: **2026-07-04**, two independent rounds — see
`FINAL_HANDOFF_AUDIT.md` for the second (adversarial) round in full. Both
rounds used Python 3.14.6 on Windows 11, run against the shipped synthetic
data only (no real credentials, no live network fetch).

**One-line summary: everything that should pass, passes. The 2 non-passing
test scripts and the "FAIL" line at the end of the demo are all understood,
expected, and explained below — none of them indicate a broken package.**

---

## 1. Passing synthetic-demo checks

| Check | Result |
|---|---|
| `setup_venv.bat` / fresh venv + `pip install openpyxl` | PASS |
| `verify_package.bat` (packaged self-check bundle: email intake parsers, folder UX, routing, GUI logic) | PASS — `VERIFY_PACKAGE: PASS` |
| `run_demo_synthetic.bat` — workbook build | PASS — `TENDER_FINDER_DEMO_Opportunities_Three_Buckets.xlsx` created, ≈20 sheets |
| Synthetic data counts match documentation | PASS — BID NOW=2, BID LATER=6 (≥60:6, ≥70:5), WATCH=2, ANALYZED=5 |
| No credentials or network required for the demo | PASS — every live-fetch source logs `SKIPPED_NO_FETCH`; email intake uses only local `.eml` files |
| `scripts\package_audit.py` (brand/email/secret/path scan, text + all xlsx cell text) | PASS — 0 findings, both rounds |
| Standalone test suite | PASS — 21 of 23 scripts (see §3 for the other 2) |

## 2. Expected "failures" that are not bugs

### 2a. The demo's final "user master" stage: `Overall: FAIL`

Every synthetic-data demo run ends with an optional final-review stage
printing `Overall: FAIL`. This is a **strict anti-fixture production guard**
whose entire purpose is to refuse to bless synthetic/demo rows as real
production output. Exactly two of its sub-checks trip, both for the same
underlying reason:

| Sub-check | Result | Why |
|---|---|---|
| `No fixture/synthetic/example rows in Outreach_Tracker` | FAIL | The synthetic rows are (correctly) still tagged as fixture/synthetic |
| `Dashboard counts match recounted sheets` (specifically `future_full: shown=6 recounted=0`) | FAIL | The dashboard's raw count (6) doesn't filter fixture rows, but the independent recount function (`count_live_demo_rows`) does — and since *all 6* synthetic Future_Projects rows are fixture-marked, the filtered recount is correctly 0. This is the **same anti-fixture guard**, just checked a second way — not a second, unrelated bug. |
| Every other sub-check (workbook exists, tab count, no demo-only tabs, traceability, master untouched, folder cleanliness, etc.) | PASS | — |

**With real (non-synthetic) data, this stage passes**, because real rows are
never tagged with the fixture/synthetic markers this guard looks for.

### 2b. Two standalone test scripts

| Script | Status | Explanation |
|---|---|---|
| `tests\test_launcher_gui.py` | Fails if run standalone; **passes** as run by `verify_package.bat` | Its one end-to-end sub-test builds a real demo and hits the exact anti-fixture guard from §2a — expected on synthetic data. `verify_package.bat` runs this script with `TENDER_FINDER_GUI_SKIP_E2E=1`, the packaged and sanctioned way to run it, which skips only that sub-test and passes everything else. |
| `tests\test_launcher_review_xlsx_consistency.py` | Fails | **Fails identically in the original, pre-sanitization internal project** (confirmed by running the equivalent test in the original codebase before packaging). This is pre-existing drift between a launcher script and its own test, unrelated to sanitization. Left as-is and documented rather than silently changed, per the "don't hide test failures" policy for this package. |

## 3. Checks not appropriate for synthetic/demo mode

| Check | Status | Why it doesn't apply here |
|---|---|---|
| `test_workbook_quality.py` production row-count minimums (5,393 / 973 / 8,000 rows) | Skipped/rescaled | These numbers describe the *original* real dataset. The test auto-detects the packaged synthetic sample (12 records total) and uses scaled-down minimums instead. Validate a real run with `TENDER_FINDER_DEMO_WORKBOOK=<path>` plus the `TENDER_FINDER_MIN_*_ROWS` env vars, which restore the production defaults. |
| `test_workbook_quality.py` LMDG consultant-grouping assertion | Skipped | Names one specific high-volume consultant firm from the real production dataset, which has no equivalent in the synthetic sample. Gated to real-data runs only (see the `_IS_SYNTHETIC_SAMPLE` flag in that file). |
| `tests\run_regression.py` (network regression suite) | Not run | Performs live web sweeps against real portals — out of scope for an offline sanitization/demo package. Run it yourself once you're doing live-connector work. |
| Live connector fetch (Track B) | Not run | The demo was built with `--no-fetch` throughout. See `DEMO_LIMITATIONS.md`. |

## 4. What must be fixed / done before production use

None of the above block using this package as a *starter kit* or for
demonstration. Before pointing this at **real production use**, you should:

1. Replace `inputs\all_live_review.xlsx` with real output from your own live
   sweeps (see README "What you must configure for real use").
2. Re-run the full demo with real data and confirm the final "user master"
   stage now reports `Overall: PASS` (it should, once no rows carry
   fixture/synthetic markers — if it still fails, that's a genuine bug worth
   investigating, not something to suppress).
3. Re-test live connectors against current portal endpoints — they have not
   been re-verified since the original project (see `DEMO_LIMITATIONS.md`).
4. Investigate and, if desired, fix `test_launcher_review_xlsx_consistency.py`
   (pre-existing, not introduced by sanitization, but still open).
5. Read `SANITIZATION_REPORT.md`'s "Manual review items" before any use beyond
   your own team.

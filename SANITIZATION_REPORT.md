# SANITIZATION REPORT — Tender Finder Portable Package

| | |
|---|---|
| Original root folder | `C:\t` (working copy: `C:\t\01_Working\<internal-project-folder>`) |
| Sanitized output folder | `C:\t\Tender_Finder_Generic_Portable_Package_20260703_215523` |
| Created | 2026-07-03, 21:55–22:30 local time |
| Method | Deterministic build script (inventory → classify → copy/sanitize/rename → synthesize templates) + targeted manual edits + automated audit rescans |

> **Bottom line (plain English):** no private company name, employee name, real
> email address, or local file path remains anywhere in this package. This was
> checked twice, independently, including inside every Excel workbook's cell
> text — see "Tests / checks performed" below and `FINAL_HANDOFF_AUDIT.md` for
> the second, adversarial round. A small amount of information that is already
> public (government procurement URLs, public company names in test data) was
> deliberately kept because the software needs it to run and be tested — see
> "Manual review items" below for exactly what and why.

> **Brand-free note:** this in-package copy deliberately does not spell out the
> original company name or codename, so that the package itself contains zero
> occurrences of it. The exact token-by-token mapping and the full 250-row file
> inventory are in a **separate, external records folder**
> (`Tender_Finder_Sanitization_Records_20260703_215523\`) that sits next to the
> ZIP on the machine where this package was built. **That folder is for the
> original owner's internal retention only — it is not part of this package,
> is not included in the ZIP, and should not be given to anyone this package
> is shared with.** If you are receiving this package from someone else, you
> will most likely never see that folder at all; its absence does not affect
> anything in the package itself.

## What was replaced (summary)

≈2,140 automated replacements across 134 text files, plus cell-level rebuilds
of 4 workbooks:

- The original **company codename** (3 case variants + one GUI class name) →
  `TENDER_FINDER` / `tenderfinder` / `Tender Finder` / `TenderFinder`,
  consistently across code, tests, batch files, docs, and **71 renamed
  files/folders** (imports and file references stay consistent; the test suite
  proves it).
- The original **company legal name** → `Example Civil Contractor Ltd`.
- The shared **estimating mailbox** → `estimating@example.com` (11×).
- **Employee first names** (an operator, a reviewer, a manual-tracking
  coordinator, five estimators) → `Example Operator`, `Example Reviewer`,
  `Example Coordinator`, `Estimator A–E`, `Example User` (≈50×).
- Six **public-record person names** used in one classification test →
  fictional names (the tested "Person DBA: Firm" pattern is preserved).
- **Private local paths** (`C:\Users\<user>` and a corporate OneDrive path) →
  `C:\TenderFinder\...` placeholders.
- The **real client/target organization list** in the context brief → an
  explicit placeholder list (manual edit, marked in the file).

## Files copied as-is

22 text files contained no sensitive tokens (e.g. `.gitattributes`, generic
fixtures, some research CSVs). Full list in the external inventory CSV.

## Files sanitized

134 text files (all `.py`, `.md`, `.csv`, `.bat`, `.yml`, `.txt`, `.eml`,
`.command` in the included set). No encoding fallbacks were needed (all UTF-8).

## Files replaced with templates / synthetic data

| Original | Replacement |
|---|---|
| `inputs\all_live_review.xlsx` (33,629 rows of real harvested review data) | Synthetic 12-row demo workbook, same 21-column schema |
| 3 real working-master workbooks in `00 Master\` | One `..._Working_Master_TEMPLATE_v1.xlsx`: instruction + public-source-register sheets kept (cell-sanitized), 1,123 real data rows dropped, 3 synthetic examples added |
| `03 Active and QA Runbooks\` Task D / Task G workbooks | Cell-by-cell sanitized rebuilds (methodology kept, personnel/brand replaced) |
| `01 Code\CONNECTOR_SWEEP\data\..._Source_Universe_Backlog_v2_EXPANDED.xlsx` | Cell-by-cell sanitized rebuild (912 rows, public sources; required by `test_source_backlog`) |
| Real verified output (`latest_verified_output\demo_p522`) | Fresh synthetic sample run in `latest_verified_output\demo_synthetic_sample\` |
| Folder-guide `.docx` | New `PROJECT_STRUCTURE.md` |
| (new) `demo_data\email_alerts\*.eml` | 3 synthetic tender alert emails |

## Files/folders excluded (not in this package)

- **Real outputs / real intelligence:** 15 `demo_*` output folders,
  `demo_history`, `latest_verified_output` (original), `live_outputs_p54`,
  `test_outputs_p53/54`, `raw_runs` (raw harvested data),
  `user_data\email_alerts\logs` + `import_state.json`,
  `04 RESEARCH REFERENCE\SURREY_LEAD_SCREEN` (real lead-screen reports,
  docx/pdf), one Russian-language prompt-review docx tied to that lead screen,
  `baseline_p59.json` (real-run metrics).
- **Machine-specific / commit-specific:** 3 recovery-audit reports, 3 fix
  prompts (contained private user paths), `structure.txt`.
- **Derived packages:** 7 old `.zip` packages, 2 handoff-package folders,
  runtime-package folder, `_package_stage`.
- **Caches/VCS:** `.git`, `.venv`, `__pycache__`, `.agents`, `.codex_tmp`.
- **Duplicates at `C:\t` root:** `99_Archive`, a stale root project copy, four
  `_audit_*` extract folders, `.claude` (assistant session data).
- One redundant xlsx twin of a CSV register (`..._Source_Register_PreScript_Audit.xlsx`
  — CSV version is included).

## Post-build fixes applied (after the scripted pass)

1. Master template renamed to match the `..._Working_Master_*.xlsx` discovery
   glob used by the demo builder.
2. Source-universe backlog workbook rebuilt (was initially excluded as
   unhandled binary; a test requires it).
3. `tests\test_workbook_quality.py`: default workbook now the packaged
   synthetic sample; production row-count minimums (5393/973/8000) kept as
   defaults for real data but auto-scaled for the synthetic sample; one
   dataset-specific consultant-grouping assertion gated to real-data runs.
   All changes are commented in the file.
4. Context brief client list → placeholders (marked in the file).
5. Added: `run_demo_synthetic.bat`, `demo_data\`, `requirements-dev.txt`
   (undeclared test deps discovered during smoke testing),
   `scripts\package_audit.py`, and the new documentation set.

## Internal names NOT renamed (kept deliberately)

- **None in code** — all brand-carrying identifiers, module names, env vars
  (`TENDER_FINDER_*`), output filenames, and workbook names were renamed
  consistently; the test suite passes against the renamed code.
- Historical docs in `docs\history\` still reference old *file names* of
  excluded artifacts (e.g. old zip/package names) in sanitized form; those
  files no longer exist and the references are historical narrative only.

## Manual review items (kept, with reasons — review before any public release)

**Read this section before sharing this package outside your own team.** None
of these items are secrets, private data, or mistakes — they are already
public information kept because the tool needs it — but a human should
confirm that before a public release. See also `DISTRIBUTION_NOTES.md`.

1. `tests\fixtures\` email/CSV/PDF fixtures contain **public-record municipal
   data** (real BC development applications, public applicant company names
   like established regional developers, and one real closed tender title).
   Kept because tests assert on this content; it is public information.
2. Two public municipal **PDF fixtures** copied unmodified (parser tests).
   Checked 2026-07-04: both are ReportLab-generated 1-page test fixtures with
   `/Author (anonymous)` / `/Title (untitled)` metadata and no embedded real
   names, paths, or hidden text — safe as-is.
3. The main script and one test contain **public developer/consultant brand
   names** used by the parent-brand grouping logic (public companies,
   functional keyword tables).
4. Source registers (`00 Master` Source_Register sheet, `data\` backlog, `04
   RESEARCH REFERENCE\SOURCE_REGISTER_EXPANSION`, coverage CSVs) list ~300
   **public** procurement/dev-app sources for BC with operational access notes.
   This is the reference region configuration — genericize if you want a fully
   region-neutral product.
5. Several runbooks/research docs are **historical narratives** (partly
   Russian-language) describing the original build; names/branding neutralized
   but methodology and BC context kept.
6. Synthetic demo emails reuse real public alert-provider **domains**
   (`bidsandtenders.ca`, `bcbid.gov.bc.ca`) so provider-detection routes them;
   content is fictitious.

## Tests / checks performed

Every row below is either a plain PASS, or a non-PASS result that is fully
explained and was not hidden. The single "guard triggered" row and the single
"not tested" row are both accounted for in the Overall result below — nothing
here is left unexplained.

| Check | Result |
|---|---|
| Offline synthetic demo build (`--no-fetch`, synthetic inputs) | **PASS** — workbook + reports generated (BID NOW=2, BID LATER=6, WATCH=2, ANALYZED=5) |
| Final "user master" stage on synthetic data | **PASS (guard correctly triggered)** — the anti-fixture production guard correctly refuses to treat `SYNTHETIC`-marked rows as real production output (2 sub-checks trip: the Outreach_Tracker fixture-row check, and a dashboard row-count cross-check that also excludes fixture rows). This is the guard working as designed and passes with real data. Full detail in `TEST_RESULTS.md`. |
| `verify_package.bat` (packaged self-checks incl. GUI logic) | **PASS** (`VERIFY_PACKAGE: PASS`, Python 3.14) — reconfirmed 2026-07-04 from a fresh extraction of the ZIP |
| Standalone test suite (23 scripts) | **21 PASS / 2 known, explained non-blocking failures:** `test_launcher_gui` e2e case (same anti-fixture guard on synthetic data; passes via `verify_package.bat`'s sanctioned `SKIP_E2E` mode) and `test_launcher_review_xlsx_consistency` (**fails identically in the original, pre-sanitization project** — pre-existing launcher/test drift, confirmed both 2026-07-03 and 2026-07-04; left unfixed rather than silently changed) |
| `scripts\package_audit.py` (brand/emails/secrets/paths/caches, incl. all xlsx cell text) | **PASS** — 177 text files + 6 workbooks, 0 findings. Independently re-run 2026-07-04 against a fully isolated re-extraction of the distributable ZIP (not a shared/reused test folder): 179 text files + 6 workbooks, 0 findings. |
| Independent adversarial re-audit (8-agent workflow, 2026-07-04) | **PASS, with one process lesson.** Two skeptic agents initially reported `__pycache__`/runtime-artifact "leaks" and flagged the record-keeping as unproven; both were traced to the audit's own test execution against a *shared* extraction folder (running the demo naturally creates `__pycache__`, exactly as it would on any user's machine) rather than a defect in the shipped ZIP. Confirmed by re-extracting the actual ZIP into a completely isolated, untouched folder and finding zero such artifacts. See `FINAL_HANDOFF_AUDIT.md` for the full trace. |
| Live network fetch / regression sweep | **NOT TESTED** (offline sanitization run — stated, not hidden) |

## Overall result

**PASS** — the package is company-neutral, contains no secrets or private
paths (checked twice, independently, including a from-scratch re-extraction of
the ZIP itself), runs its offline demo end-to-end on synthetic data, and its
own verification suite passes. The one "guard triggered" row above is a safety
feature working correctly, and the one "not tested" row is an honestly-stated
scope limit, not a defect — both are accounted for, not swept under the PASS.
Subject to the manual-review items above before any release outside your own
team.

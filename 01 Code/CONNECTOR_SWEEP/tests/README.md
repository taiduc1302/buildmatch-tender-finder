# TENDER_FINDER Regression Tests — README

**Patch 5.0 — Stabilization, Regression Recovery, and Connector Coverage Lock**

This directory contains the regression test framework that protects against connector regressions and pipeline failures.

---

## Quick Start

```bash
# Install dependencies
pip install openpyxl pyyaml --break-system-packages

# Run full regression suite
cd 01\ Code/CONNECTOR_SWEEP
python tests/run_regression.py --all --output-dir C:\tenderfinder_out\regression

# Run a specific protected-source suite
python tests/run_regression.py --suite surrey
python tests/run_regression.py --suite langley
python tests/run_regression.py --suite maple_ridge

# Verify output files only
python tests/run_regression.py --verify-outputs --output-dir C:\tenderfinder_out\regression
```

The regression runner generates `REGRESSION_TEST_REPORT.md` in the output directory.

---

## Files in This Directory

| File | Purpose |
|------|---------|
| `regression_expected_outputs.yml` | Baseline fixtures and expected row counts |
| `run_regression.py` | Python test runner (Patch 5.0) |
| `run_failure_tests.py` | Existing failure/error simulation tests |
| `test_search_api_errors.py` | Existing search API error tests |
| `fixtures/` | Sample CSV input files for unit tests |
| `README.md` | This file |

---

## Protected Sources (Must Never Regress)

These three connectors are protected by the regression suite. Any patch that causes them to produce zero rows **fails automatically**.

### 1. Surrey Planning Reports (`surrey_planning_reports`)
- **Source:** Public Surrey in-process PDFs
- **URLs:** `RezoningInProcess-Result.pdf`, `DP-IN-PROCESS.pdf`
- **Minimum rows:** 10 (expected: 15–25 per run)
- **Minimum Future_Projects:** 5
- **Fixture IDs (must appear):** `SURREY-25-0366`, `SURREY-25-0268`, `SURREY-26-0004` and others
- **Test command:**
  ```bash
  python tenderfinder_raw_sweep.py --only surrey_planning_reports --review-only --out C:\tenderfinder_out\surrey_review.xlsx
  ```

### 2. Township of Langley Dev Activity (`twp_langley_devactivity`)
- **Source:** ArcGIS Hub item `aea97e65c9db4dad8242783c96e6b70c`, layer 1
- **Minimum rows:** 600 (baseline: ~780)
- **Minimum Future_Projects:** 550
- **Fixture IDs (must appear):** `RZ100710`, `SA101389`, `DP101299`, `SA101395`, `RO100158`
- **Test command:**
  ```bash
  python tenderfinder_raw_sweep.py --only twp_langley_devactivity --review-only --out C:\tenderfinder_out\tol_review.xlsx
  ```

### 3. Maple Ridge Active Dev Apps (`maple_ridge_devapps`)
- **Source:** ArcGIS Hub item `c92b571eb6064a059781573466a7b38c`, layer 2
- **Minimum rows:** 500 (baseline: ~879)
- **Minimum Future_Projects:** 450
- **Fixture IDs (must appear):** `2023-019-RZ`, `2026-016-SD`
- **Batching:** 250 records per batch, 3 retries on 504
- **Test commands:**
  ```bash
  # Small run
  python tenderfinder_raw_sweep.py --only maple_ridge_devapps --max-records 500 --review-only --out C:\tenderfinder_out\maple_500.xlsx
  # Full run (batching)
  python tenderfinder_raw_sweep.py --only maple_ridge_devapps --review-only --out C:\tenderfinder_out\maple_full.xlsx
  ```

---

## Required Output Files

Every run must produce these files (none may be missing or zero-byte):

```
TENDER_FINDER_Run_Source_Summary.csv           — per-connector row counts
TENDER_FINDER_Demo_Top_Leads.xlsx              — demo workbook (when --demo-output)
<review>.xlsx                          — review workbook (when --review-only)
TENDER_FINDER_Link_Check_Run_Log.txt           — preflight run log
TENDER_FINDER_Link_Check_Debug_Log.txt         — preflight debug log
TENDER_FINDER_Source_Register_URL_Live_Audit.csv
TENDER_FINDER_Source_Register_URL_Live_Audit.xlsx
TENDER_FINDER_Source_Register_Fix_Queue.csv
TENDER_FINDER_Source_Register_Cleaned_For_Script.csv
```

---

## Regression Fixture Baselines

Baselines are defined in `regression_expected_outputs.yml`. Key values:

| Source | Rows (min) | FP rows (min) | Fixture IDs |
|--------|-----------|--------------|-------------|
| Surrey Planning Reports | 10 | 5 | 20 IDs |
| Township Langley | 600 | 550 | 13 IDs |
| Maple Ridge | 500 | 450 | 2 IDs |
| Preflight (no-search) | 159 sources | — | counts only |

---

## Safety Rules (Enforced by Regression Suite)

- A source that previously produced rows **must not** silently become manual/zero
- No run reports success if a required output file is missing or zero-byte
- No `.env.tenderfinder.local` with real credentials may appear in test output or zip
- Review-only mode must never write to the master workbook
- Write-master mode must create a backup before any write
- Protected v6 workbook checksum must not change

---

## How to Add a New Regression Fixture

1. Add the source to `regression_expected_outputs.yml` under `regression_fixtures:`
2. Run the connector and record actual row counts
3. Set `expected_min_rows` and `expected_min_future_projects` to 80% of actual
4. Add 3–5 sample `sample_record_ids` from the actual output
5. Add the connector to the `test_phases.phase_1_unit_tests.test_list`
6. Run `python tests/run_regression.py --all` to confirm it passes

---

## Troubleshooting Common Failures

| Failure | Likely Cause | Fix |
|---------|-------------|-----|
| Surrey rows = 0 | surrey.ca network unreachable | Check network; run locally |
| Maple Ridge 504 | Server busy or batch too large | Already fixed: 250/batch, 3 retries |
| Output file missing | Long OneDrive path | Already fixed: auto-redirect to `C:\tenderfinder_tmp` |
| Langley rows drop < 600 | ArcGIS service changed | Re-probe endpoint |
| `connector_module_missing` | `tenderfinder_surrey_inprocess.py` not in same dir as `tenderfinder_raw_sweep.py` | Copy/confirm file location |

---

*TENDER_FINDER Patch 5.0 — Regression Test Framework*

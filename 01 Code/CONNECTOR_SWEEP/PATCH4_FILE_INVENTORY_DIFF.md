# PATCH4_FILE_INVENTORY_DIFF.md

## 1. Base package proof

Patch Attempt 4 was built by extracting and patching this base package:

```text
TENDER_FINDER_bulk_harvest_patch_attempt_3.zip
```

The original Patch Attempt 3 folder structure was preserved. The harvester was not rebuilt from scratch and the master workbook was not recreated.

## 2. Protected master workbook hash

Protected workbook:

```text
00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx
```

SHA-256 in Patch Attempt 3 base:

```text
ca20abca726a31828a2b6033bd8d44a1b4b94b301854bcf0d0c80afd4e54bc7c
```

SHA-256 in Patch Attempt 4 working package:

```text
ca20abca726a31828a2b6033bd8d44a1b4b94b301854bcf0d0c80afd4e54bc7c
```

Result: PASS — protected v6 workbook hash is unchanged.

## 3. Deleted files

Deleted files = 0.

## 4. Files added

- `01 Code/CONNECTOR_SWEEP/LINK_PREFLIGHT_FINAL_TEST_REPORT.md`
- `01 Code/CONNECTOR_SWEEP/LINK_PREFLIGHT_INTEGRATION_CHANGELOG.md`
- `01 Code/CONNECTOR_SWEEP/PATCH4_FILE_INVENTORY_DIFF.md`
- `01 Code/CONNECTOR_SWEEP/tests/LAST_TEST_RUN.txt`
- `01 Code/CONNECTOR_SWEEP/tests/fixtures/test_register.csv`
- `01 Code/CONNECTOR_SWEEP/tests/run_failure_tests.py`
- `01 Code/CONNECTOR_SWEEP/tenderfinder_link_preflight.py`
- `01 Code/CONNECTOR_SWEEP/tenderfinder_live_link_checker.py`

## 5. Files modified

- `01 Code/CONNECTOR_SWEEP/RUN_ALL_SOURCES_SAFE.md`
- `01 Code/CONNECTOR_SWEEP/tenderfinder_raw_sweep.py`

## 6. Files preserved

Preserved unchanged file count: 41

Key preserved areas:

- `00 Master`: unchanged
- `02 Runbooks And Plans`: unchanged
- `03 Active and QA Runbooks`: unchanged
- `04 RESEARCH REFERENCE`: unchanged
- `05_PROMPTS`: unchanged
- `_ss`: unchanged

## 7. Integration-specific inventory notes

- `tenderfinder_raw_sweep.py` was modified minimally to expose and run link preflight options.
- `tenderfinder_live_link_checker.py` was copied from the accepted v2.1.0 package and patched only for the real master workbook URL column alias.
- `tenderfinder_link_preflight.py` was added as the safe wrapper between the harvester and checker.
- Link checker tests were copied into `01 Code / CONNECTOR_SWEEP / tests /`.
- `RUN_ALL_SOURCES_SAFE.md` was updated with Patch 4 preflight commands and routing rules.
- No Excel source files were intentionally modified.

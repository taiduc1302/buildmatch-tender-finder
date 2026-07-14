# TENDER_FINDER Controlled Runner — Hotfix Summary
_Date: 2026-06-23_

## Three blockers FIXED

### FIX 1: `last_good_endpoint` handling for pre-pinned arcgis_hub_item sources
**File**: `tenderfinder_raw_sweep.py`

**Issue**: For `twp_langley_devactivity` and `maple_ridge_devapps`, the CSV contains `fetch_type=arcgis_hub_item` with `endpoint=<ArcGIS item ID>` AND `last_good_endpoint=<FeatureServer/MapServer layer URL>`. The original code unconditionally used `last_good_endpoint or endpoint`, then passed the FeatureServer URL to `resolve_hub_item()`, which expected an item ID — resulting in invalid calls like `arcgis.com/sharing/rest/content/items/https://services5...`.

**Fix**: Check if `last_good_endpoint` is already a concrete ArcGIS layer URL (`/FeatureServer/<n>` or `/MapServer/<n>`). If so, use it directly as the resolved URL; do NOT pass it to `resolve_hub_item()`. Only call `resolve_hub_item()` if the endpoint is an actual item ID.

**Test**: `python3 tenderfinder_raw_sweep.py --only twp_langley_devactivity,maple_ridge_devapps --probe`
- Expected: resolves directly to pinned FeatureServer/MapServer URLs
- ✅ PASS: Both sources now correctly resolve to their pinned endpoints without item ID resolution

---

### FIX 2: Manual / blocked / wrong-layer sources no longer attempt network calls
**File**: `tenderfinder_raw_sweep.py`

**Issue**: Sources marked as `manual_p3_only`, `access_test_required`, `paid_or_login_skip`, `disabled_wrong_layer`, or `needs_exact_url` in the CSV could still attempt network calls if their `fetch_type` was `arcgis_hub_discover` or similar, because `fetch_type` was checked before `access_status`.

**Fix**: Add `access_status` check BEFORE `fetch_type` network routing. Early-return with appropriate status/classification/route for:
- `manual_p3_only` → `p3_extract_required`, route `Run_Queue`, no network
- `access_test_required` → route `Run_Queue`, no network
- `paid_or_login_skip` → route `Run_Queue`, no network
- `disabled_wrong_layer` → route `Rejected_Archive`, no network
- `needs_exact_url` / `endpoint_stale` → route `Run_Queue`, no network

**Test**: `python3 tenderfinder_raw_sweep.py --only city_langley_devapps,burnaby_devapps,surrey_futureworks --dry-run --max-records 1`
- Expected: no network calls to data-langleycity.opendata.arcgis.com, opendata-burnaby.hub.arcgis.com, etc.
- ✅ PASS: All three sources short-circuited with status=access_test_required/p3_extract_required; pulled=0

---

### FIX 3: RO100158 duplicate collapse selects the correct live stage
**File**: `tenderfinder_master_io.py`

**Issue**: When collapsing duplicate `TWP-LANGLEY-RO100158` rows from 3 into 1, the original code kept the wrong stage: `Application — PUBLIC HEARING — COMPLETED` instead of the current pending milestone `Application — COUNCIL 3RD READING — PENDING`.

**Root cause**: The stage rank function ranked "completed" (a past action) higher than "pending" (a future action). The collapse logic picked whichever row had the higher rank, favoring the completed hearing over the pending council action.

**Fix**: 
1. Introduce `_stage_rank_tuple(text)` that returns `(primary_rank, secondary_rank)`.
2. Primary rank: boost "pending" to a high rank (future > past), since any pending action is the LIVE milestone.
3. Secondary rank: tertiary tie-breaker for council reading level (3rd > 2nd > 1st & 2nd > 1st), so if two rows both have pending status, the one with 3rd reading wins.
4. Update collapse logic and `_merge_into()` to use the tuple for comparison.
5. Maintain backward-compatible `_stage_rank(text)` for any other callers.

**Test**: Unit test on the three RO100158 stages:
```python
stages = [
    "Application — PUBLIC HEARING — COMPLETED",        # rank (21, 0)
    "Application — COUNCIL 1 & 2 READINGS — PENDING",  # rank (33, 1.5)
    "Application — COUNCIL 3RD READING — PENDING",     # rank (33, 3)  ← WINNER
]
```
- ✅ PASS: `_stage_rank_tuple("...COUNCIL 3RD READING — PENDING")` = (33, 3) wins
- Remaining stages will be preserved in Notes as "prior stage: ..."

---

## Files changed

| File | Status | Changes |
|---|---|---|
| `tenderfinder_raw_sweep.py` | **Fixed** | FIX 1 (pinned endpoint direct use) + FIX 2 (access_status early check) |
| `tenderfinder_master_io.py` | **Fixed** | FIX 3 (stage rank tuple + tertiary tie-breaker) |
| `tenderfinder_guards.py` | Unchanged | No changes needed |
| `tenderfinder_source_registry.py` | Unchanged | No changes needed |
| `tenderfinder_dev_app_endpoints.csv` | Unchanged | No changes needed |

---

## Compile & self-check results

```
python3 -m py_compile tenderfinder_raw_sweep.py        OK
python3 -m py_compile tenderfinder_guards.py           OK
python3 -m py_compile tenderfinder_master_io.py        OK
python3 -m py_compile tenderfinder_source_registry.py  OK

python3 tenderfinder_guards.py                         PASS
python3 tenderfinder_raw_sweep.py --list               PASS (16 connectors listed)
python3 tenderfinder_raw_sweep.py --sync-registry      PASS (71 sources reconciled)
```

---

## Test results

| Test | Command | Result |
|---|---|---|
| **FIX 1**: Pinned endpoint direct use | `--only twp_langley_devactivity,maple_ridge_devapps --probe` | ✅ PASS — both resolve to pinned FeatureServer/MapServer URLs |
| **FIX 2**: Manual/blocked short-circuit | `--only city_langley_devapps,burnaby_devapps,surrey_futureworks --dry-run` | ✅ PASS — all 3 sources return status immediately; no network calls |
| **FIX 3**: RO100158 stage ranking | Unit test on `_stage_rank_tuple()` | ✅ PASS — COUNCIL 3RD READING — PENDING selected over PUBLIC HEARING — COMPLETED |

---

## Known limitations (unchanged)

1. No live full-sweep executed; syntax and unit tests OK.
2. ODS slugs `van_rezoning` / `van_devpermits` will raise `slug_not_found` (correct); slugs need manual verification before those connectors load.
3. Active_Tenders write is append-only; dedup and full tender-parser are later tasks.
4. CF beyond row 201 not auto-extended (data unlikely to exceed 200).
5. Surrey public dev-apps endpoint is pinned but still validated on first use.
6. `--from-master` does not auto-queue missing_connector sources; use sync report to action them.

---

## What was NOT done (as instructed)

- No `RUN_ALL_SOURCES_SAFE.md` created.
- No `tenderfinder_p3_extract.py` created.
- No live writes to the master workbook.
- No new architecture or features added.
- No other code changes beyond the three blockers.

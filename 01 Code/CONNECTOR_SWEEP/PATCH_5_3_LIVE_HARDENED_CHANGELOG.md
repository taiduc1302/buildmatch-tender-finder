# TENDER_FINDER Patch 5.3 — Live Hardened — Changelog

Built from the Patch 5.0 verified package after the full live capability run on
Windows (25,995 records pulled across 17 connectors). This patch fixes the four
P0 issues that run exposed and improves routing/output honesty. No new Source
Register rows were added; the master workbook is never written during testing.

---

## P0.1 — Surrey Planning Reports parser extracted 0 rows

**Root cause.** Both PDFs downloaded fine, but `_extract_pdf_rows` used an
either/or strategy: if `extract_tables()` returned anything it never tried text
parsing, and the table path discarded every row whose cells didn't line up with
the expected column order. When Surrey's PDFs render as flowing text (no ruling
lines) the result was a silent zero.

**Fix (`tenderfinder_surrey_inprocess.py`).** Replaced the extractor with a layered,
layout-robust pipeline that runs per page until one strategy yields rows:

1. ruled-table extraction (lines strategy),
2. text-strategy table extraction (no ruling lines),
3. id-anchored text-line parsing (anchors each record on an application id and
   absorbs wrapped continuation lines),
4. positional word-cluster reconstruction (`extract_words` grouped by y-band).

Document-level safeguard: if every strategy returns nothing but recognizable
application ids exist anywhere in the text, minimal id-only rows are emitted
rather than returning a silent zero (brief requirement). A debug artifact
(`TENDER_FINDER_Surrey_Parse_Debug_<label>.txt`, raw text + per-page id matches) is
written whenever extraction is empty or falls back to id-only salvage, so a
future layout change is diagnosable instead of invisible.

Also: `APP_NO_RE` confirmed to match all required id shapes
(`25-0366`, `25-0268`, `26-0004`, `7926-0157-00`, `7925-0256-00`); `ADDR_RE`
fixed to handle Surrey numbered streets (`13458 78 Ave`, `7685 152 St`), which
the old pattern rejected because it required the street name to start with a
letter.

**Verified in-sandbox** by `tests/test_surrey_pdf_parser.py` (16/16) against
representative synthetic PDFs in both layouts (ruled + flowing text), plus the
id-only salvage path and the debug-artifact path.

> **Live confirmation still required on your machine.** This sandbox cannot
> reach `surrey.ca` (egress returns HTTP 403), so the parser was proven against
> representative synthetic PDFs, not Surrey's live bytes. Run the acceptance
> command below on Windows. If the live layout still yields 0 rows, the new
> debug artifact will capture the exact text/columns so the regexes can be
> tuned to the real layout.

---

## P0.2 — Vancouver permit eligible-count inflation (the dangerous one)

**Root cause.** `apply_van_permit_filter` correctly tiered the 20,000 permits
(strong / watchlist / bulk / noisy) and set `write_eligible=False` on the
non-strong tiers — but `_apply_write_gates`, which runs afterward, then did:

```
lead["proposed_route"] = "Future_Projects"      # unconditional
lead["write_eligible"] = not hold_reasons        # recomputed, ignoring tier
lead["hold_reason"]    = "; ".join(hold_reasons) # wiped van_permit_* reason
```

With the default gates (`min_fit_score=None`) `hold_reasons` was always empty,
so every watchlist/bulk/noisy permit was flipped back to eligible Future_Projects.
That is why 17,906 normalized records were all reported as eligible — including
5,870 bulk + 9,725 noisy + 1,261 watchlist rows that could have contaminated the
master.

**Fix (`tenderfinder_raw_sweep.py`).**
- `_apply_write_gates` now **respects per-connector routing**. A new
  `_connector_pre_routed()` check leaves any already-held / non-Future_Projects
  lead exactly as the connector routed it. The optional thresholds can only
  **tighten** (move an otherwise-clean lead to held); they can never loosen a
  held lead back into Future_Projects.
- `apply_van_permit_filter` now sets explicit `routing_decision` /
  `routing_reason` on every tier (including `Future_Projects` on strong), so the
  routing is auditable per row.

**Verified in-sandbox** by `tests/test_routing_gates.py` (21/21): with the bug,
14 van leads would be eligible; now exactly the 3 strong leads are, bulk →
`Bulk_Intake_Raw`, noisy → `Rejected_Archive`, watchlist → `Run_Queue`, and a
clean connector's leads still pass.

---

## P0.3 — Windows console `UnicodeEncodeError`

**Root cause.** Arrow/em-dash/check-mark characters reached a cp1252 console.

**Fix.** Two layers:
1. `init_windows_safe_console()` reconfigures stdout/stderr to UTF-8 with
   `errors="replace"` at import time in `tenderfinder_raw_sweep.py` and
   `tenderfinder_live_link_checker.py` (the latter before its logging StreamHandler
   binds). This makes a crash impossible even if a stray Unicode char slips
   through. File logs remain full-fidelity UTF-8.
2. Every `print()`/`logger` line carrying `→ — – ✓ … ═ ─` across the package was
   replaced with ASCII (`->`, `-`, `[ok]`, `...`, `=`). The package now has zero
   non-ASCII characters in any console-bound output.

**Verified in-sandbox** by running `--list` and the full all-17 review with
`PYTHONIOENCODING=cp1252`: no `UnicodeEncodeError`, exit 0. Added as a standing
regression check (`P0.3: --list clean under cp1252 console`).

---

## P0.4 — Source summary was not honest

**Root cause.** Both the global RUN SUMMARY and the per-connector CSV read lead
state *after* the gates had clobbered it, so everything inherited the inflated
Future_Projects count and quality problems were hidden behind one number.

**Fix (`tenderfinder_raw_sweep.py`).**
- New `_categorize_result()` produces an honest per-connector breakdown from the
  final (post-gate, post-dedupe) routing: `records_clean_future_projects`,
  `records_watchlist`, `records_bulk_intake`, `records_rejected`,
  `records_manual_or_p3`, `records_failed_extraction`, `duplicates_skipped`.
- `write_source_summary()` emits these columns (plus `route` and `status`) and
  keeps the original columns the regression checks for. `records_eligible` now
  equals clean Future_Projects only.
- The console RUN SUMMARY prints the same breakdown and, for Vancouver, an
  explicit `strong / watchlist / bulk / noisy` tier line noting only strong rows
  reach Future_Projects.

Manual/P3 connectors and failed extractions are now visible as their own counts
rather than silent zeros.

---

## P0.5 — regression suite could hang after the Maple Ridge step

**Root cause.** The fixture-backed connectors (Surrey, Langley, Maple Ridge)
attempted a **live fetch first** and only fell back to fixtures *after* the HTTP
call failed. In a sandbox whose egress hangs (TCP connects but never responds)
instead of failing fast, each connector blocked for its full per-request timeout
(Surrey 45s x 2 PDFs; ArcGIS up to 90s), so the combined run right after the
Maple Ridge step looked like a hang.

**Fix (`tenderfinder_raw_sweep.py`).** When `TENDER_FINDER_OFFLINE_FIXTURES` is set (only the
regression harness sets it), `run_connector` now **skips the network entirely**:
fixture-backed connectors load their fixture immediately, and any other
connector that would otherwise fetch returns a fast `offline_no_fixture` stub.
Manual/P3/access connectors keep their real fast status. Result: `--all` is
hermetic, deterministic, and fast (~9s here) regardless of the sandbox's network
behavior. Production never sets the flag, so live runs are unchanged. Verified:
an offline Surrey run shows no `[surrey] fetching` line -- no network is touched.

> Because `--all` is now hermetic, it proves runner / output / routing /
> promotion behavior, **not** live-source availability. Live-source proof comes
> from the manual acceptance commands below, which you run without the flag.

---

## Packaging / generated outputs

The deliverable ships a fully generated **`test_outputs_p53/`** at the package
root, produced by a clean `--all` run (24/24 PASS). Both commands therefore work
immediately from a fresh unzip:

```powershell
cd "TENDER_FINDER_Patch_5_0\01 Code\CONNECTOR_SWEEP"

# Regenerate everything (hermetic, ~seconds, writes to ..\..\test_outputs_p53):
python tests\run_regression.py --all

# Verify the shipped (or freshly regenerated) outputs:
python tests\run_regression.py --verify-outputs --output-dir "..\..\test_outputs_p53"
```

The regression harness default output directory is now `test_outputs_p53`
(was `test_outputs_p50`). `--all` clears and regenerates that folder;
`--verify-outputs` preserves it and checks the files in place.

---

## P1 — backlog connectors (assessment only, no new rows)

P0 was the focus per the brief. The eight backlog connectors keep their
previously documented, honest statuses in `tenderfinder_dev_app_endpoints.csv` — no rows
were added or relabelled as working. Summary of current truthful state:

| connector | documented status |
|---|---|
| coquitlam_devapps | Hub root confirmed; dev-application FeatureServer to resolve at runtime (clearest near-term add) |
| van_rezoning / van_devpermits | ODS slug to verify; auto-searches ODS catalog by keyword if slug 404s |
| city_langley_devapps | Hub root confirmed; web-only, no application API — manual/P3 |
| burnaby_devapps | Hub root confirmed; little per-application detail published — manual/P3 |
| abbotsford_devapps | thin polygon-only application-areas layer — not scoreable |
| surrey_devapps | resolves to subdivision boundary markers — wrong layer |
| surrey_futureworks | office-network gated — disabled until access test passes |

No connector is claimed to pull rows that does not.

---

## Tests / verification

`python tests/run_regression.py --all` → **24/24 PASS** in this sandbox,
including the four new P0-targeted checks. New tests:
`tests/test_surrey_pdf_parser.py`, `tests/test_routing_gates.py`,
`tests/make_surrey_fixtures.py` (regenerates the synthetic Surrey PDFs).

**What was proven here vs. what needs your live run:** routing/gate logic (P0.2,
P0.4), Windows-safe console (P0.3), and the Surrey parser logic (P0.1) are
proven deterministically in-sandbox. Live-source availability — the real Surrey
PDF bytes and the live Vancouver permit tier counts — must be confirmed by
running the acceptance commands on the networked Windows machine, because this
sandbox's egress is blocked. The packaged offline fixtures are gated behind the
`TENDER_FINDER_OFFLINE_FIXTURES` flag set only by the regression harness; production runs
never set it, so a real government 403 is still surfaced honestly as
`FORBIDDEN_BUT_LIKELY_VALID` and is never silently replaced with fixture data.

## Acceptance commands (run on Windows)

```powershell
cd "TENDER_FINDER_Patch_5_0\01 Code\CONNECTOR_SWEEP"
python -m py_compile tenderfinder_raw_sweep.py tenderfinder_live_link_checker.py tenderfinder_surrey_inprocess.py tenderfinder_source_registry.py
python tenderfinder_raw_sweep.py --list

mkdir C:\tenderfinder_out\patch5_3_verify -Force
python tenderfinder_raw_sweep.py --only surrey_planning_reports --review-only --out "C:\tenderfinder_out\patch5_3_verify\surrey_planning_reports_review.xlsx"
python tenderfinder_raw_sweep.py --only van_building_permits --review-only --out "C:\tenderfinder_out\patch5_3_verify\van_permits_review.xlsx"
python tenderfinder_raw_sweep.py --review-only --out "C:\tenderfinder_out\patch5_3_verify\all17_live_review.xlsx"

# Regression: hermetic (offline fixtures), regenerates ..\..\test_outputs_p53
python tests\run_regression.py --all
# Verify the shipped or regenerated outputs in place
python tests\run_regression.py --verify-outputs --output-dir "..\..\test_outputs_p53"
```

The first block (review/only runs, no flag) is the **live-source proof** against
the real municipal endpoints. The regression block is the **hermetic behavioral
proof** and ships pre-generated under `test_outputs_p53/`.


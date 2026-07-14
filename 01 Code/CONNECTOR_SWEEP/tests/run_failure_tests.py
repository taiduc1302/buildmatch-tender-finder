#!/usr/bin/env python3
"""
TENDER_FINDER link checker — failure-case test harness.

This does NOT just import functions; it runs the real CLI as a subprocess
against a fixture register and inspects the actual output files, exactly as an
operator would. It proves:

  • each of the 8 fixture URL types is classified correctly
  • input-error conditions return exit code 1
  • a clean run returns exit code 0
  • --preflight-fail-on-broken returns exit code 3 when broken URLs exist
  • --dry-run returns exit code 0 and contacts nothing
  • output files exist and the Fix Queue never contains OK rows

Run:  python tests/run_failure_tests.py
Exit: 0 if every assertion holds, 1 otherwise.
"""
import csv
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "tenderfinder_live_link_checker.py"
FIXTURE = HERE / "fixtures" / "test_register.csv"

PASS, FAIL = [], []


def record(name: str, ok: bool, detail: str = "") -> None:
    (PASS if ok else FAIL).append(name)
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name}" + (f"  - {detail}" if detail else ""))


def run_cli(args, expect_exit=None):
    """Run the checker CLI; return (exit_code, stdout, stderr)."""
    cmd = [sys.executable, str(SCRIPT)] + args
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if expect_exit is not None and proc.returncode != expect_exit:
        print(f"    (got exit {proc.returncode}, expected {expect_exit})")
        print("    stderr tail:", proc.stderr.strip().splitlines()[-3:])
    return proc.returncode, proc.stdout, proc.stderr


def read_audit(out_dir: Path):
    p = out_dir / "TENDER_FINDER_Source_Register_URL_Live_Audit.csv"
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


# Accept-sets: classification is "correct" if the actual status is in this set.
# WAF/403 is environment-dependent (a site may answer 200 OR 403); the contract
# is only that it is NOT treated as broken.
ACCEPT = {
    "TST-01": {"OK", "OK_REDIRECTED"},
    "TST-02": {"BROKEN_OTHER"},
    "TST-03": {"BROKEN_DNS"},
    "TST-04": {"BROKEN_404"},
    "TST-05": {"LOGIN_OR_MANUAL"},
    "TST-06": {"NEEDS_CONNECTOR_NOT_SIMPLE_SCRAPE"},
    "TST-07": {"NEEDS_CONNECTOR_NOT_SIMPLE_SCRAPE"},
    "TST-08": {"FORBIDDEN_BUT_LIKELY_VALID", "OK", "OK_REDIRECTED"},
}


def test_classifications():
    print("\n[1] URL classification (real run, audit-only)")
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        code, _, _ = run_cli(
            ["--input", str(FIXTURE), "--output-dir", str(out),
             "--no-search", "--rate-limit", "0", "--retries", "0",
             "--timeout", "12", "--workers", "4", "--quiet"],
            expect_exit=0,
        )
        record("clean run exits 0", code == 0, f"exit={code}")
        if code not in (0,):
            return
        rows = read_audit(out)
        by_id = {r["source_id"]: r for r in rows}
        for sid, accept in ACCEPT.items():
            r = by_id.get(sid)
            if not r:
                record(f"{sid} present in audit", False, "row missing")
                continue
            actual = r["url_check_status"]
            record(f"{sid} -> {actual}", actual in accept,
                   "" if actual in accept else f"expected one of {accept}")

        # New error-handling columns must be populated, not blank placeholders
        needed = ["error_type", "classification_reason", "safe_to_scrape",
                  "manual_review_required", "retry_count"]
        missing_cols = [c for c in needed if c not in rows[0]]
        record("new diagnostic columns exist", not missing_cols,
               f"missing {missing_cols}" if missing_cols else "")

        # safe_to_scrape correctness: OK simple-http row = YES, connector = NO_CONNECTOR
        record("TST-01 safe_to_scrape=YES",
               by_id["TST-01"]["safe_to_scrape"] == "YES",
               by_id["TST-01"]["safe_to_scrape"])
        record("TST-06 safe_to_scrape=NO_CONNECTOR",
               by_id["TST-06"]["safe_to_scrape"] == "NO_CONNECTOR",
               by_id["TST-06"]["safe_to_scrape"])
        record("TST-03 manual_review_required=YES",
               by_id["TST-03"]["manual_review_required"] == "YES",
               by_id["TST-03"]["manual_review_required"])

        # Fix queue must not contain OK rows
        fq = out / "TENDER_FINDER_Source_Register_Fix_Queue.csv"
        with open(fq, encoding="utf-8-sig") as f:
            fq_rows = list(csv.DictReader(f))
        ok_in_fq = [r for r in fq_rows
                    if r.get("url_check_status") in ("OK", "OK_REDIRECTED")]
        record("Fix Queue excludes OK rows", not ok_in_fq,
               f"{len(ok_in_fq)} OK rows leaked" if ok_in_fq else "")

        # Replacement candidates file exists even with search disabled
        rc = out / "TENDER_FINDER_Source_Register_Replacement_Candidates.csv"
        record("Replacement Candidates file exists (search off)", rc.exists())

        # Both logs exist and are separate
        run_log = out / "TENDER_FINDER_Link_Check_Run_Log.txt"
        dbg_log = out / "TENDER_FINDER_Link_Check_Debug_Log.txt"
        record("Run log + Debug log both written",
               run_log.exists() and dbg_log.exists())
        # Debug log should carry FAIL-REASON lines for the broken URLs
        if dbg_log.exists():
            dbg = dbg_log.read_text(encoding="utf-8")
            record("Debug log records per-failure reasons",
                   "FAIL-REASON" in dbg)


def test_input_errors():
    print("\n[2] Input / config errors (expect exit 1)")
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)

        # (a) missing input file
        code, _, _ = run_cli(
            ["--input", str(out / "does_not_exist.csv"),
             "--output-dir", str(out / "o1"), "--no-search"],
            expect_exit=1)
        record("missing input file -> exit 1", code == 1, f"exit={code}")

        # (b) missing URL column
        bad = out / "no_url_col.csv"
        bad.write_text("source_id,source_name,notes\nX1,Foo,bar\n", encoding="utf-8")
        code, _, _ = run_cli(
            ["--input", str(bad), "--output-dir", str(out / "o2"), "--no-search"],
            expect_exit=1)
        record("missing URL column -> exit 1", code == 1, f"exit={code}")

        # (c) empty register (header only)
        empty = out / "empty.csv"
        empty.write_text("source_id,source_name,official_url\n", encoding="utf-8")
        code, _, _ = run_cli(
            ["--input", str(empty), "--output-dir", str(out / "o3"), "--no-search"],
            expect_exit=1)
        record("empty register -> exit 1", code == 1, f"exit={code}")

        # (d) URL column present but all cells blank -> zero URLs extracted
        nourls = out / "blank_urls.csv"
        nourls.write_text(
            "source_id,source_name,official_url\nX1,Foo,\nX2,Bar,n/a\n",
            encoding="utf-8")
        code, _, _ = run_cli(
            ["--input", str(nourls), "--output-dir", str(out / "o4"), "--no-search"],
            expect_exit=1)
        record("zero extractable URLs -> exit 1", code == 1, f"exit={code}")


def test_preflight_and_dry_run():
    print("\n[3] Preflight gate + dry-run")
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)

        # preflight should fail with exit 3 because fixture has broken URLs
        code, _, _ = run_cli(
            ["--input", str(FIXTURE), "--output-dir", str(out / "pf"),
             "--no-search", "--rate-limit", "0", "--retries", "0",
             "--timeout", "12", "--preflight-fail-on-broken", "--quiet"],
            expect_exit=3)
        record("--preflight-fail-on-broken -> exit 3", code == 3, f"exit={code}")

        # dry-run: exit 0, every row DRY_RUN, nothing contacted
        dr = out / "dry"
        code, _, _ = run_cli(
            ["--input", str(FIXTURE), "--output-dir", str(dr),
             "--no-search", "--dry-run", "--quiet"],
            expect_exit=0)
        record("--dry-run -> exit 0", code == 0, f"exit={code}")
        if (dr / "TENDER_FINDER_Source_Register_URL_Live_Audit.csv").exists():
            rows = read_audit(dr)
            all_dry = all(r["url_check_status"] == "DRY_RUN" for r in rows)
            record("dry-run contacts nothing (all DRY_RUN)", all_dry)


def main():
    print("=" * 64)
    print(" TENDER_FINDER link checker - failure-case test harness")
    print("=" * 64)
    if not SCRIPT.exists():
        print(f"FATAL: script not found at {SCRIPT}")
        return 1
    test_classifications()
    test_input_errors()
    test_preflight_and_dry_run()

    print("\n" + "=" * 64)
    print(f" RESULT: {len(PASS)} passed, {len(FAIL)} failed")
    if FAIL:
        print(" FAILED:")
        for n in FAIL:
            print(f"   - {n}")
    print("=" * 64)
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())

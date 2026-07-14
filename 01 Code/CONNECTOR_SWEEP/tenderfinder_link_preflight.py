#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tenderfinder_link_preflight.py — safe integration wrapper for TENDER_FINDER live link checker
===========================================================================
This module lets tenderfinder_raw_sweep.py run the accepted v2.1.0 link checker as a
preflight/source-health gate without replacing the harvester or changing the
master workbook.

Rules enforced here:
  * Source rows are never deleted or overwritten.
  * Broken URL statuses are excluded from simple scraping unless the runner uses
    --include-broken-sources.
  * 403/connector/manual/timeout statuses are routed to review/connector/manual
    workflows, not treated as deleted/broken source rows.
  * Original URLs stay preserved in the checker outputs.
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

import tenderfinder_live_link_checker as LLC

# Critical URL states that should not move into simple scraping by default.
BROKEN_FOR_SIMPLE_SCRAPE: Set[str] = {
    "BROKEN_DNS",
    "BROKEN_SSL",
    "BROKEN_404",
    "BROKEN_OTHER",
    "FIX_URL_FIRST",
    "NO_REPLACEMENT_FOUND",
}

# Important non-delete/review states. These are NOT automatically broken.
REVIEW_OR_CONNECTOR_SAFE: Set[str] = {
    "FORBIDDEN_BUT_LIKELY_VALID",
    "NEEDS_CONNECTOR_NOT_SIMPLE_SCRAPE",
    "LOGIN_OR_MANUAL",
    "TIMEOUT_RETRY_NEEDED",
}

REQUIRED_OUTPUTS = [
    "TENDER_FINDER_Source_Register_URL_Live_Audit.csv",
    "TENDER_FINDER_Source_Register_URL_Live_Audit.xlsx",
    "TENDER_FINDER_Source_Register_Fix_Queue.csv",
    "TENDER_FINDER_Source_Register_Replacement_Candidates.csv",
    "TENDER_FINDER_Source_Register_Cleaned_For_Script.csv",
    "TENDER_FINDER_Link_Check_Run_Log.txt",
    "TENDER_FINDER_Link_Check_Debug_Log.txt",
]


@dataclass
class PreflightResult:
    exit_code: int
    input_path: Path
    output_dir: Path
    files: Dict[str, Path] = field(default_factory=dict)
    row_counts: Dict[str, int] = field(default_factory=dict)
    blocked_source_keys: Set[str] = field(default_factory=set)
    review_source_keys: Set[str] = field(default_factory=set)
    connector_source_keys: Set[str] = field(default_factory=set)
    manual_source_keys: Set[str] = field(default_factory=set)
    retry_source_keys: Set[str] = field(default_factory=set)
    errors: List[str] = field(default_factory=list)


def _norm_key(value: object) -> str:
    return str(value or "").strip().lower()


def _add_source_keys(target: Set[str], row: Dict[str, str]) -> None:
    for key in ("source_id", "source_name"):
        val = _norm_key(row.get(key))
        if val:
            target.add(val)


def _read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _collect_output_metadata(output_dir: Path, result: PreflightResult) -> None:
    for name in REQUIRED_OUTPUTS:
        p = output_dir / name
        result.files[name] = p
        if not p.exists():
            result.errors.append(f"Missing required preflight output: {name}")
            continue
        if p.suffix.lower() == ".csv":
            result.row_counts[name] = len(_read_csv_rows(p))
        elif p.suffix.lower() == ".xlsx":
            # Avoid opening the workbook here; existence + non-empty is enough for wrapper metadata.
            result.row_counts[name] = -1 if p.stat().st_size > 0 else 0
        else:
            result.row_counts[name] = -1 if p.stat().st_size > 0 else 0

    audit_rows = _read_csv_rows(output_dir / "TENDER_FINDER_Source_Register_URL_Live_Audit.csv")
    for row in audit_rows:
        status = (row.get("url_check_status") or row.get("script_ready") or "").strip()
        script_ready = (row.get("script_ready") or "").strip()
        if status in BROKEN_FOR_SIMPLE_SCRAPE or script_ready == "FIX_URL_FIRST":
            _add_source_keys(result.blocked_source_keys, row)
        elif status == "FORBIDDEN_BUT_LIKELY_VALID":
            _add_source_keys(result.review_source_keys, row)
        elif status == "NEEDS_CONNECTOR_NOT_SIMPLE_SCRAPE" or script_ready == "YES_CONNECTOR_REQUIRED":
            _add_source_keys(result.connector_source_keys, row)
        elif status == "LOGIN_OR_MANUAL" or script_ready == "MANUAL_WORKFLOW_ONLY":
            _add_source_keys(result.manual_source_keys, row)
        elif status == "TIMEOUT_RETRY_NEEDED":
            _add_source_keys(result.retry_source_keys, row)


def run_preflight(
    input_path: str,
    output_dir: str = "./link_audit_out",
    no_search: bool = False,
    search_provider: str = "tavily",
    timeout: int = 20,
    retries: int = 2,
    workers: int = 4,
    rate_limit: float = 1.0,
    fail_on_broken: bool = False,
    dry_run: bool = False,
) -> PreflightResult:
    """Run the accepted live link checker in-process and return metadata."""
    in_path = Path(input_path).resolve()
    out_dir = Path(output_dir).resolve()

    argv = [
        "--input", str(in_path),
        "--output-dir", str(out_dir),
        "--search-provider", search_provider,
        "--timeout", str(timeout),
        "--retries", str(retries),
        "--workers", str(workers),
        "--rate-limit", str(rate_limit),
    ]
    if no_search:
        argv.append("--no-search")
    if fail_on_broken:
        argv.append("--preflight-fail-on-broken")
    if dry_run:
        argv.append("--dry-run")

    print("\nTENDER_FINDER link preflight - running through tenderfinder_raw_sweep.py")
    print(f"  input      : {in_path}")
    print(f"  output_dir : {out_dir}")
    print(f"  no_search  : {no_search}")
    print(f"  dry_run    : {dry_run}")

    code = LLC.main(argv)
    result = PreflightResult(exit_code=code, input_path=in_path, output_dir=out_dir)
    _collect_output_metadata(out_dir, result)

    print("\nTENDER_FINDER link preflight - output validation summary")
    for name in REQUIRED_OUTPUTS:
        p = result.files.get(name, out_dir / name)
        exists = p.exists()
        size = p.stat().st_size if exists else 0
        rows = result.row_counts.get(name, "")
        row_text = f", rows={rows}" if isinstance(rows, int) and rows >= 0 else ""
        print(f"  {'OK' if exists and size else '--'} {name} size={size}{row_text}")

    print("TENDER_FINDER link preflight - routing summary")
    print(f"  blocked/simple-scrape excluded : {len(result.blocked_source_keys)}")
    print(f"  review/403 likely valid        : {len(result.review_source_keys)}")
    print(f"  connector workflow             : {len(result.connector_source_keys)}")
    print(f"  manual workflow                : {len(result.manual_source_keys)}")
    print(f"  retry/review                   : {len(result.retry_source_keys)}")
    return result


def run_preflight_from_runner_args(args) -> PreflightResult:
    """Build wrapper settings from tenderfinder_raw_sweep.py argparse args."""
    return run_preflight(
        input_path=args.from_master,
        output_dir=args.preflight_output_dir,
        no_search=args.preflight_no_search,
        search_provider=args.preflight_search_provider,
        timeout=args.preflight_timeout,
        retries=args.preflight_retries,
        workers=args.preflight_workers,
        rate_limit=args.preflight_rate_limit,
        fail_on_broken=args.preflight_fail_on_broken,
        dry_run=args.dry_run,
    )


def filter_connectors_by_preflight(rows: Iterable[Dict[str, str]], result: Optional[PreflightResult], include_broken_sources: bool = False) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """Return (kept, skipped) connectors after source-health gating.

    This never deletes connector rows. It only prevents obvious broken URL rows
    from moving into simple scraping unless --include-broken-sources is provided.
    """
    rows = list(rows)
    if include_broken_sources or result is None or not result.blocked_source_keys:
        return rows, []

    kept: List[Dict[str, str]] = []
    skipped: List[Dict[str, str]] = []
    for row in rows:
        source_keys = {
            _norm_key(row.get("source_id")),
            _norm_key(row.get("id")),
            _norm_key(row.get("name")),
            _norm_key(row.get("source_name")),
        }
        if source_keys & result.blocked_source_keys:
            skipped.append(row)
        else:
            kept.append(row)
    return kept, skipped

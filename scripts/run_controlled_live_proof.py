#!/usr/bin/env python3
"""Run a bounded, explicit one-or-two-source public live proof."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = ROOT / "01 Code" / "CONNECTOR_SWEEP"
sys.path.insert(0, str(CODE_DIR))

from tenderfinder_engine import test_source_definition  # noqa: E402
from tenderfinder_source_registry import load_source_rows, registry_summary  # noqa: E402


VANCOUVER = ZoneInfo("America/Vancouver")
SAMPLE_FIELDS = (
    "source_id", "project_id", "lead_id", "app_no", "tender_title", "title",
    "municipality", "issuer", "status", "current_stage", "scope_summary",
    "source_url", "url", "fit_score", "signal_quality", "fit_tier", "route",
    "output_route", "civil_relevant", "closing_date",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact_sample(record: dict[str, Any]) -> dict[str, Any]:
    return {
        field: record.get(field)
        for field in SAMPLE_FIELDS
        if record.get(field) not in (None, "", [], {})
    }


def relevance_for(sample: dict[str, Any], track: str) -> dict[str, Any]:
    if track == "tender":
        relevant = bool(sample.get("civil_relevant"))
        reason = "normalized tender civil relevance flag"
    else:
        score = int(sample.get("fit_score") or 0)
        route = str(sample.get("route") or sample.get("output_route") or "")
        relevant = score >= 50 or route == "Future_Projects"
        reason = f"fit_score={score}; route={route or '(blank)'}"
    return {"relevant": relevant, "reason": reason}


def run_proof(source_ids: list[str], *, persist: bool, output_dir: Path) -> dict[str, Any]:
    if not 1 <= len(source_ids) <= 2:
        raise ValueError("Controlled live proof requires exactly one or two source IDs")
    rows = {row["source_id"]: row for row in load_source_rows(root=ROOT)}
    missing = [source_id for source_id in source_ids if source_id not in rows]
    if missing:
        raise KeyError(f"Unknown source ID(s): {', '.join(missing)}")

    source_path = ROOT / "config" / "sources.csv"
    before_hash = sha256(source_path)
    started = datetime.now(VANCOUVER).isoformat(timespec="seconds")
    results = []
    for source_id in source_ids:
        row = rows[source_id]
        result = test_source_definition(
            source_id,
            root=ROOT,
            sources_path=source_path,
            allow_network=True,
            persist_result=persist,
        )
        samples = [compact_sample(record) for record in result.get("normalized_preview") or []]
        results.append(
            {
                "source_id": source_id,
                "source_type": row["track"],
                "public_url": row["url"] if row["track"] == "tender" else row["endpoint"],
                "timestamp": result.get("test_timestamp") or datetime.now(VANCOUVER).isoformat(timespec="seconds"),
                "http_result": result.get("http_status") or "not reported",
                "final_validated_public_url": result.get("final_validated_url") or "",
                "adapter": row["adapter"],
                "status": result.get("status"),
                "status_code": result.get("status_code"),
                "raw_candidates": int(result.get("raw_candidate_count") or 0),
                "normalized_records": int(result.get("normalized_count") or 0),
                "rejected_candidates": int(result.get("rejected_count") or 0),
                "warnings": list(result.get("warnings") or []),
                "errors": list(result.get("errors") or []),
                "sample_sanitized_records": samples,
                "sample_score_results": [
                    {
                        "fit_score": sample.get("fit_score"),
                        "tier": sample.get("signal_quality") or sample.get("fit_tier"),
                        "route": sample.get("route") or sample.get("output_route"),
                    }
                    for sample in samples
                ],
                "sample_relevance_results": [relevance_for(sample, row["track"]) for sample in samples],
                "final_operational_classification": result.get("operational_status") or row["operational_status"],
                "passed": bool(result.get("passed")),
                "network_used": bool(result.get("network_used")),
                "parser_used": bool(result.get("parser_used")),
                "probe_output": result.get("probe_output"),
                "manual_sample_review": "PENDING_AGENT_REVIEW",
            }
        )

    after_hash = sha256(source_path)
    payload = {
        "schema_version": 1,
        "scope": "controlled public BC live proof; maximum two explicit sources",
        "started_at": started,
        "finished_at": datetime.now(VANCOUVER).isoformat(timespec="seconds"),
        "persisted_registry_metadata": persist,
        "source_registry_sha256_before": before_hash,
        "source_registry_sha256_after": after_hash,
        "source_registry_summary_after": registry_summary(root=ROOT),
        "results": results,
        "all_passed": all(result["passed"] for result in results),
    }
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "controlled_live_proof.json"
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    payload["output_path"] = str(output_path)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a bounded public Tender Finder live proof.")
    parser.add_argument("--source-id", action="append", required=True)
    parser.add_argument("--persist", action="store_true", help="Persist truthful last-test/status metadata.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(r"C:\tenderfinder_out\release_evidence_work\controlled_live"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = run_proof(args.source_id, persist=args.persist, output_dir=args.output_dir)
    except Exception as exc:
        print(f"CONTROLLED_LIVE_PROOF: FAIL - {type(exc).__name__}: {exc}")
        return 1
    print("CONTROLLED_LIVE_PROOF: " + ("PASS" if payload["all_passed"] else "FAIL"))
    print(f"OUTPUT: {payload['output_path']}")
    for result in payload["results"]:
        print(
            f"SOURCE {result['source_id']}: {result['status_code']} "
            f"HTTP={result['http_result']} raw={result['raw_candidates']} "
            f"normalized={result['normalized_records']} rejected={result['rejected_candidates']} "
            f"operational={result['final_operational_classification']}"
        )
    return 0 if payload["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

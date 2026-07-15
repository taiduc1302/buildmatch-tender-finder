#!/usr/bin/env python3
"""Display-independent source configuration and offline-adapter testing.

The fixture runner is deliberately pure: it reads a local sanitized fixture,
executes the same parser/normalizer primitives used by the live adapter, and
never calls a network helper.  Adapter-level fixture success proves the code
path, not that every website using the adapter currently works.
"""
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from tenderfinder_package_paths import detect_package_root


NO_FIXTURE_STATUS = "NOT TESTED — NO APPLICABLE OFFLINE FIXTURE"
FIXTURE_PASS_STATUS = "ADAPTER FIXTURE PASS"
FIXTURE_FAIL_STATUS = "ADAPTER FIXTURE FAIL"

ADAPTER_FIXTURES = {
    "public_listing": "adapter_public_listing.html",
    "bc_bid_browser": "adapter_bc_bid_browser.html",
    "arcgis_hub_discover": "adapter_arcgis_hub_discover.json",
    "arcgis_hub_item": "adapter_arcgis_hub_item.json",
    "arcgis_map_discover": "adapter_arcgis_map_discover.json",
    "arcgis_rest_layer": "adapter_arcgis_rest_layer.json",
    "ods_v21": "adapter_ods_v21.json",
    "surrey_planning_reports": "surrey_rezoning_inprocess_sample.pdf",
}


def fixture_catalog(*, root: str | Path | None = None) -> dict[str, Path]:
    package_root = detect_package_root(Path(root).resolve() if root else None)
    fixture_root = package_root / "01 Code" / "CONNECTOR_SWEEP" / "tests" / "fixtures"
    return {adapter: fixture_root / name for adapter, name in ADAPTER_FIXTURES.items()}


def applicable_fixture(row: dict[str, Any], *, root: str | Path | None = None) -> Path | None:
    fixture = fixture_catalog(root=root).get(str(row.get("adapter") or "").casefold())
    return fixture if fixture and fixture.is_file() else None


def _plain(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items() if not str(key).startswith("_raw")}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _required_fields_ok(track: str, record: dict[str, Any]) -> bool:
    if track == "tender":
        return bool(record.get("source_id") and record.get("tender_title") and record.get("url"))
    return bool(
        record.get("project_id")
        and record.get("source_url")
        and record.get("title")
        and record.get("municipality")
        and record.get("fit_score") is not None
    )


def _public_listing_fixture(row: dict[str, Any], fixture: Path) -> tuple[int, list[dict[str, Any]], str]:
    import tenderfinder_demo_three_buckets as demo

    body = fixture.read_text(encoding="utf-8-sig")
    base_url = str(row.get("url") or "https://public.example.org/opportunities")
    if body.lstrip().startswith("<") and any(
        marker in body[:1000].casefold() for marker in ("<rss", "<feed")
    ):
        candidates = demo.parse_rss(body, row, base_url, base_url)
        parser = "public_listing_rss"
    else:
        candidates = demo.parse_html_links(body, row, base_url)
        parser = "public_listing_html"
    return len(candidates), [_plain(candidate) for candidate in candidates], parser


def _bc_bid_fixture(row: dict[str, Any], fixture: Path) -> tuple[int, list[dict[str, Any]], str]:
    import tenderfinder_demo_three_buckets as demo

    body = fixture.read_text(encoding="utf-8-sig")
    final_url = str(row.get("url") or "https://bcbid.gov.bc.ca/page.aspx/en/rfp/request_browse_public")
    candidates = demo.parse_bc_bid_listing_html(body, row, final_url)
    return len(candidates), [_plain(candidate) for candidate in candidates], "bc_bid_listing_html"


def _development_json_fixture(
    row: dict[str, Any],
    fixture: Path,
) -> tuple[int, list[dict[str, Any]], str]:
    import tenderfinder_raw_sweep as raw

    payload = json.loads(fixture.read_text(encoding="utf-8-sig"))
    adapter = str(row.get("adapter") or "").casefold()
    keywords = [
        item.strip().casefold()
        for item in str(row.get("layer_keywords") or "development").split(";")
        if item.strip()
    ]
    layer_name = str(row.get("name") or adapter)
    selection_count = 1
    if adapter == "arcgis_hub_discover":
        selections = raw.hub_candidates_from_feed(payload, keywords)
        if not selections:
            selections = raw.hub_candidates_from_feed(payload, ["development", "application"])
        if not selections:
            return 0, [], "arcgis_hub_dcat"
        layer_name = selections[0][0]
        selection_count = len(selections)
        records = raw.arcgis_attributes_from_payload(payload)
        parser = "arcgis_hub_dcat"
    elif adapter == "arcgis_hub_item":
        item = payload.get("item") or {}
        layer_name, _resolved = raw.hub_item_candidate_from_metadata(
            item,
            str(item.get("id") or row.get("endpoint") or "fixture-item"),
            row.get("layer_index") or 0,
        )
        records = raw.arcgis_attributes_from_payload(payload)
        parser = "arcgis_hub_item"
    elif adapter == "arcgis_map_discover":
        base = str(row.get("endpoint") or row.get("url") or "https://public.example.org/MapServer")
        selections = raw.map_candidates_from_metadata(payload, base, keywords)
        if not selections:
            selections = raw.map_candidates_from_metadata(
                payload, "https://public.example.org/MapServer", ["development", "application"]
            )
        if not selections:
            return 0, [], "arcgis_map_discover"
        layer_name = selections[0][0]
        selection_count = len(selections)
        records = raw.arcgis_attributes_from_payload(payload)
        parser = "arcgis_map_discover"
    elif adapter == "arcgis_rest_layer":
        records = raw.arcgis_attributes_from_payload(payload)
        parser = "arcgis_rest_layer"
    elif adapter == "ods_v21":
        records = raw.ods_records_from_payload(payload)
        parser = "ods_v21"
    else:
        return 0, [], adapter
    normalized = [raw.normalize_lead(row, layer_name, attrs) for attrs in records]
    return max(selection_count, len(records)), [_plain(record) for record in normalized], parser


def _surrey_pdf_fixture(row: dict[str, Any], fixture: Path) -> tuple[int, list[dict[str, Any]], str]:
    import tenderfinder_surrey_inprocess as surrey

    raw_rows, debug = surrey._extract_pdf_rows(
        fixture.read_bytes(),
        "SanitizedFixture",
        "Rezoning",
        debug_dir=None,
    )
    normalized = [
        surrey._normalize_surrey_lead(
            raw,
            str(row.get("url") or "https://www.surrey.ca/planning"),
            "SanitizedFixture",
            "Rezoning",
            "OFFLINE-FIXTURE",
        )
        for raw in raw_rows
    ]
    return len(raw_rows), [_plain(record) for record in normalized], str(debug.get("strategy_used") or "surrey_pdf")


def run_offline_adapter_fixture(
    row: dict[str, Any],
    *,
    root: str | Path | None = None,
    fixture_path: str | Path | None = None,
) -> dict[str, Any]:
    """Execute one adapter with a local fixture and return an honest result."""
    package_root = detect_package_root(Path(root).resolve() if root else None)
    fixture = (
        Path(fixture_path).expanduser().resolve()
        if fixture_path is not None
        else applicable_fixture(row, root=package_root)
    )
    base = {
        "passed": False,
        "network_used": False,
        "parser_used": False,
        "source_id": str(row.get("source_id") or ""),
        "track": str(row.get("track") or ""),
        "adapter": str(row.get("adapter") or ""),
        "fixture": str(fixture) if fixture else "",
        "fixture_scope": (
            "source_specific" if str(row.get("adapter") or "") == "surrey_planning_reports" else "adapter_level"
        ),
        "status": NO_FIXTURE_STATUS,
        "status_code": "NOT_TESTED_NO_FIXTURE",
        "candidate_count": 0,
        "normalized_count": 0,
        "normalized_preview": [],
        "warnings": [],
        "errors": [],
    }
    if fixture is None or not fixture.is_file():
        return base
    try:
        adapter = base["adapter"]
        if adapter == "public_listing":
            candidates, normalized, parser = _public_listing_fixture(row, fixture)
        elif adapter == "bc_bid_browser":
            candidates, normalized, parser = _bc_bid_fixture(row, fixture)
        elif adapter in {
            "arcgis_hub_discover", "arcgis_hub_item", "arcgis_map_discover",
            "arcgis_rest_layer", "ods_v21",
        }:
            candidates, normalized, parser = _development_json_fixture(row, fixture)
        elif adapter == "surrey_planning_reports":
            candidates, normalized, parser = _surrey_pdf_fixture(row, fixture)
        else:
            return base
        usable = [record for record in normalized if _required_fields_ok(base["track"], record)]
        passed = candidates > 0 and len(usable) > 0
        base.update(
            {
                "passed": passed,
                "parser_used": True,
                "status": FIXTURE_PASS_STATUS if passed else FIXTURE_FAIL_STATUS,
                "status_code": "PASS_ADAPTER_FIXTURE" if passed else "FAIL_ADAPTER_FIXTURE",
                "parser": parser,
                "candidate_count": candidates,
                "normalized_count": len(usable),
                "normalized_preview": usable[:5],
                "details": {
                    "fixture": str(fixture),
                    "fixture_scope": base["fixture_scope"],
                    "parser": parser,
                },
            }
        )
        if candidates and len(usable) != len(normalized):
            base["warnings"].append(
                f"{len(normalized) - len(usable)} normalized record(s) missed required fields"
            )
    except Exception as exc:
        base.update(
            {
                "status": FIXTURE_FAIL_STATUS,
                "status_code": "FAIL_ADAPTER_FIXTURE",
                "errors": [f"{type(exc).__name__}: {exc}"],
            }
        )
    return base

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tenderfinder_source_registry.py — Source_Register <-> connector-CSV bridge
==================================================================
Reads the BUSINESS source list (Source_Register tab of the master workbook) and
the TECHNICAL endpoint list (tenderfinder_dev_app_endpoints.csv), reconciles them, and
emits a sync report assigning every source a controlled status + next action.

The master's Source_Register has NO source_id (sources are keyed by name); the
connector CSV is keyed by source_id. This module bridges the two by name alias.

Sync statuses (handoff section 8):
  ready_for_probe | ready_for_load | missing_connector | needs_exact_url |
  manual_p3_only | paid_or_login_skip | access_test_required |
  disabled_wrong_layer | endpoint_stale | blocked | not_automation_ready

Dependency: openpyxl (only when reading the workbook).
"""

import csv
import os
import re

# Map Source_Register names -> connector CSV source_id. Substring match,
# checked longest-first so specific names win.
NAME_TO_CONNECTOR = {
    "township of langley development activity": "twp_langley_devactivity",
    "maple ridge active development application": "maple_ridge_devapps",
    "surrey development applications / open dat": "surrey_devapps",
    "surrey development applications v2": "surrey_devapps_v2",
    "surrey planning reports": "surrey_planning_reports",
    "surrey planning reports / in-process": "surrey_planning_reports",
    "city of surrey - planning reports": "surrey_planning_reports",
    "surrey gis / futureworks": "surrey_futureworks",
    "surrey capital / futureworks layers": "surrey_futureworks",
    "city of langley development portal": "city_langley_devapps",
    "vancouver issued building permits": "van_building_permits",
    "vancouver open data": "van_city_projects",
    "abbotsford development / open data": "abbotsford_devapps",
    "new westminster open data": "new_west_currentdev",
    "burnaby open data / capital projects": "burnaby_devapps",
    "coquitlam development information portal": "coquitlam_devapps",
    "delta current development applications": "delta_devapps",
    "district of north vancouver geoweb": "dnv_devapps",
}

# Category-driven defaults for sources WITHOUT a technical connector.
PAID_TOKENS = ("paid",)
LOGIN_TOKENS = ("login", "registration", "bceid", "ariba", "supplier portal")
ACTIVE_TENDER_CAT = "a —"          # category A — active tender portals
NEWS_CAT = "g —"                   # category G — news / early-signal
COUNCIL_CAT = "c —"                # category C — council / committee agendas
CAPITAL_CAT = "d —"                # category D — capital plans
GC_CAT = "f —"                     # category F — GC / developer invitations
PAID_CAT = "e —"                   # category E — paid intelligence


def _norm(s):
    return re.sub(r"\s+", " ", str(s or "").strip().lower())


def load_connectors(csv_path):
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    # tolerant key access: source_id or id
    out = {}
    for r in rows:
        sid = r.get("source_id") or r.get("id")
        if sid:
            out[sid] = r
    return out


def load_source_register(master_path):
    import openpyxl
    wb = openpyxl.load_workbook(master_path, data_only=True)
    ws = wb["Source_Register"]
    hdr = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
    out = []
    for r in range(2, ws.max_row + 1):
        name = ws.cell(r, 1).value
        if not name:
            continue
        rec = {hdr[c - 1]: ws.cell(r, c).value for c in range(1, ws.max_column + 1)}
        out.append(rec)
    return out


def match_connector(source_name, connectors):
    """Return connector source_id for a Source_Register name, or None."""
    n = _norm(source_name)
    # longest alias first for specificity
    for alias in sorted(NAME_TO_CONNECTOR, key=len, reverse=True):
        if alias in n or n in alias:
            sid = NAME_TO_CONNECTOR[alias]
            if sid in connectors:
                return sid
    return None


def classify_source(sr_row, connector):
    """Decide the sync status + next action for one Source_Register row.
    sr_row    : dict from Source_Register
    connector : dict from connector CSV, or None
    Returns dict with sync fields."""
    cat = _norm(sr_row.get("Category"))
    cost = _norm(sr_row.get("Cost"))
    access = _norm(sr_row.get("Access Status / Confidence"))
    name = sr_row.get("Source Name")

    # ---- paid / login first (never scrape) -------------------------------
    if cat.startswith(PAID_CAT) or any(t in cost for t in PAID_TOKENS):
        return _mk("paid_or_login_skip", "skip unless paid access configured",
                   connector, sr_row)
    if any(t in access for t in LOGIN_TOKENS) and cat.startswith(ACTIVE_TENDER_CAT):
        return _mk("paid_or_login_skip",
                   "login/registration portal — use alerts, do not scrape",
                   connector, sr_row)

    # ---- active tender portals (separate track) --------------------------
    if cat.startswith(ACTIVE_TENDER_CAT):
        return _mk("not_automation_ready",
                   "Active-tender track: configure alerts in Task D Phase 0",
                   connector, sr_row, route="Active_Tenders",
                   prompt="PROMPT_ACTIVE_TENDER_PARSE")

    # ---- has a technical connector ---------------------------------------
    if connector:
        acc = _norm(connector.get("access_status"))
        if acc == "ready_for_load":
            return _mk("ready_for_load", "Tier load OK — run --tier with richness gate",
                       connector, sr_row)
        if acc == "ready_for_probe":
            return _mk("ready_for_probe", "probe + verify layer before load",
                       connector, sr_row)
        if acc == "needs_exact_url":
            return _mk("needs_exact_url",
                       "verify endpoint manually (no silent fallback)",
                       connector, sr_row)
        if acc == "disabled_wrong_layer":
            return _mk("disabled_wrong_layer",
                       "wrong layer — denylisted; re-pin to a real dev-app layer",
                       connector, sr_row, route="Rejected_Archive")
        if acc == "access_test_required":
            return _mk("access_test_required",
                       "run from TENDER_FINDER office network (Surrey Test #1)",
                       connector, sr_row)
        if acc == "trailing_context":
            return _mk("ready_for_probe",
                       "trailing/context only — load to Rejected_Archive/Context, not FP",
                       connector, sr_row, route="Rejected_Archive")
        if acc == "manual_p3_only":
            return _mk("manual_p3_only", "run P3 web/PDF extractor",
                       connector, sr_row, route="Run_Queue",
                       prompt="PROMPT_WEB_PDF_EXTRACT")
        # connector exists but status unknown
        return _mk("ready_for_probe", "probe to confirm layer",
                   connector, sr_row)

    # ---- no connector: route by category ---------------------------------
    if cat.startswith(COUNCIL_CAT):
        return _mk("manual_p3_only", "run P3 council-agenda extractor", None,
                   sr_row, route="Run_Queue", prompt="PROMPT_COUNCIL_CAPITAL")
    if cat.startswith(CAPITAL_CAT):
        return _mk("manual_p3_only", "run P3 capital-plan extractor", None,
                   sr_row, route="Run_Queue", prompt="PROMPT_COUNCIL_CAPITAL")
    if cat.startswith(GC_CAT):
        return _mk("not_automation_ready",
                   "GC invites: estimating@example.com auto-forward (Task D)", None,
                   sr_row, route="Active_Tenders", prompt="PROMPT_ACTIVE_TENDER_PARSE")
    if cat.startswith(NEWS_CAT):
        return _mk("manual_p3_only", "manual/LLM news scan (low priority)", None,
                   sr_row, route="Run_Queue", prompt="PROMPT_WEB_PDF_EXTRACT")
    # municipal dev-app source with no connector
    return _mk("missing_connector",
               "add endpoint to connector CSV, then probe", None, sr_row,
               route="Run_Queue", prompt="PROMPT_WEB_PDF_EXTRACT")


def _mk(status, next_action, connector, sr_row, route=None, prompt=None):
    fetch = connector.get("fetch_type") if connector else ""
    endpoint = (connector.get("last_good_endpoint") or connector.get("endpoint")) if connector else ""
    layer = connector.get("layer_index") if connector else ""
    auto = (connector.get("automation_feasibility") if connector
            else sr_row.get("Automation Feasibility")) or ""
    out_route = route or (connector.get("output_route") if connector else "") or ""
    ptype = prompt or (connector.get("prompt_type") if connector else "") or ""
    return {
        "source_register_status": sr_row.get("Access Status / Confidence") or "",
        "connector_registry_status": status,
        "fetch_type": fetch, "endpoint": endpoint, "layer": layer,
        "automation_feasibility": auto, "access_status": status,
        "output_route": out_route, "prompt_type": ptype,
        "next_action": next_action,
    }


def build_sync_report(master_path, csv_path):
    """Return (rows, summary) where rows match the handoff section-8 schema."""
    connectors = load_connectors(csv_path)
    sources = load_source_register(master_path)
    used_connectors = set()
    rows = []
    for sr in sources:
        sid = match_connector(sr.get("Source Name"), connectors)
        conn = connectors.get(sid) if sid else None
        if sid:
            used_connectors.add(sid)
        cls = classify_source(sr, conn)
        rows.append({
            "source_id": sid or _slug(sr.get("Source Name")),
            "source_name": sr.get("Source Name"),
            "category": sr.get("Category"),
            "priority_tier": sr.get("Priority Tier"),
            **cls,
            "notes": sr.get("Notes / Cleanup") or "",
        })
    # connectors not present in Source_Register
    for sid, conn in connectors.items():
        if sid not in used_connectors:
            rows.append({
                "source_id": sid, "source_name": conn.get("name"),
                "category": conn.get("category"),
                "priority_tier": conn.get("priority_tier"),
                "source_register_status": "NOT IN SOURCE_REGISTER",
                "connector_registry_status": conn.get("access_status") or "ready_for_probe",
                "fetch_type": conn.get("fetch_type"),
                "endpoint": conn.get("last_good_endpoint") or conn.get("endpoint"),
                "layer": conn.get("layer_index"),
                "automation_feasibility": conn.get("automation_feasibility"),
                "access_status": conn.get("access_status"),
                "output_route": conn.get("output_route"),
                "prompt_type": conn.get("prompt_type"),
                "next_action": "connector present but no business source row — review",
                "notes": conn.get("notes") or "",
            })
    summary = {}
    for r in rows:
        s = r["connector_registry_status"]
        summary[s] = summary.get(s, 0) + 1
    return rows, summary


def _slug(name):
    return re.sub(r"[^a-z0-9]+", "_", _norm(name)).strip("_")[:40]


SYNC_COLUMNS = [
    "source_id", "source_name", "category", "priority_tier",
    "source_register_status", "connector_registry_status", "fetch_type",
    "endpoint", "layer", "automation_feasibility", "access_status",
    "output_route", "prompt_type", "next_action", "notes",
]


def write_sync_report_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=SYNC_COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in SYNC_COLUMNS})


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="TENDER_FINDER Source_Register <-> connector sync")
    ap.add_argument("--from-master", required=True)
    ap.add_argument("--config", default="tenderfinder_dev_app_endpoints.csv")
    ap.add_argument("--out", default="sync_report.csv")
    a = ap.parse_args()
    rows, summary = build_sync_report(a.from_master, a.config)
    write_sync_report_csv(rows, a.out)
    print(f"Sync report: {len(rows)} sources -> {a.out}")
    for k in sorted(summary):
        print(f"  {k:<24} {summary[k]}")

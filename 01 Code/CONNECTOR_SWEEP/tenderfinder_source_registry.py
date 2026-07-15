#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical editable source registry for TENDER_FINDER.

``config/sources.csv`` is the single runtime source of truth for both tender
and development tracks. This module strictly validates the registry, exposes
active rows to both collection paths, and provides atomic add/edit/toggle
operations used by the GUI.

The lower compatibility section can still reconcile a historical
``Source_Register`` worksheet with the canonical CSV for audit reports. Its
name aliases are reference-only; they do not define normal runtime sources.
"""

import csv
import ipaddress
import os
import re
from pathlib import Path
from urllib.parse import urlparse

from tenderfinder_package_paths import detect_package_root, sources_config_path


REGISTRY_ENV_VAR = "TENDER_FINDER_SOURCES_CONFIG"
SOURCE_COLUMNS = (
    "source_id", "name", "track", "active", "adapter", "municipality", "url", "rss",
    "url_variants", "no_retry", "category", "tier", "platform", "fetch_type", "endpoint",
    "layer_index", "layer_keywords", "priority_tier", "access_status",
    "automation_feasibility", "output_route", "prompt_type", "status", "last_probe_status",
    "last_good_endpoint", "notes",
)
SOURCE_TRACKS = frozenset({"tender", "development"})
TENDER_ADAPTERS = frozenset({"public_listing", "bc_bid_browser"})
DEVELOPMENT_ADAPTERS = frozenset(
    {
        "arcgis_hub_discover", "arcgis_hub_item", "arcgis_map_discover",
        "arcgis_rest_layer", "ods_v21", "surrey_planning_reports",
    }
)
SOURCE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_]{2,63}$")
RESERVED_SOURCE_IDS = frozenset({"email_alert_intake"})


class SourceRegistryError(RuntimeError):
    """Raised when the founder-editable runtime source registry is unsafe."""

    def __init__(self, path, errors):
        self.path = Path(path)
        self.errors = tuple(str(error) for error in errors)
        details = "\n".join(f"  - {error}" for error in self.errors)
        super().__init__(f"Source registry is invalid: {self.path}\n{details}")


def resolve_registry_path(path=None, root=None):
    if path:
        return Path(path).expanduser().resolve()
    override = os.environ.get(REGISTRY_ENV_VAR, "").strip()
    if override:
        return Path(override).expanduser().resolve()
    package_root = detect_package_root(Path(root).resolve() if root else None)
    return sources_config_path(package_root).resolve()


def _is_public_url(value):
    parsed = urlparse(str(value or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        return False
    hostname = parsed.hostname.casefold().rstrip(".")
    if hostname == "localhost" or hostname.endswith((".localhost", ".local", ".internal")):
        return False
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return True
    return not (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
        or address.is_unspecified
    )


def _normalized_source_row(row):
    out = {column: str(row.get(column, "") or "").strip() for column in SOURCE_COLUMNS}
    out["source_id"] = out["source_id"].casefold()
    out["track"] = out["track"].casefold()
    out["active"] = out["active"].upper()
    out["adapter"] = out["adapter"].casefold()
    out["no_retry"] = (out["no_retry"] or "N").upper()
    if not out["fetch_type"]:
        out["fetch_type"] = out["adapter"]
    if out["track"] == "development" and not out["endpoint"]:
        out["endpoint"] = out["url"]
    return out


def source_readiness_errors(row):
    """Return reasons why one row cannot be enabled or explicitly tested.

    Disabled rows are allowed to be incomplete drafts in the canonical CSV.
    This helper is the single readiness gate used when enabling/running them.
    """
    errors = []
    if not row["name"]:
        errors.append("name is required")
    if row["track"] == "tender":
        if not row["adapter"]:
            errors.append("adapter is required")
        elif row["adapter"] not in TENDER_ADAPTERS:
            errors.append(
                "custom adapter required; supported tender adapters are "
                + ", ".join(sorted(TENDER_ADAPTERS))
            )
        if not _is_public_url(row["url"]):
            errors.append("tender url must be a public http(s) URL")
        if row["rss"] and not _is_public_url(row["rss"]):
            errors.append("rss must be a public http(s) URL")
        for variant in (part.strip() for part in row["url_variants"].split("|") if part.strip()):
            if not _is_public_url(variant):
                errors.append(f"invalid url_variants entry '{variant}'")
    elif row["track"] == "development":
        if not row["adapter"]:
            errors.append("adapter is required")
        elif row["adapter"] not in DEVELOPMENT_ADAPTERS:
            errors.append(
                "custom adapter required; supported development adapters are "
                + ", ".join(sorted(DEVELOPMENT_ADAPTERS))
            )
        if not row["endpoint"]:
            errors.append("development endpoint is required")
        if row["url"] and "://" in row["url"] and not _is_public_url(row["url"]):
            errors.append("development url must be a public http(s) URL when supplied")
    return errors


def _validate_rows(rows, path):
    errors = []
    seen = set()
    for row_number, row in enumerate(rows, start=2):
        sid = row["source_id"]
        prefix = f"row {row_number}"
        if not SOURCE_ID_RE.fullmatch(sid):
            errors.append(f"{prefix}: source_id '{sid}' must use lowercase letters, numbers, and underscores")
        if sid in RESERVED_SOURCE_IDS:
            errors.append(f"{prefix}: source_id '{sid}' is reserved for an internal source")
        if sid in seen:
            errors.append(f"{prefix}: duplicate source_id '{sid}'")
        seen.add(sid)
        if row["track"] not in SOURCE_TRACKS:
            errors.append(f"{prefix}: track must be tender or development")
        if row["active"] not in {"Y", "N"}:
            errors.append(f"{prefix}: active must be Y or N")
        if row["no_retry"] not in {"Y", "N"}:
            errors.append(f"{prefix}: no_retry must be Y or N")
        if row["track"] in SOURCE_TRACKS and row["active"] == "Y":
            errors.extend(f"{prefix}: {message}" for message in source_readiness_errors(row))
        elif row["track"] == "tender":
            # Drafts may be incomplete or may name a future custom adapter,
            # but populated URLs must still be safe to retain in config.
            for label, value in (("url", row["url"]), ("rss", row["rss"])):
                if value and not _is_public_url(value):
                    errors.append(f"{prefix}: draft {label} must be a public http(s) URL when supplied")
            for variant in (part.strip() for part in row["url_variants"].split("|") if part.strip()):
                if not _is_public_url(variant):
                    errors.append(f"{prefix}: invalid draft url_variants entry '{variant}'")
        elif row["track"] == "development":
            # Several discovery adapters intentionally store an ArcGIS item
            # id or ODS dataset slug here.  Enforce the network guard only
            # when a disabled draft contains a URL.
            if row["url"] and "://" in row["url"] and not _is_public_url(row["url"]):
                errors.append(f"{prefix}: draft development url must be public when supplied")
    if errors:
        raise SourceRegistryError(path, errors)


def load_source_rows(path=None, *, root=None, active_only=False, track=None):
    """Load and strictly validate the one canonical runtime source registry."""
    resolved = resolve_registry_path(path, root)
    if not resolved.exists():
        raise SourceRegistryError(resolved, ["sources.csv is missing"])
    try:
        with resolved.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            headers = tuple(reader.fieldnames or ())
            missing = [column for column in SOURCE_COLUMNS if column not in headers]
            if missing:
                raise SourceRegistryError(resolved, [f"missing column(s): {', '.join(missing)}"])
            rows = [_normalized_source_row(row) for row in reader]
    except SourceRegistryError:
        raise
    except Exception as exc:
        raise SourceRegistryError(resolved, [f"could not read registry: {exc}"]) from exc
    _validate_rows(rows, resolved)
    if track is not None:
        normalized_track = str(track).strip().casefold()
        if normalized_track not in SOURCE_TRACKS:
            raise SourceRegistryError(resolved, [f"unknown track '{track}'"])
        rows = [row for row in rows if row["track"] == normalized_track]
    if active_only:
        rows = [row for row in rows if row["active"] == "Y"]
    return rows


def load_tender_sources(path=None, *, root=None, active_only=True):
    sources = []
    for row in load_source_rows(path, root=root, active_only=active_only, track="tender"):
        source = dict(row)
        source["url_variants"] = [part.strip() for part in row["url_variants"].split("|") if part.strip()]
        source["no_retry"] = row["no_retry"] == "Y"
        sources.append(source)
    return sources


def load_development_connectors(path=None, *, root=None, active_only=True):
    return {
        row["source_id"]: row
        for row in load_source_rows(path, root=root, active_only=active_only, track="development")
    }


def registry_summary(path=None, *, root=None):
    resolved = resolve_registry_path(path, root)
    rows = load_source_rows(resolved)
    return {
        "path": str(resolved),
        "total": len(rows),
        "active": sum(row["active"] == "Y" for row in rows),
        "tender": sum(row["track"] == "tender" for row in rows),
        "development": sum(row["track"] == "development" for row in rows),
    }


def write_source_rows(rows, path=None, *, root=None):
    """Validate and atomically replace a registry edited by the desktop GUI."""
    resolved = resolve_registry_path(path, root)
    normalized = [_normalized_source_row(row) for row in rows]
    _validate_rows(normalized, resolved)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    temporary = resolved.with_suffix(resolved.suffix + ".tmp")
    try:
        with temporary.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=SOURCE_COLUMNS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows({column: row.get(column, "") for column in SOURCE_COLUMNS} for row in normalized)
        os.replace(temporary, resolved)
    finally:
        if temporary.exists():
            temporary.unlink()
    return resolved


def upsert_source(source, path=None, *, root=None):
    rows = load_source_rows(path, root=root)
    incoming = _normalized_source_row(source)
    replaced = False
    for index, row in enumerate(rows):
        if row["source_id"] == incoming["source_id"]:
            rows[index] = incoming
            replaced = True
            break
    if not replaced:
        rows.append(incoming)
    return write_source_rows(rows, path, root=root)


def set_source_active(source_id, active, path=None, *, root=None):
    rows = load_source_rows(path, root=root)
    wanted = str(source_id).strip().casefold()
    found = False
    for row in rows:
        if row["source_id"] == wanted:
            row["active"] = "Y" if bool(active) else "N"
            found = True
            break
    if not found:
        raise SourceRegistryError(resolve_registry_path(path, root), [f"source_id '{source_id}' was not found"])
    return write_source_rows(rows, path, root=root)

# Compatibility-only map from historical Source_Register display names to
# canonical source IDs. Runtime collection never reads this list.
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
        reader = csv.DictReader(f)
        fieldnames = tuple(reader.fieldnames or ())
        rows = list(reader)
    if "track" in fieldnames:
        rows = load_source_rows(csv_path, active_only=False, track="development")
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
    ap = argparse.ArgumentParser(description="Reconcile a historical Source_Register sheet with the canonical source registry")
    ap.add_argument("--from-master", required=True)
    ap.add_argument("--config", default=str(resolve_registry_path()))
    ap.add_argument("--out", default="sync_report.csv")
    a = ap.parse_args()
    rows, summary = build_sync_report(a.from_master, a.config)
    write_sync_report_csv(rows, a.out)
    print(f"Sync report: {len(rows)} sources -> {a.out}")
    for k in sorted(summary):
        print(f"  {k:<24} {summary[k]}")

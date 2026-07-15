#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tenderfinder_surrey_inprocess.py — Surrey Planning Reports / In-Process PDF Connector
===============================================================================
Patch 5.0: Restores previously demonstrated Surrey lead workflow.

Fetches and parses Surrey City planning PDFs:
  - RezoningInProcess-Result.pdf     (RZ applications in process)
  - DP-IN-PROCESS.pdf               (Development Permit applications in process)
  - Planning Reports page            (council-approved planning reports)

Output normalizes to the TENDER_FINDER Future_Projects schema with all required fields:
  project_id, app_no, address, owner_applicant, app_type_stage,
  scope_summary, fit_score, fit_reason, source_url, evidence_url, etc.

Route: Future_Projects (passing TENDER_FINDER fit score >= 40)
       Run_Queue (incomplete records, fit score < 40)

Dependencies: requests or urllib (in TENDER_FINDER standard environment)
              pdfplumber (for PDF table extraction)
              openpyxl (already required by tenderfinder_raw_sweep.py)

Usage from tenderfinder_raw_sweep.py:
  python tenderfinder_raw_sweep.py --only surrey_planning_reports --review-only --out ./surrey_review.xlsx
"""

import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

try:
    import requests
    _HAVE_REQUESTS = True
except ImportError:
    _HAVE_REQUESTS = False

try:
    import pdfplumber
    _HAVE_PDFPLUMBER = True
except ImportError:
    _HAVE_PDFPLUMBER = False

# Import guards from parent module (same directory)
sys.path.insert(0, os.path.dirname(__file__))
try:
    import tenderfinder_guards as G
except ImportError:
    G = None  # graceful fallback for unit testing outside CONNECTOR_SWEEP/
from tenderfinder_url_safety import safe_requests_request, safe_urllib_fetch

# ---------------------------------------------------------------------------
# Surrey source URLs (public, no login required)
# ---------------------------------------------------------------------------
SURREY_SOURCES = [
    {
        "label": "RezoningInProcess",
        "url": "https://www.surrey.ca/sites/default/files/media/documents/RezoningInProcess-Result.pdf",
        "app_type": "Rezoning",
        "id_prefix": "SURREY",
    },
    {
        "label": "DPInProcess",
        "url": "https://www.surrey.ca/sites/default/files/media/documents/DP-IN-PROCESS.pdf",
        "app_type": "Development Permit",
        "id_prefix": "SURREY",
    },
]

UA = "TENDER_FINDER-tender-intel/2.0 (civil contractor lead screen; contact estimating@example.com)"

# ---------------------------------------------------------------------------
# Regex patterns for Surrey application IDs
# ---------------------------------------------------------------------------
# Matches: 7926-0157-00, 7925-0256-00, 25-0366, 25-0268, 24-0345, etc.
APP_NO_RE = re.compile(r"\b(\d{2,4}-\d{4}(?:-\d{2})?)\b")

# Surrey civic address pattern: number + street (handles numbered streets like
# "13458 78 Ave", "7685 152 St", and named streets like "King George Blvd").
ADDR_RE = re.compile(
    r"\b(\d{1,6}(?:\s*-\s*\d{1,6})?\s+[A-Za-z0-9][A-Za-z0-9\s,\.]*?"
    r"(?:St|Street|Ave|Avenue|Blvd|Boulevard|Dr|Drive|Rd|Road|Cres|Crescent|"
    r"Pl|Place|Crt|Court|Hwy|Highway|Way|Gate|Pkwy|Parkway|Terr|Loop|Diversion))\b",
    re.I)

# Common Surrey applicant/owner patterns
APPLICANT_RE = re.compile(r"(?:Applicant|Owner|Developer|Agent)\s*[:\-]?\s*([A-Z][A-Za-z0-9\s\.,&]+(?:Ltd|Inc|Corp|LP|LLP|Group|Homes|Properties|Holdings|Development)?\.?)", re.I)

# Surrey rezoning scope keywords
CIVIL_KEYWORDS = [
    "subdivision", "servicing", "site servicing", "road works", "civil",
    "multi-family", "multifamily", "townhouse", "mixed-use", "industrial",
    "commercial", "institutional", "rezoning", "development permit",
    "density", "lot consolidation", "strata",
]


# ---------------------------------------------------------------------------
# HTTP fetch helpers
# ---------------------------------------------------------------------------
def _http_get_bytes(url, timeout=30):
    """Return raw bytes from a URL."""
    if _HAVE_REQUESTS:
        fetched = safe_requests_request(
            "GET",
            url,
            request_callable=requests.request,
            headers={"User-Agent": UA},
            timeout=timeout,
        )
        r = fetched.response
        r.raise_for_status()
        return r.content
    return safe_urllib_fetch(
        url,
        headers={"User-Agent": UA},
        timeout=timeout,
        max_bytes=20_000_000,
    ).body


# ---------------------------------------------------------------------------
# PDF parsing  (Patch 5.3 P0.1 — hardened, layout-robust, never-silent-zero)
# ---------------------------------------------------------------------------
_HEADER_HINTS = ("application no", "file no", "appl. no", "app no", "address",
                 "applicant", "owner", "proposal", "stage", "status",
                 "description", "file manager", "planner")


def _looks_like_header(text_lower):
    return sum(1 for h in _HEADER_HINTS if h in text_lower) >= 2


def _rows_from_table(table, app_type, page_num, source_label):
    """Turn one extracted table (list of row-lists) into structured dicts."""
    out = []
    for row in table or []:
        if not row or all(c is None or str(c).strip() == "" for c in row):
            continue
        cells = [str(c).strip() if c not in (None,) else "" for c in row]
        combined = " ".join(cells).lower()
        if _looks_like_header(combined):
            continue
        # Only keep rows that actually contain an application id or an address;
        # otherwise table extraction has mis-split the page.
        if not APP_NO_RE.search(combined) and not ADDR_RE.search(" ".join(cells)):
            continue
        parsed = _parse_table_row(cells, app_type)
        parsed["page"] = page_num
        parsed["source_label"] = source_label
        out.append(parsed)
    return out


def _rows_from_text_lines(text, app_type, page_num, source_label):
    """Anchor on application-id lines and absorb wrapped continuation lines.

    Surrey in-process PDFs frequently render as flowing text with no ruling
    lines, so extract_tables() returns nothing. We anchor each record on a line
    that contains a recognizable application id and pull address/applicant/scope
    from that line plus the following wrapped lines until the next id.
    """
    rows = []
    lines = [ln.rstrip() for ln in (text or "").split("\n")]
    # indices of lines that start a new application record
    anchors = [i for i, ln in enumerate(lines) if APP_NO_RE.search(ln)]
    for idx, i in enumerate(anchors):
        start = i
        end = anchors[idx + 1] if idx + 1 < len(anchors) else len(lines)
        block_lines = lines[start:end]
        block = " ".join(block_lines)
        if _looks_like_header(block.lower()):
            continue
        m = APP_NO_RE.search(block)
        app_no = m.group(1) if m else ""
        am = ADDR_RE.search(block)
        address = am.group(1).strip() if am else ""
        apm = APPLICANT_RE.search(block)
        applicant = apm.group(1).strip() if apm else ""
        scope_parts = [kw for kw in CIVIL_KEYWORDS if kw in block.lower()]
        scope = "; ".join(scope_parts[:3]) or app_type
        rows.append({
            "app_no": app_no, "address": address, "applicant": applicant,
            "scope": scope, "stage": app_type, "page": page_num,
            "source_label": source_label,
        })
    return rows


def _rows_from_words(page, app_type, page_num, source_label):
    """Last-resort positional reconstruction: cluster words into visual rows by
    their top (y) coordinate, then parse each reconstructed line."""
    rows = []
    try:
        words = page.extract_words(use_text_flow=False, keep_blank_chars=False) or []
    except Exception:
        return rows
    if not words:
        return rows
    words.sort(key=lambda w: (round(float(w.get("top", 0)) / 3.0), float(w.get("x0", 0))))
    line_map = {}
    for w in words:
        band = round(float(w.get("top", 0)) / 3.0)
        line_map.setdefault(band, []).append(w)
    for band in sorted(line_map):
        ws = sorted(line_map[band], key=lambda w: float(w.get("x0", 0)))
        line = " ".join(str(w.get("text", "")) for w in ws).strip()
        if not line or _looks_like_header(line.lower()):
            continue
        if not APP_NO_RE.search(line):
            continue
        m = APP_NO_RE.search(line)
        am = ADDR_RE.search(line)
        apm = APPLICANT_RE.search(line)
        scope_parts = [kw for kw in CIVIL_KEYWORDS if kw in line.lower()]
        rows.append({
            "app_no": m.group(1) if m else "",
            "address": am.group(1).strip() if am else "",
            "applicant": apm.group(1).strip() if apm else "",
            "scope": "; ".join(scope_parts[:3]) or app_type,
            "stage": app_type, "page": page_num, "source_label": source_label,
        })
    return rows


def _emit_rows_from_ids(full_text, app_type, source_label):
    """Never-silent-zero safeguard (brief P0.1): if structured parsing found
    nothing but the document clearly contains recognizable application ids,
    emit one minimal row per unique id so the leads are not lost. These rows
    carry a flag so reviewers know context was sparse."""
    rows = []
    seen = set()
    for m in APP_NO_RE.finditer(full_text or ""):
        app_no = m.group(1)
        if app_no in seen:
            continue
        seen.add(app_no)
        # grab a little surrounding context for an address/scope guess
        s, e = max(0, m.start() - 80), min(len(full_text), m.end() + 120)
        ctx = full_text[s:e]
        am = ADDR_RE.search(ctx)
        scope_parts = [kw for kw in CIVIL_KEYWORDS if kw in ctx.lower()]
        rows.append({
            "app_no": app_no,
            "address": am.group(1).strip() if am else "",
            "applicant": "",
            "scope": "; ".join(scope_parts[:3]) or app_type,
            "stage": app_type,
            "page": None,
            "source_label": source_label,
            "id_only_fallback": True,
        })
    return rows


def _write_parse_debug(debug_dir, source_label, page_dumps, reason):
    """Write a human-readable debug artifact explaining a zero/low extraction."""
    try:
        os.makedirs(debug_dir, exist_ok=True)
        path = os.path.join(debug_dir, f"TENDER_FINDER_Surrey_Parse_Debug_{source_label}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"Surrey parse debug — {source_label}\n")
            f.write(f"reason: {reason}\n")
            f.write(f"generated: {dt.datetime.now().isoformat(timespec='seconds')}\n")
            f.write("=" * 70 + "\n")
            for pageno, raw_text, table_count, word_count in page_dumps:
                f.write(f"\n--- PAGE {pageno} | tables={table_count} words={word_count} ---\n")
                f.write("APP_NO regex matches on this page: "
                        + ", ".join(sorted(set(APP_NO_RE.findall(raw_text or "")))) + "\n")
                f.write("RAW TEXT (first 4000 chars):\n")
                f.write((raw_text or "")[:4000] + "\n")
        return path
    except Exception as exc:  # never let debug writing crash the run
        print(f"    [surrey] WARNING: could not write parse debug: {exc}")
        return ""


def _extract_pdf_rows(pdf_bytes, source_label, app_type, debug_dir=None):
    """Extract application rows from a Surrey in-process PDF.

    Multi-strategy, in order, stopping per page at the first that yields rows:
      A. ruled-table extraction (lines strategy)
      B. text-strategy table extraction (no ruling lines)
      C. id-anchored text-line parsing
      D. positional word-cluster reconstruction
    Document-level safeguard (E): if every page yields zero rows but recognizable
    application ids exist anywhere in the text, emit minimal id-only rows rather
    than silently returning nothing. A debug artifact is written when extraction
    is empty (brief P0.1).

    Returns (rows, debug_info_dict).
    """
    if not _HAVE_PDFPLUMBER:
        raise RuntimeError("pdfplumber is required for Surrey PDF extraction. "
                           "Install with: pip install pdfplumber --break-system-packages")

    import io
    rows = []
    page_dumps = []
    full_text_parts = []
    strategy_used = []

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            page_rows = []
            # A: ruled tables
            try:
                for table in (page.extract_tables() or []):
                    page_rows += _rows_from_table(table, app_type, page_num, source_label)
                if page_rows:
                    strategy_used.append(f"p{page_num}:ruled_table")
            except Exception:
                pass
            # B: text-strategy tables
            if not page_rows:
                try:
                    text_tables = page.extract_tables(table_settings={
                        "vertical_strategy": "text", "horizontal_strategy": "text"}) or []
                    for table in text_tables:
                        page_rows += _rows_from_table(table, app_type, page_num, source_label)
                    if page_rows:
                        strategy_used.append(f"p{page_num}:text_table")
                except Exception:
                    pass
            # C + D need the page text
            text = ""
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""
            full_text_parts.append(text)
            # C: id-anchored line parse
            if not page_rows:
                page_rows += _rows_from_text_lines(text, app_type, page_num, source_label)
                if page_rows:
                    strategy_used.append(f"p{page_num}:text_lines")
            # D: positional word reconstruction
            if not page_rows:
                page_rows += _rows_from_words(page, app_type, page_num, source_label)
                if page_rows:
                    strategy_used.append(f"p{page_num}:word_cluster")

            try:
                wc = len(page.extract_words() or [])
            except Exception:
                wc = 0
            try:
                tc = len(page.extract_tables() or [])
            except Exception:
                tc = 0
            page_dumps.append((page_num, text, tc, wc))
            rows.extend(page_rows)

    full_text = "\n".join(full_text_parts)

    # E: document-level never-silent-zero safeguard
    id_only = False
    if not rows:
        salvage = _emit_rows_from_ids(full_text, app_type, source_label)
        if salvage:
            rows = salvage
            id_only = True
            strategy_used.append("doc:id_only_salvage")

    # Dedupe by app_no within the PDF (keep id-less address rows too)
    seen = set()
    out = []
    for r in rows:
        key = r.get("app_no") or ""
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        if r.get("app_no") or r.get("address"):
            out.append(r)

    debug_info = {
        "strategy_used": ",".join(strategy_used) or "none",
        "id_only_fallback": id_only,
        "ids_in_text": sorted(set(APP_NO_RE.findall(full_text))),
        "rows_extracted": len(out),
        "debug_path": "",
    }

    # Write a debug artifact whenever extraction is empty (or only salvaged ids)
    if (not out or id_only) and debug_dir:
        reason = ("zero rows extracted by all strategies"
                  if not out else "structured parse failed; emitted id-only salvage rows")
        debug_info["debug_path"] = _write_parse_debug(debug_dir, source_label, page_dumps, reason)

    return out, debug_info


def _parse_table_row(cells, app_type):
    """Parse one table row (list of cell strings) into a structured dict."""
    # Heuristic: first cell often has the app number
    app_no = ""
    address = ""
    applicant = ""
    scope = ""
    stage = ""

    for cell in cells:
        cell = cell.strip()
        if not cell:
            continue
        # Check for app number pattern
        m = APP_NO_RE.search(cell)
        if m and not app_no:
            app_no = m.group(1)
        # Check for address
        am = ADDR_RE.search(cell)
        if am and not address:
            address = am.group(1).strip()
        # Applicant in subsequent cells
        if not applicant and len(cell) > 3 and not APP_NO_RE.match(cell):
            # Cells containing no app number and reasonable length = likely applicant or scope
            if not address and not app_no:
                continue
            if applicant == "" and len(cell) > 5:
                applicant = cell

    # Scope: collect any remaining cells
    scope_parts = []
    for i, cell in enumerate(cells):
        cell = cell.strip()
        if cell and cell != app_no and cell != address and cell != applicant:
            if any(kw in cell.lower() for kw in CIVIL_KEYWORDS):
                scope_parts.append(cell)
    scope = "; ".join(scope_parts[:3]) or app_type

    # Fragmented text-strategy tables split a single address across several
    # narrow cells, so also scan the joined row text as a fallback.
    joined = " ".join(c.strip() for c in cells if c and c.strip())
    if not app_no:
        m = APP_NO_RE.search(joined)
        if m:
            app_no = m.group(1)
    if not address:
        addr_text = joined.replace(app_no, " ") if app_no else joined
        am = ADDR_RE.search(addr_text)
        if am:
            address = am.group(1).strip()
    if not scope_parts:
        kw_hits = [kw for kw in CIVIL_KEYWORDS if kw in joined.lower()]
        if kw_hits:
            scope = "; ".join(kw_hits[:3])

    return {
        "app_no": app_no,
        "address": address,
        "applicant": applicant,
        "scope": scope,
        "stage": stage or app_type,
    }


def _parse_text_block(text, app_type, page_num):
    """Fallback text parser: extract app numbers and surrounding context."""
    rows = []
    lines = text.split("\n")
    for i, line in enumerate(lines):
        m = APP_NO_RE.search(line)
        if not m:
            continue
        app_no = m.group(1)
        # Collect context: this line + next 2
        context = " ".join(lines[i:i+3])
        # Extract address
        am = ADDR_RE.search(context)
        address = am.group(1).strip() if am else ""
        # Extract applicant
        apm = APPLICANT_RE.search(context)
        applicant = apm.group(1).strip() if apm else ""
        # Extract scope keywords
        scope_parts = [kw for kw in CIVIL_KEYWORDS if kw in context.lower()]
        scope = "; ".join(scope_parts[:3]) or app_type

        rows.append({
            "app_no": app_no,
            "address": address,
            "applicant": applicant,
            "scope": scope,
            "stage": app_type,
        })

    return rows


# ---------------------------------------------------------------------------
# Normalization to TENDER_FINDER lead format
# ---------------------------------------------------------------------------
def _normalize_surrey_lead(raw_row, source_url, source_label, app_type, run_id):
    """Normalize one Surrey in-process row to TENDER_FINDER Future_Projects schema."""
    app_no = raw_row.get("app_no") or ""
    address = raw_row.get("address") or ""
    applicant = raw_row.get("applicant") or "Not available"
    scope = raw_row.get("scope") or app_type
    stage = raw_row.get("stage") or app_type

    # Build project ID
    muni_tag = "SURREY"
    if app_no:
        pid = f"{muni_tag}-{app_no.replace(' ', '').replace('/', '-')}"
    elif address:
        pid = f"{muni_tag}-{re.sub(r'[^A-Z0-9]', '-', address.upper()[:20])}"
    else:
        pid = f"{muni_tag}-UNKNOWN-{hashlib.md5((scope[:20]).encode()).hexdigest()[:6]}"

    # Fit scoring
    blob = f"{app_type} {scope} {address} {stage} Surrey"
    fit_score = G.score_civil_fit(blob, "Surrey") if G else _simple_fit_score(blob)

    # Fit reason
    fit_reason_parts = []
    for kw in CIVIL_KEYWORDS:
        if kw in blob.lower():
            fit_reason_parts.append(kw)
    fit_reason = "civil_signals:" + ",".join(fit_reason_parts[:4]) if fit_reason_parts else app_type

    # Determine route
    if not app_no and not address:
        proposed_route = "Run_Queue"
        hold_reason = "incomplete_record_no_appno_or_address"
        write_eligible = False
    elif fit_score < 40:
        proposed_route = "Run_Queue"
        hold_reason = f"fit_score_below_40:{fit_score}"
        write_eligible = False
    else:
        proposed_route = "Future_Projects"
        hold_reason = ""
        write_eligible = True

    # Raw hash for dedupe
    raw_hash = hashlib.md5(f"{pid}{source_url}".encode()).hexdigest()[:12]
    dedupe_key = f"surrey-{(G.norm_appno(app_no) if G else app_no.replace('-', ''))}"

    return {
        "project_id": pid,
        "source_id": "surrey_planning_reports",
        "source_name": "City of Surrey - Planning Reports / In-Process",
        "municipality": "Surrey",
        "app_no": app_no,
        "address": address,
        "owner": applicant,
        "owner_applicant": applicant,
        "app_type_stage": f"{app_type} — {stage}",
        "scope_summary": scope[:300],
        "fit_score": fit_score,
        "fit_reason": fit_reason,
        "proposed_route": proposed_route,
        "write_eligible": write_eligible,
        "hold_reason": hold_reason,
        "source_url": source_url,
        "evidence_url": source_url,
        "date_found": dt.date.today().isoformat(),
        "run_id": run_id,
        "raw_hash": raw_hash,
        "dedupe_key": dedupe_key,
        # Fields required by tenderfinder_raw_sweep.py normalize_lead schema
        "date_found": dt.date.today().isoformat(),
        "source": "City of Surrey - Planning Reports / In-Process",
        "title": f"Surrey {app_type}: {app_no or address or pid}",
        "verification": "Needs Review",
        "horizon": "",
        "est_value": "Not available",
        "next_milestone": stage,
        "assigned_to": "",
        "notes": f"Auto-extracted from {source_label} PDF. Verify app details at surrey.ca.",
        "_raw": raw_row,
    }


def _simple_fit_score(blob):
    """Minimal fit score if tenderfinder_guards not available."""
    score = 35
    for kw in CIVIL_KEYWORDS:
        if kw in blob.lower():
            score += 8
    return min(100, score)


# ---------------------------------------------------------------------------
# Main connector entry point
# ---------------------------------------------------------------------------
def run_surrey_connector(conn, max_records, probe=False, result_template=None, debug_dir=None):
    """Entry point called by tenderfinder_raw_sweep.py run_connector() for fetch_type=surrey_planning_reports."""
    cid = conn.get("source_id") or "surrey_planning_reports"
    run_id = f"RUN-{dt.date.today().isoformat()}"
    if debug_dir is None:
        debug_dir = os.environ.get("TENDER_FINDER_SURREY_DEBUG_DIR") or os.getcwd()

    res = result_template or {
        "source_id": cid,
        "source_name": conn.get("name") or "City of Surrey - Planning Reports / In-Process",
        "fetch_type": "surrey_planning_reports",
        "tier": conn.get("priority_tier") or "1",
        "municipality": "Surrey",
        "access_status": conn.get("access_status") or "public",
        "resolved": [], "resolved_endpoint": "", "raw_records": [],
        "raw_json_path": "", "records_pulled": 0, "classification": None,
        "output_route": None, "status": "", "richness": "", "error": "",
        "next_action": "", "leads": [], "rejected": [],
    }

    if probe:
        res["resolved_endpoint"] = SURREY_SOURCES[0]["url"]
        res["resolved"] = [f"{s['label']} -> {s['url']}" for s in SURREY_SOURCES]
        res["status"] = "resolved_ok"
        res["next_action"] = "ready for --tier load"
        return res

    all_leads = []
    errors = []
    debug_artifacts = []
    strategies = []

    for source in SURREY_SOURCES:
        label = source["label"]
        url = source["url"]
        app_type = source["app_type"]

        print(f"    [surrey] fetching {label} from {url}")

        try:
            pdf_bytes = _http_get_bytes(url, timeout=45)
            if len(pdf_bytes) < 1000:
                errors.append(f"{label}: response too short ({len(pdf_bytes)} bytes) - likely blocked or redirected")
                continue

            print(f"    [surrey] {label}: downloaded {len(pdf_bytes):,} bytes")
            raw_rows, dbg = _extract_pdf_rows(pdf_bytes, label, app_type, debug_dir=debug_dir)
            strategies.append(f"{label}:{dbg.get('strategy_used')}")
            if dbg.get("debug_path"):
                debug_artifacts.append(dbg["debug_path"])
            id_note = " (id-only salvage)" if dbg.get("id_only_fallback") else ""
            print(f"    [surrey] {label}: extracted {len(raw_rows)} application rows"
                  f" via {dbg.get('strategy_used')}{id_note}")
            if not raw_rows and dbg.get("ids_in_text"):
                # Should not happen now (salvage covers it), but log loudly if it does.
                print(f"    [surrey] WARNING {label}: {len(dbg['ids_in_text'])} ids seen in text "
                      f"but 0 rows built; see debug artifact")

            for row in raw_rows[:max_records]:
                lead = _normalize_surrey_lead(row, url, label, app_type, run_id)
                all_leads.append(lead)

        except Exception as e:
            errors.append(f"{label}: {type(e).__name__}: {e}")
            print(f"    [surrey] ERROR {label}: {e}")
            continue

        time.sleep(0.5)  # polite delay between PDF fetches

    # Filter to respectable records (app_no or address must exist)
    valid_leads = [l for l in all_leads if l.get("app_no") or l.get("address")]
    rejected_leads = [l for l in all_leads if not l.get("app_no") and not l.get("address")]

    # Dedupe within this run
    seen_app_nos = set()
    deduped = []
    dupes_skipped = 0
    for lead in valid_leads:
        key = lead.get("app_no") or ""
        if key and key in seen_app_nos:
            dupes_skipped += 1
            continue
        if key:
            seen_app_nos.add(key)
        deduped.append(lead)

    # Set classification
    if deduped:
        res["leads"] = deduped
        res["classification"] = "dev_application_lead"
        res["output_route"] = "Future_Projects"
        res["status"] = "loaded"
        res["next_action"] = "review in Future_Projects; verify app details at surrey.ca"
    elif errors:
        res["error"] = " | ".join(errors)
        res["status"] = "fetch_failed"
        res["classification"] = "manual_review_needed"
        res["output_route"] = "Run_Queue"
        res["next_action"] = "verify Surrey PDF URLs are accessible from your network"
    else:
        res["status"] = "no_records_extracted"
        res["classification"] = "manual_review_needed"
        res["output_route"] = "Run_Queue"
        if debug_artifacts:
            res["next_action"] = ("0 rows after multi-strategy parse; inspect debug artifact(s): "
                                  + "; ".join(debug_artifacts))
        else:
            res["next_action"] = "verify PDF structure matches parser expectations"

    res["records_pulled"] = len(all_leads)
    res["records_normalized"] = len(deduped)
    res["_dupes_skipped"] = dupes_skipped
    res["_parse_strategies"] = "; ".join(strategies)
    res["_debug_artifacts"] = debug_artifacts
    res["resolved"] = [f"{s['label']} -> {s['url']}" for s in SURREY_SOURCES]
    res["resolved_endpoint"] = SURREY_SOURCES[0]["url"]
    res["richness"] = (f"surrey_pdf_extraction ({len(deduped)} valid records, "
                       f"{len(errors)} errors; strategies: {'; '.join(strategies) or 'none'})")

    if rejected_leads:
        res["rejected"] = [{
            "project_id": l.get("project_id"),
            "source": l.get("source"),
            "source_url": l.get("source_url"),
            "title": "Incomplete Surrey record",
            "municipality": "Surrey",
            "scope_summary": l.get("scope_summary") or "",
            "reason": "no_appno_or_address",
            "verification": "Rejected",
            "notes": "Record extracted from PDF but missing application number and address.",
        } for l in rejected_leads[:20]]

    if errors:
        res["error"] = " | ".join(errors)
        print(f"    [surrey] completed with {len(deduped)} leads, {dupes_skipped} dupes, {len(errors)} errors")
    else:
        print(f"    [surrey] completed with {len(deduped)} leads, {dupes_skipped} dupes skipped")

    return res


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Surrey Planning Reports Connector - Standalone Test")
    print("="*60)
    print("Testing PDF fetch from Surrey public sources...")

    result = run_surrey_connector(
        conn={
            "source_id": "surrey_planning_reports",
            "name": "City of Surrey - Planning Reports / In-Process",
            "priority_tier": "1",
            "access_status": "public",
        },
        max_records=500,
        probe=False,
    )

    print(f"\nResult:")
    print(f"  Status:      {result['status']}")
    print(f"  Records:     {result['records_pulled']} pulled, {result['records_normalized']} normalized")
    print(f"  Leads:       {len(result['leads'])}")
    print(f"  Rejected:    {len(result['rejected'])}")
    print(f"  Errors:      {result.get('error') or 'none'}")

    if result["leads"]:
        print(f"\nSample leads (first 5):")
        for lead in result["leads"][:5]:
            print(f"  - {lead['project_id']}: {lead['app_no']} | {lead['address']} | "
                  f"fit={lead['fit_score']} | route={lead['proposed_route']}")

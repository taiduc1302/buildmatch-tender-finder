#!/usr/bin/env python3
"""
Example Civil Contractor – Tender Finder: Source Register Live URL Auditor
==================================================================
Version : 2.1.0  (error-handling & failure-diagnostics pass)
Author  : Example Civil Contractor / Tender Finder Project
Purpose : Check every URL in the TENDER_FINDER Source Register before adding sources
          into the main tender-finding automation.  Goes well beyond a simple
          HTTP-200 check: handles procurement portals, login gates, RSS feeds,
          PDFs, platform connectors (bidsandtenders, Bonfire, MERX, BC Bid),
          redirect chains, SSL errors, DNS failures, and – when a URL is
          broken – searches for the correct replacement.

CLI example
-----------
python tenderfinder_live_link_checker.py \\
    --input  TENDER_FINDER_Source_Register_PreScript_Audit.xlsx \\
    --output-dir ./link_audit_output \\
    --search-provider bing \\
    --timeout 20 \\
    --retries 2 \\
    --rate-limit 1.0

Dry-run (shows what would be checked, no HTTP requests):
    python tenderfinder_live_link_checker.py --input ... --dry-run

Audit-only (skip replacement search):
    python tenderfinder_live_link_checker.py --input ... --no-search
"""

# --- Standard library ----------------------------------------------------------
import argparse
import csv
import json
import logging
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs


# --- Patch 5.3 (P0.3): Windows-safe console -------------------------------------
def _init_windows_safe_console() -> None:
    """Reconfigure stdout/stderr to UTF-8 with errors='replace' so the link
    preflight never crashes with UnicodeEncodeError on a cp1252 Windows console.
    Must run before the logging StreamHandler binds to sys.stdout."""
    for _name in ("stdout", "stderr"):
        _stream = getattr(sys, _name, None)
        if _stream is None:
            continue
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            try:
                import io as _io
                setattr(sys, _name, _io.TextIOWrapper(
                    _stream.buffer, encoding="utf-8", errors="replace", line_buffering=True))
            except Exception:
                pass


_init_windows_safe_console()

# --- Third-party ---------------------------------------------------------------
try:
    import pandas as pd
    import openpyxl
    import requests

    from requests.adapters import HTTPAdapter
    from requests.exceptions import (
        ConnectionError as RequestsConnectionError,
        ConnectTimeout,
        ReadTimeout,
        SSLError,
        TooManyRedirects,
    )
    from urllib3.util.retry import Retry
    from urllib3.exceptions import InsecureRequestWarning
    import urllib3
    urllib3.disable_warnings(InsecureRequestWarning)
except ImportError as _e:
    sys.exit(
        f"Missing dependency: {_e}\n"
        "Run: pip install requests pandas openpyxl urllib3"
    )

from tenderfinder_url_safety import (
    URLSafetyError,
    safe_requests_request,
    validate_public_url_syntax,
)
from tenderfinder_excel_safety import safe_untrusted_excel_value


# Local secret/env loader.
# Loads non-committed local env files without adding a python-dotenv dependency.
# Existing process env vars always win.
def _load_local_env_files() -> None:
    candidates = []
    try:
        here = Path(__file__).resolve().parent
        candidates.extend([
            here / ".env.tenderfinder.local",
            here / ".env.local",
            here / ".env",
            Path.cwd() / ".env.tenderfinder.local",
            Path.cwd() / ".env.local",
            Path.cwd() / ".env",
        ])
    except Exception:
        return

    for env_path in candidates:
        if not env_path.exists() or not env_path.is_file():
            continue
        try:
            for raw_line in env_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
        except Exception:
            # Do not fail the checker just because an optional local env file is unreadable.
            continue


_load_local_env_files()

# ==============================================================================
# 1.  CONSTANTS & CONFIGURATION
# ==============================================================================

VERSION = "2.1.0"
SCRIPT_NAME = "tenderfinder_live_link_checker"
RUN_TS = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# -- CLI exit codes (documented in README) --------------------------------------
EXIT_OK = 0                 # run completed successfully
EXIT_INPUT_ERROR = 1        # input / config error (missing file, columns, no rows)
EXIT_OUTPUT_INVALID = 2     # output validation failed
EXIT_PREFLIGHT_BROKEN = 3   # critical broken URLs found + --preflight-fail-on-broken
EXIT_RUNTIME_ERROR = 4      # unexpected runtime error

# Required columns: at least ONE url column AND a source identifier must exist.
# These are checked against the *normalised* column names.
REQUIRED_URL_COLUMNS = ("official_url", "primary_url", "example_url",
                        "secondary_urls", "example_relevant_page_or_record_url")
# Patch 4 integration note: the TENDER_FINDER master workbook uses "URL / Portal";
# normalize_columns maps that alias into official_url before validation.
REQUIRED_ID_COLUMNS = ("source_id", "source_name")

# url_check_status values considered "critically broken" for --preflight-fail-on-broken
CRITICAL_BROKEN_STATUSES = frozenset({
    "BROKEN_404", "BROKEN_DNS", "BROKEN_SSL", "BROKEN_OTHER", "NO_REPLACEMENT_FOUND",
})

# url_check_status values that are SAFE for a plain HTTP scrape
SAFE_TO_SCRAPE_STATUSES = frozenset({"OK", "OK_REDIRECTED"})

# url_check_status values that always require a human to look before scripting
MANUAL_REVIEW_STATUSES = frozenset({
    "LOGIN_OR_MANUAL", "FORBIDDEN_BUT_LIKELY_VALID", "NEEDS_CONNECTOR_NOT_SIMPLE_SCRAPE",
    "TIMEOUT_RETRY_NEEDED", "BROKEN_404", "BROKEN_DNS", "BROKEN_SSL", "BROKEN_OTHER",
    "REPLACEMENT_FOUND_HIGH_CONFIDENCE", "REPLACEMENT_FOUND_LOW_CONFIDENCE",
    "NO_REPLACEMENT_FOUND", "REVIEW_REQUIRED",
})

# Browser-like User-Agent pool (rotated by thread index)
BROWSER_HEADERS_POOL = [
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-CA,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
    },
    {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/17.3 Safari/605.1.15"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-CA,en;q=0.9",
        "Connection": "keep-alive",
    },
    {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) "
            "Gecko/20100101 Firefox/124.0"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-CA,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    },
]

# URL parameter keys to strip (tracking / analytics)
TRACKING_PARAMS = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "utm_reader", "fbclid", "gclid", "msclkid", "ref",
    "_ga", "_gl", "mc_cid", "mc_eid", "yclid", "zanpid", "dclid",
})

# Procurement / tender keywords (used for scoring and query-building)
PROCUREMENT_KEYWORDS = {
    "tender", "tenders", "rfp", "rfps", "rfq", "rfqs", "rfi", "rfis",
    "rft", "bid", "bids", "procurement", "purchasing", "purchase",
    "contract", "contracts", "opportunity", "opportunities",
    "solicitation", "solicitations", "sourcing", "award", "awards",
    "capital-project", "capital-projects", "capital_project",
    "infrastructure", "development-application", "development-applications",
    "rezoning", "subdivision", "construction", "contractors",
    "suppliers", "vendor", "vendors", "prequalification", "prequalify",
    "shortlist", "proponent",
}

# Domains that map to a specific named platform
PLATFORM_DOMAIN_MAP = {
    "bidsandtenders.ca":    "bidsandtenders",
    "bonfirehub.ca":        "bonfire",
    "merx.com":             "merx",
    "bcbid.gov.bc.ca":      "bcbid",
    "ariba.com":            "ariba",
    "jaggaer.com":          "jaggaer",
    "ionwave.net":          "ionwave",
    "publicsectornetwork.com": "psn",
}

# Platforms that always need a connector (not plain HTTP scraping)
CONNECTOR_PLATFORMS = frozenset({
    "bidsandtenders", "bonfire", "merx", "bcbid",
    "ariba", "jaggaer", "ionwave",
})

# Paths / query strings that indicate a login / auth page
LOGIN_SIGNALS = frozenset({
    "login", "signin", "sign-in", "/auth/", "authenticate",
    "/register", "/registration", "/account", "/myaccount",
    "prequalification", "prequal", "prequalify",
})

# Fetch types that indicate a manual-only workflow
MANUAL_FETCH_TYPES = frozenset({
    "manual_p3", "paid_login_stub", "email_forwarded", "login_required",
    "manual_review", "paid_intelligence", "manual",
})

# Social / commercial domains to reject as replacement candidates
SPAM_DOMAINS = frozenset({
    "pinterest", "instagram", "facebook.com", "twitter.com", "x.com",
    "linkedin.com", "youtube.com", "reddit.com", "amazon.com",
    "ebay.com", "kijiji", "craiglist", "yelp.com",
})

# ==============================================================================
# 2.  LOGGING
# ==============================================================================

def setup_logging(debug_log_path: Path, verbose: bool = False,
                  quiet: bool = False) -> logging.Logger:
    """
    Configure logging with a clean separation of concerns:

      • DEBUG LOG FILE (TENDER_FINDER_Link_Check_Debug_Log.txt)
            Always receives the *full* DEBUG-level trace: every request, retry,
            error stack reason, and classification decision. This is the noisy
            diagnostic file.

      • CONSOLE
            Receives INFO by default (or DEBUG when --verbose, or WARNING+ when
            --quiet). Kept readable so the operator is not drowned in trace spam.

    The human-readable *summary* (TENDER_FINDER_Link_Check_Run_Log.txt) is written
    separately by write_run_log() and never contains debug spam.
    """
    logger = logging.getLogger(SCRIPT_NAME)
    logger.setLevel(logging.DEBUG)            # capture everything; handlers filter
    logger.handlers.clear()                   # avoid duplicate handlers on re-run

    file_fmt = logging.Formatter(
        "%(asctime)s [%(levelname)-7s] %(threadName)-10s %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )
    console_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                                    "%H:%M:%S")

    # Full debug trace → file (always DEBUG)
    fh = logging.FileHandler(debug_log_path, encoding="utf-8", mode="w")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(file_fmt)
    logger.addHandler(fh)

    # Console handler
    if quiet:
        console_level = logging.WARNING
    elif verbose:
        console_level = logging.DEBUG
    else:
        console_level = logging.INFO
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(console_level)
    ch.setFormatter(console_fmt)
    logger.addHandler(ch)

    logger.propagate = False
    return logger


log = logging.getLogger(SCRIPT_NAME)  # module-level shorthand

# ==============================================================================
# 3.  URL UTILITIES
# ==============================================================================

_EMPTY_VALUES = frozenset({"", "nan", "none", "#", "n/a", "n/a.", "tbd", "-", "–", "na"})


def is_empty_url(value: Any) -> bool:
    """Return True if the value is effectively an empty / missing URL."""
    return str(value).strip().lower() in _EMPTY_VALUES


def normalize_url(raw: Any) -> str:
    """
    Normalise a URL string:
    • strip whitespace
    • prepend https:// if schema is missing
    • remove tracking parameters
    • remove URL fragment
    • preserve meaningful portal / filter query parameters
    Returns empty string if the input is unusable.
    """
    if is_empty_url(raw):
        return ""

    url = str(raw).strip()

    # Fix common copy-paste artefacts
    url = url.replace("\u200b", "").replace("\xa0", " ").strip()

    # Schema repair
    if url.startswith("//"):
        url = "https:" + url
    elif not re.match(r"^https?://", url, re.I):
        if re.match(r"^(www\.|[a-z0-9-]+\.[a-z]{2,})", url, re.I):
            url = "https://" + url

    try:
        parsed = urlparse(url)

        # Strip tracking params but keep the rest
        if parsed.query:
            params = parse_qs(parsed.query, keep_blank_values=True)
            cleaned = {
                k: v for k, v in params.items()
                if k.lower() not in TRACKING_PARAMS
            }
            new_query = urlencode(cleaned, doseq=True)
            parsed = parsed._replace(query=new_query)

        # Strip fragment
        parsed = parsed._replace(fragment="")

        result = urlunparse(parsed)
        # Ensure trailing slash for bare domains
        if parsed.path == "":
            parsed = parsed._replace(path="/")
            result = urlunparse(parsed)

        return result
    except Exception:
        return url


def extract_urls_from_row(row: Dict) -> List[Dict]:
    """
    Return a list of {url_role, original_url, normalized_url} dicts
    from a source register row, handling semicolon-separated secondary URLs.
    """
    entries = []
    seen: set = set()

    def _add(role: str, raw: str) -> None:
        raw = str(raw).strip()
        if is_empty_url(raw):
            return
        norm = normalize_url(raw)
        if not norm or norm in seen:
            return
        seen.add(norm)
        entries.append({"url_role": role, "original_url": raw, "normalized_url": norm})

    # Primary URL field (may be called official_url or primary_url)
    for key in ("official_url", "primary_url"):
        val = row.get(key, "")
        if not is_empty_url(val):
            _add("primary_url", val)
            break  # only take the first populated one

    # Secondary / example URL field (may contain semicolon-separated list)
    for key in ("example_url", "secondary_urls", "example_relevant_page_or_record_url"):
        val = str(row.get(key, "")).strip()
        if is_empty_url(val):
            continue
        # Split on semicolons
        parts = [p.strip() for p in val.split(";") if p.strip()]
        for idx, part in enumerate(parts):
            role = "example_url" if idx == 0 else f"secondary_url_{idx}"
            _add(role, part)

    return entries


# ==============================================================================
# 4.  PLATFORM / CONNECTOR DETECTION
# ==============================================================================

def detect_platform(
    url: str,
    source_type: str = "",
    fetch_type: str = "",
    access_status: str = "",
    connector_type_hint: str = "",
) -> str:
    """
    Determine what kind of platform/connector this URL needs.
    Returns a short identifier string:
      bidsandtenders | bonfire | merx | bcbid | ariba | jaggaer |
      rss | pdf | manual | login_portal | html_listing
    """
    # If a previous audit already set connector_type, trust it
    hint = connector_type_hint.lower()
    if "bidsandtenders" in hint:
        return "bidsandtenders"
    if "bonfire" in hint:
        return "bonfire"
    if "merx" in hint:
        return "merx"
    if "bc_bid" in hint or "bcbid" in hint:
        return "bcbid"
    if "rss" in hint:
        return "rss"
    if "pdf" in hint:
        return "pdf"
    if "manual" in hint:
        return "manual"

    url_lower = url.lower()

    try:
        parsed = urlparse(url_lower)
        host = parsed.netloc.lstrip("www.")
        path = parsed.path
    except Exception:
        host, path = "", ""

    # Named platform domains
    for domain, platform in PLATFORM_DOMAIN_MAP.items():
        if host.endswith(domain) or host == domain:
            return platform

    # RSS / feed detection
    if any(x in url_lower for x in (".rss", ".xml", "/feed", "/rss", "/atom", "feed=")):
        return "rss"
    if "rss" in source_type.lower():
        return "rss"

    # PDF detection
    if path.lower().endswith(".pdf") or "/pdf/" in path.lower():
        return "pdf"

    # Manual workflow detection
    fetch_lower = fetch_type.lower()
    if fetch_lower in MANUAL_FETCH_TYPES or any(kw in fetch_lower for kw in MANUAL_FETCH_TYPES):
        return "manual"
    access_lower = access_status.lower()
    if any(x in access_lower for x in ("login", "paid", "manual", "register", "prequalif")):
        return "manual"

    # Login page detection by path
    if any(sig in path.lower() for sig in LOGIN_SIGNALS):
        return "login_portal"

    return "html_listing"


def is_connector_required(platform: str) -> bool:
    return platform in CONNECTOR_PLATFORMS


def is_manual_only(platform: str, fetch_type: str = "", access_status: str = "") -> bool:
    if platform in ("manual", "login_portal"):
        return True
    if fetch_type.lower() in MANUAL_FETCH_TYPES:
        return True
    return False


# ==============================================================================
# 5.  HTTP CHECKING
# ==============================================================================

def _make_session(verify_ssl: bool = True) -> requests.Session:
    session = requests.Session()
    retry_strategy = Retry(
        total=0,       # We handle retries manually for full control
        backoff_factor=0.5,
        status_forcelist=[429, 503, 504],
        allowed_methods=["HEAD", "GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    # Certificate verification is mandatory.  The compatibility parameter is
    # retained for old callers but can no longer disable TLS verification.
    session.verify = True
    return session


def check_url(
    url: str,
    timeout: int = 20,
    retries: int = 2,
    headers_idx: int = 0,
    verify_ssl: bool = True,
    _retry_no_ssl: bool = False,
) -> Dict:
    """
    Check a single URL: HEAD first, fallback to GET.
    Follows redirects, records the full chain.

    Returns a dict with:
      http_status_code, final_url_after_redirect, redirect_chain,
      content_type, response_time_seconds, error_type, error_message,
      method_used, ssl_verified
    """
    result: Dict[str, Any] = {
        "http_status_code": None,
        "final_url_after_redirect": url,
        "redirect_chain": [],
        "content_type": "",
        "response_time_seconds": 0.0,
        "error_type": "",
        "error_message": "",
        "method_used": "",
        "ssl_verified": True,
        "retry_count": 0,          # number of *extra* attempts made beyond the first
    }

    # -- Guard: syntactically invalid / unparseable URL ----------------------
    # Never let a bad string reach requests and raise an opaque error.
    try:
        validate_public_url_syntax(url)
    except URLSafetyError as exc:
        result["error_type"] = "UNSAFE_URL"
        result["error_message"] = str(exc)[:350]
        return result

    headers = BROWSER_HEADERS_POOL[headers_idx % len(BROWSER_HEADERS_POOL)]
    url_lower = url.lower()

    # Choose method order based on URL characteristics
    # PDFs and feeds are better with GET; normal pages: HEAD first
    skip_head = (
        url_lower.endswith(".pdf")
        or url_lower.endswith(".rss")
        or url_lower.endswith(".xml")
        or "/feed" in url_lower
        or "rss" in url_lower.split("?")[0]
    )
    method_order = ["GET"] if skip_head else ["HEAD", "GET"]

    for attempt in range(retries + 1):
        result["retry_count"] = attempt        # 0 on first try, 1, 2, ...
        if attempt > 0:
            backoff = min(30, 2 ** attempt)
            log.debug(f"Retry {attempt}/{retries} for {url} — waiting {backoff}s")
            time.sleep(backoff)

        t0 = time.time()
        session = _make_session(verify_ssl=verify_ssl)

        for method in method_order:
            try:
                fetched = safe_requests_request(
                    method,
                    url,
                    request_callable=session.request,
                    headers=headers,
                    timeout=(min(timeout // 2, 10), timeout),  # (connect, read)
                    stream=(method == "GET"),
                )
                resp = fetched.response
                elapsed = round(time.time() - t0, 3)

                result["response_time_seconds"] = elapsed
                result["http_status_code"] = resp.status_code
                result["final_url_after_redirect"] = fetched.final_url
                result["redirect_chain"] = list(fetched.redirect_chain[:-1])
                result["content_type"] = resp.headers.get("Content-Type", "")
                result["method_used"] = method

                # HEAD returned 405/501/400 → the server doesn't support HEAD; fall through to GET
                if method == "HEAD" and resp.status_code in (400, 405, 501):
                    log.debug(f"HEAD returned {resp.status_code} for {url}; falling back to GET")
                    continue

                if method == "GET":
                    # Read a small chunk to confirm the connection but don't download everything
                    try:
                        resp.content  # for non-streamed or read first 1KB
                    except Exception:
                        pass

                return result

            except SSLError as exc:
                result["response_time_seconds"] = round(time.time() - t0, 3)
                result["error_type"] = "BROKEN_SSL"
                result["error_message"] = str(exc)[:350]
                return result

            except URLSafetyError as exc:
                result["response_time_seconds"] = round(time.time() - t0, 3)
                result["error_type"] = "UNSAFE_URL"
                result["error_message"] = str(exc)[:350]
                return result

            except (ConnectTimeout, ReadTimeout) as exc:
                result["response_time_seconds"] = round(time.time() - t0, 3)
                result["error_type"] = "TIMEOUT"
                result["error_message"] = str(exc)[:350]
                if attempt < retries:
                    break   # outer retry loop
                return result

            except RequestsConnectionError as exc:
                result["response_time_seconds"] = round(time.time() - t0, 3)
                err_str = str(exc)
                dns_signals = (
                    "Name or service not known",
                    "getaddrinfo failed",
                    "nodename nor servname",
                    "Temporary failure in name resolution",
                    "No address associated",
                    "Failed to resolve",
                )
                refused_signals = (
                    "Connection refused",
                    "ConnectionRefusedError",
                    "Errno 111",
                    "actively refused",
                    "No route to host",
                )
                if any(sig in err_str for sig in dns_signals):
                    result["error_type"] = "DNS_ERROR"
                elif any(sig in err_str for sig in refused_signals):
                    result["error_type"] = "CONNECTION_REFUSED"
                else:
                    result["error_type"] = "CONNECTION_ERROR"
                result["error_message"] = err_str[:350]
                if attempt < retries:
                    break
                return result

            except TooManyRedirects as exc:
                result["response_time_seconds"] = round(time.time() - t0, 3)
                result["error_type"] = "TOO_MANY_REDIRECTS"
                result["error_message"] = str(exc)[:350]
                return result

            except Exception as exc:
                result["response_time_seconds"] = round(time.time() - t0, 3)
                result["error_type"] = "UNKNOWN_ERROR"
                result["error_message"] = f"{type(exc).__name__}: {str(exc)[:300]}"
                if attempt < retries:
                    break
                return result

    return result


# ==============================================================================
# 6.  URL STATUS CLASSIFICATION
# ==============================================================================

def _is_likely_valid_403(url: str, row: Dict) -> bool:
    """
    Return True when a 403/429 is probably bot-blocking from a live procurement
    portal, rather than a genuinely removed or forbidden page.

    Key insight: from a data-centre IP almost every WAF-protected procurement
    portal returns 403. A clean 403 response means the server IS reachable and
    is actively rejecting the bot — the page almost certainly exists.
    """
    url_lower = url.lower()
    parsed = urlparse(url_lower)
    host = parsed.netloc.lstrip("www.")
    path_lower = parsed.path.lower()
    host_path = host + path_lower

    # 1. Named platform domains — always valid even when blocking bots
    for domain in PLATFORM_DOMAIN_MAP:
        if host.endswith(domain) or host == domain:
            return True

    # 2. Procurement / supplier keywords in path or host
    if any(kw in host_path for kw in PROCUREMENT_KEYWORDS):
        return True

    # 3. Government / authority TLD patterns
    gov_patterns = [
        r"\.(gov|govt|government|municipal|authority)(\.|$)",
        r"\.(city|district|county|region|metro)(\.|$)",
        r"\.gc\.ca", r"\.gov\.bc\.ca",
        r"\.(hydro|transit|airport|port|board)\.",
    ]
    for pat in gov_patterns:
        if re.search(pat, host):
            return True

    # 4. Doing-business / supplier path signals (any TLD)
    # "Doing business" / supplier / project path signals (any TLD)
    # These paths are used by both gov and private developer sites to list
    # projects, news, and contracting opportunities.
    biz_signals = (
        "work-with-us", "doing-business", "business-with",
        "supplier", "suppliers", "vendor", "vendors", "contracting",
        "contractor", "prequalification", "prequalify", "procurement",
        "work-with", "bid-opportunit",
        # Developer / project page patterns common on private org sites
        "project", "projects", "news", "portfolio", "development",
        "developments", "current-work", "our-work", "agenda",
        "council", "minutes", "infrastructure", "capital",
    )
    if any(sig in path_lower for sig in biz_signals):
        return True

    # 5. Recognisable Canadian utilities and institutions in hostname
    ca_org_hints = (
        "hydro", "transit", "translink", "yvr", "bcit", "ubc", "sfu",
        "kwantlen", "langara", "capilano", "fraserhealth", "vch", "phsa",
        "viha", "nhsbc", "bchousing", "portvancouver", "vfpa",
        "musqueam", "squamish", "tsleil", "metro", "commission",
    )
    if any(hint in host for hint in ca_org_hints):
        return True

    return False


def classify_url_status(
    check_result: Dict,
    platform: str,
    row: Dict,
    normalized_url: str,
) -> Tuple[str, str]:
    """
    Map an HTTP check result + platform context to one of the 13 defined
    url_check_status values.

    Returns a tuple of (url_check_status, classification_reason) where the
    reason is a short human-readable explanation of *why* that status was
    chosen — recorded in the output so reviewers don't have to re-derive it.
    """
    error_type = check_result.get("error_type", "")
    status_code = check_result.get("http_status_code")
    final_url = check_result.get("final_url_after_redirect", "")
    content_type = check_result.get("content_type", "").lower()
    redirects = check_result.get("redirect_chain", [])

    # -- Hard input errors (always first) --
    if error_type == "INVALID_URL":
        return "BROKEN_OTHER", "URL is syntactically invalid (no scheme/host)."

    # -- Connector platforms (judged by platform identity, BEFORE network) --
    # A recognised bids&tenders / Bonfire / MERX / BC Bid portal needs a
    # connector regardless of what HTTP status (or transport error) we see from
    # our checking host — a WAF/IP block must never demote it to "broken".
    if is_connector_required(platform):
        return ("NEEDS_CONNECTOR_NOT_SIMPLE_SCRAPE",
                f"Recognised {platform} portal — requires a connector, not plain scraping.")

    # -- Manual / login platforms (also identity-based) --
    if platform in ("manual", "login_portal"):
        return "LOGIN_OR_MANUAL", "Platform flagged as manual/login workflow."

    # -- Network / transport errors --
    if error_type == "DNS_ERROR":
        return "BROKEN_DNS", "DNS resolution failed — host does not resolve."
    if error_type == "BROKEN_SSL":
        return "BROKEN_SSL", "TLS/SSL certificate could not be verified."
    if error_type == "TIMEOUT":
        return "TIMEOUT_RETRY_NEEDED", "Request timed out after retries; server slow or unreachable."
    if error_type == "CONNECTION_REFUSED":
        return "BROKEN_OTHER", "Connection actively refused by host."
    if error_type == "TOO_MANY_REDIRECTS":
        return "BROKEN_OTHER", "Redirect loop / too many redirects."
    if error_type in ("CONNECTION_ERROR", "UNKNOWN_ERROR") and status_code is None:
        return "BROKEN_OTHER", f"Connection error ({error_type}); no HTTP response."

    if status_code is None:
        return "BROKEN_OTHER", "No HTTP status returned."

    # -- Auth gates --
    if status_code == 401:
        return "LOGIN_OR_MANUAL", "HTTP 401 — authentication required (login portal)."

    if status_code in (403, 429):
        label = "429 rate-limited" if status_code == 429 else "403 forbidden"
        if _is_likely_valid_403(normalized_url, row):
            return ("FORBIDDEN_BUT_LIKELY_VALID",
                    f"HTTP {status_code} but host matches a known/valid procurement or "
                    f"gov pattern — almost certainly bot-blocking ({label}), not removed.")
        return "BROKEN_OTHER", f"HTTP {status_code} with no signal the page is valid."

    # -- Redirect to login --
    if redirects or status_code in range(300, 400):
        check_url_str = (final_url + " ".join(redirects)).lower()
        if any(sig in check_url_str for sig in LOGIN_SIGNALS):
            return "LOGIN_OR_MANUAL", "Redirected to a login/auth page."

    # -- Definitive broken --
    if status_code in (404, 410, 451):
        return "BROKEN_404", f"HTTP {status_code} — page not found / gone."

    if status_code >= 500:
        return "BROKEN_OTHER", f"HTTP {status_code} — server error."

    # -- OK cases --
    if 200 <= status_code < 300:
        ctype = f" ({content_type.split(';')[0]})" if content_type else ""
        if redirects:
            return "OK_REDIRECTED", f"HTTP {status_code} after redirect{ctype}."
        return "OK", f"HTTP {status_code}{ctype}."

    if 300 <= status_code < 400:
        return "OK_REDIRECTED", f"HTTP {status_code} permanent redirect."

    return "BROKEN_OTHER", f"Unhandled HTTP status {status_code}."


# ==============================================================================
# 7.  SCRIPT-READINESS AND RECOMMENDED ACTION
# ==============================================================================

def classify_script_ready(
    url_status: str,
    platform: str,
    fetch_type: str = "",
    access_status: str = "",
) -> str:
    """Return one of the five script_ready values."""

    if url_status in ("OK", "OK_REDIRECTED"):
        if is_connector_required(platform):
            return "YES_CONNECTOR_REQUIRED"
        if is_manual_only(platform, fetch_type, access_status):
            return "MANUAL_WORKFLOW_ONLY"
        if platform == "pdf":
            # PDFs are valid evidence but shouldn't be live-feed targets
            return "REVIEW_REQUIRED"
        return "YES_SIMPLE_HTTP"

    if url_status == "NEEDS_CONNECTOR_NOT_SIMPLE_SCRAPE":
        return "YES_CONNECTOR_REQUIRED"

    if url_status == "LOGIN_OR_MANUAL":
        if is_connector_required(platform):
            return "YES_CONNECTOR_REQUIRED"
        return "MANUAL_WORKFLOW_ONLY"

    if url_status == "FORBIDDEN_BUT_LIKELY_VALID":
        if is_connector_required(platform):
            return "YES_CONNECTOR_REQUIRED"
        # 403/429 from a government/procurement site is usually bot-blocking from
        # data-centre IPs — verify from a residential/business IP before scripting.
        return "REVIEW_REQUIRED"

    if url_status in (
        "BROKEN_404", "BROKEN_DNS", "BROKEN_SSL", "BROKEN_OTHER",
        "REPLACEMENT_FOUND_HIGH_CONFIDENCE", "REPLACEMENT_FOUND_LOW_CONFIDENCE",
        "NO_REPLACEMENT_FOUND",
    ):
        return "FIX_URL_FIRST"

    if url_status == "TIMEOUT_RETRY_NEEDED":
        return "REVIEW_REQUIRED"

    return "REVIEW_REQUIRED"


def get_recommended_action(
    url_status: str,
    platform: str,
    replacement_url: str = "",
    confidence: str = "",
) -> str:
    """Generate a human-readable recommended next step."""
    repl = f" → Candidate: {replacement_url}" if replacement_url else ""
    conf = f" ({confidence} confidence)" if confidence else ""

    actions = {
        "OK": (
            f"URL is live. "
            + (f"Use {platform.upper()} connector." if is_connector_required(platform)
               else "Proceed to scripting.")
        ),
        "OK_REDIRECTED": (
            "URL redirects to final destination. "
            "Update registered URL to avoid unnecessary hops."
        ),
        "NEEDS_CONNECTOR_NOT_SIMPLE_SCRAPE": (
            f"Platform connector required for {platform.upper()}. "
            "Do not attempt plain HTML scraping."
        ),
        "LOGIN_OR_MANUAL": (
            "Login or manual workflow required. "
            "Set up account/credentials, track manually or via Run_Queue."
        ),
        "FORBIDDEN_BUT_LIKELY_VALID": (
            "403/429 from a likely-valid portal (bot-blocking). "
            "Verify manually. Connector, auth, or rate-limited approach needed."
        ),
        "TIMEOUT_RETRY_NEEDED": (
            "Timed out. Retry off-peak or increase --timeout. "
            "Server may be slow or temporarily unavailable."
        ),
        "BROKEN_404": f"404 Not Found. Page removed or path changed.{conf}{repl}",
        "BROKEN_DNS": f"DNS failure — domain unreachable or removed.{conf}{repl}",
        "BROKEN_SSL": "SSL certificate error. Try HTTP fallback or verify cert manually.",
        "BROKEN_OTHER": f"Connection error. Verify manually.{conf}{repl}",
        "REPLACEMENT_FOUND_HIGH_CONFIDENCE": f"High-confidence replacement found{conf}.{repl}",
        "REPLACEMENT_FOUND_LOW_CONFIDENCE": f"Low-confidence replacement found{conf}. Verify before use.{repl}",
        "NO_REPLACEMENT_FOUND": "Broken URL — no replacement found automatically. Manual investigation required.",
        "DRY_RUN": "Dry run — no HTTP request made.",
    }
    return actions.get(url_status, "Review required before scripting.")


# Map the raw internal error_type from check_url() onto a stable, documented
# vocabulary for the output `error_type` column.
ERROR_TYPE_OUTPUT_MAP = {
    "":                   "",
    "DNS_ERROR":          "DNS_FAILURE",
    "BROKEN_SSL":         "SSL_CERTIFICATE_ERROR",
    "TIMEOUT":            "TIMEOUT",
    "CONNECTION_REFUSED": "CONNECTION_REFUSED",
    "CONNECTION_ERROR":   "CONNECTION_ERROR",
    "TOO_MANY_REDIRECTS": "TOO_MANY_REDIRECTS",
    "INVALID_URL":        "INVALID_URL_SYNTAX",
    "UNKNOWN_ERROR":      "UNKNOWN_ERROR",
}


def derive_error_type(check_result: Dict, url_status: str) -> str:
    """
    Produce the stable output `error_type` value.

    Distinguishes HTTP-level errors (which have a status code) from
    transport-level errors (which do not).  For HTTP responses we report the
    HTTP-shaped error category so reviewers can filter cleanly.
    """
    raw = check_result.get("error_type", "")
    if raw:
        return ERROR_TYPE_OUTPUT_MAP.get(raw, raw)

    code = check_result.get("http_status_code")
    if code is None:
        return ""
    if code == 401:
        return "HTTP_401_LOGIN_REQUIRED"
    if code == 403:
        return "HTTP_403_FORBIDDEN"
    if code == 429:
        return "HTTP_429_RATE_LIMIT"
    if code in (404, 410, 451):
        return "HTTP_404_NOT_FOUND"
    if 500 <= code < 600:
        return "HTTP_5XX_SERVER_ERROR"
    return ""   # 2xx / 3xx — no error


def derive_safe_to_scrape(url_status: str, platform: str) -> str:
    """Return 'YES' / 'NO' / 'NO_CONNECTOR' for the safe_to_scrape column."""
    if url_status in SAFE_TO_SCRAPE_STATUSES:
        if is_connector_required(platform) or is_manual_only(platform):
            return "NO_CONNECTOR"
        return "YES"
    if url_status == "NEEDS_CONNECTOR_NOT_SIMPLE_SCRAPE":
        return "NO_CONNECTOR"
    return "NO"


def derive_manual_review_required(url_status: str) -> str:
    """Return 'YES' / 'NO' for the manual_review_required column."""
    return "YES" if url_status in MANUAL_REVIEW_STATUSES else "NO"


# ==============================================================================
# 8.  SEARCH PROVIDERS
# ==============================================================================

def _get_api_key(provider: str) -> Tuple[str, str]:
    """Return (api_key, extra_key) for the given provider from env vars."""
    if provider == "bing":
        return os.environ.get("BING_SEARCH_API_KEY", ""), ""
    if provider == "serpapi":
        return os.environ.get("SERPAPI_API_KEY", ""), ""
    if provider == "tavily":
        return os.environ.get("TAVILY_API_KEY", ""), ""
    if provider == "google":
        return os.environ.get("GOOGLE_SEARCH_API_KEY", ""), os.environ.get("GOOGLE_CSE_ID", "")
    return "", ""


def has_search_api_key(provider: str) -> bool:
    key, extra = _get_api_key(provider)
    if provider == "google":
        return bool(key) and bool(extra)
    return bool(key)



class SearchProviderError(RuntimeError):
    """Raised when replacement-search provider fails in a way operators should see."""

    def __init__(self, provider: str, reason: str, message: str = "", status_code: Optional[int] = None):
        self.provider = provider
        self.reason = reason
        self.status_code = status_code
        self.message = message or reason
        status = f" HTTP {status_code}" if status_code is not None else ""
        super().__init__(f"{provider}{status}: {reason}: {self.message}")


def _summarize_provider_body(resp: requests.Response) -> str:
    """Return a short, safe summary of a provider error body."""
    text = ""
    try:
        data = resp.json()
        if isinstance(data, dict):
            for key in ("error", "message", "detail", "details", "description"):
                val = data.get(key)
                if isinstance(val, str) and val.strip():
                    text = val.strip()
                    break
            if not text:
                text = str(data)[:300]
        else:
            text = str(data)[:300]
    except Exception:
        try:
            text = resp.text[:300]
        except Exception:
            text = ""
    return " ".join(text.split())[:300]


def _raise_for_search_response(provider: str, resp: requests.Response) -> None:
    """Raise explicit key/quota/search errors instead of hiding them as empty results."""
    if 200 <= resp.status_code < 300:
        return
    body = _summarize_provider_body(resp)
    body_lower = body.lower()
    status = resp.status_code

    if status in (401, 403):
        reason = "SEARCH_API_KEY_INVALID_OR_FORBIDDEN"
    elif status in (402,):
        reason = "SEARCH_API_PAYMENT_OR_PLAN_REQUIRED"
    elif status == 429:
        # For Tavily and similar providers this usually means quota/rate limit/credits exhausted.
        reason = "SEARCH_API_QUOTA_OR_RATE_LIMIT"
    elif "quota" in body_lower or "credit" in body_lower or "usage" in body_lower or "limit" in body_lower:
        reason = "SEARCH_API_QUOTA_OR_RATE_LIMIT"
    elif 500 <= status < 600:
        reason = "SEARCH_API_PROVIDER_5XX"
    else:
        reason = "SEARCH_API_HTTP_ERROR"
    raise SearchProviderError(provider, reason, body, status_code=status)


def _search_bing(query: str, api_key: str, n: int = 5) -> List[Dict]:
    resp = safe_requests_request(
        "GET",
        "https://api.bing.microsoft.com/v7.0/search",
        request_callable=requests.request,
        headers={"Ocp-Apim-Subscription-Key": api_key},
        params={"q": query, "count": n, "mkt": "en-CA"},
        timeout=15,
    ).response
    _raise_for_search_response("bing", resp)
    items = resp.json().get("webPages", {}).get("value", [])
    return [{"url": i["url"], "title": i.get("name", ""), "snippet": i.get("snippet", "")} for i in items]


def _search_serpapi(query: str, api_key: str, n: int = 5) -> List[Dict]:
    resp = safe_requests_request(
        "GET",
        "https://serpapi.com/search",
        request_callable=requests.request,
        params={"q": query, "api_key": api_key, "num": n, "gl": "ca"},
        timeout=15,
    ).response
    _raise_for_search_response("serpapi", resp)
    items = resp.json().get("organic_results", [])
    return [{"url": i.get("link", ""), "title": i.get("title", ""), "snippet": i.get("snippet", "")} for i in items]


def _search_tavily(query: str, api_key: str, n: int = 5) -> List[Dict]:
    resp = safe_requests_request(
        "POST",
        "https://api.tavily.com/search",
        request_callable=requests.request,
        json={"api_key": api_key, "query": query, "max_results": n},
        timeout=15,
    ).response
    _raise_for_search_response("tavily", resp)
    items = resp.json().get("results", [])
    return [{"url": i.get("url", ""), "title": i.get("title", ""), "snippet": i.get("content", "")} for i in items]


def _search_google(query: str, api_key: str, cse_id: str, n: int = 5) -> List[Dict]:
    resp = safe_requests_request(
        "GET",
        "https://www.googleapis.com/customsearch/v1",
        request_callable=requests.request,
        params={"key": api_key, "cx": cse_id, "q": query, "num": min(n, 10), "gl": "ca"},
        timeout=15,
    ).response
    _raise_for_search_response("google", resp)
    items = resp.json().get("items", [])
    return [{"url": i.get("link", ""), "title": i.get("title", ""), "snippet": i.get("snippet", "")} for i in items]


def do_search(query: str, provider: str, n: int = 5) -> List[Dict]:
    """Route a search query to the configured provider.

    Search provider failures are intentionally not hidden as "no results" because
    operators need to know when the Tavily/Bing/etc. key is missing, invalid,
    exhausted, or rate-limited.
    """
    key, extra = _get_api_key(provider)
    if not key:
        raise SearchProviderError(provider, "SEARCH_SKIPPED_NO_API_KEY", "No API key found in environment/local env file")
    if provider == "google" and not extra:
        raise SearchProviderError(provider, "SEARCH_GOOGLE_CSE_ID_MISSING", "GOOGLE_CSE_ID is required for Google Custom Search")
    try:
        if provider == "bing":
            return _search_bing(query, key, n)
        if provider == "serpapi":
            return _search_serpapi(query, key, n)
        if provider == "tavily":
            return _search_tavily(query, key, n)
        if provider == "google":
            return _search_google(query, key, extra, n)
    except SearchProviderError:
        raise
    except requests.Timeout as exc:
        raise SearchProviderError(provider, "SEARCH_API_TIMEOUT", str(exc)) from exc
    except requests.ConnectionError as exc:
        raise SearchProviderError(provider, "SEARCH_API_CONNECTION_ERROR", str(exc)) from exc
    except ValueError as exc:
        raise SearchProviderError(provider, "SEARCH_API_BAD_JSON_RESPONSE", str(exc)) from exc
    except Exception as exc:
        raise SearchProviderError(provider, "SEARCH_API_UNEXPECTED_ERROR", str(exc)) from exc
    return []


# ==============================================================================
# 9.  REPLACEMENT FINDER
# ==============================================================================

def _first_nonempty(row: Dict, keys: List[str]) -> str:
    """Return the first non-empty string value for any key in the list."""
    for key in keys:
        val = str(row.get(key, "")).strip()
        if val and val.lower() not in _EMPTY_VALUES:
            return val
    return ""


def build_search_query(row: Dict, broken_url: str) -> str:
    """
    Build a targeted web-search query to locate the correct replacement URL.
    Uses organisation name, geography, signal type, and broken-URL domain.
    """
    parts: List[str] = []

    org = _first_nonempty(row, [
        "owner_organization", "owner / organization", "owner/organization",
        "organization", "source_name", "final_source_name",
    ])
    geo = _first_nonempty(row, ["geography_coverage", "geography / coverage", "geography/coverage"])
    signal = _first_nonempty(row, ["likely_signal_type", "signal_type"])
    source_type = _first_nonempty(row, ["source_type"])

    if org:
        parts.append(org)

    # Add geography only if it adds something beyond the org name
    if geo and geo.lower() not in (org or "").lower():
        parts.append(geo)

    # Translate signal types into search-friendly keywords
    signal_lower = signal.lower()
    if any(x in signal_lower for x in ("tender", "rfp", "rfq", "bid", "procurement")):
        parts.append("tenders RFPs procurement bids")
    elif any(x in signal_lower for x in ("development application", "rezoning", "subdivision")):
        parts.append("development applications rezoning current developments")
    elif any(x in signal_lower for x in ("capital project", "infrastructure", "construction")):
        parts.append("capital projects infrastructure construction")
    elif any(x in signal_lower for x in ("supplier", "prequalification", "prequalify")):
        parts.append("suppliers bidding opportunities contractor prequalification")
    elif "rss" in signal_lower:
        parts.append("tenders RSS feed")
    elif signal:
        parts.append(signal)

    # Add domain context from broken URL
    try:
        broken_host = urlparse(broken_url).netloc
        if broken_host and len(broken_host) < 60:
            # Only include domain if it doesn't duplicate org
            if broken_host.replace("www.", "").split(".")[0].lower() not in (org or "").lower():
                parts.append(f"site:{broken_host}")
    except Exception:
        pass

    return " ".join(parts[:6]).strip()


def score_replacement_candidate(
    candidate: Dict,
    row: Dict,
    broken_url: str,
    platform: str,
) -> Tuple[int, str]:
    """
    Score a search result as a potential replacement URL.
    Returns (score 0-100+, reason_string).
    Score >= 80  → HIGH confidence
    Score 60-79  → MEDIUM confidence
    Score 40-59  → LOW confidence
    Score < 40   → reject
    """
    cand_url = candidate.get("url", "")
    if not cand_url:
        return 0, "Empty URL"

    title = candidate.get("title", "").lower()
    snippet = candidate.get("snippet", "").lower()
    cand_lower = cand_url.lower()

    try:
        cand_parsed = urlparse(cand_lower)
        cand_host = cand_parsed.netloc.lstrip("www.")
        cand_path = cand_parsed.path
    except Exception:
        return 0, "Unparseable URL"

    try:
        broken_host = urlparse(broken_url.lower()).netloc.lstrip("www.")
    except Exception:
        broken_host = ""

    org = _first_nonempty(row, [
        "owner_organization", "owner / organization", "source_name", "final_source_name"
    ]).lower()
    geo = _first_nonempty(row, ["geography_coverage", "geography / coverage"]).lower()

    score = 0
    reasons: List[str] = []

    # -- Hard rejects --
    for spam in SPAM_DOMAINS:
        if spam in cand_host:
            return -100, f"Social/commercial domain rejected: {spam}"

    # -- Same domain as broken URL --
    if broken_host:
        if cand_host == broken_host:
            score += 40
            reasons.append("Exact same domain")
        else:
            # Same root domain (e.g. subdomain changed)
            broken_root = ".".join(broken_host.split(".")[-2:])
            if cand_host.endswith("." + broken_root) or cand_host == broken_root:
                score += 30
                reasons.append("Same root domain")

    # -- Organisation name in content --
    if org:
        org_tokens = [w for w in re.split(r"\W+", org) if len(w) > 3]
        matches_in_title = sum(1 for t in org_tokens if t in title)
        matches_in_snippet = sum(1 for t in org_tokens if t in snippet)
        total_org_matches = matches_in_title + matches_in_snippet
        if total_org_matches >= 3:
            score += 25
            reasons.append(f"Strong org name match ({total_org_matches} tokens)")
        elif total_org_matches >= 1:
            score += 12
            reasons.append(f"Partial org name match ({total_org_matches} tokens)")

        # Org slug in candidate domain
        org_slug = re.sub(r"\W+", "", org.replace(" of ", "").replace(" the ", ""))[:20]
        if len(org_slug) > 4 and org_slug in cand_host.replace("-", "").replace(".", ""):
            score += 15
            reasons.append("Org slug in candidate domain")

    # -- Procurement keywords in path --
    path_hits = [kw for kw in PROCUREMENT_KEYWORDS if kw in cand_path.lower()]
    if path_hits:
        score += min(20, len(path_hits) * 7)
        reasons.append(f"Path keywords: {', '.join(path_hits[:3])}")

    # -- Procurement keywords in title / snippet --
    text_all = title + " " + snippet
    text_hits = [kw for kw in PROCUREMENT_KEYWORDS if kw in text_all]
    if text_hits:
        score += min(15, len(text_hits) * 5)
        reasons.append(f"Content keywords: {', '.join(text_hits[:3])}")

    # -- Geography match --
    if geo:
        geo_tokens = [w for w in re.split(r"\W+", geo) if len(w) > 3]
        if any(t in title or t in snippet or t in cand_host for t in geo_tokens):
            score += 10
            reasons.append("Geography match")

    # -- Official domain bonus --
    if re.search(r"\.(gov|govt|government|city|district|county|region|metro|municipal|authority)(\.|$)", cand_host):
        score += 10
        reasons.append("Official gov/org domain")
    if cand_host.endswith(".ca"):
        score += 5
        reasons.append("Canadian domain")

    # -- Penalties --
    if cand_path in ("/", "") and not cand_parsed.query:
        score -= 15
        reasons.append("Generic homepage — weak target")

    third_party_aggregators = ["bcbid.gov.bc.ca", "merx.com", "buyandsell.gc.ca"]
    orig_source_type = _first_nonempty(row, ["source_type"]).lower()
    if any(a in cand_host for a in third_party_aggregators):
        if "aggregator" not in orig_source_type:
            score -= 10
            reasons.append("Third-party aggregator (original was not)")

    reason_str = "; ".join(reasons) if reasons else "No matching factors"
    return max(0, score), reason_str


def get_confidence_level(score: int) -> str:
    if score >= 80:
        return "HIGH"
    if score >= 60:
        return "MEDIUM"
    if score >= 40:
        return "LOW"
    return "INSUFFICIENT"


# ==============================================================================
# 10.  INPUT READING & COLUMN NORMALISATION
# ==============================================================================

# Maps canonical names → list of possible aliases in input files
COLUMN_ALIASES: Dict[str, List[str]] = {
    "source_id": [
        "proposed_source_id", "final_source_id", "source_id", "id", "row_id"
    ],
    "source_name": [
        "source_name", "final_source_name", "name", "source"
    ],
    "source_category": ["source_category", "category"],
    "owner_organization": [
        "owner_organization", "owner / organization", "owner/organization",
        "organization", "owner", "org"
    ],
    "geography_coverage": [
        "geography_coverage", "geography / coverage", "geography/coverage",
        "geography", "coverage", "geo"
    ],
    "source_type": ["source_type", "type"],
    "official_url": [
        "URL / Portal", "URL/Portal", "url portal", "portal",
        "official_url", "primary_url", "url", "URL", "website"
    ],
    "primary_url": ["primary_url"],
    "example_url": [
        "example_relevant_page_or_record_url", "secondary_urls",
        "example_url", "secondary_url", "example"
    ],
    "likely_signal_type": ["likely_signal_type", "signal_type", "signal"],
    "why_relevant": ["why_relevant_to_tenderfinder", "why_relevant", "relevance"],
    "automation_feasibility": ["automation_feasibility", "feasibility"],
    "access_status": ["access_status", "access"],
    "suggested_fetch_type": ["suggested_fetch_type", "fetch_type"],
    "suggested_output_route": ["suggested_output_route", "output_route"],
    "priority_tier": ["priority_tier", "priority", "tier"],
    "notes": ["notes", "note", "comments"],
    "pre_script_status": ["pre_script_status", "row_pre_script_status"],
    "connector_type": ["connector_type"],
    "register_action": ["register_action"],
}


def _normalise_col_name(name: str) -> str:
    """Lower-case and collapse whitespace/special chars."""
    return re.sub(r"[^a-z0-9]", "_", name.lower()).strip("_")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename DataFrame columns to canonical names where aliases match."""
    col_map: Dict[str, str] = {}
    # Build a lookup: normalised_alias → original_column_name
    existing_norm: Dict[str, str] = {
        _normalise_col_name(c): c for c in df.columns
    }

    for canonical, aliases in COLUMN_ALIASES.items():
        if canonical in df.columns:
            continue  # already canonical
        for alias in aliases:
            norm_alias = _normalise_col_name(alias)
            if norm_alias in existing_norm:
                col_map[existing_norm[norm_alias]] = canonical
                break

    if col_map:
        df = df.rename(columns=col_map)
    return df


def read_input(path: Path, sheet: Optional[str] = None) -> pd.DataFrame:
    """Read .xlsx, .xls, or .csv into a normalised DataFrame.

    For Excel files: if `sheet` is given it must exist (clear error otherwise).
    If not given, prefer a sheet whose name looks like the source register
    (Source_Register / Audited_Register), else fall back to the first sheet.
    """
    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xlsm"):
        xl = pd.ExcelFile(path, engine="openpyxl")
        if sheet is not None:
            if sheet not in xl.sheet_names:
                raise InputValidationError(
                    f"Requested sheet '{sheet}' not found in {path.name}. "
                    f"Available sheets: {xl.sheet_names}"
                )
            chosen = sheet
        else:
            # Prefer recognisable register sheet names
            preferred = [s for s in xl.sheet_names
                         if re.search(r"source.?register|audited.?register",
                                      s, re.I)]
            chosen = preferred[0] if preferred else xl.sheet_names[0]
        log.info(f"Reading sheet '{chosen}' from {path.name} "
                 f"(available: {xl.sheet_names})")
        df = pd.read_excel(path, sheet_name=chosen, engine="openpyxl")
    elif suffix == ".xls":
        df = pd.read_excel(path, engine="xlrd")
    elif suffix in (".csv", ".tsv"):
        sep = "\t" if suffix == ".tsv" else ","
        df = pd.read_csv(path, encoding="utf-8-sig", sep=sep)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")

    df = normalize_columns(df)
    df = df.fillna("")
    # Drop entirely empty rows
    df = df[df.apply(lambda r: any(str(v).strip() for v in r.values), axis=1)]
    return df.reset_index(drop=True)


class InputValidationError(Exception):
    """Raised when the input register is missing required structure."""


def validate_input_dataframe(df: pd.DataFrame) -> int:
    """
    Validate the loaded register BEFORE any HTTP work. Raises
    InputValidationError (with a clear, actionable message) on:
      • zero source rows
      • no URL column present at all
      • no source identifier column present
      • zero extractable URLs across the whole register

    Returns the number of extractable URLs (informational).
    """
    cols = set(df.columns)

    if len(df) == 0:
        raise InputValidationError(
            "Source register loaded 0 rows. The sheet/file is empty or every row "
            "was blank. Nothing to audit."
        )

    if not (cols & set(REQUIRED_ID_COLUMNS)):
        raise InputValidationError(
            "No source identifier column found. Expected one of: "
            f"{', '.join(REQUIRED_ID_COLUMNS)} (or a recognised alias). "
            f"Columns present: {sorted(cols)}"
        )

    url_cols_present = cols & set(REQUIRED_URL_COLUMNS)
    if not url_cols_present:
        raise InputValidationError(
            "No URL column found. Expected at least one of: "
            f"{', '.join(REQUIRED_URL_COLUMNS)} (or a recognised alias). "
            f"Columns present: {sorted(cols)}"
        )

    # Count extractable URLs across the register
    total_urls = 0
    for _, row in df.iterrows():
        total_urls += len(extract_urls_from_row(row.to_dict()))

    if total_urls == 0:
        raise InputValidationError(
            f"Found URL column(s) {sorted(url_cols_present)} but extracted 0 usable "
            "URLs from all rows. All URL cells appear empty or malformed. "
            "Check that the URL column actually contains http(s) addresses."
        )

    return total_urls


# ==============================================================================
# 11.  CORE PROCESSING
# ==============================================================================

# Rate-limit lock (shared across threads)
_rate_lock = threading.Lock()
_last_request_time: float = 0.0


def _rate_limited_sleep(rate_limit: float) -> None:
    """Block until at least `rate_limit` seconds have elapsed since last call."""
    global _last_request_time
    with _rate_lock:
        now = time.time()
        elapsed = now - _last_request_time
        if elapsed < rate_limit:
            time.sleep(rate_limit - elapsed)
        _last_request_time = time.time()


def process_url_entry(
    url_entry: Dict,
    row: Dict,
    args: argparse.Namespace,
    thread_idx: int = 0,
) -> Dict:
    """
    Full processing pipeline for one URL:
    normalise → platform detect → HTTP check → classify → search replacement.
    Returns a flat dict ready for DataFrame/CSV output.
    """
    original_url = url_entry["original_url"]
    normalized_url = url_entry["normalized_url"]
    url_role = url_entry.get("url_role", "url")

    # Context from the source register row
    source_id = str(row.get("source_id", "")).strip()
    source_name = str(row.get("source_name", "")).strip()
    source_category = str(row.get("source_category", "")).strip()
    owner_org = str(row.get("owner_organization", "")).strip()
    geo = str(row.get("geography_coverage", "")).strip()
    source_type = str(row.get("source_type", "")).strip()
    fetch_type = str(row.get("suggested_fetch_type", "")).strip()
    output_route = str(row.get("suggested_output_route", "")).strip()
    access_status = str(row.get("access_status", "")).strip()
    priority = str(row.get("priority_tier", "")).strip()
    signal = str(row.get("likely_signal_type", "")).strip()
    connector_hint = str(row.get("connector_type", "")).strip()
    pre_script = str(row.get("pre_script_status", "")).strip()
    notes = str(row.get("notes", "")).strip()

    # Detect platform
    platform = detect_platform(
        normalized_url, source_type, fetch_type, access_status, connector_hint
    )

    # Base output row (all fields present in final CSVs)
    out: Dict[str, Any] = {
        # Pass-through source register columns
        "source_id":          source_id,
        "source_name":        source_name,
        "source_category":    source_category,
        "owner_organization": owner_org,
        "geography_coverage": geo,
        "source_type":        source_type,
        "suggested_fetch_type":  fetch_type,
        "suggested_output_route": output_route,
        "access_status":      access_status,
        "priority_tier":      priority,
        "likely_signal_type": signal,
        "notes":              notes,
        "pre_script_status":  pre_script,
        # URL audit columns
        "url_role":           url_role,
        "original_url":       original_url,
        "normalized_url":     normalized_url,
        "detected_platform":  platform,
        # To be filled below
        "final_url_after_redirect":  normalized_url,
        "url_check_status":          "",
        "http_status_code":          "",
        "content_type":              "",
        "response_time_seconds":     "",
        "redirect_chain":            "",
        "error_type":                "",
        "error_message":             "",
        "retry_count":               "",
        "classification_reason":     "",
        "safe_to_scrape":            "",
        "manual_review_required":    "",
        "replacement_candidate_url": "",
        "replacement_confidence_score": "",
        "replacement_confidence_level": "",
        "replacement_reason":        "",
        "recommended_action":        "",
        "script_ready":              "",
    }

    # -- NO USABLE URL (placeholder row) --------------------------------------
    if not normalized_url:
        out["url_check_status"] = "BROKEN_OTHER"
        out["error_type"] = "NO_URL_IN_ROW"
        out["error_message"] = "Row has no usable URL in any URL column."
        out["classification_reason"] = "Source row carried no official/example URL to validate."
        out["safe_to_scrape"] = "NO"
        out["manual_review_required"] = "YES"
        out["recommended_action"] = "Add a source URL to this row before scripting."
        out["script_ready"] = "FIX_URL_FIRST"
        log.debug(f"[NO-URL] source_id={source_id} has no URL")
        return out

    # -- DRY RUN --------------------------------------------------------------
    if args.dry_run:
        out["url_check_status"] = "DRY_RUN"
        out["classification_reason"] = "Dry-run mode — URL not contacted."
        out["safe_to_scrape"] = "UNKNOWN"
        out["manual_review_required"] = "YES"
        out["recommended_action"] = "Dry run — no HTTP request made"
        out["script_ready"] = "REVIEW_REQUIRED"
        log.info(f"[DRY RUN] {normalized_url}")
        return out

    # -- MANUAL-ONLY: skip HTTP (just validate landing if it's a URL) ---------
    if is_manual_only(platform, fetch_type, access_status):
        out["url_check_status"] = "LOGIN_OR_MANUAL"
        out["error_message"] = "Manual workflow — HTTP check skipped"
        out["classification_reason"] = (
            f"Source marked manual/login workflow (platform={platform}, "
            f"fetch_type={fetch_type or 'n/a'}); not auto-scraped."
        )
        out["safe_to_scrape"] = "NO"
        out["manual_review_required"] = "YES"
        out["recommended_action"] = "Manual workflow. No automated scraping."
        out["script_ready"] = "MANUAL_WORKFLOW_ONLY"
        log.info(f"[MANUAL] {normalized_url}")
        return out

    # -- RATE LIMIT -----------------------------------------------------------
    _rate_limited_sleep(args.rate_limit)

    # -- HTTP CHECK -----------------------------------------------------------
    log.info(f"[CHECK ] {normalized_url}")
    check_result = check_url(
        normalized_url,
        timeout=args.timeout,
        retries=args.retries,
        headers_idx=thread_idx,
    )

    url_status, classification_reason = classify_url_status(
        check_result, platform, row, normalized_url
    )
    log.info(
        f"  → {url_status} | HTTP {check_result.get('http_status_code', '?')} | "
        f"{check_result.get('response_time_seconds', 0):.1f}s"
    )
    if url_status in CRITICAL_BROKEN_STATUSES or url_status == "TIMEOUT_RETRY_NEEDED":
        log.debug(
            f"  FAIL-REASON {normalized_url} :: {url_status} :: {classification_reason} "
            f":: error_type={check_result.get('error_type')!r} "
            f":: msg={check_result.get('error_message', '')[:200]!r}"
        )

    out["final_url_after_redirect"] = check_result.get("final_url_after_redirect", normalized_url)
    out["http_status_code"] = check_result.get("http_status_code", "")
    out["content_type"] = check_result.get("content_type", "")
    out["response_time_seconds"] = check_result.get("response_time_seconds", "")
    out["redirect_chain"] = " → ".join(check_result.get("redirect_chain", []))
    out["error_type"] = derive_error_type(check_result, url_status)
    out["error_message"] = check_result.get("error_message", "")
    out["retry_count"] = check_result.get("retry_count", 0)
    out["classification_reason"] = classification_reason

    # -- REPLACEMENT SEARCH ---------------------------------------------------
    replacement_url = ""
    replacement_score = 0
    replacement_level = ""
    replacement_reason = ""

    is_broken = url_status in (
        "BROKEN_404", "BROKEN_DNS", "BROKEN_SSL", "BROKEN_OTHER",
    )

    if is_broken:
        if args.no_search:
            replacement_reason = "SEARCH_DISABLED"
            log.debug(f"  → Replacement search disabled (--no-search) for {normalized_url}")
        elif not has_search_api_key(args.search_provider):
            replacement_reason = "SEARCH_SKIPPED_NO_API_KEY"
            log.debug(f"  → Search skipped: no API key for {args.search_provider}")
        else:
            query = build_search_query(row, normalized_url)
            if query:
                log.info(f"  → Searching replacement: {query[:80]}")
                _rate_limited_sleep(args.rate_limit)  # respect rate limit for search too
                try:
                    candidates = do_search(query, args.search_provider, n=5)
                except SearchProviderError as exc:
                    candidates = []
                    replacement_reason = exc.reason
                    log.warning(
                        f"  → Replacement search failed for provider={exc.provider}: {exc.reason}. "
                        f"This is a search API/key/quota issue, not proof the source URL is valid or invalid."
                    )
                    log.debug(f"  → Search provider error for {query!r}: {exc}")
                except Exception as exc:
                    candidates = []
                    replacement_reason = f"SEARCH_API_UNEXPECTED_ERROR: {type(exc).__name__}"
                    log.debug(f"  → Search error for {query!r}: {exc}")

                best_score = 0
                best_candidate: Optional[Dict] = None
                best_reason = ""

                for cand in candidates:
                    s, reason = score_replacement_candidate(cand, row, normalized_url, platform)
                    if s > best_score:
                        best_score, best_candidate, best_reason = s, cand, reason

                if best_candidate and best_score >= 40:
                    replacement_url = best_candidate["url"]
                    replacement_score = best_score
                    replacement_level = get_confidence_level(best_score)
                    replacement_reason = best_reason
                    url_status = (
                        "REPLACEMENT_FOUND_HIGH_CONFIDENCE"
                        if replacement_level in ("HIGH", "MEDIUM")
                        else "REPLACEMENT_FOUND_LOW_CONFIDENCE"
                    )
                    log.info(f"  → Replacement ({replacement_level}): {replacement_url}")
                elif not replacement_reason:
                    url_status = "NO_REPLACEMENT_FOUND"
                    log.info("  → No suitable replacement found")

    out["url_check_status"] = url_status
    out["replacement_candidate_url"] = replacement_url
    out["replacement_confidence_score"] = replacement_score if replacement_score else ""
    out["replacement_confidence_level"] = replacement_level
    out["replacement_reason"] = replacement_reason
    out["recommended_action"] = get_recommended_action(
        url_status, platform, replacement_url, replacement_level
    )
    out["script_ready"] = classify_script_ready(url_status, platform, fetch_type, access_status)
    out["safe_to_scrape"] = derive_safe_to_scrape(url_status, platform)
    out["manual_review_required"] = derive_manual_review_required(url_status)

    return out


def process_all_urls(
    df: pd.DataFrame,
    args: argparse.Namespace,
) -> Tuple[List[Dict], List[Dict]]:
    """
    Expand source register rows into per-URL tasks and process them.
    Returns (all_url_results, source_row_results).
    """
    # Build task list: [(url_entry, row_dict, thread_idx), ...]
    tasks: List[Tuple[Dict, Dict, int]] = []
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        entries = extract_urls_from_row(row_dict)
        if not entries:
            # Row has no usable URL — add a placeholder so it still appears in output
            tasks.append((
                {"url_role": "no_url", "original_url": "", "normalized_url": ""},
                row_dict, len(tasks),
            ))
        for entry in entries:
            tasks.append((entry, row_dict, len(tasks)))

    log.info(f"Processing {len(tasks)} URL tasks from {len(df)} source rows ...")

    results: List[Optional[Dict]] = [None] * len(tasks)

    def _worker(idx: int, entry: Dict, row: Dict, tidx: int) -> Tuple[int, Dict]:
        return idx, process_url_entry(entry, row, args, thread_idx=tidx)

    workers = min(args.workers, len(tasks))

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_worker, i, entry, row, tidx): i
            for i, (entry, row, tidx) in enumerate(tasks)
        }
        done = 0
        for future in as_completed(futures):
            idx, result = future.result()
            results[idx] = result
            done += 1
            if done % 10 == 0 or done == len(tasks):
                log.info(f"  Progress: {done}/{len(tasks)} URLs checked")

    url_results = [r for r in results if r is not None]

    # Build per-source summary (for Cleaned_For_Script output)
    source_summary: Dict[str, Dict] = {}
    for r in url_results:
        sid = r.get("source_id", "") or r.get("source_name", "")
        if sid not in source_summary:
            source_summary[sid] = {
                **{k: v for k, v in r.items() if k in (
                    "source_id", "source_name", "source_category",
                    "owner_organization", "geography_coverage", "source_type",
                    "suggested_fetch_type", "suggested_output_route",
                    "access_status", "priority_tier", "likely_signal_type",
                    "notes", "pre_script_status",
                )},
                "primary_validated_url": "",
                "primary_url_status": "",
                "primary_script_ready": "",
                "any_broken": False,
                "any_replacement_found": False,
                "all_url_statuses": [],
            }
        entry = source_summary[sid]

        # Track primary URL result
        if r.get("url_role") == "primary_url" and not entry["primary_validated_url"]:
            entry["primary_validated_url"] = r.get("final_url_after_redirect", r.get("normalized_url", ""))
            entry["primary_url_status"] = r.get("url_check_status", "")
            entry["primary_script_ready"] = r.get("script_ready", "")

        status = r.get("url_check_status", "")
        entry["all_url_statuses"].append(status)

        if status in ("BROKEN_404", "BROKEN_DNS", "BROKEN_SSL", "BROKEN_OTHER", "NO_REPLACEMENT_FOUND"):
            entry["any_broken"] = True
        if "REPLACEMENT_FOUND" in status:
            entry["any_replacement_found"] = True

    # Finalise source-level rows
    source_rows: List[Dict] = []
    for sid, entry in source_summary.items():
        statuses = entry.pop("all_url_statuses", [])
        entry["all_url_statuses_summary"] = "|".join(statuses)
        # Overall row readiness
        if entry["any_broken"] and not entry["any_replacement_found"]:
            entry["row_script_ready"] = "FIX_URL_FIRST"
        elif entry["primary_script_ready"]:
            entry["row_script_ready"] = entry["primary_script_ready"]
        else:
            entry["row_script_ready"] = "REVIEW_REQUIRED"
        source_rows.append(entry)

    return url_results, source_rows


# ==============================================================================
# 12.  OUTPUT WRITING
# ==============================================================================

# Column order for the main audit file
AUDIT_COLUMNS = [
    "source_id", "source_name", "source_category", "owner_organization",
    "geography_coverage", "source_type", "priority_tier", "likely_signal_type",
    "url_role", "original_url", "normalized_url", "detected_platform",
    "final_url_after_redirect", "url_check_status", "http_status_code",
    "content_type", "response_time_seconds", "redirect_chain",
    "error_type", "error_message", "retry_count", "classification_reason",
    "safe_to_scrape", "manual_review_required",
    "replacement_candidate_url", "replacement_confidence_score",
    "replacement_confidence_level", "replacement_reason",
    "recommended_action", "script_ready",
    "suggested_fetch_type", "suggested_output_route", "access_status",
    "pre_script_status", "notes",
]

FIX_QUEUE_STATUSES = frozenset({
    "BROKEN_404", "BROKEN_DNS", "BROKEN_SSL", "BROKEN_OTHER",
    "TIMEOUT_RETRY_NEEDED", "REPLACEMENT_FOUND_HIGH_CONFIDENCE",
    "REPLACEMENT_FOUND_LOW_CONFIDENCE", "NO_REPLACEMENT_FOUND",
    "REVIEW_REQUIRED",
})


def _df_from_results(results: List[Dict], columns: List[str]) -> pd.DataFrame:
    """Build a DataFrame from results, ensuring all columns are present."""
    if not results:
        return pd.DataFrame(columns=columns)
    df = pd.DataFrame(results)
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df[columns].fillna("")


SAFE_OUTPUT_DIR = Path(r"C:\tenderfinder_tmp")


def _safe_output_dir(path: Path) -> Path:
    """If `path`'s parent directory is long enough to risk exceeding
    Windows' 260-char MAX_PATH, redirect `path` to live under
    SAFE_OUTPUT_DIR instead, preserving just the filename.

    Shared by _safe_atomic_write() (CSV/XLSX outputs) and the two log-file
    writers (setup_logging()'s debug log, write_run_log()'s run log), which
    previously opened their target path directly and could crash with
    FileNotFoundError under a long --output-dir (confirmed: directory
    creation via Path.mkdir succeeds even at this depth in this
    environment, but opening a file at the same depth does not).
    """
    path = Path(path)
    parent_str = str(path.parent)
    if os.name == "nt" and len(parent_str) > 220:
        SAFE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        safe_path = SAFE_OUTPUT_DIR / path.name
        log.warning(
            f"Output path too long ({len(str(path))} chars): {path}. "
            f"Auto-redirecting output to: {safe_path}. "
            f"Copy manually to your OneDrive folder after the run."
        )
        return safe_path
    return path


def _safe_atomic_write(path: Path, writer_fn, label: str) -> Path:
    """Write an output file safely.

    Patch 5.0 long-path fix:
      * write to system temp dir with a SHORT filename to avoid Windows
        260-char path length limit on deeply-nested OneDrive paths;
      * move/copy to final output path after successful write;
      * fall back to direct write if move fails;
      * raise a clear error so output validation returns a non-zero status.

    Root cause (Patch 4.x regression):
      Using path.with_name(f".{stem}.{ts}.{pid}.tmp{suffix}") creates a
      filename beside the target.  When the target is inside a long OneDrive
      path the composed temp path can exceed 260 chars on Windows and fail.
    """
    import tempfile
    import shutil

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Check if the output path itself would be too long for Windows.
    # MAX_PATH = 260. If the parent dir alone is > 220 chars, redirect to
    # SAFE_OUTPUT_DIR.
    redirected_path = _safe_output_dir(path)
    if redirected_path != path:
        path = redirected_path
        path.parent.mkdir(parents=True, exist_ok=True)

    # Write to system temp dir with a short name, then move to final path.
    # This avoids any path-length issue regardless of where final output lives.
    suffix = path.suffix
    tmp_path = None
    try:
        tmp_fd, tmp_str = tempfile.mkstemp(suffix=suffix, prefix="tenderfinder_")
        os.close(tmp_fd)
        tmp_path = Path(tmp_str)
    except Exception as e:
        # Ultra-fallback: short name beside target (may fail on very long paths)
        log.warning(f"Could not create system temp file ({e}); using short local tmp name.")
        tmp_path = path.with_name(f".tenderfinder_tmp{suffix}")

    try:
        writer_fn(tmp_path)
        if not tmp_path.exists():
            raise RuntimeError(f"temporary file was not created: {tmp_path}")
        if tmp_path.stat().st_size == 0:
            raise RuntimeError(f"temporary file is zero bytes: {tmp_path}")

        try:
            shutil.move(str(tmp_path), str(path))
            log.info(f"  Wrote {label:<5}: {path}")
            return path
        except Exception as replace_exc:
            # shutil.move can fail if target is locked (AV/OneDrive). Try a
            # direct write to the final path as fallback.
            log.warning(
                f"Move to final path failed for {path}: {type(replace_exc).__name__}: {replace_exc}. "
                "Trying direct write fallback."
            )
            try:
                writer_fn(path)
                if not path.exists() or path.stat().st_size == 0:
                    raise RuntimeError(f"direct output file missing or zero bytes: {path}")
                log.info(f"  Wrote {label:<5}: {path}  (direct fallback)")
                return path
            except Exception as direct_exc:
                raise RuntimeError(
                    f"Could not write {label} output to {path}. "
                    f"Atomic replace failed with {type(replace_exc).__name__}: {replace_exc}; "
                    f"direct fallback failed with {type(direct_exc).__name__}: {direct_exc}."
                ) from direct_exc
    finally:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception as cleanup_exc:
            log.debug(f"Could not remove temp output file {tmp_path}: {cleanup_exc}")


def _spreadsheet_safe_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy safe to open in Excel, including CSV exports."""
    safe_df = df.copy()
    for column in safe_df.columns:
        safe_df[column] = safe_df[column].map(safe_untrusted_excel_value)
    return safe_df


def _save_csv(df: pd.DataFrame, path: Path) -> Path:
    def _writer(target: Path) -> None:
        _spreadsheet_safe_dataframe(df).to_csv(
            target, index=False, encoding="utf-8-sig"
        )
    final_path = _safe_atomic_write(path, _writer, "CSV")
    log.info(f"            rows={len(df)}")
    return final_path


def _save_xlsx(df: pd.DataFrame, path: Path, sheet_name: str = "Sheet1") -> Path:
    def _writer(target: Path) -> None:
        with pd.ExcelWriter(target, engine="openpyxl") as writer:
            _spreadsheet_safe_dataframe(df).to_excel(
                writer, index=False, sheet_name=sheet_name
            )
    final_path = _safe_atomic_write(path, _writer, "XLSX")
    log.info(f"            rows={len(df)}")
    return final_path


def write_outputs(
    url_results: List[Dict],
    source_rows: List[Dict],
    output_dir: Path,
) -> Tuple[Dict[str, int], Dict[str, Path]]:
    """
    Write all output files. Returns (stats, written_files) where written_files
    maps a logical name to the Path actually written — used by validate_outputs.

    Patch 4.3 output-writer contract:
      * all expected output paths are registered even if one write fails;
      * one failed file does not delete files already written in the same run;
      * write failures are logged and then surfaced through output validation
        as EXIT_OUTPUT_INVALID rather than as a false success.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    written: Dict[str, Path] = {}
    output_errors: List[str] = []

    def _attempt(key: str, path: Path, writer_call) -> None:
        written[key] = path
        try:
            actual_path = writer_call(path)
            if actual_path:
                written[key] = Path(actual_path)
        except Exception as exc:
            msg = f"{key}: {path}: {type(exc).__name__}: {exc}"
            output_errors.append(msg)
            log.exception(f"Output write failed for {key}: {path}: {exc}")

    # 1. Main URL audit (CSV + XLSX)
    audit_df = _df_from_results(url_results, AUDIT_COLUMNS)
    _attempt(
        "audit_csv",
        output_dir / "TENDER_FINDER_Source_Register_URL_Live_Audit.csv",
        lambda path: _save_csv(audit_df, path),
    )
    _attempt(
        "audit_xlsx",
        output_dir / "TENDER_FINDER_Source_Register_URL_Live_Audit.xlsx",
        lambda path: _save_xlsx(audit_df, path, "URL_Live_Audit"),
    )

    # 2. Fix queue — only rows needing action
    fix_df = audit_df[audit_df["url_check_status"].isin(FIX_QUEUE_STATUSES)].copy()
    fix_cols = [
        "source_id", "source_name", "owner_organization", "geography_coverage",
        "url_role", "original_url", "normalized_url", "url_check_status",
        "http_status_code", "error_type", "error_message", "retry_count",
        "classification_reason", "safe_to_scrape", "manual_review_required",
        "replacement_candidate_url",
        "replacement_confidence_level", "replacement_reason",
        "recommended_action", "script_ready",
    ]
    fix_df = fix_df[[c for c in fix_cols if c in fix_df.columns]]
    _attempt(
        "fix_queue",
        output_dir / "TENDER_FINDER_Source_Register_Fix_Queue.csv",
        lambda path: _save_csv(fix_df, path),
    )

    # 3. Replacement candidates — every candidate is retained, including rows
    #    that were later marked REJECT/REVIEW by the operator. The file is
    #    ALWAYS written, even with headers only.
    repl_mask = audit_df["url_check_status"].astype(str).str.startswith("REPLACEMENT_FOUND")
    if "replacement_candidate_url" in audit_df.columns:
        repl_mask = repl_mask | audit_df["replacement_candidate_url"].astype(str).str.strip().ne("")
    repl_df = audit_df[repl_mask].copy()
    _attempt(
        "replacements",
        output_dir / "TENDER_FINDER_Source_Register_Replacement_Candidates.csv",
        lambda path: _save_csv(repl_df, path),
    )

    # 4. Cleaned for script — one row per source, with validated primary URL
    cleaned_cols = [
        "source_id", "source_name", "source_category", "owner_organization",
        "geography_coverage", "source_type", "priority_tier",
        "primary_validated_url", "primary_url_status", "primary_script_ready",
        "row_script_ready", "all_url_statuses_summary",
        "any_broken", "any_replacement_found",
        "suggested_fetch_type", "suggested_output_route", "access_status",
        "likely_signal_type", "notes",
    ]
    cleaned_df = _df_from_results(source_rows, cleaned_cols)
    _attempt(
        "cleaned",
        output_dir / "TENDER_FINDER_Source_Register_Cleaned_For_Script.csv",
        lambda path: _save_csv(cleaned_df, path),
    )

    # Compute stats
    statuses = audit_df["url_check_status"].tolist()
    stats = {
        "total_source_rows":          len(source_rows),
        "total_urls_checked":         len(url_results),
        "fix_queue_rows":             len(fix_df),
        "replacement_rows":           len(repl_df),
        "cleaned_rows":               len(cleaned_df),
        "ok":                         statuses.count("OK"),
        "ok_redirected":              statuses.count("OK_REDIRECTED"),
        "needs_connector":            statuses.count("NEEDS_CONNECTOR_NOT_SIMPLE_SCRAPE"),
        "login_or_manual":            statuses.count("LOGIN_OR_MANUAL"),
        "forbidden_likely_valid":     statuses.count("FORBIDDEN_BUT_LIKELY_VALID"),
        "timeout":                    statuses.count("TIMEOUT_RETRY_NEEDED"),
        "broken_404":                 statuses.count("BROKEN_404"),
        "broken_dns":                 statuses.count("BROKEN_DNS"),
        "broken_ssl":                 statuses.count("BROKEN_SSL"),
        "broken_other":               statuses.count("BROKEN_OTHER"),
        "replacement_high":           statuses.count("REPLACEMENT_FOUND_HIGH_CONFIDENCE"),
        "replacement_low":            statuses.count("REPLACEMENT_FOUND_LOW_CONFIDENCE"),
        "no_replacement":             statuses.count("NO_REPLACEMENT_FOUND"),
        "review_required":            statuses.count("REVIEW_REQUIRED"),
        "dry_run":                    statuses.count("DRY_RUN"),
        "script_ready_simple_http":   (audit_df["script_ready"] == "YES_SIMPLE_HTTP").sum(),
        "script_ready_connector":     (audit_df["script_ready"] == "YES_CONNECTOR_REQUIRED").sum(),
        "script_ready_manual":        (audit_df["script_ready"] == "MANUAL_WORKFLOW_ONLY").sum(),
        "fix_url_first":              (audit_df["script_ready"] == "FIX_URL_FIRST").sum(),
        "critical_broken":            int(audit_df["url_check_status"].isin(CRITICAL_BROKEN_STATUSES).sum()),
        "output_write_errors":        len(output_errors),
        "output_error_messages":      " | ".join(output_errors),
    }
    # Cast numpy ints to plain ints for clean logging / JSON
    stats = {k: (int(v) if hasattr(v, "item") else v) for k, v in stats.items()}
    return stats, written

def write_run_log(stats: Dict, args: argparse.Namespace, output_dir: Path, elapsed: float) -> None:
    """Write the human-readable run log."""
    log_path = _safe_output_dir(output_dir / "TENDER_FINDER_Link_Check_Run_Log.txt")
    lines = [
        "=" * 70,
        f"  TENDER_FINDER Source Register – Live URL Audit Run Log",
        f"  Script version : {VERSION}",
        f"  Run timestamp  : {RUN_TS}",
        f"  Elapsed time   : {elapsed:.1f}s",
        "=" * 70,
        "",
        "SETTINGS",
        f"  Input file       : {args.input}",
        f"  Output directory : {args.output_dir}",
        f"  Search provider  : {args.search_provider}",
        f"  Search enabled   : {not args.no_search}",
        f"  Timeout (s)      : {args.timeout}",
        f"  Retries          : {args.retries}",
        f"  Rate limit (s)   : {args.rate_limit}",
        f"  Workers          : {args.workers}",
        f"  Dry run          : {args.dry_run}",
        "",
        "RESULTS SUMMARY",
        f"  Source rows processed      : {stats['total_source_rows']}",
        f"  Total URLs checked         : {stats['total_urls_checked']}",
        "",
        "  URL Check Status",
        f"    OK                       : {stats['ok']}",
        f"    OK_REDIRECTED            : {stats['ok_redirected']}",
        f"    NEEDS_CONNECTOR          : {stats['needs_connector']}",
        f"    LOGIN_OR_MANUAL          : {stats['login_or_manual']}",
        f"    FORBIDDEN_LIKELY_VALID   : {stats['forbidden_likely_valid']}",
        f"    TIMEOUT_RETRY_NEEDED     : {stats['timeout']}",
        f"    BROKEN_404               : {stats['broken_404']}",
        f"    BROKEN_DNS               : {stats['broken_dns']}",
        f"    BROKEN_SSL               : {stats['broken_ssl']}",
        f"    BROKEN_OTHER             : {stats['broken_other']}",
        f"    REPLACEMENT_FOUND_HIGH   : {stats['replacement_high']}",
        f"    REPLACEMENT_FOUND_LOW    : {stats['replacement_low']}",
        f"    NO_REPLACEMENT_FOUND     : {stats['no_replacement']}",
        f"    REVIEW_REQUIRED          : {stats['review_required']}",
        f"    DRY_RUN                  : {stats['dry_run']}",
        "",
        "  Script Readiness",
        f"    YES_SIMPLE_HTTP          : {stats['script_ready_simple_http']}",
        f"    YES_CONNECTOR_REQUIRED   : {stats['script_ready_connector']}",
        f"    MANUAL_WORKFLOW_ONLY     : {stats['script_ready_manual']}",
        f"    FIX_URL_FIRST            : {stats['fix_url_first']}",
        "",
        "OUTPUT FILES",
        "  TENDER_FINDER_Source_Register_URL_Live_Audit.csv   (full per-URL audit)",
        "  TENDER_FINDER_Source_Register_URL_Live_Audit.xlsx  (same, Excel)",
        "  TENDER_FINDER_Source_Register_Fix_Queue.csv        (only review/fix items)",
        "  TENDER_FINDER_Source_Register_Replacement_Candidates.csv (always written)",
        "  TENDER_FINDER_Source_Register_Cleaned_For_Script.csv     (1 row per source)",
        "  TENDER_FINDER_Link_Check_Run_Log.txt   (this clean summary)",
        "  TENDER_FINDER_Link_Check_Debug_Log.txt (full DEBUG trace + per-failure reasons)",
        "",
        "ERROR / DIAGNOSTICS",
        f"  Critical broken URLs       : {stats.get('critical_broken', 0)}",
        f"  Fix Queue rows             : {stats.get('fix_queue_rows', 0)}",
        f"  Replacement candidate rows : {stats.get('replacement_rows', 0)}",
        "  Per-URL failure reasons     -> see classification_reason column +",
        "                                 'FAIL-REASON' lines in the debug log.",
        "",
        "EXIT CODES",
        "  0  success            2  output validation failed",
        "  1  input/config error 3  critical broken + --preflight-fail-on-broken",
        "                        4  unexpected runtime error",
        "",
        "STATUS CODE GUIDE",
        "  OK                          URL live, no redirect, ready to script",
        "  OK_REDIRECTED               URL works but path changed — update registered URL",
        "  NEEDS_CONNECTOR             Platform connector required (bidsandtenders, Bonfire, etc.)",
        "  LOGIN_OR_MANUAL             Auth / manual workflow — no automated scraping",
        "  FORBIDDEN_BUT_LIKELY_VALID  403/429 from real portal — connector or auth needed",
        "  TIMEOUT_RETRY_NEEDED        Server slow — retry later or increase timeout",
        "  BROKEN_404                  Page not found — URL needs fixing",
        "  BROKEN_DNS                  Domain unreachable — possibly moved or gone",
        "  BROKEN_SSL                  TLS/SSL certificate issue",
        "  BROKEN_OTHER                Other connection error",
        "  REPLACEMENT_FOUND_HIGH      Replacement URL found, high confidence",
        "  REPLACEMENT_FOUND_LOW       Replacement URL found, verify before use",
        "  NO_REPLACEMENT_FOUND        Broken — manual investigation required",
        "=" * 70,
    ]
    log_path.write_text("\n".join(lines), encoding="utf-8")
    log.info(f"  Wrote log  : {log_path}")


# ==============================================================================
# 12b. OUTPUT VALIDATION
# ==============================================================================

def validate_outputs(
    written: Dict[str, Path],
    stats: Dict,
    expected_source_rows: int,
    expected_url_count: int,
) -> Tuple[bool, List[str]]:
    """
    After a run, prove the outputs are real and consistent. Returns
    (ok, problems). `ok` is False if any hard validation fails — the caller
    then exits with EXIT_OUTPUT_INVALID (2) instead of falsely claiming success.

    Checks performed:
      • every expected output file exists on disk
      • the audit CSV/XLSX are non-empty (have a data row) when URLs were checked
      • audit row count matches the number of URLs processed
      • cleaned row count matches the number of source rows loaded
      • fix queue / replacement files exist (may legitimately be empty)
    """
    problems: List[str] = []

    if int(stats.get("output_write_errors", 0) or 0) > 0:
        problems.append(
            f"Output writer reported {stats.get('output_write_errors')} error(s): "
            f"{stats.get('output_error_messages', '')}"
        )

    # 1. All files must exist
    for name, path in written.items():
        if not path.exists():
            problems.append(f"Missing output file: {path}")
        elif path.stat().st_size == 0:
            problems.append(f"Output file is zero bytes: {path}")

    # 2. Audit must have a data row when we actually checked URLs
    audit_csv = written.get("audit_csv")
    if audit_csv and audit_csv.exists():
        try:
            adf = pd.read_csv(audit_csv, encoding="utf-8-sig", dtype=str).fillna("")
        except Exception as exc:
            problems.append(f"Audit CSV unreadable: {exc}")
            adf = None
        if adf is not None:
            if expected_url_count > 0 and len(adf) == 0:
                problems.append(
                    f"Audit CSV has 0 rows but {expected_url_count} URLs were expected."
                )
            if len(adf) != expected_url_count:
                problems.append(
                    f"Audit row count ({len(adf)}) != URLs processed ({expected_url_count})."
                )
            # Confirm the new error-handling columns are present
            required_cols = {
                "error_type", "error_message", "http_status_code",
                "final_url_after_redirect", "redirect_chain", "retry_count",
                "classification_reason", "recommended_action",
                "safe_to_scrape", "manual_review_required",
            }
            missing = required_cols - set(adf.columns)
            if missing:
                problems.append(f"Audit CSV missing required columns: {sorted(missing)}")

    # 3. Cleaned register must keep one row per source (no silent shrink)
    cleaned = written.get("cleaned")
    if cleaned and cleaned.exists():
        try:
            cdf = pd.read_csv(cleaned, encoding="utf-8-sig", dtype=str).fillna("")
            if expected_source_rows > 0 and len(cdf) == 0:
                problems.append("Cleaned_For_Script is empty but source rows were loaded.")
            if len(cdf) > expected_source_rows:
                problems.append(
                    f"Cleaned_For_Script grew beyond source rows "
                    f"({len(cdf)} > {expected_source_rows})."
                )
        except Exception as exc:
            problems.append(f"Cleaned CSV unreadable: {exc}")

    # 4. Fix queue must contain only actionable items (never OK rows)
    fixq = written.get("fix_queue")
    if fixq and fixq.exists():
        try:
            fdf = pd.read_csv(fixq, encoding="utf-8-sig", dtype=str).fillna("")
            if "url_check_status" in fdf.columns and len(fdf):
                bad = fdf[fdf["url_check_status"].isin(["OK", "OK_REDIRECTED"])]
                if len(bad):
                    problems.append(
                        f"Fix Queue contains {len(bad)} OK rows that should not be there."
                    )
        except Exception as exc:
            problems.append(f"Fix Queue CSV unreadable: {exc}")

    ok = len(problems) == 0
    if ok:
        log.info("Output validation passed.")
    else:
        for prob in problems:
            log.error(f"OUTPUT VALIDATION: {prob}")
    return ok, problems


# ==============================================================================
# 13.  CLI ARGUMENT PARSING
# ==============================================================================

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog=SCRIPT_NAME,
        description=(
            f"TENDER_FINDER Tender Finder – Source Register Live URL Auditor v{VERSION}\n"
            "Validates every URL in the TENDER_FINDER Source Register before automation."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Full audit with Tavily search:
    python tenderfinder_live_link_checker.py --input register.xlsx --search-provider tavily

  Audit-only (no replacement search):
    python tenderfinder_live_link_checker.py --input register.xlsx --no-search

  Dry run (show tasks, no HTTP):
    python tenderfinder_live_link_checker.py --input register.xlsx --dry-run

Environment variables for search API keys:
  TAVILY_API_KEY             Tavily (recommended for this project)
  BING_SEARCH_API_KEY        Bing Web Search API v7
  SERPAPI_API_KEY            SerpAPI
  GOOGLE_SEARCH_API_KEY      Google Custom Search API key
  GOOGLE_CSE_ID              Google Custom Search Engine ID
        """,
    )

    parser.add_argument(
        "--input", "-i",
        required=True,
        type=Path,
        metavar="FILE",
        help="Source register file (.xlsx, .csv, .xls)",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=Path("./link_audit_output"),
        type=Path,
        metavar="DIR",
        help="Directory to write output files (default: ./link_audit_output)",
    )
    parser.add_argument(
        "--search-provider",
        default="tavily",
        choices=["bing", "serpapi", "tavily", "google"],
        help="Web search provider for finding replacement URLs (default: tavily)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        metavar="SECONDS",
        help="HTTP request timeout in seconds (default: 20)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=2,
        metavar="N",
        help="Number of retries per URL on timeout/error (default: 2)",
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=1.0,
        metavar="SECONDS",
        help="Minimum delay between requests in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        metavar="N",
        help="Number of concurrent worker threads (default: 4)",
    )
    parser.add_argument(
        "--no-search",
        action="store_true",
        help="Skip replacement URL search (audit-only mode)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be checked without making any HTTP requests",
    )
    parser.add_argument(
        "--sheet",
        default=None,
        metavar="NAME",
        help="Worksheet name to read from an Excel input (default: auto-detect "
             "Source_Register / first sheet)",
    )
    parser.add_argument(
        "--preflight-fail-on-broken",
        action="store_true",
        help="Exit with code 3 if any critically broken URLs (404/DNS/SSL/other "
             "with no replacement) are found. Use in CI gates.",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Reduce console output to warnings and errors only "
             "(full trace still written to the debug log)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging on the console",
    )
    return parser.parse_args(argv)


# ==============================================================================
# 14.  MAIN
# ==============================================================================

def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    # Set up logging early — debug trace is separate from the run summary.
    try:
        args.output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        print(f"ERROR: cannot create output directory {args.output_dir}: {exc}",
              file=sys.stderr)
        return EXIT_INPUT_ERROR

    debug_log_path = _safe_output_dir(args.output_dir / "TENDER_FINDER_Link_Check_Debug_Log.txt")
    setup_logging(debug_log_path, verbose=args.verbose, quiet=args.quiet)

    log.info("=" * 60)
    log.info(f"TENDER_FINDER Source Register Live URL Auditor v{VERSION}")
    log.info(f"Run: {RUN_TS}")
    log.info("=" * 60)

    # -- 1. INPUT FILE EXISTS ------------------------------------------------
    if not args.input.exists():
        log.error(f"Input file not found: {args.input}")
        log.error("Provide a valid --input path to the Source Register (.xlsx/.csv).")
        return EXIT_INPUT_ERROR
    if not args.input.is_file():
        log.error(f"Input path is not a file: {args.input}")
        return EXIT_INPUT_ERROR

    # -- 2. READ INPUT (clear errors, never crash silently) ------------------
    log.info(f"Reading input: {args.input}")
    try:
        df = read_input(args.input, sheet=args.sheet)
    except InputValidationError as exc:
        log.error(f"Input error: {exc}")
        return EXIT_INPUT_ERROR
    except FileNotFoundError as exc:
        log.error(f"Input error: {exc}")
        return EXIT_INPUT_ERROR
    except ValueError as exc:
        log.error(f"Input error: {exc}")
        return EXIT_INPUT_ERROR
    except Exception as exc:
        log.exception(f"Unexpected error reading input: {exc}")
        return EXIT_RUNTIME_ERROR

    log.info(f"Loaded {len(df)} source rows, columns: {list(df.columns)}")

    # -- 3. VALIDATE REGISTER STRUCTURE (rows / columns / URLs) --------------
    try:
        expected_url_count = validate_input_dataframe(df)
    except InputValidationError as exc:
        log.error(f"Register validation failed: {exc}")
        # Write a diagnostic note so the operator has a record of *why* nothing ran
        try:
            diag = _safe_output_dir(args.output_dir / "TENDER_FINDER_Link_Check_Run_Log.txt")
            diag.write_text(
                "TENDER_FINDER URL Audit ABORTED — input validation failed.\n\n"
                f"Reason: {exc}\n\n"
                f"Input file: {args.input}\n"
                f"Rows loaded: {len(df)}\n"
                f"Columns: {list(df.columns)}\n"
                f"See {debug_log_path.name} for the full trace.\n",
                encoding="utf-8",
            )
        except Exception:
            pass
        return EXIT_INPUT_ERROR

    expected_source_rows = len(df)
    log.info(f"Validation OK — {expected_source_rows} source rows, "
             f"{expected_url_count} extractable URLs.")

    # -- Search-key advisory -------------------------------------------------
    search_mode = "ENABLED"
    if args.dry_run:
        search_mode = "SKIPPED (dry-run)"
    elif args.no_search:
        search_mode = "DISABLED (--no-search)"
    elif not has_search_api_key(args.search_provider):
        search_mode = f"SKIPPED (no API key for '{args.search_provider}')"
        log.warning(
            f"No API key found for '{args.search_provider}'. Replacement search "
            "will be skipped and broken URLs marked SEARCH_SKIPPED_NO_API_KEY. "
            "Set the appropriate env var or use --no-search to silence this."
        )
    log.info(f"Replacement search: {search_mode}")

    # -- 4. PROCESS ----------------------------------------------------------
    t_start = time.time()
    interrupted = False
    try:
        url_results, source_rows = process_all_urls(df, args)
    except KeyboardInterrupt:
        log.warning("Interrupted by user — writing partial results ...")
        interrupted = True
        url_results, source_rows = [], []
    except Exception as exc:
        log.exception(f"Unexpected runtime error during processing: {exc}")
        return EXIT_RUNTIME_ERROR

    elapsed = time.time() - t_start

    # -- 5. WRITE OUTPUTS ----------------------------------------------------
    try:
        log.info("Writing output files ...")
        stats, written = write_outputs(url_results, source_rows, args.output_dir)
        write_run_log(stats, args, args.output_dir, elapsed)
    except Exception as exc:
        log.exception(f"Unexpected error writing outputs: {exc}")
        return EXIT_RUNTIME_ERROR

    # -- 6. VALIDATE OUTPUTS -------------------------------------------------
    # When interrupted, partial output is expected — skip strict count checks.
    if not interrupted:
        ok, problems = validate_outputs(
            written, stats,
            expected_source_rows=expected_source_rows,
            expected_url_count=len(url_results),
        )
    else:
        ok, problems = True, []

    # -- Console summary -----------------------------------------------------
    broken_total = (stats.get("broken_404", 0) + stats.get("broken_dns", 0)
                    + stats.get("broken_ssl", 0) + stats.get("broken_other", 0))
    print("\n" + "=" * 60)
    print(f"  TENDER_FINDER URL Audit complete - {elapsed:.1f}s")
    print(f"  Source rows : {stats['total_source_rows']}")
    print(f"  URLs checked: {stats['total_urls_checked']}")
    print(f"  OK          : {stats['ok']}")
    print(f"  Redirected  : {stats['ok_redirected']}")
    print(f"  Connector   : {stats['needs_connector']}")
    print(f"  Manual/Login: {stats['login_or_manual']}")
    print(f"  Broken      : {broken_total}")
    print(f"  Replacement [ok] (high): {stats['replacement_high']}")
    print(f"  Replacement ~ (low) : {stats['replacement_low']}")
    print(f"  No replacement found: {stats['no_replacement']}")
    print(f"  Critical broken     : {stats['critical_broken']}")
    print(f"\n  Outputs in: {args.output_dir.resolve()}")

    if not ok:
        print("  OUTPUT VALIDATION: FAILED")
        for prob in problems:
            print(f"    - {prob}")
        print("=" * 60 + "\n")
        return EXIT_OUTPUT_INVALID

    # -- 7. PREFLIGHT GATE ---------------------------------------------------
    if args.preflight_fail_on_broken and stats["critical_broken"] > 0:
        print(f"  PREFLIGHT: {stats['critical_broken']} critical broken URL(s) - "
              "failing as requested (--preflight-fail-on-broken).")
        print("=" * 60 + "\n")
        log.error(f"Preflight failure: {stats['critical_broken']} critical broken URLs.")
        return EXIT_PREFLIGHT_BROKEN

    print("  Status: OK")
    print("=" * 60 + "\n")
    return EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as _fatal:                                # last-resort guard
        # Anything that escaped main()'s own handling — never crash silently.
        print(f"FATAL: unhandled exception: {type(_fatal).__name__}: {_fatal}",
              file=sys.stderr)
        sys.exit(EXIT_RUNTIME_ERROR)

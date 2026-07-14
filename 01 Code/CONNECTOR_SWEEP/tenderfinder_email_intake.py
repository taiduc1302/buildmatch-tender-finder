from __future__ import annotations

import argparse
import csv
import datetime as dt
import email
import hashlib
import json
import quopri
import re
import urllib.parse
from dataclasses import asdict, dataclass, field
from email import policy
from email.message import Message
from pathlib import Path
from typing import Any

from tenderfinder_package_paths import (
    detect_package_root,
    email_import_state_path,
    email_inbox_dir,
    email_logs_dir,
    ensure_email_alert_dirs,
    load_user_config,
    save_user_config,
    tenderfinder_user_config_path,
)

try:
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover - graceful fallback
    BeautifulSoup = None


CANONICAL_ALERT_SENDERS = (
    "bidsandtenders.ca",
    "bcbid.gov.bc.ca",
    "gov.bc.ca",
    "bidcentral.ca",
    "civicinfo.bc.ca",
)

CIVIL_KEYWORDS = (
    "civil", "earthwork", "excavat", "grading", "site servic", "underground",
    "utility", "utilities", "water", "potable", "watercourse", "watermain",
    "water main", "sewer", "sanitary", "sanitary main", "storm", "storm main",
    "drainage", "road", "paving", "curb", "sidewalk", "bridge", "servicing",
    "infrastructure", "pump station", "lift station", "trench", "pipe",
    "culvert", "erosion", "slope", "embankment", "fill", "compaction",
    "geotechnical", "aggregate", "subgrade", "catchbasin", "catch basin",
    "manhole", "tie-in", "tie in", "utility corridor", "right-of-way",
    "right of way", "dyke", "dike", "forcemain", "force main", "reservoir",
)

PROVIDER_KEYS = (
    "bidsandtenders.ca",
    "bidcentral.ca",
    "bcbid.gov.bc.ca",
    "civicinfo.bc.ca",
    "unknown",
)


@dataclass
class EmailTender:
    provider: str
    source: str
    issuer: str
    tender_title: str
    civil_relevant: bool
    status: str
    closing_date: str
    contact_email: str
    contact_phone: str
    url: str
    found_via: str
    snippet: str
    message_id: str
    received_date: str
    email_subject: str = ""
    email_from: str = ""
    email_date: str = ""
    raw_provider_category: str = ""
    parsed_from_email_file: str = ""
    parse_confidence: str = ""
    filtered_reason: str = ""


@dataclass
class EmailProviderConfig:
    provider: str = "manual_folder"
    connected: bool = False
    account_label: str = ""
    import_path: str = ""


@dataclass
class EmailRejectedFile:
    filename: str
    reason: str
    provider: str = "unknown"


@dataclass
class EmailIntakeTestResult:
    provider: str
    mailbox_connected: bool
    selected_folder: str
    is_fixture_source: bool
    alert_emails_found: int
    alerts_parsed: int
    civil_alerts_found: int
    new_tender_rows_created: int
    recognized_provider_counts: dict[str, int] = field(default_factory=dict)
    emails_rejected: int = 0
    rejected_reasons: dict[str, int] = field(default_factory=dict)
    tender_rows_parsed: int = 0
    open_actionable_rows: int = 0
    duplicate_emails_detected: int = 0
    log_path: str = ""


def clean_text(value: Any, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 3].rstrip() + "..."
    return text


def is_alert_sender(sender: str) -> bool:
    sender_l = (sender or "").lower()
    return any(domain in sender_l for domain in CANONICAL_ALERT_SENDERS)


def provider_key(sender: str) -> str:
    sender_l = (sender or "").lower()
    if "bidsandtenders.ca" in sender_l:
        return "bidsandtenders.ca"
    if "bidcentral.ca" in sender_l:
        return "bidcentral.ca"
    if "bcbid.gov.bc.ca" in sender_l or "gov.bc.ca" in sender_l:
        return "bcbid.gov.bc.ca"
    if "civicinfo.bc.ca" in sender_l:
        return "civicinfo.bc.ca"
    return "unknown"


def infer_source(sender: str) -> str:
    key = provider_key(sender)
    return {
        "bidsandtenders.ca": "bidsandtenders.ca",
        "bidcentral.ca": "BidCentral",
        "bcbid.gov.bc.ca": "BC Bid / gov.bc.ca",
        "civicinfo.bc.ca": "CivicInfo BC",
        "unknown": "email_alert",
    }[key]


def provider_display_name(provider: str) -> str:
    return {
        "gmail_oauth": "Gmail OAuth",
        "m365_oauth": "Microsoft 365 / Outlook OAuth",
        "imap": "IMAP fallback",
        "manual_folder": "Manual local folder import",
    }.get(provider, provider or "Not connected")


def civil_keyword_match(text: str) -> bool:
    low = text.lower()
    return any(k in low for k in CIVIL_KEYWORDS)


def extract_contact_email(text: str) -> str:
    matches = re.findall(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", text, flags=re.I)
    for match in matches:
        low = match.lower()
        if not any(skip in low for skip in ("example.", "noreply", "no-reply")):
            return match
    return ""


def extract_contact_phone(text: str) -> str:
    matches = re.findall(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?:\s*(?:x|ext\.?|extension)\s*\d{2,6})?", text, flags=re.I)
    for match in matches:
        digits = re.sub(r"\D", "", match)
        if len(digits) >= 10:
            return clean_text(match)
    return ""


def extract_closing_date(text: str) -> str:
    patterns = [
        r"(?:closing|close|closes|deadline|submission deadline|bid close)(?: date| time)?[:\s-]{0,20}([A-Z][a-z]+\.?\s+\d{1,2},?\s+\d{4})",
        r"(?:closing|close|closes|deadline|submission deadline|bid close)(?: date| time)?[:\s-]{0,20}(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
        r"(?:closing|close|closes|deadline|submission deadline|bid close)(?: date| time)?[:\s-]{0,20}(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
    ]
    formats = ("%B %d, %Y", "%B %d %Y", "%b %d, %Y", "%b %d %Y", "%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y")
    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.I):
            value = clean_text(match).replace(".", "")
            for fmt in formats:
                try:
                    parsed = dt.datetime.strptime(value, fmt).date()
                    if 2020 <= parsed.year <= 2035:
                        return parsed.isoformat()
                except ValueError:
                    continue
    return ""


def infer_status(text: str, closing_date: str) -> str:
    low = text.lower()
    if any(x in low for x in ("closed", "cancelled", "canceled", "awarded", "expired")):
        return "closed"
    if closing_date:
        try:
            return "open" if dt.date.fromisoformat(closing_date) >= dt.date.today() else "closed"
        except ValueError:
            pass
    return "open"


def safe_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._ -]+", "_", name).strip() or "email.eml"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def decode_bytes(payload: bytes | None, charset: str | None) -> str:
    if not payload:
        return ""
    encodings = [charset or "", "utf-8", "iso-8859-1", "latin-1"]
    for encoding in encodings:
        if not encoding:
            continue
        try:
            return payload.decode(encoding, errors="replace")
        except Exception:
            continue
    return payload.decode("utf-8", errors="replace")


def decode_part_text(part: Message) -> str:
    payload = part.get_payload(decode=True)
    if payload is None:
        raw = part.get_payload()
        if isinstance(raw, str):
            transfer = (part.get("Content-Transfer-Encoding") or "").lower()
            if transfer == "quoted-printable":
                return quopri.decodestring(raw).decode(part.get_content_charset() or "utf-8", errors="replace")
            return raw
        return ""
    return decode_bytes(payload, part.get_content_charset())


def extract_message_bodies(msg: Message) -> tuple[list[str], list[str]]:
    plain_parts: list[str] = []
    html_parts: list[str] = []
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue
            content_type = part.get_content_type()
            if content_type == "text/plain":
                plain_parts.append(decode_part_text(part))
            elif content_type == "text/html":
                html_parts.append(decode_part_text(part))
    else:
        text = decode_part_text(msg)
        if msg.get_content_type() == "text/html":
            html_parts.append(text)
        else:
            plain_parts.append(text)
    return plain_parts, html_parts


def html_to_text_and_links(html_text: str) -> tuple[str, list[tuple[str, str]]]:
    if not html_text:
        return "", []
    if BeautifulSoup is None:
        text = clean_text(re.sub(r"<[^>]+>", " ", html_text), 12000)
        links = re.findall(r'href=["\']([^"\']+)["\']', html_text, flags=re.I)
        return text, [(clean_text(url), clean_text(url)) for url in links]
    soup = BeautifulSoup(html_text, "html.parser")
    links: list[tuple[str, str]] = []
    for anchor in soup.find_all("a", href=True):
        label = clean_text(anchor.get_text(" ", strip=True), 220)
        href = clean_text(anchor["href"], 800)
        if href:
            links.append((label or href, href))
    for table in soup.find_all("table"):
        table_text = table.get_text(" ", strip=True)
        if table_text:
            links.append((clean_text(table_text, 220), ""))
    return clean_text(soup.get_text(" ", strip=True), 12000), links


def normalize_url(url: str) -> str:
    if not url:
        return ""
    parsed = urllib.parse.urlparse(url)
    if "sendgrid" in parsed.netloc.lower() or "mandrill" in parsed.netloc.lower():
        query = urllib.parse.parse_qs(parsed.query)
        for key in ("url", "u", "redirect", "redirect_url", "upn"):
            for value in query.get(key, []):
                decoded = urllib.parse.unquote(value)
                if decoded.startswith("http"):
                    return decoded
    return url


def first_url(text: str, link_pairs: list[tuple[str, str]] | None = None) -> tuple[str, str]:
    candidates: list[str] = []
    if link_pairs:
        candidates.extend(href for _, href in link_pairs if href)
    candidates.extend(re.findall(r"https?://[^\s>)\]]+", text))
    for raw in candidates:
        cleaned_raw = raw.rstrip(".,;")
        clean = normalize_url(cleaned_raw)
        if clean and not any(skip in clean.lower() for skip in ("unsubscribe", "privacy", "terms", "viewemail")):
            found_via = "email_tracking_link" if clean != cleaned_raw else "email_alert"
            return clean, found_via
    return "", "email_alert"


def clean_subject(subject: str) -> str:
    subject = re.sub(
        r"(?i)^(alert|notification|new opportunity|bid opportunity|bc bid alert|bc bid|daily notification|daily matches?)\s*[:\-]\s*",
        "",
        subject or "",
    )
    subject = re.sub(r"(?i)^daily matches?\s*-\s*bidcentral\s*-\s*", "", subject)
    subject = re.sub(r"(?i)^bidcentral\s*-\s*", "", subject)
    subject = re.sub(r"(?i)\s*\|\s*(bidsandtenders|bc bid|bidcentral|civicinfo).*$", "", subject)
    return clean_text(subject, 220)


def extract_issuer(subject: str, text: str, source: str) -> str:
    for pattern in [
        r"(?im)\bissuer[:\s]+(.+)$",
        r"(?im)\bowner[:\s]+(.+)$",
        r"(?im)\borganization[:\s]+(.+)$",
        r"(?im)\bcontracting authority[:\s]+(.+)$",
    ]:
        match = re.search(pattern, text)
        if match:
            return clean_text(match.group(1), 120)
    if " - " in subject:
        return clean_text(subject.split(" - ", 1)[0], 120)
    return source


def extract_provider_category(text: str) -> str:
    for pattern in [
        r"(?im)\bcategory[:\s]+(.+)$",
        r"(?im)\bcommodity[:\s]+(.+)$",
        r"(?im)\bopportunity type[:\s]+(.+)$",
    ]:
        match = re.search(pattern, text)
        if match:
            return clean_text(match.group(1), 120)
    return ""


def parse_confidence(title: str, issuer: str, url: str, closing_date: str) -> str:
    score = sum(1 for value in (title, issuer, url, closing_date) if value)
    if score >= 4:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def normalize_row_key(row: EmailTender) -> str:
    basis = "|".join([
        clean_text(row.url).lower(),
        clean_text(row.tender_title).lower(),
        clean_text(row.closing_date).lower(),
    ])
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def load_import_state(root: Path | None = None) -> dict[str, Any]:
    path = email_import_state_path(root)
    if not path.exists():
        return {"messages": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and isinstance(payload.get("messages"), list):
            return payload
    except Exception:
        pass
    return {"messages": []}


def save_import_state(state: dict[str, Any], root: Path | None = None) -> Path:
    ensure_email_alert_dirs(root)
    path = email_import_state_path(root)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return path


def current_email_import_folder(root: Path | None = None) -> Path:
    ensure_email_alert_dirs(root)
    config = load_user_config(root)
    chosen = clean_text(config.get("email_import_path"))
    if chosen:
        return Path(chosen)
    return email_inbox_dir(root)


def load_email_provider_config(root: Path | None = None) -> EmailProviderConfig:
    ensure_email_alert_dirs(root)
    config = load_user_config(root)
    import_path = clean_text(config.get("email_import_path"))
    provider = clean_text(config.get("email_provider") or "manual_folder") or "manual_folder"
    connected = bool(config.get("email_connected", bool(import_path)))
    account_label = clean_text(config.get("email_account_label")) or provider_display_name(provider)
    if not import_path:
        import_path = str(email_inbox_dir(root))
        connected = False
    return EmailProviderConfig(
        provider=provider,
        connected=connected,
        account_label=account_label,
        import_path=import_path,
    )


def save_email_provider_config(config: EmailProviderConfig, root: Path | None = None) -> Path:
    return save_user_config(
        {
            "email_provider": config.provider,
            "email_connected": config.connected,
            "email_account_label": config.account_label,
            "email_import_path": config.import_path,
        },
        root=root,
    )


def disconnect_email_provider(root: Path | None = None) -> Path:
    return save_email_provider_config(
        EmailProviderConfig(
            provider="manual_folder",
            connected=False,
            account_label=provider_display_name("manual_folder"),
            import_path=str(email_inbox_dir(root)),
        ),
        root=root,
    )


def connect_email_provider(provider: str, account_label: str = "", import_path: str = "", root: Path | None = None) -> Path:
    ensure_email_alert_dirs(root)
    chosen_path = import_path or str(email_inbox_dir(root))
    connected = provider == "manual_folder" and bool(chosen_path)
    return save_email_provider_config(
        EmailProviderConfig(
            provider=provider,
            connected=connected,
            account_label=account_label or provider_display_name(provider),
            import_path=chosen_path,
        ),
        root=root,
    )


def reset_email_import_folder_to_default(root: Path | None = None) -> Path:
    return connect_email_provider(
        "manual_folder",
        account_label=provider_display_name("manual_folder"),
        import_path=str(email_inbox_dir(root)),
        root=root,
    )


def _resolve_fixture_dir(fixtures_dir: Path | None, provider_config: EmailProviderConfig | None, root: Path | None = None) -> Path | None:
    if fixtures_dir:
        return fixtures_dir
    config = provider_config or load_email_provider_config(root)
    if config.provider == "manual_folder" and config.import_path:
        return Path(config.import_path)
    return None


def is_fixture_source_folder(folder: str | Path | None) -> bool:
    """True when an email-source folder is the checked-in test fixtures
    directory (tests/fixtures/email_alerts) rather than a real user inbox.
    Used so demo reports never present fixture/synthetic parsing as live
    email-intake proof."""
    if not folder:
        return False
    parts = {p.lower() for p in Path(folder).parts}
    return "tests" in parts and "fixtures" in parts


def is_fixture_email_filename(filename: str | Path | None) -> bool:
    name = Path(filename or "").name.lower()
    return bool(re.match(r"^fixture_\d+.*\.eml$", name))


def _parse_message(path: Path) -> tuple[EmailTender | None, str, str]:
    msg = email.message_from_binary_file(path.open("rb"), policy=policy.default)
    sender = clean_text(msg.get("From", ""))
    provider = provider_key(sender)
    if not is_alert_sender(sender):
        return None, "unknown_provider", provider
    subject = clean_subject(str(msg.get("Subject", "")))
    plain_parts, html_parts = extract_message_bodies(msg)
    html_text = "\n".join(html_parts)
    plain_text = "\n".join(plain_parts)
    html_visible, html_links = html_to_text_and_links(html_text)
    joined = clean_text("\n".join([subject, plain_text, html_visible]), 16000)
    title = subject
    if not title:
        for pattern in [
            r"(?im)\bopportunity title[:\s]+(.+)$",
            r"(?im)\bproject title[:\s]+(.+)$",
            r"(?im)\bsolicitation[:\s]+(.+)$",
        ]:
            match = re.search(pattern, joined)
            if match:
                title = clean_text(match.group(1), 220)
                break
    if not title:
        return None, "missing_tender_title", provider
    close_date = extract_closing_date(joined)
    source = infer_source(sender)
    issuer = extract_issuer(subject, joined, source)
    url, found_via = first_url("\n".join([plain_text, html_text, html_visible]), html_links)
    status = infer_status(joined, close_date)
    civil = civil_keyword_match(joined)
    filtered_reason = ""
    if not civil:
        filtered_reason = "non_civil_email_alert"
    elif status != "open":
        filtered_reason = "closed_or_non_actionable_email_alert"
    row = EmailTender(
        provider=provider,
        source=source,
        issuer=issuer,
        tender_title=title,
        civil_relevant=civil,
        status=status,
        closing_date=close_date,
        contact_email=extract_contact_email(joined),
        contact_phone=extract_contact_phone(joined),
        url=url,
        found_via=found_via,
        snippet="Email alert parsed. Raw message body stays in the mailbox/import folder and is not copied into TENDER_FINDER outputs.",
        message_id=clean_text(msg.get("Message-ID") or ""),
        received_date=clean_text(msg.get("Date") or ""),
        email_subject=subject,
        email_from=sender,
        email_date=clean_text(msg.get("Date") or ""),
        raw_provider_category=extract_provider_category(joined),
        parsed_from_email_file=safe_filename(path.name),
        parse_confidence=parse_confidence(title, issuer, url, close_date),
        filtered_reason=filtered_reason,
    )
    return row, "", provider


def parse_eml(path: Path) -> EmailTender | None:
    row, reason, _ = _parse_message(path)
    return row if not reason else None


def parse_eml_dir(path: Path) -> list[EmailTender]:
    if not path.exists():
        return []
    rows = [row for file in sorted(path.glob("*.eml")) if (row := parse_eml(file))]
    deduped: dict[str, EmailTender] = {}
    for row in rows:
        deduped[normalize_row_key(row)] = row
    return list(deduped.values())


def evaluate_email_folder(
    folder: Path | None,
    provider_config: EmailProviderConfig | None = None,
    dry_run: bool = True,
    update_state: bool = False,
    root: Path | None = None,
) -> tuple[list[EmailTender], EmailIntakeTestResult, list[EmailRejectedFile]]:
    package_root = detect_package_root(root)
    ensure_email_alert_dirs(package_root)
    config = provider_config or load_email_provider_config(package_root)
    selected = folder or _resolve_fixture_dir(None, config, package_root)
    selected_folder = str(selected) if selected else ""
    files = sorted(selected.glob("*.eml")) if selected and selected.exists() else []
    fixture_folder_source = bool(selected and is_fixture_source_folder(selected_folder))
    fixture_source = bool(
        selected
        and (
            fixture_folder_source
            or (files and all(is_fixture_email_filename(path.name) for path in files))
        )
    )
    provider_counts = {key: 0 for key in PROVIDER_KEYS}
    rejected: list[EmailRejectedFile] = []
    rows: list[EmailTender] = []
    duplicate_emails = 0
    row_seen: set[str] = set()
    state = {"messages": []} if fixture_folder_source else load_import_state(package_root)
    seen_message_ids = {clean_text(entry.get("message_id")).lower() for entry in state.get("messages", []) if entry.get("message_id")}
    seen_hashes = {clean_text(entry.get("file_hash")).lower() for entry in state.get("messages", []) if entry.get("file_hash")}
    now = dt.datetime.now().isoformat(timespec="seconds")
    new_state_messages = list(state.get("messages", []))
    def remember_processed_email(row: EmailTender | None, file_hash: str, path: Path, parsed_row_count: int, reason: str = "") -> None:
        if not (update_state and not dry_run):
            return
        new_state_messages.append(
            {
                "message_id": row.message_id if row else "",
                "file_hash": file_hash,
                "filename": path.name,
                "first_seen_at": now,
                "last_processed_at": now,
                "provider": row.provider if row else provider,
                "parsed_row_count": parsed_row_count,
                "reason": reason,
            }
        )

    for path in files:
        file_hash = file_sha256(path)
        row, reason, provider = _parse_message(path)
        provider_counts[provider] = provider_counts.get(provider, 0) + 1
        if row is None:
            rejected.append(EmailRejectedFile(path.name, reason or "parse_failed", provider))
            remember_processed_email(None, file_hash, path, 0, reason or "parse_failed")
            continue
        duplicate_email = False
        message_id = clean_text(row.message_id).lower()
        if message_id and message_id in seen_message_ids:
            duplicate_email = True
        elif file_hash.lower() in seen_hashes:
            duplicate_email = True
        if duplicate_email:
            duplicate_emails += 1
            rejected.append(EmailRejectedFile(path.name, "duplicate_email", provider))
            continue
        row_key = normalize_row_key(row)
        if row_key in row_seen:
            duplicate_emails += 1
            rejected.append(EmailRejectedFile(path.name, "duplicate_row", provider))
            remember_processed_email(row, file_hash, path, 0, "duplicate_row")
            continue
        row_seen.add(row_key)
        rows.append(row)
        remember_processed_email(row, file_hash, path, 1)

    rejected_reasons: dict[str, int] = {}
    for item in rejected:
        rejected_reasons[item.reason] = rejected_reasons.get(item.reason, 0) + 1

    civil_rows = sum(1 for row in rows if row.civil_relevant)
    open_rows = sum(1 for row in rows if row.civil_relevant and row.status == "open")
    result = EmailIntakeTestResult(
        provider=provider_display_name(config.provider),
        mailbox_connected=bool(config.connected),
        selected_folder=selected_folder,
        is_fixture_source=fixture_source,
        alert_emails_found=len(files),
        alerts_parsed=len(rows),
        civil_alerts_found=civil_rows,
        new_tender_rows_created=open_rows,
        recognized_provider_counts=provider_counts,
        emails_rejected=len(rejected),
        rejected_reasons=rejected_reasons,
        tender_rows_parsed=len(rows),
        open_actionable_rows=open_rows,
        duplicate_emails_detected=duplicate_emails,
    )

    if dry_run:
        log_dir = email_logs_dir(package_root)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"email_import_test_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        log_path.write_text(
            json.dumps(
                {
                    "selected_folder": selected_folder,
                    "result": asdict(result),
                    "rejected": [asdict(item) for item in rejected],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        result.log_path = str(log_path)
    elif update_state and not fixture_folder_source:
        save_import_state({"messages": new_state_messages}, package_root)
    return rows, result, rejected


def test_email_intake(fixtures_dir: Path | None = None, provider_config: EmailProviderConfig | None = None, root: Path | None = None) -> EmailIntakeTestResult:
    ensure_email_alert_dirs(root)
    config = provider_config or load_email_provider_config(root)
    folder = fixtures_dir or _resolve_fixture_dir(None, config, root)
    _, result, _ = evaluate_email_folder(folder, provider_config=config, dry_run=True, update_state=False, root=root)
    return result


def write_outputs(rows: list[EmailTender], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "tenderfinder_email_intake_results.json"
    csv_path = out_dir / "BID_NOW_from_email_alerts.csv"
    json_path.write_text(json.dumps([asdict(r) for r in rows], indent=2), encoding="utf-8")
    empty_row = EmailTender("", "", "", "", False, "", "", "", "", "", "", "", "", "")
    fieldnames = list(asdict(rows[0]).keys()) if rows else list(asdict(empty_row).keys())
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def run_email_intake(
    out_dir: Path,
    fixtures_dir: Path | None = None,
    dry_run: bool = False,
    provider_config: EmailProviderConfig | None = None,
    root: Path | None = None,
) -> tuple[str, list[EmailTender], EmailIntakeTestResult]:
    package_root = detect_package_root(root)
    ensure_email_alert_dirs(package_root)
    config = provider_config or load_email_provider_config(package_root)
    source_dir = fixtures_dir or _resolve_fixture_dir(None, config, package_root)
    if not source_dir:
        result = EmailIntakeTestResult(
            provider=provider_display_name(config.provider),
            mailbox_connected=False,
            selected_folder="",
            is_fixture_source=False,
            alert_emails_found=0,
            alerts_parsed=0,
            civil_alerts_found=0,
            new_tender_rows_created=0,
        )
        return "EMAIL_INTAKE_SKIPPED_NO_FOLDER", [], result
    rows, result, rejected = evaluate_email_folder(
        source_dir,
        provider_config=config,
        dry_run=dry_run,
        update_state=not dry_run,
        root=package_root,
    )
    if not dry_run:
        write_outputs(rows, out_dir)
    if result.alert_emails_found == 0:
        status = "EMAIL_INTAKE_NO_FILES"
    elif result.tender_rows_parsed > 0:
        status = "EMAIL_INTAKE_PARSED_ROWS"
    elif result.emails_rejected > 0:
        status = "EMAIL_INTAKE_REJECTED_FILES"
    else:
        status = "EMAIL_INTAKE_PARSE_ZERO_ROWS"
    if result.alert_emails_found > 0:
        print(
            f"EMAIL_IMPORT folder={result.selected_folder} files={result.alert_emails_found} "
            f"parsed_rows={result.tender_rows_parsed} civil={result.civil_alerts_found} "
            f"open_actionable={result.open_actionable_rows} duplicates={result.duplicate_emails_detected} "
            f"rejected={result.emails_rejected}"
        )
    else:
        print(f"NO_ALERT_EMAILS_FOUND provider={provider_display_name(config.provider)} connected={config.connected} folder={result.selected_folder}")
    return status, rows, result


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Parse TENDER_FINDER tender alert emails.")
    ap.add_argument("--fixtures-dir", default="", help="Directory of .eml files for offline parsing/testing.")
    ap.add_argument("--out-dir", default="email_intake_out", help="Output directory.")
    ap.add_argument("--dry-run", action="store_true", help="Parse and report without writing outputs or updating duplicate state.")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    fixtures = Path(args.fixtures_dir) if args.fixtures_dir else None
    run_email_intake(Path(args.out_dir), fixtures, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

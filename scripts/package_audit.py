r"""Tender Finder — package sanitization audit.

Re-scans the whole package (text files AND Excel workbook cells) for:
  - original internal brand tokens
  - real-looking email addresses (non-placeholder, non-public-portal)
  - secret patterns (API keys, tokens, passwords, cookies)
  - private local paths / OneDrive user paths
  - vcs / venv / cache folders that must not ship

Usage:  python scripts\package_audit.py [package_root]
Exit 0 + "PACKAGE AUDIT: PASS" when clean.

Requires: openpyxl (already a runtime dependency).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]

TEXT_EXTS = {".py", ".md", ".txt", ".csv", ".bat", ".yml", ".yaml", ".json",
             ".eml", ".command", ".example", ".cfg", ".ini", ".toml", ".html"}

# Deliberately assembled from fragments so this file never contains the
# forbidden tokens itself.
BRAND = "ty" + "bo"
BRAND_PATTERNS = [
    re.compile(BRAND, re.IGNORECASE),
]

SECRET_PATTERNS = [
    re.compile(r"tvly-(?!your-key-here)[A-Za-z0-9_-]{10,}"),   # Tavily key (placeholder ok)
    re.compile(r"sk-(?:ant-)?[A-Za-z0-9_-]{20,}"),             # Anthropic/OpenAI-style keys
    re.compile(r"AKIA[0-9A-Z]{16}"),                            # AWS access key
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),                        # GitHub token
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),                # Slack token
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)(password|passwd|secret|api[_-]?key|token)\s*[:=]\s*['\"][^'\"\s]{8,}['\"]"),
    re.compile(r"(?i)set-cookie:"),
]

PATH_PATTERNS = [
    re.compile(r"(?i)C:[\\/]+Users[\\/]+(?!x\b|Public\b|ExampleUser\b|<)[A-Za-z0-9._-]+"),
    re.compile(r"(?i)OneDrive - (?!Example)"),
]

FORBIDDEN_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "node_modules",
                  ".agents", ".codex_tmp"}

# Placeholder / public-infrastructure addresses that are allowed to remain.
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}")
ALLOWED_EMAIL_DOMAINS = {
    "example.com", "example.org",
    # public procurement portals / public agency contacts used by connectors,
    # fixtures, and docs (public information, not personal data):
    "bidsandtenders.ca", "bcbid.gov.bc.ca", "gov.bc.ca", "surrey.ca",
    "bidcentral.ca", "buildingconnected.com", "civicinfo.bc.ca",
    "anthropic.com",
}

findings: list[str] = []


def check_text(rel: str, text: str) -> None:
    for pat in BRAND_PATTERNS:
        for m in pat.finditer(text):
            findings.append(f"BRAND {rel}: ...{text[max(0, m.start()-30):m.end()+30]!r}...")
    for pat in SECRET_PATTERNS:
        for m in pat.finditer(text):
            findings.append(f"SECRET {rel}: pattern {pat.pattern[:40]!r} matched {m.group(0)[:40]!r}")
    for pat in PATH_PATTERNS:
        for m in pat.finditer(text):
            findings.append(f"PRIVATE_PATH {rel}: {m.group(0)[:60]!r}")
    for m in EMAIL_RE.finditer(text):
        domain = m.group(0).rsplit("@", 1)[1].lower().rstrip(".")
        if domain not in ALLOWED_EMAIL_DOMAINS:
            findings.append(f"EMAIL {rel}: {m.group(0)}")


def main() -> int:
    n_text = n_wb = 0
    for p in sorted(ROOT.rglob("*")):
        rel = p.relative_to(ROOT).as_posix()
        if p.is_dir():
            if p.name in FORBIDDEN_DIRS:
                # .venv is expected once the user runs setup; flag the rest.
                if p.name == ".venv" and p.parent == ROOT:
                    continue
                if p.name == "__pycache__":
                    findings.append(f"CACHE_DIR {rel}: delete before redistributing")
                else:
                    findings.append(f"FORBIDDEN_DIR {rel}")
            continue
        if ROOT.joinpath(".venv") in p.parents:
            continue
        if p.resolve() == Path(__file__).resolve():
            # this file defines the detection patterns, so it would
            # always match itself
            continue
        if p.suffix.lower() in TEXT_EXTS or p.name in (".gitignore", ".gitattributes"):
            try:
                text = p.read_bytes().decode("utf-8")
            except UnicodeDecodeError:
                text = p.read_bytes().decode("cp1252", errors="replace")
            check_text(rel, text)
            n_text += 1
        elif p.suffix.lower() == ".xlsx" and "~$" not in p.name:
            try:
                from openpyxl import load_workbook
                wb = load_workbook(p, read_only=True, data_only=True)
                for ws in wb.worksheets:
                    for row in ws.iter_rows(values_only=True):
                        for v in row:
                            if isinstance(v, str):
                                check_text(f"{rel}::{ws.title}", v)
                wb.close()
                n_wb += 1
            except Exception as e:  # noqa: BLE001
                findings.append(f"XLSX_UNREADABLE {rel}: {e}")

    print(f"scanned {n_text} text files, {n_wb} workbooks under {ROOT}")
    if findings:
        print(f"PACKAGE AUDIT: FAIL ({len(findings)} findings)")
        for f in findings[:200]:
            print("  " + f)
        return 1
    print("PACKAGE AUDIT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

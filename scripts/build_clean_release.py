#!/usr/bin/env python3
"""Build the deterministic Tender Finder internal-beta source ZIP.

The archive is allowlist-based.  It intentionally ships no virtual
environment, Git metadata, caches, runtime state, user data, browser state, or
historical generated output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RELEASE_VERSION = "internal-weekly-beta-v1"
ARCHIVE_FOLDER = "Tender_Finder_Internal_Weekly_Beta_v1"
FIXED_ZIP_TIMESTAMP = (2026, 7, 15, 0, 0, 0)
CANONICAL_TEXT_SUFFIXES = {
    ".bat",
    ".cfg",
    ".cmd",
    ".command",
    ".csv",
    ".html",
    ".ini",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".sh",
    ".toml",
    ".tsv",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
WINDOWS_CRLF_SUFFIXES = {".bat", ".cmd"}

ROOT_FILES = {
    "Launch_TENDER_FINDER_GUI.bat",
    "run_tenderfinder_demo.bat",
    "run_tenderfinder_demo_fast.bat",
    "setup_tenderfinder_environment.bat",
    "_python_bootstrap.bat",
    "verify_package.bat",
    "requirements.txt",
    "README.md",
    "README_START_HERE.txt",
    "README_QUICKSTART.md",
    "README_INSTALL.md",
    "INSTALL.md",
    "RUNBOOK.md",
    "KNOWN_LIMITATIONS.md",
    "SOURCE_STATUS_EXPLANATION.md",
    "Email_Setup_Guide.md",
    "MANUAL_PORTAL_WORKFLOW.md",
    "ENTRY_POINTS.md",
    "FUTURE_WEB_APP_PLAN.md",
    "PACKAGE_MANIFEST.md",
    "TENDER_FINDER_Connector_Coverage_Map.csv",
}

EXACT_FILES = {
    ".github/workflows/offline-ci.yml",
    "00 Master/README.md",
    "00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_TEMPLATE_v1.xlsx",
    "01 Code/tenderfinder_agent2.py",
    "01 Code/CONNECTOR_SWEEP/requirements.txt",
    "01 Code/CONNECTOR_SWEEP/requirements-dev.txt",
    "01 Code/CONNECTOR_SWEEP/RUN_ALL_SOURCES_SAFE.md",
    "01 Code/CONNECTOR_SWEEP/tenderfinder_dev_app_endpoints.csv",
    "config/keywords.xlsx",
    "config/keywords_template.xlsx",
    "config/sources.csv",
    "inputs/all_live_review.xlsx",
    "inputs/README_INPUTS.md",
    "docs/GETTING_STARTED.md",
    "docs/KEYWORDS_CONFIG_DECISIONS.md",
    "docs/EMAIL_INTAKE_SPEC.md",
    "docs/BC_BID_NETWORK_AUDIT.md",
    "scripts/offline_ci_check.py",
    "scripts/build_clean_release.py",
    "scripts/verify_clean_release.py",
    "scripts/package_audit.py",
}

SELF_TEST_FILES = {
    "test_stabilization_security.py",
    "test_source_registry_stabilization.py",
    "test_keywords_config.py",
    "test_rescore_always_e2e.py",
    "test_standalone_weekly_release.py",
    "test_engine_contract.py",
    "test_launcher_portability.py",
    "test_offline_ci_workflow.py",
    "test_clean_release_packaging.py",
    "test_launcher_gui.py",
    "test_routing_gates.py",
    "test_outreach_persistence.py",
    "test_launcher_review_xlsx_consistency.py",
    "test_tender_signal_routing.py",
}

FORBIDDEN_PARTS = {
    ".git",
    ".venv",
    ".codex_tmp",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    "user_data",
    "demo_history",
    "raw_runs",
    "latest_verified_output",
}
FORBIDDEN_SUFFIXES = {
    ".pyc", ".pyo", ".log", ".tmp", ".eml", ".db", ".sqlite", ".sqlite3", ".zip",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(*args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return completed.stdout.strip() if completed.returncode == 0 else ""


def source_identity() -> dict[str, object]:
    status = _git("status", "--porcelain", "--untracked-files=all")
    return {
        "source_commit_sha": _git("rev-parse", "HEAD") or "unavailable-no-git-metadata",
        "source_commit_time": _git("show", "-s", "--format=%cI", "HEAD") or "unavailable",
        "source_worktree_dirty": bool(status),
    }


def _safe_relative(path: Path) -> str:
    relative = path.resolve().relative_to(ROOT.resolve()).as_posix()
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts:
        raise ValueError(f"Unsafe release path: {relative}")
    if FORBIDDEN_PARTS.intersection(part.casefold() for part in pure.parts):
        raise ValueError(f"Forbidden release path: {relative}")
    if path.suffix.casefold() in FORBIDDEN_SUFFIXES or path.name.startswith("~$"):
        raise ValueError(f"Forbidden release file: {relative}")
    return relative


def _existing(paths: Iterable[Path]) -> set[Path]:
    result = set()
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(f"Required release file is missing: {path}")
        _safe_relative(path)
        result.add(path.resolve())
    return result


def gather_release_files() -> list[Path]:
    files = _existing(ROOT / name for name in sorted(ROOT_FILES | EXACT_FILES))
    code_dir = ROOT / "01 Code" / "CONNECTOR_SWEEP"
    files.update(_existing(code_dir.glob("tenderfinder_*.py")))
    files.update(_existing(path for path in (code_dir / "data").rglob("*") if path.is_file()))
    tests_dir = code_dir / "tests"
    files.update(_existing(tests_dir / name for name in sorted(SELF_TEST_FILES)))
    # Ship test fixtures, but never forbidden-suffix files (e.g. synthetic
    # ``.eml`` samples used only by the developer pytest suite). The release
    # must stay ``.eml``-free so a real inbox message can never leak into a
    # package; the loud ``_safe_relative`` guard still protects everything that
    # IS shipped.
    files.update(
        _existing(
            path
            for path in (tests_dir / "fixtures").rglob("*")
            if path.is_file() and path.suffix.casefold() not in FORBIDDEN_SUFFIXES
        )
    )
    files.update(_existing([tests_dir / "offline_guard" / "sitecustomize.py"]))
    return sorted(files, key=lambda path: _safe_relative(path).casefold())


def _zip_write_bytes(archive: zipfile.ZipFile, relative: str, data: bytes) -> None:
    info = zipfile.ZipInfo(f"{ARCHIVE_FOLDER}/{relative}", FIXED_ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    info.create_system = 3
    archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def canonical_release_bytes(path: Path) -> bytes:
    """Return checkout-independent bytes for a source release entry."""
    data = path.read_bytes()
    suffix = path.suffix.casefold()
    if suffix not in CANONICAL_TEXT_SUFFIXES:
        return data
    normalized = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    if suffix in WINDOWS_CRLF_SUFFIXES:
        return normalized.replace(b"\n", b"\r\n")
    return normalized


def build_release(
    output_dir: Path,
    *,
    release_version: str = DEFAULT_RELEASE_VERSION,
    require_clean: bool = False,
) -> dict[str, object]:
    identity = source_identity()
    if require_clean and identity["source_worktree_dirty"]:
        raise RuntimeError("Refusing final release build from a dirty Git worktree")
    files = gather_release_files()
    entries = []
    payloads: list[tuple[str, bytes]] = []
    for path in files:
        relative = _safe_relative(path)
        data = canonical_release_bytes(path)
        entries.append({"path": relative, "bytes": len(data), "sha256": sha256_bytes(data)})
        payloads.append((relative, data))

    metadata = {
        "schema_version": 1,
        "product": "Tender Finder",
        "classification": "internal weekly beta",
        "release_version": release_version,
        **identity,
        "archive_root": ARCHIVE_FOLDER,
        "included_source_files": len(entries),
        "self_contained_executable": False,
        "first_run_install_required": True,
        "text_line_endings": "LF except .bat/.cmd CRLF",
    }
    included_manifest = "\n".join(
        f"{entry['sha256']}  {entry['bytes']:>10}  {entry['path']}" for entry in entries
    ) + "\n"
    excluded_summary = (
        "Tender Finder clean-release exclusions\n"
        "- version-control metadata (.git)\n"
        "- virtual environments (.venv, venv)\n"
        "- Codex/test/cache directories (.codex_tmp, .pytest_cache, __pycache__)\n"
        "- runtime outputs, run history, logs, manifests, and screenshots\n"
        "- user data, email content/state, browser profiles, and credentials\n"
        "- downloaded websites/source pages and historical generated outputs\n"
        "- temporary files, lock files, local environment files, and ZIP files\n"
        "- non-release historical development material\n"
    )

    generated = [
        ("RELEASE_METADATA.json", (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode("utf-8")),
        ("INCLUDED_FILES_MANIFEST.txt", included_manifest.encode("utf-8")),
        ("EXCLUDED_CATEGORY_SUMMARY.txt", excluded_summary.encode("utf-8")),
    ]

    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"Tender_Finder_{release_version}.zip"
    with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp", dir=output_dir) as handle:
        temp_path = Path(handle.name)
    try:
        with zipfile.ZipFile(temp_path, "w", allowZip64=True) as archive:
            for relative, data in payloads:
                _zip_write_bytes(archive, relative, data)
            for relative, data in generated:
                _zip_write_bytes(archive, relative, data)
        os.replace(temp_path, zip_path)
    finally:
        temp_path.unlink(missing_ok=True)

    zip_sha = sha256_file(zip_path)
    checksum_path = zip_path.with_suffix(zip_path.suffix + ".sha256")
    checksum_path.write_text(f"{zip_sha}  {zip_path.name}\n", encoding="utf-8", newline="\n")
    external_manifest = {
        **metadata,
        "zip_path": str(zip_path),
        "zip_bytes": zip_path.stat().st_size,
        "zip_sha256": zip_sha,
        "checksum_path": str(checksum_path),
        "archive_entries": len(payloads) + len(generated),
    }
    manifest_path = zip_path.with_suffix(".manifest.json")
    manifest_path.write_text(
        json.dumps(external_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    external_manifest["manifest_path"] = str(manifest_path)
    return external_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the deterministic Tender Finder clean source release.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(r"C:\tenderfinder_out\release"),
        help="External release-artifact directory.",
    )
    parser.add_argument("--release-version", default=DEFAULT_RELEASE_VERSION)
    parser.add_argument("--require-clean", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_release(
        args.output_dir,
        release_version=args.release_version,
        require_clean=args.require_clean,
    )
    print("CLEAN_RELEASE_BUILD: PASS")
    print(f"RELEASE_ZIP: {result['zip_path']}")
    print(f"RELEASE_SHA256: {result['zip_sha256']}")
    print(f"SOURCE_COMMIT: {result['source_commit_sha']}")
    print(f"SOURCE_WORKTREE_DIRTY: {result['source_worktree_dirty']}")
    print(f"RELEASE_MANIFEST: {result['manifest_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

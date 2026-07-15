#!/usr/bin/env python3
"""Verify Tender Finder clean-release ZIP structure, hashes, and CRC."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path, PurePosixPath


FORBIDDEN_PARTS = {
    ".git", ".venv", "venv", ".codex_tmp", ".pytest_cache", "__pycache__",
    "user_data", "demo_history", "raw_runs", "latest_verified_output",
}
FORBIDDEN_SUFFIXES = {
    ".pyc", ".pyo", ".log", ".tmp", ".eml", ".db", ".sqlite", ".sqlite3", ".zip",
}
REQUIRED_BASENAMES = {
    "Launch_TENDER_FINDER_GUI.bat",
    "setup_tenderfinder_environment.bat",
    "verify_package.bat",
    "requirements.txt",
    "README.md",
    "keywords.xlsx",
    "sources.csv",
    "all_live_review.xlsx",
    "tenderfinder_engine.py",
    "tenderfinder_launcher_gui.py",
    "tenderfinder_self_test.py",
    "RELEASE_METADATA.json",
    "INCLUDED_FILES_MANIFEST.txt",
    "EXCLUDED_CATEGORY_SUMMARY.txt",
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_release(zip_path: Path, extract_to: Path | None = None) -> dict[str, object]:
    zip_path = zip_path.expanduser().resolve()
    if not zip_path.is_file():
        raise FileNotFoundError(zip_path)
    with zipfile.ZipFile(zip_path, "r") as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            raise ValueError("ZIP contains duplicate entries")
        if archive.testzip() is not None:
            raise ValueError("ZIP CRC verification failed")
        roots = set()
        for name in names:
            pure = PurePosixPath(name)
            if pure.is_absolute() or ".." in pure.parts:
                raise ValueError(f"Unsafe ZIP path: {name}")
            if not pure.parts:
                raise ValueError("ZIP contains an empty path")
            roots.add(pure.parts[0])
            folded_parts = {part.casefold() for part in pure.parts}
            if FORBIDDEN_PARTS.intersection(folded_parts):
                raise ValueError(f"Forbidden directory in ZIP: {name}")
            if pure.suffix.casefold() in FORBIDDEN_SUFFIXES or pure.name.startswith("~$"):
                raise ValueError(f"Forbidden file in ZIP: {name}")
        if len(roots) != 1:
            raise ValueError(f"ZIP must contain exactly one top-level folder: {sorted(roots)}")
        basenames = {PurePosixPath(name).name for name in names}
        missing = REQUIRED_BASENAMES - basenames
        if missing:
            raise ValueError(f"ZIP is missing required files: {sorted(missing)}")

        root = next(iter(roots))
        metadata = json.loads(archive.read(f"{root}/RELEASE_METADATA.json"))
        manifest_text = archive.read(f"{root}/INCLUDED_FILES_MANIFEST.txt").decode("utf-8")
        manifest_rows = {}
        for line in manifest_text.splitlines():
            digest, size, relative = line.split(maxsplit=2)
            manifest_rows[relative] = (digest, int(size))
        for relative, (expected_digest, expected_size) in manifest_rows.items():
            data = archive.read(f"{root}/{relative}")
            if len(data) != expected_size or _sha256(data) != expected_digest:
                raise ValueError(f"Included-file manifest mismatch: {relative}")

        if extract_to is not None:
            extract_to = extract_to.expanduser().resolve()
            if extract_to.exists():
                raise FileExistsError(f"Extraction target already exists: {extract_to}")
            extract_to.mkdir(parents=True)
            archive.extractall(extract_to)
            extracted_root = extract_to / root
            for relative, (expected_digest, expected_size) in manifest_rows.items():
                path = extracted_root / Path(relative)
                data = path.read_bytes()
                if len(data) != expected_size or _sha256(data) != expected_digest:
                    raise ValueError(f"Extracted file mismatch: {relative}")

    return {
        "zip_path": str(zip_path),
        "zip_sha256": _sha256(zip_path.read_bytes()),
        "entries": len(names),
        "top_level_folder": next(iter(roots)),
        "source_commit_sha": metadata.get("source_commit_sha", ""),
        "source_worktree_dirty": metadata.get("source_worktree_dirty"),
        "extracted_root": str(extract_to / next(iter(roots))) if extract_to else "",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify a Tender Finder clean release ZIP.")
    parser.add_argument("zip_path", type=Path)
    parser.add_argument("--extract-to", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = verify_release(args.zip_path, args.extract_to)
    print("CLEAN_RELEASE_VERIFY: PASS")
    print(f"ZIP_SHA256: {result['zip_sha256']}")
    print(f"ENTRIES: {result['entries']}")
    print(f"SOURCE_COMMIT: {result['source_commit_sha']}")
    if result["extracted_root"]:
        print(f"EXTRACTED_ROOT: {result['extracted_root']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

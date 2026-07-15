from __future__ import annotations

import sys
import tempfile
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from build_clean_release import build_release, canonical_release_bytes  # noqa: E402
from verify_clean_release import verify_release  # noqa: E402


def test_allowlist_release_is_deterministic_and_clean() -> None:
    with tempfile.TemporaryDirectory(prefix="tenderfinder_package_test_") as temp:
        output = Path(temp) / "out"
        first = build_release(output, release_version="test-internal-beta")
        first_bytes = Path(first["zip_path"]).read_bytes()
        second = build_release(output, release_version="test-internal-beta")
        second_bytes = Path(second["zip_path"]).read_bytes()
        assert first_bytes == second_bytes
        assert first["zip_sha256"] == second["zip_sha256"]

        with zipfile.ZipFile(first["zip_path"], "r") as archive:
            names = [name.casefold() for name in archive.namelist()]
        forbidden = ("/.git/", "/.venv/", "/.codex_tmp/", "/__pycache__/", "/latest_verified_output/")
        assert not any(marker in name for marker in forbidden for name in names)
        assert not any(name.endswith((".pyc", ".log", ".eml", ".db", ".sqlite", ".zip")) for name in names)


def test_release_verifier_checks_crc_manifest_and_extraction() -> None:
    with tempfile.TemporaryDirectory(prefix="tenderfinder_package_verify_") as temp:
        base = Path(temp)
        result = build_release(base / "out", release_version="test-internal-beta")
        verified = verify_release(Path(result["zip_path"]), base / "extracted")
        assert verified["entries"] > 40
        extracted = Path(verified["extracted_root"])
        assert (extracted / "Launch_TENDER_FINDER_GUI.bat").is_file()
        assert not (extracted / ".venv").exists()
        assert not (extracted / ".git").exists()


def test_release_text_bytes_are_checkout_independent() -> None:
    with tempfile.TemporaryDirectory(prefix="tenderfinder_line_endings_") as temp:
        base = Path(temp)
        python_lf = base / "lf.py"
        python_crlf = base / "crlf.py"
        batch_lf = base / "lf.bat"
        batch_crlf = base / "crlf.bat"
        python_lf.write_bytes(b"print('ok')\n")
        python_crlf.write_bytes(b"print('ok')\r\n")
        batch_lf.write_bytes(b"@echo off\necho ok\n")
        batch_crlf.write_bytes(b"@echo off\r\necho ok\r\n")

        assert canonical_release_bytes(python_lf) == canonical_release_bytes(python_crlf)
        assert canonical_release_bytes(python_lf) == b"print('ok')\n"
        assert canonical_release_bytes(batch_lf) == canonical_release_bytes(batch_crlf)
        assert canonical_release_bytes(batch_lf) == b"@echo off\r\necho ok\r\n"


def main() -> int:
    tests = [
        test_allowlist_release_is_deterministic_and_clean,
        test_release_verifier_checks_crc_manifest_and_extraction,
        test_release_text_bytes_are_checkout_independent,
    ]
    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")
    print(f"Clean release packaging tests: {len(tests)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

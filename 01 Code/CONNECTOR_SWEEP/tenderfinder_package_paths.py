from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


PACKAGE_MARKERS = (
    "run_tenderfinder_demo.bat",
    "verify_package.bat",
    Path("01 Code") / "CONNECTOR_SWEEP",
    "inputs",
)


def _candidate_dirs(start: Path | None = None) -> list[Path]:
    candidates: list[Path] = []
    for raw in [start, Path(__file__).resolve(), Path(sys.argv[0]).resolve() if sys.argv and sys.argv[0] else None, Path.cwd()]:
        if raw is None:
            continue
        path = raw if raw.is_dir() else raw.parent
        if path not in candidates:
            candidates.append(path)
    return candidates


def _looks_like_package_root(path: Path) -> bool:
    for marker in PACKAGE_MARKERS:
        marker_path = path / marker
        if not marker_path.exists():
            return False
    return True


def detect_package_root(start: Path | None = None) -> Path:
    for candidate in _candidate_dirs(start):
        for path in [candidate, *candidate.parents]:
            if _looks_like_package_root(path):
                return path
    return Path(__file__).resolve().parents[2]


def user_data_root(root: Path | None = None) -> Path:
    return detect_package_root(root) / "user_data"


def email_alerts_root(root: Path | None = None) -> Path:
    return user_data_root(root) / "email_alerts"


def email_inbox_dir(root: Path | None = None) -> Path:
    return email_alerts_root(root) / "inbox"


def email_processed_dir(root: Path | None = None) -> Path:
    return email_alerts_root(root) / "processed"


def email_rejected_dir(root: Path | None = None) -> Path:
    return email_alerts_root(root) / "rejected"


def email_logs_dir(root: Path | None = None) -> Path:
    return email_alerts_root(root) / "logs"


def email_import_state_path(root: Path | None = None) -> Path:
    return email_alerts_root(root) / "import_state.json"


def tenderfinder_user_config_path(root: Path | None = None) -> Path:
    return user_data_root(root) / "tenderfinder_user_config.json"


def ensure_email_alert_dirs(root: Path | None = None) -> dict[str, Path]:
    package_root = detect_package_root(root)
    dirs = {
        "package_root": package_root,
        "user_data": user_data_root(package_root),
        "inbox": email_inbox_dir(package_root),
        "processed": email_processed_dir(package_root),
        "rejected": email_rejected_dir(package_root),
        "logs": email_logs_dir(package_root),
    }
    for key, path in dirs.items():
        if key == "package_root":
            continue
        path.mkdir(parents=True, exist_ok=True)
    readmes = {
        "inbox": "Save or copy approved .eml alert files into this folder, then run Test Email Import.\n",
        "processed": "Reserved for an optional future copy-only processed-mail workflow. TENDER_FINDER does not move user emails in this patch.\n",
        "rejected": "Reserved for optional future rejected-mail copies. TENDER_FINDER does not move user emails in this patch.\n",
        "logs": "Dry-run and import logs are written here. Real emails are never copied into this folder.\n",
    }
    for key, text in readmes.items():
        readme = dirs[key] / "README.md"
        if not readme.exists():
            readme.write_text(text, encoding="utf-8")
    return dirs


def load_user_config(root: Path | None = None) -> dict[str, Any]:
    path = tenderfinder_user_config_path(root)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_user_config(updates: dict[str, Any], root: Path | None = None) -> Path:
    ensure_email_alert_dirs(root)
    path = tenderfinder_user_config_path(root)
    config = load_user_config(root)
    config.update(updates)
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return path

"""Runtime-state isolation and small manifest helpers for TENDER_FINDER.

The package directory contains code and founder-edited configuration only.
History, cached user-master state, self-test output, and run manifests belong
under the selected output/state root (normally ``C:\\tenderfinder_out``).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from tenderfinder_package_paths import detect_package_root


STATE_ROOT_ENV_VAR = "TENDER_FINDER_STATE_ROOT"
RUN_MODE_ENV_VAR = "TENDER_FINDER_RUN_MODE"
_ATOMIC_JSON_WRITE_LOCK = threading.Lock()


class RuntimeStateError(RuntimeError):
    """Raised when a runtime state path could contaminate the package."""


def default_output_root() -> Path:
    if sys.platform.startswith("win"):
        return Path(r"C:\tenderfinder_out")
    return Path.home() / "tenderfinder_out"


def safe_component(value: str, fallback: str = "cli") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(value or "").strip()).strip("._")
    return cleaned[:80] or fallback


def _is_below(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def resolve_state_root(
    explicit: str | Path | None = None,
    *,
    mode: str | None = None,
    package_root: str | Path | None = None,
) -> Path:
    raw = str(explicit or os.environ.get(STATE_ROOT_ENV_VAR, "")).strip()
    run_mode = safe_component(mode or os.environ.get(RUN_MODE_ENV_VAR, "cli"))
    resolved = (
        Path(raw).expanduser().resolve()
        if raw
        else (default_output_root() / "state" / run_mode).resolve()
    )
    package = detect_package_root(Path(package_root).resolve() if package_root else None).resolve()
    if _is_below(resolved, package):
        raise RuntimeStateError(
            f"Runtime state must be outside the package repository: {resolved}"
        )
    return resolved


def user_settings_root(
    *,
    package_root: str | Path | None = None,
    create: bool = False,
) -> Path:
    """Return the external root for persistent operator settings.

    An engine subprocess uses its explicitly supplied state root, which keeps
    Self-Test isolated. A directly launched GUI/CLI without that environment
    uses one stable shared-user state root instead of writing into the package.
    """
    explicit = os.environ.get(STATE_ROOT_ENV_VAR, "").strip()
    selected = explicit or str(default_output_root() / "state" / "user")
    root = resolve_state_root(selected, mode="user", package_root=package_root)
    settings = root / "settings"
    if create:
        settings.mkdir(parents=True, exist_ok=True)
    return settings


@dataclass(frozen=True)
class RuntimePaths:
    root: Path
    history: Path
    latest_user_master: Path
    settings: Path


def runtime_paths(
    explicit: str | Path | None = None,
    *,
    mode: str | None = None,
    package_root: str | Path | None = None,
    create: bool = True,
) -> RuntimePaths:
    root = resolve_state_root(explicit, mode=mode, package_root=package_root)
    paths = RuntimePaths(
        root=root,
        history=root / "history",
        latest_user_master=root / "latest_user_master.xlsx",
        settings=root / "settings",
    )
    if create:
        paths.history.mkdir(parents=True, exist_ok=True)
        paths.settings.mkdir(parents=True, exist_ok=True)
    return paths


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_json(path: str | Path, payload: dict[str, Any]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with _ATOMIC_JSON_WRITE_LOCK:
        temporary: Path | None = None
        try:
            # A unique same-directory temporary file keeps staging names from
            # colliding. The process lock also avoids WinError 5 when two GUI
            # worker threads replace the same target simultaneously.
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=target.parent,
                prefix=f".{target.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temporary = Path(handle.name)
                handle.write(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            # Closing before os.replace is required on Windows.
            os.replace(temporary, target)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
    return target


def timestamp_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")

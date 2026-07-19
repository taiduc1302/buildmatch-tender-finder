"""Display-agnostic TENDER_FINDER service API.

Tkinter, a future web endpoint, and command-line launchers can all use this
module to prepare and run the same engine command. It owns preflight,
mode-specific state isolation, streaming process execution, and the run
manifest; it never imports or creates GUI widgets.
"""
from __future__ import annotations

import os
import json
import re
import subprocess
import sys
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable

from tenderfinder_keywords_config import (
    KEYWORDS_STATE_ROOT_ENV_VAR,
    load_keywords_config,
    resolve_keywords_path,
)
from tenderfinder_package_paths import detect_package_root
from tenderfinder_runtime import (
    RUN_MODE_ENV_VAR,
    STATE_ROOT_ENV_VAR,
    atomic_write_json,
    default_output_root,
    runtime_paths,
    sha256_file,
    timestamp_now,
)
from tenderfinder_source_registry import (
    load_source_rows,
    load_tender_sources,
    registry_summary,
    resolve_registry_path,
    source_configuration_errors,
    source_is_runtime_eligible,
    source_readiness_errors,
    source_skip_reason,
    update_source_test_metadata,
)
from tenderfinder_source_testing import (
    ADAPTER_FIXTURES,
    fixture_catalog,
    run_offline_adapter_fixture,
)


MODE_LIVE = "live"
MODE_OFFLINE = "offline"
MODE_SELF_TEST = "self_test"
RUN_MODES = frozenset({MODE_LIVE, MODE_OFFLINE, MODE_SELF_TEST})
PAUSE_EXIT_CODE = 86

SELF_TEST_SCRIPTS = (
    ("stabilization_security", "test_stabilization_security.py"),
    ("source_registry_and_offline_fixtures", "test_source_registry_stabilization.py"),
    ("keyword_configuration", "test_keywords_config.py"),
    ("rescore_always_end_to_end", "test_rescore_always_e2e.py"),
    ("standalone_trust_safeguards", "test_standalone_weekly_release.py"),
    ("engine_contract", "test_engine_contract.py"),
    ("launcher_portability", "test_launcher_portability.py"),
    ("offline_ci_workflow", "test_offline_ci_workflow.py"),
    ("clean_release_packaging", "test_clean_release_packaging.py"),
    ("launcher_headless_logic", "test_launcher_gui.py"),
    ("routing_gates", "test_routing_gates.py"),
    ("manual_outreach_persistence", "test_outreach_persistence.py"),
    ("review_workbook_discovery", "test_launcher_review_xlsx_consistency.py"),
    ("tender_signal_routing", "test_tender_signal_routing.py"),
)

SELF_TEST_INTENTIONAL_EXCLUSIONS = (
    {
        "name": "controlled_live_source_proof",
        "status": "EXCLUDED_LIVE",
        "reason": "Self-Test is strictly offline; the controlled one-or-two-source live proof is a separate release gate.",
    },
    {
        "name": "visual_gui_black_box",
        "status": "EXCLUDED_DISPLAY",
        "reason": "Automated Self-Test is headless; double-click visual acceptance and screenshots are a separate release gate.",
    },
    {
        "name": "legacy_agent2_live_execution",
        "status": "EXCLUDED_FROZEN",
        "reason": "tenderfinder_agent2.py is frozen and verified by static isolation only.",
    },
)


@dataclass(frozen=True)
class RunRequest:
    review_xlsx: Path
    out_dir: Path
    mode: str
    python_exe: str = sys.executable
    email_intake: bool = True
    email_import_path: str = ""
    keywords_path: Path | None = None
    sources_path: Path | None = None
    state_root: Path | None = None
    keywords_state_root: Path | None = None
    run_id: str = ""
    source_ids: tuple[str, ...] = ()
    offline: bool | None = None
    self_test: bool = False

    def to_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))


@dataclass(frozen=True)
class RunPlan:
    run_id: str
    mode: str
    root: Path
    out_dir: Path
    state_root: Path
    keywords_state_root: Path
    review_xlsx: Path
    keywords_path: Path
    keywords_effective_path: Path
    keywords_source_kind: str
    keywords_validation_errors: tuple[str, ...]
    sources_path: Path
    source_ids: tuple[str, ...]
    offline: bool
    self_test: bool
    command: tuple[str, ...]
    manifest_path: Path


@dataclass(frozen=True)
class EngineRunResult:
    passed: bool
    return_code: int
    status: str
    run_id: str
    out_dir: Path
    manifest_path: Path
    artifacts: tuple[str, ...]
    started_at: str = ""
    finished_at: str = ""
    source_counts: dict[str, Any] = field(default_factory=dict)
    record_counts: dict[str, Any] = field(default_factory=dict)
    score_bucket_summaries: dict[str, Any] = field(default_factory=dict)
    output_paths: dict[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    test_totals: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def new_run_id(mode: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{mode}_{stamp}_{uuid.uuid4().hex[:8]}"


def _read_commit(root: Path) -> str:
    head = root / ".git" / "HEAD"
    try:
        value = head.read_text(encoding="utf-8").strip()
        if value.startswith("ref:"):
            ref_path = root / ".git" / value.split(":", 1)[1].strip()
            if ref_path.exists():
                return ref_path.read_text(encoding="utf-8").strip()
        return value
    except OSError:
        return "snapshot-no-git-marker"


def prepare_run(request: RunRequest, *, root: Path | None = None) -> RunPlan:
    mode = str(request.mode).strip().casefold()
    if mode not in RUN_MODES:
        raise ValueError(f"mode must be one of {', '.join(sorted(RUN_MODES))}")
    expected_offline = mode != MODE_LIVE
    if request.offline is not None and bool(request.offline) != expected_offline:
        raise ValueError(f"offline={request.offline} conflicts with run mode '{mode}'")
    if request.self_test and mode != MODE_SELF_TEST:
        raise ValueError("self_test=True requires mode='self_test'")
    package_root = detect_package_root(root).resolve()
    review = Path(request.review_xlsx).expanduser().resolve()
    if not review.exists():
        raise FileNotFoundError(f"review workbook not found: {review}")
    keywords = resolve_keywords_path(request.keywords_path, package_root)
    sources = resolve_registry_path(request.sources_path, package_root)

    run_id = request.run_id.strip() or new_run_id(mode)
    isolated_state = request.state_root
    if isolated_state is None:
        if mode == MODE_SELF_TEST:
            isolated_state = default_output_root() / "state" / MODE_SELF_TEST / run_id
        else:
            isolated_state = default_output_root() / "state" / mode
    paths = runtime_paths(isolated_state, mode=mode, package_root=package_root, create=True)
    keyword_state_root = (
        Path(request.keywords_state_root).expanduser().resolve()
        if request.keywords_state_root is not None
        else paths.root
        if mode == MODE_SELF_TEST or request.state_root is not None
        else (default_output_root() / "state" / "user").resolve()
    )
    keyword_config = load_keywords_config(
        keywords,
        root=package_root,
        state_root=keyword_state_root,
        force_reload=True,
    )
    source_rows = load_source_rows(sources)
    source_ids = tuple(
        dict.fromkeys(
            str(source_id).strip().casefold()
            for source_id in request.source_ids
            if str(source_id).strip()
        )
    )
    if source_ids:
        by_id = {row["source_id"]: row for row in source_rows}
        unknown = [source_id for source_id in source_ids if source_id not in by_id]
        if unknown:
            raise ValueError(f"unknown source selection: {', '.join(unknown)}")
        unsupported = [
            source_id
            for source_id in source_ids
            if by_id[source_id].get("track") != "tender"
            or not source_is_runtime_eligible(by_id[source_id])
        ]
        if unsupported:
            raise ValueError(
                "selected source(s) are not active runtime-eligible tender sources: "
                + ", ".join(unsupported)
            )
    out_dir = Path(request.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    script = package_root / "01 Code" / "CONNECTOR_SWEEP" / "tenderfinder_demo_three_buckets.py"
    if not script.exists():
        raise FileNotFoundError(f"engine script not found: {script}")

    command = [
        request.python_exe,
        "-u",
        str(script),
        "--review-xlsx", str(review),
        "--out-dir", str(out_dir),
        "--keywords-config", str(keywords),
        "--sources-config", str(sources),
        "--state-root", str(paths.root),
        "--keywords-state-root", str(Path(keyword_state_root).resolve()),
        "--run-id", run_id,
        "--run-mode", mode,
    ]
    for source_id in source_ids:
        command.extend(["--source-id", source_id])
    if request.email_intake:
        command.append("--email-intake")
    if request.email_import_path.strip():
        command.extend(["--email-import-path", request.email_import_path.strip()])
    if mode != MODE_LIVE:
        command.append("--no-fetch")

    return RunPlan(
        run_id=run_id,
        mode=mode,
        root=package_root,
        out_dir=out_dir,
        state_root=paths.root,
        keywords_state_root=Path(keyword_state_root).resolve(),
        review_xlsx=review,
        keywords_path=keywords,
        keywords_effective_path=keyword_config.path,
        keywords_source_kind=keyword_config.source_kind,
        keywords_validation_errors=keyword_config.validation_errors,
        sources_path=sources,
        source_ids=source_ids,
        offline=expected_offline,
        self_test=mode == MODE_SELF_TEST,
        command=tuple(command),
        manifest_path=out_dir / "run_manifest.json",
    )


def build_command_for_paths(
    review_xlsx: Path,
    out_dir: Path,
    *,
    fast_mode: bool,
    email_import_path: str = "",
    python_exe: str | None = None,
    mode: str | None = None,
    root: Path | None = None,
) -> list[str]:
    """Build a launch command without touching the filesystem.

    GUI callers use this while editing paths, before a workbook necessarily
    exists.  The strict preflight remains in :func:`plan_from_command`, which
    is always called by the actual engine runner.
    """
    selected_mode = mode or (MODE_OFFLINE if fast_mode else MODE_LIVE)
    selected_mode = str(selected_mode).strip().casefold()
    if selected_mode not in RUN_MODES:
        raise ValueError(f"mode must be one of {', '.join(sorted(RUN_MODES))}")

    package_root = detect_package_root(root).resolve()
    run_id = new_run_id(selected_mode)
    if selected_mode == MODE_SELF_TEST:
        state_root = default_output_root() / "state" / MODE_SELF_TEST / run_id
        keywords_state_root = state_root
    else:
        state_root = default_output_root() / "state" / selected_mode
        keywords_state_root = default_output_root() / "state" / "user"
    script = package_root / "01 Code" / "CONNECTOR_SWEEP" / "tenderfinder_demo_three_buckets.py"
    sources = resolve_registry_path(None, package_root)
    keywords = resolve_keywords_path(None, package_root)
    command = [
        python_exe or sys.executable,
        "-u",
        str(script),
        "--review-xlsx", str(Path(review_xlsx).expanduser().resolve()),
        "--out-dir", str(Path(out_dir).expanduser().resolve()),
        "--keywords-config", str(keywords),
        "--sources-config", str(sources),
        "--state-root", str(state_root.resolve()),
        "--keywords-state-root", str(keywords_state_root.resolve()),
        "--run-id", run_id,
        "--run-mode", selected_mode,
        "--email-intake",
    ]
    if email_import_path.strip():
        command.extend(["--email-import-path", email_import_path.strip()])
    if selected_mode != MODE_LIVE:
        command.append("--no-fetch")
    return command


def plan_from_command(command: Iterable[str], *, root: Path | None = None) -> RunPlan:
    values = list(command)

    def option(name: str, default: str = "") -> str:
        try:
            return values[values.index(name) + 1]
        except (ValueError, IndexError):
            return default

    mode = option("--run-mode") or (MODE_OFFLINE if "--no-fetch" in values else MODE_LIVE)
    run_id = option("--run-id") or new_run_id(mode)
    selected_sources = tuple(
        values[index + 1]
        for index, value in enumerate(values[:-1])
        if value == "--source-id"
    )
    request = RunRequest(
        review_xlsx=Path(option("--review-xlsx")),
        out_dir=Path(option("--out-dir")),
        mode=mode,
        python_exe=values[0] if values else sys.executable,
        email_intake="--email-intake" in values,
        email_import_path=option("--email-import-path"),
        keywords_path=Path(option("--keywords-config")) if option("--keywords-config") else None,
        sources_path=Path(option("--sources-config")) if option("--sources-config") else None,
        state_root=Path(option("--state-root")) if option("--state-root") else None,
        keywords_state_root=(
            Path(option("--keywords-state-root"))
            if option("--keywords-state-root")
            else None
        ),
        run_id=run_id,
        source_ids=selected_sources,
        offline="--no-fetch" in values,
        self_test=mode == MODE_SELF_TEST,
    )
    plan = prepare_run(request, root=root)
    # Preserve any caller-specific switches while still using the validated
    # request metadata and manifest path.
    return RunPlan(**{**asdict(plan), "command": tuple(values)})


def _artifact_list(out_dir: Path) -> tuple[str, ...]:
    if not out_dir.exists():
        return ()
    return tuple(
        str(path.relative_to(out_dir))
        for path in sorted(out_dir.rglob("*"))
        if path.is_file() and path.name != "engine.log"
    )


def _safe_sha256(path: Path) -> str:
    try:
        return sha256_file(path) if path.exists() else ""
    except OSError:
        return ""


def _run_output_summary(lines: Iterable[str]) -> tuple[dict[str, int], dict[str, int]]:
    text = "\n".join(lines)
    record_counts: dict[str, int] = {}
    buckets: dict[str, int] = {}
    bid_now = re.search(
        r"BID NOW total / civil / open civil:\s*(\d+)\s*/\s*(\d+)\s*/\s*(\d+)",
        text,
        re.IGNORECASE,
    )
    if bid_now:
        record_counts.update(
            {
                "bid_now_total": int(bid_now.group(1)),
                "bid_now_civil": int(bid_now.group(2)),
                "bid_now_open_civil": int(bid_now.group(3)),
            }
        )
        buckets["bid_now"] = int(bid_now.group(1))
    later = re.search(
        r"BID LATER / WATCH / ANALYZED:\s*(\d+)\s*/\s*(\d+)\s*/\s*(\d+)",
        text,
        re.IGNORECASE,
    )
    if later:
        record_counts.update(
            {
                "bid_later": int(later.group(1)),
                "watchlist": int(later.group(2)),
                "analyzed": int(later.group(3)),
            }
        )
        buckets.update(
            {
                "bid_later": int(later.group(1)),
                "watchlist": int(later.group(2)),
            }
        )
    return record_counts, buckets


def _diagnostic_lines(lines: Iterable[str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    warnings: list[str] = []
    errors: list[str] = []
    for line in lines:
        stripped = str(line).strip()
        upper = stripped.upper()
        if upper.startswith(("ERROR", "TRACEBACK")):
            errors.append(stripped)
        elif upper.startswith(("WARNING", "WARN")) or "USER_ACTION_REQUIRED" in upper:
            warnings.append(stripped)
    return tuple(warnings[-100:]), tuple(errors[-100:])


def _base_manifest(plan: RunPlan) -> dict[str, Any]:
    source_registry = registry_summary(plan.sources_path)
    source_counts = {
        "configured": source_registry.get("total", 0),
        "enabled": source_registry.get("active", source_registry.get("enabled", 0)),
        "runtime_eligible": source_registry.get("runtime_eligible", 0),
        "selected": len(plan.source_ids),
    }
    return {
        "schema_version": 2,
        "run_id": plan.run_id,
        "mode": plan.mode,
        "offline": plan.mode != MODE_LIVE,
        "status": "RUNNING",
        "started_at": timestamp_now(),
        "finished_at": None,
        "return_code": None,
        "package_root": str(plan.root),
        "code_commit": _read_commit(plan.root),
        "python": sys.version,
        "command": list(plan.command),
        "review_xlsx": str(plan.review_xlsx),
        "review_sha256": sha256_file(plan.review_xlsx),
        "keywords_xlsx": str(plan.keywords_path),
        "keywords_sha256": _safe_sha256(plan.keywords_path),
        "keywords_effective_xlsx": str(plan.keywords_effective_path),
        "keywords_effective_sha256": _safe_sha256(plan.keywords_effective_path),
        "keywords_source_kind": plan.keywords_source_kind,
        "keywords_validation_errors": list(plan.keywords_validation_errors),
        "keywords_state_root": str(plan.keywords_state_root),
        "sources_csv": str(plan.sources_path),
        "sources_sha256": sha256_file(plan.sources_path),
        "source_registry": source_registry,
        "source_selection": list(plan.source_ids),
        "source_counts": source_counts,
        "state_root": str(plan.state_root),
        "out_dir": str(plan.out_dir),
        "request": {
            "offline": plan.offline,
            "self_test": plan.self_test,
            "mode": plan.mode,
        },
        "record_counts": {},
        "score_bucket_summaries": {},
        "warnings": [],
        "errors": [],
        "test_totals": {},
        "output_paths": {},
        "artifacts": [],
    }


def run_plan(
    plan: RunPlan,
    *,
    on_line: Callable[[str], None] | None = None,
    started_callback: Callable[[subprocess.Popen[str]], None] | None = None,
    environment_overrides: dict[str, str] | None = None,
) -> EngineRunResult:
    manifest = _base_manifest(plan)
    atomic_write_json(plan.manifest_path, manifest)
    log_path = plan.out_dir / "engine.log"
    env = os.environ.copy()
    env.update(
        {
            "PYTHONUTF8": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "TENDER_FINDER_DEMO_NO_OPEN": "1",
            RUN_MODE_ENV_VAR: plan.mode,
            STATE_ROOT_ENV_VAR: str(plan.state_root),
            KEYWORDS_STATE_ROOT_ENV_VAR: str(plan.keywords_state_root),
            "TENDER_FINDER_KEYWORDS_CONFIG": str(plan.keywords_path),
            "TENDER_FINDER_SOURCES_CONFIG": str(plan.sources_path),
        }
    )
    if environment_overrides:
        env.update({str(key): str(value) for key, value in environment_overrides.items()})
    lines: list[str] = []

    def emit(line: str) -> None:
        lines.append(line)
        if on_line:
            on_line(line)

    try:
        proc = subprocess.Popen(
            list(plan.command),
            cwd=str(plan.root),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        if started_callback:
            started_callback(proc)
        assert proc.stdout is not None
        for raw in proc.stdout:
            emit(raw.rstrip("\r\n"))
        proc.wait()
        return_code = int(proc.returncode or 0)
    except Exception as exc:
        emit(f"ERROR: engine could not start or monitor the run: {exc}")
        return_code = -1

    log_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    status = "PASS" if return_code == 0 else "PAUSED" if return_code == PAUSE_EXIT_CODE else "FAIL"
    artifacts = _artifact_list(plan.out_dir)
    summary_lines = list(lines)
    for report_name in ("DEMO_BUILD_REPORT.md", "demo_summary.txt"):
        report_path = plan.out_dir / report_name
        try:
            if report_path.exists():
                summary_lines.extend(report_path.read_text(encoding="utf-8", errors="replace").splitlines())
        except OSError:
            pass
    record_counts, bucket_summaries = _run_output_summary(summary_lines)
    warnings, errors = _diagnostic_lines(lines)
    if return_code not in (0, PAUSE_EXIT_CODE) and not errors:
        errors = (f"Engine process exited with return code {return_code}.",)
    finished_at = timestamp_now()
    output_paths = {
        "out_dir": str(plan.out_dir),
        "manifest": str(plan.manifest_path),
        "engine_log": str(log_path),
        "artifacts": [str(plan.out_dir / artifact) for artifact in artifacts],
    }
    manifest.update(
        {
            "status": status,
            "finished_at": finished_at,
            "return_code": return_code,
            "artifacts": list(artifacts),
            "log": str(log_path),
            "record_counts": record_counts,
            "score_bucket_summaries": bucket_summaries,
            "warnings": list(warnings),
            "errors": list(errors),
            "output_paths": output_paths,
        }
    )
    atomic_write_json(plan.manifest_path, manifest)
    return EngineRunResult(
        passed=return_code == 0,
        return_code=return_code,
        status=status,
        run_id=plan.run_id,
        out_dir=plan.out_dir,
        manifest_path=plan.manifest_path,
        artifacts=artifacts,
        started_at=str(manifest.get("started_at", "")),
        finished_at=finished_at,
        source_counts=dict(manifest.get("source_counts", {})),
        record_counts=record_counts,
        score_bucket_summaries=bucket_summaries,
        output_paths=output_paths,
        warnings=warnings,
        errors=errors,
        test_totals={},
    )


def run_command(
    command: Iterable[str],
    *,
    root: Path | None = None,
    on_line: Callable[[str], None] | None = None,
    started_callback: Callable[[subprocess.Popen[str]], None] | None = None,
) -> EngineRunResult:
    return run_plan(
        plan_from_command(command, root=root),
        on_line=on_line,
        started_callback=started_callback,
    )


def prepare_self_test(
    *,
    root: Path | None = None,
    output_root: Path | None = None,
    python_exe: str | None = None,
) -> RunPlan:
    package_root = detect_package_root(root).resolve()
    run_id = new_run_id(MODE_SELF_TEST)
    out_dir = (output_root or default_output_root()) / "self_test" / run_id
    review = package_root / "inputs" / "all_live_review.xlsx"
    return prepare_run(
        RunRequest(
            review_xlsx=review,
            out_dir=out_dir,
            mode=MODE_SELF_TEST,
            python_exe=python_exe or sys.executable,
            email_intake=True,
            run_id=run_id,
            offline=True,
            self_test=True,
        ),
        root=package_root,
    )


_TEST_MARKER_RE = re.compile(r"^\[(PASS|FAIL|SKIP|NOT TESTED)\]\s*", re.IGNORECASE)


def _test_marker_totals(lines: Iterable[str], return_code: int) -> dict[str, int]:
    totals = {"passed": 0, "failed": 0, "skipped": 0, "not_tested_fixture": 0}
    for line in lines:
        match = _TEST_MARKER_RE.match(str(line).strip())
        if not match:
            continue
        marker = match.group(1).upper()
        if marker == "PASS":
            totals["passed"] += 1
        elif marker == "FAIL":
            totals["failed"] += 1
        elif marker == "SKIP":
            totals["skipped"] += 1
        else:
            totals["not_tested_fixture"] += 1
    if return_code != 0 and totals["failed"] == 0:
        totals["failed"] = 1
    elif return_code == 0 and not any(totals.values()):
        totals["passed"] = 1
    return totals


def _git_worktree_status(root: Path) -> str | None:
    if not (root / ".git").exists():
        return None
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return completed.stdout if completed.returncode == 0 else None


def _protected_release_hashes(root: Path) -> dict[str, str]:
    paths = {
        "canonical_keywords": root / "config" / "keywords.xlsx",
        "canonical_sources": root / "config" / "sources.csv",
        "frozen_agent2": root / "01 Code" / "tenderfinder_agent2.py",
        "canonical_launcher": root / "Launch_TENDER_FINDER_GUI.bat",
    }
    return {name: _safe_sha256(path) for name, path in paths.items()}


def run_self_test(
    *,
    root: Path | None = None,
    output_root: Path | None = None,
    on_line: Callable[[str], None] | None = None,
    started_callback: Callable[[subprocess.Popen[str]], None] | None = None,
) -> EngineRunResult:
    """Run the one shared, strictly offline package health suite.

    Both the desktop GUI and ``verify_package.bat`` call this function.  It
    runs focused script checks first, then the real end-to-end pipeline with
    ``--no-fetch`` in unique state, and records every PASS/FAIL/exclusion in
    the same manifest.
    """
    package_root = detect_package_root(root).resolve()
    protected_before = _protected_release_hashes(package_root)
    git_status_before = _git_worktree_status(package_root)
    plan = prepare_self_test(root=package_root, output_root=output_root)
    all_lines: list[str] = []
    checks: list[dict[str, Any]] = []
    totals = {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "intentionally_excluded": len(SELF_TEST_INTENTIONAL_EXCLUSIONS),
        "not_tested_fixture": 0,
    }
    exclusions = list(SELF_TEST_INTENTIONAL_EXCLUSIONS)

    def emit(line: str) -> None:
        all_lines.append(line)
        if on_line:
            on_line(line)

    emit(f"SELF_TEST_RUN_ID: {plan.run_id}")
    emit("SELF_TEST_NETWORK_POLICY: OFFLINE_ONLY (process-wide DNS/socket deny guard + --no-fetch)")
    tests_dir = plan.root / "01 Code" / "CONNECTOR_SWEEP" / "tests"
    guard_dir = tests_dir / "offline_guard"
    network_guard_log = plan.out_dir / "network_attempts.log"
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "").strip()
    env.update(
        {
            "PYTHONUTF8": "1",
            "TENDER_FINDER_GUI_SKIP_E2E": "1",
            "TENDER_FINDER_OFFLINE_ONLY": "1",
            RUN_MODE_ENV_VAR: MODE_SELF_TEST,
            STATE_ROOT_ENV_VAR: str(plan.state_root),
            KEYWORDS_STATE_ROOT_ENV_VAR: str(plan.keywords_state_root),
            "TENDER_FINDER_KEYWORDS_CONFIG": str(plan.keywords_path),
            "TENDER_FINDER_SOURCES_CONFIG": str(plan.sources_path),
            "TENDER_FINDER_NETWORK_GUARD_LOG": str(network_guard_log),
            "TENDER_FINDER_OUTPUT_ROOT": str(plan.out_dir / "isolated_gui_outputs"),
            "PYTHONPATH": str(guard_dir)
            + (os.pathsep + existing_pythonpath if existing_pythonpath else ""),
        }
    )

    guard_probe = subprocess.run(
        [
            plan.command[0],
            "-c",
            "import socket; raise SystemExit(0 if socket.socket.__name__ == 'OfflineBlockedSocket' else 1)",
        ],
        cwd=str(plan.root),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )
    guard_passed = guard_probe.returncode == 0
    checks.append(
        {
            "name": "offline_network_guard_installed",
            "status": "PASS" if guard_passed else "FAIL",
            "return_code": guard_probe.returncode,
            "details": (guard_probe.stdout + guard_probe.stderr).strip(),
        }
    )
    totals["passed" if guard_passed else "failed"] += 1
    emit(
        "SELF_TEST_CHECK_"
        + ("PASS" if guard_passed else "FAIL")
        + ": offline_network_guard_installed"
    )

    for check_name, script_name in SELF_TEST_SCRIPTS:
        script = tests_dir / script_name
        started = time.perf_counter()
        emit(f"SELF_TEST_CHECK_START: {check_name} ({script_name})")
        output_lines: list[str] = []
        return_code = -1
        try:
            proc = subprocess.Popen(
                [plan.command[0], "-u", str(script)],
                cwd=str(plan.root),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
            if started_callback:
                started_callback(proc)
            assert proc.stdout is not None
            for raw in proc.stdout:
                line = raw.rstrip("\r\n")
                output_lines.append(line)
                emit(line)
            proc.wait()
            return_code = int(proc.returncode or 0)
        except Exception as exc:
            output_lines.append(f"Could not run check: {exc}")
            emit(f"SELF_TEST_CHECK_ERROR: {check_name}: {exc}")
        marker_totals = _test_marker_totals(output_lines, return_code)
        for key in ("passed", "failed", "skipped", "not_tested_fixture"):
            totals[key] += marker_totals[key]
        status = (
            "FAIL"
            if return_code != 0
            else "PASS"
            if marker_totals["passed"]
            else "SKIP"
            if marker_totals["skipped"]
            else "NOT_TESTED_NO_FIXTURE"
            if marker_totals["not_tested_fixture"]
            else "PASS"
        )
        elapsed = round(time.perf_counter() - started, 3)
        checks.append(
            {
                "name": check_name,
                "script": str(script),
                "status": status,
                "return_code": return_code,
                "elapsed_seconds": elapsed,
                "totals": marker_totals,
                "output_tail": output_lines[-20:],
            }
        )
        emit(f"SELF_TEST_CHECK_{status}: {check_name} return_code={return_code} elapsed={elapsed:.3f}s")

    emit("SELF_TEST_CHECK_START: offline_end_to_end_pipeline")
    pipeline_result = run_plan(
        plan,
        on_line=emit,
        started_callback=started_callback,
        environment_overrides=env,
    )
    checks.append(
        {
            "name": "offline_end_to_end_pipeline",
            "script": str(plan.command[2]),
            "status": "PASS" if pipeline_result.passed else "FAIL",
            "return_code": pipeline_result.return_code,
            "manifest": str(pipeline_result.manifest_path),
        }
    )
    emit(
        "SELF_TEST_CHECK_"
        + ("PASS" if pipeline_result.passed else "FAIL")
        + f": offline_end_to_end_pipeline return_code={pipeline_result.return_code}"
    )
    totals["passed" if pipeline_result.passed else "failed"] += 1

    missing_fixtures = [
        adapter
        for adapter, path in fixture_catalog(root=plan.root).items()
        if adapter in ADAPTER_FIXTURES and not path.is_file()
    ]
    for adapter in missing_fixtures:
        checks.append(
            {
                "name": f"offline_fixture_{adapter}",
                "status": "NOT_TESTED_NO_FIXTURE",
                "reason": "Required maintained adapter fixture is missing.",
            }
        )
        totals["not_tested_fixture"] += 1
        totals["failed"] += 1

    network_attempts = ""
    try:
        if network_guard_log.exists():
            network_attempts = network_guard_log.read_text(
                encoding="utf-8", errors="replace"
            ).strip()
    except OSError as exc:
        network_attempts = f"Could not read network guard log: {exc}"
    network_clean = not network_attempts
    checks.append(
        {
            "name": "zero_network_attempts",
            "status": "PASS" if network_clean else "FAIL",
            "log": str(network_guard_log),
            "attempts": network_attempts.splitlines()[:20],
        }
    )
    totals["passed" if network_clean else "failed"] += 1
    emit(
        "SELF_TEST_CHECK_"
        + ("PASS" if network_clean else "FAIL")
        + ": zero_network_attempts"
    )

    protected_after = _protected_release_hashes(plan.root)
    for name, before_hash in protected_before.items():
        unchanged = bool(before_hash) and protected_after.get(name) == before_hash
        checks.append(
            {
                "name": f"protected_file_unchanged_{name}",
                "status": "PASS" if unchanged else "FAIL",
                "before_sha256": before_hash,
                "after_sha256": protected_after.get(name, ""),
            }
        )
        totals["passed" if unchanged else "failed"] += 1
        emit(
            "SELF_TEST_CHECK_"
            + ("PASS" if unchanged else "FAIL")
            + f": protected_file_unchanged_{name}"
        )

    git_status_after = _git_worktree_status(plan.root)
    if git_status_before is None or git_status_after is None:
        exclusions.append(
            {
                "name": "git_worktree_cleanliness",
                "status": "EXCLUDED_SNAPSHOT_NO_GIT",
                "reason": "Package is not a Git checkout; protected-file hashes and runtime isolation still ran.",
            }
        )
        totals["intentionally_excluded"] += 1
    else:
        unchanged_status = git_status_before == git_status_after
        checks.append(
            {
                "name": "git_worktree_unchanged_by_self_test",
                "status": "PASS" if unchanged_status else "FAIL",
                "baseline_clean": not bool(git_status_before),
                "final_clean": not bool(git_status_after),
            }
        )
        totals["passed" if unchanged_status else "failed"] += 1
        if git_status_before:
            checks.append(
                {
                    "name": "clean_git_worktree_after_self_test",
                    "status": "SKIP_BASELINE_DIRTY",
                    "reason": "The checkout already had uncommitted stabilization work before Self-Test.",
                }
            )
            totals["skipped"] += 1
        else:
            clean_after = not bool(git_status_after)
            checks.append(
                {
                    "name": "clean_git_worktree_after_self_test",
                    "status": "PASS" if clean_after else "FAIL",
                }
            )
            totals["passed" if clean_after else "failed"] += 1

    passed_count = totals["passed"]
    failed_count = totals["failed"]
    skipped_count = totals["skipped"]
    excluded_count = totals["intentionally_excluded"]
    not_tested_fixture_count = totals["not_tested_fixture"]
    final_passed = failed_count == 0 and not_tested_fixture_count == 0
    final_return_code = 0 if final_passed else 1

    try:
        manifest = json.loads(plan.manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        manifest = _base_manifest(plan)
    manifest.update(
        {
            "status": "PASS" if final_passed else "FAIL",
            "return_code": final_return_code,
            "finished_at": timestamp_now(),
            "self_test": {
                "offline": True,
                "passed": passed_count,
                "failed": failed_count,
                "skipped": skipped_count,
                "intentionally_excluded": excluded_count,
                "not_tested_fixture": not_tested_fixture_count,
                "checks": checks,
                "exclusions": exclusions,
                "network_guard_log": str(network_guard_log),
                "protected_hashes_before": protected_before,
                "protected_hashes_after": protected_after,
                "git_baseline_clean": git_status_before == "" if git_status_before is not None else None,
                "git_final_clean": git_status_after == "" if git_status_after is not None else None,
            },
            "test_totals": {
                "passed": passed_count,
                "failed": failed_count,
                "skipped": skipped_count,
                "intentionally_excluded": excluded_count,
                "not_tested_fixture": not_tested_fixture_count,
            },
        }
    )
    self_test_log = plan.out_dir / "self_test.log"
    summary = (
        f"SELF_TEST_SUMMARY: passed={passed_count} failed={failed_count} "
        f"skipped={skipped_count} intentionally_excluded={excluded_count} "
        f"not_tested_fixture={not_tested_fixture_count}"
    )
    verdict = "SELF_TEST: PASS" if final_passed else "SELF_TEST: FAIL"
    emit(summary)
    emit(verdict)
    self_test_log.write_text("\n".join(all_lines) + "\n", encoding="utf-8")
    artifacts = _artifact_list(plan.out_dir)
    warnings = tuple(
        f"{check['name']}: {check.get('status')}"
        for check in checks
        if str(check.get("status", "")).startswith(("SKIP", "NOT_TESTED"))
    )
    errors = tuple(
        f"{check['name']}: {check.get('status')}"
        for check in checks
        if check.get("status") == "FAIL"
    )
    finished_at = str(manifest.get("finished_at") or timestamp_now())
    output_paths = {
        "out_dir": str(plan.out_dir),
        "manifest": str(plan.manifest_path),
        "self_test_log": str(self_test_log),
        "artifacts": [str(plan.out_dir / artifact) for artifact in artifacts],
    }
    manifest.update(
        {
            "artifacts": list(artifacts),
            "self_test_log": str(self_test_log),
            "warnings": list(warnings),
            "errors": list(errors),
            "output_paths": output_paths,
        }
    )
    atomic_write_json(plan.manifest_path, manifest)
    return EngineRunResult(
        passed=final_passed,
        return_code=final_return_code,
        status="PASS" if final_passed else "FAIL",
        run_id=plan.run_id,
        out_dir=plan.out_dir,
        manifest_path=plan.manifest_path,
        artifacts=artifacts,
        started_at=str(manifest.get("started_at", "")),
        finished_at=finished_at,
        source_counts=dict(manifest.get("source_counts", {})),
        record_counts=dict(manifest.get("record_counts", {})),
        score_bucket_summaries=dict(manifest.get("score_bucket_summaries", {})),
        output_paths=output_paths,
        warnings=warnings,
        errors=errors,
        test_totals=dict(manifest["test_totals"]),
    )


def _source_row(source_id: str, *, root: Path, sources_path: Path) -> dict[str, Any]:
    wanted = str(source_id).strip().casefold()
    rows = load_source_rows(sources_path)
    row = next((item for item in rows if item["source_id"] == wanted), None)
    if row is None:
        raise KeyError(f"source_id '{source_id}' was not found")
    return row


def validate_source_definition(
    source_id: str,
    *,
    root: Path | None = None,
    sources_path: Path | None = None,
) -> dict[str, Any]:
    """Validate one source definition without running a parser or network."""
    package_root = detect_package_root(root).resolve()
    resolved_sources = resolve_registry_path(sources_path, package_root)
    row = _source_row(source_id, root=package_root, sources_path=resolved_sources)
    errors = list(source_configuration_errors(row))
    return {
        "passed": not errors,
        "network_used": False,
        "parser_used": False,
        "source_id": row["source_id"],
        "track": row["track"],
        "adapter": row["adapter"],
        "status": "CONFIGURATION VALID" if not errors else "CONFIGURATION INVALID",
        "status_code": "CONFIG_VALID" if not errors else "CONFIG_INVALID",
        "operational_status": row["operational_status"],
        "enabled": row["active"] == "Y",
        "runtime_eligible": source_is_runtime_eligible(row),
        "skip_reason": source_skip_reason(row),
        "errors": errors,
        "details": (
            "Required fields, adapter, status vocabulary, placeholder compatibility, "
            "duplicate runnable endpoints, and URL syntax are valid. DNS/public-address "
            "safety is rechecked immediately before every live request."
            if not errors
            else errors
        ),
    }


def _assess_development_live_sample(
    source: dict[str, Any],
    normalized: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Classify a bounded development-source sample without doing any I/O.

    A successful HTTP request and a non-empty ArcGIS layer are necessary but
    not sufficient evidence that a source is useful.  At least one row must
    contain an identifiable project plus meaningful project detail, and at
    least one row must meet the current Future_Projects score gate.
    """
    import tenderfinder_demo_three_buckets as demo

    source_id = str(source.get("source_id") or "").strip()
    source_name = str(source.get("name") or "").strip()
    enriched: list[dict[str, Any]] = []
    meaningful_count = 0
    relevant_count = 0

    for original in normalized:
        item = dict(original)
        item["source_id"] = str(item.get("source_id") or source_id)
        try:
            fit_score = float(item.get("fit_score") or 0)
        except (TypeError, ValueError):
            fit_score = 0.0
        item["fit_score"] = int(fit_score) if fit_score.is_integer() else fit_score
        tier = demo.signal_quality_for(
            {
                "fit_score": fit_score,
                "status_class": item.get("status_class") or "",
                "app_type_stage": item.get("app_type_stage") or "",
                "source_id": item["source_id"],
            }
        )
        item["signal_quality"] = tier
        item["route"] = "Future_Projects" if tier in {"HIGH", "MEDIUM"} else "Run_Queue"

        municipality = str(item.get("municipality") or "").strip()
        project_id = str(item.get("project_id") or item.get("app_no") or "").strip()
        source_url = str(item.get("source_url") or item.get("evidence_url") or "").strip()
        detail_candidates = (
            item.get("scope_summary"),
            item.get("app_type_stage"),
            item.get("title"),
        )
        generic_labels = {
            value.casefold()
            for value in (municipality, source_name, source_id)
            if value
        }
        detail = next(
            (
                str(value).strip()
                for value in detail_candidates
                if value
                and len(str(value).strip()) > 20
                and str(value).strip().casefold() not in generic_labels
            ),
            "",
        )
        meaningful = bool(project_id and municipality and source_url and detail)
        relevant = tier in {"HIGH", "MEDIUM"}
        item["live_sample_meaningful"] = meaningful
        item["live_sample_relevant"] = relevant
        item["live_sample_review_reason"] = (
            "identifiable project with meaningful detail"
            if meaningful
            else "missing project identity, public evidence URL, municipality, or meaningful detail"
        )
        meaningful_count += int(meaningful)
        relevant_count += int(relevant)
        enriched.append(item)

    warnings: list[str] = []
    if not enriched:
        warnings.append("The live endpoint returned no normalized development records.")
    if enriched and meaningful_count == 0:
        warnings.append(
            "Normalized rows were too thin to verify as useful project records; "
            "manual source review or adapter enrichment is required."
        )
    if enriched and relevant_count == 0:
        warnings.append(
            "The bounded sample contained no HIGH or MEDIUM keyword-scored project; "
            "the source remains ready_for_live_test."
        )
    return {
        "passed": bool(enriched and meaningful_count and relevant_count),
        "meaningful_count": meaningful_count,
        "relevant_count": relevant_count,
        "normalized_preview": enriched[:5],
        "warnings": warnings,
    }


def test_source_definition(
    source_id: str,
    *,
    root: Path | None = None,
    sources_path: Path | None = None,
    fixture_path: Path | None = None,
    allow_network: bool = False,
    persist_result: bool = False,
) -> dict[str, Any]:
    """Run an offline adapter fixture or one explicit live source test.

    Configuration validation is intentionally a separate operation.  With
    ``allow_network=False`` this function executes a maintained local fixture;
    if none applies it returns NOT TESTED rather than PASS.  Live mode is an
    explicit one-source action and requires the row to be runtime-eligible.
    """
    package_root = detect_package_root(root).resolve()
    sources_path = resolve_registry_path(sources_path, package_root)
    row = _source_row(source_id, root=package_root, sources_path=sources_path)
    config = validate_source_definition(
        row["source_id"], root=package_root, sources_path=sources_path
    )
    if not config["passed"]:
        custom_required = any("custom adapter required" in error for error in config["errors"])
        return {
            **config,
            "status": "CUSTOM ADAPTER REQUIRED" if custom_required else "DRAFT INCOMPLETE",
            "status_code": "CUSTOM_ADAPTER_REQUIRED" if custom_required else "DRAFT_INCOMPLETE",
        }
    if not allow_network:
        result = run_offline_adapter_fixture(
            row,
            root=package_root,
            fixture_path=fixture_path,
        )
        result["configuration"] = config
        if persist_result:
            current_status = row["operational_status"]
            new_status = (
                "adapter_fixture_pass"
                if result["passed"] and current_status in {
                    "ready_for_live_test", "config_valid_only", "adapter_fixture_pass"
                }
                else current_status
            )
            update_source_test_metadata(
                row["source_id"],
                operational_status=new_status,
                test_type="offline_fixture",
                test_result=result["status_code"],
                error="; ".join(result.get("errors") or []),
                candidate_count=result.get("candidate_count", 0),
                normalized_count=result.get("normalized_count", 0),
                path=sources_path,
                root=package_root,
            )
            result["operational_status"] = new_status
        else:
            result["operational_status"] = row["operational_status"]
        return result

    readiness_errors = source_readiness_errors(row)
    if readiness_errors:
        return {
            **config,
            "passed": False,
            "network_used": False,
            "parser_used": False,
            "status": "LIVE TEST BLOCKED",
            "status_code": "LIVE_TEST_BLOCKED",
            "errors": readiness_errors,
            "details": readiness_errors,
        }

    probe_root = default_output_root() / "source_tests" / new_run_id("source_test")
    probe_root.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        **config,
        "passed": False,
        "network_used": True,
        "parser_used": True,
        "test_timestamp": timestamp_now(),
        "requested_url": row["url"] if row["track"] == "tender" else row["endpoint"],
        "final_validated_url": "",
        "http_status": "",
        "raw_candidate_count": 0,
        "normalized_count": 0,
        "rejected_count": 0,
        "warnings": [],
        "errors": [],
    }
    try:
        if row["track"] == "tender":
            source = next(
                item for item in load_tender_sources(sources_path, active_only=False)
                if item["source_id"] == row["source_id"]
            )
            import tenderfinder_demo_three_buckets as demo

            demo.configure_runtime_state(probe_root / "state", "source_test")
            sweep = demo.sweep_source(source)
            log = asdict(sweep.log)
            normalized_count = len(sweep.candidates)
            raw_count = int(log.get("raw_links_found") or normalized_count)
            error = str(log.get("error") or "")
            passed = not error and normalized_count > 0
            result.update(
                {
                    "status": "LIVE SOURCE PASS" if passed else "LIVE SOURCE FAIL",
                    "status_code": "PASS_LIVE_SOURCE" if passed else "FAIL_LIVE_SOURCE",
                    "adapter_status": log.get("status") or "UNKNOWN",
                    "passed": passed,
                    "details": log,
                    "http_status": int(log.get("http_status") or 0) or "",
                    "raw_candidate_count": raw_count,
                    "normalized_count": normalized_count,
                    "rejected_count": max(0, raw_count - normalized_count),
                    "errors": [error] if error else [],
                    "normalized_preview": [asdict(candidate) for candidate in sweep.candidates[:5]],
                }
            )
            resolved_endpoint = str(log.get("resolved_url") or "")
        else:
            import tenderfinder_raw_sweep as raw_sweep

            connector = raw_sweep.load_config(str(sources_path))[row["source_id"]]
            probe = raw_sweep.run_connector(
                connector,
                max_records=5,
                probe=False,
                raw_dir=str(probe_root),
                query_where=row.get("test_query_where") or None,
                query_order_by=row.get("test_query_order_by") or None,
            )
            raw_count = int(probe.get("records_pulled") or 0)
            normalized = list(probe.get("leads") or [])
            rejected = list(probe.get("rejected") or [])
            error = str(probe.get("error") or "")
            fixture_fallback = bool(probe.get("_fixture_fallback"))
            assessment = _assess_development_live_sample(row, normalized)
            transport_passed = not error and not fixture_fallback and len(normalized) > 0
            passed = transport_passed and assessment["passed"]
            review_required = transport_passed and not assessment["passed"]
            result.update(
                {
                    "status": (
                        "LIVE SOURCE PASS"
                        if passed
                        else "LIVE SOURCE REVIEW REQUIRED"
                        if review_required
                        else "LIVE SOURCE FAIL"
                    ),
                    "status_code": (
                        "PASS_LIVE_SOURCE"
                        if passed
                        else "LIVE_SOURCE_REVIEW_REQUIRED"
                        if review_required
                        else "FAIL_LIVE_SOURCE"
                    ),
                    "adapter_status": str(probe.get("status") or "UNKNOWN"),
                    "passed": passed,
                    "details": probe,
                    "http_status": int(probe.get("http_status") or 0) or "",
                    "raw_candidate_count": raw_count,
                    "normalized_count": len(normalized),
                    "rejected_count": len(rejected),
                    "errors": ([error] if error else [])
                    + (["fixture fallback is not live evidence"] if fixture_fallback else []),
                    "warnings": assessment["warnings"],
                    "meaningful_sample_count": assessment["meaningful_count"],
                    "relevant_sample_count": assessment["relevant_count"],
                    "normalized_preview": assessment["normalized_preview"],
                }
            )
            resolved_endpoint = str(probe.get("resolved_endpoint") or "")
            result["final_validated_url"] = str(
                probe.get("final_validated_url") or resolved_endpoint
            )
    except Exception as exc:
        result.update(
            {
                "passed": False,
                "status": "LIVE SOURCE FAIL",
                "status_code": "FAIL_LIVE_SOURCE",
                "details": str(exc),
                "errors": [f"{type(exc).__name__}: {exc}"],
            }
        )
        resolved_endpoint = ""

    result["final_validated_url"] = str(
        result.get("final_validated_url") or resolved_endpoint
    )
    if persist_result:
        safety_failure = any(
            marker in " ".join(result.get("errors") or []).casefold()
            for marker in ("non-public", "url is unsafe", "local hostname", "redirect")
        )
        new_status = (
            "verified_live" if result["passed"]
            else "blocked" if safety_failure
            else "ready_for_live_test"
        )
        update_source_test_metadata(
            row["source_id"],
            operational_status=new_status,
            test_type="live_source_test",
            test_result=result["status_code"],
            http_status=result.get("http_status", ""),
            error="; ".join(result.get("errors") or []),
            candidate_count=result.get("raw_candidate_count", 0),
            normalized_count=result.get("normalized_count", 0),
            last_good_endpoint=resolved_endpoint if result["passed"] and resolved_endpoint else None,
            path=sources_path,
            root=package_root,
        )
        result["operational_status"] = new_status
    result["probe_output"] = str(probe_root)
    return result


# ``test_source_definition`` is a runtime source-connector entry point, not a
# pytest test.  Its ``test_`` prefix (kept for backwards-compatible callers)
# would otherwise be auto-collected by pytest wherever the symbol is imported
# into a test module's namespace, producing a spurious "fixture 'source_id' not
# found" collection error.  The marker below opts it out of collection without
# changing the public name or signature.
test_source_definition.__test__ = False


def validate_runtime_configuration(*, root: Path | None = None) -> dict[str, Any]:
    package_root = detect_package_root(root).resolve()
    keywords = load_keywords_config(root=package_root, force_reload=True)
    sources = registry_summary(root=package_root)
    review = package_root / "inputs" / "all_live_review.xlsx"
    return {
        "passed": review.exists(),
        "keywords": str(keywords.path),
        "active_keywords": keywords.active_keyword_count,
        "sources": sources,
        "review_xlsx": str(review),
        "review_exists": review.exists(),
    }

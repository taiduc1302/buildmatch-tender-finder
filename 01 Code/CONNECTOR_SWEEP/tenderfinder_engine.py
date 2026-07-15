"""Display-agnostic TENDER_FINDER service API.

Tkinter, a future web endpoint, and command-line launchers can all use this
module to prepare and run the same engine command. It owns preflight,
mode-specific state isolation, streaming process execution, and the run
manifest; it never imports or creates GUI widgets.
"""
from __future__ import annotations

import os
import json
import subprocess
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable

from tenderfinder_keywords_config import load_keywords_config, resolve_keywords_path
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
    source_readiness_errors,
    upsert_source,
)


MODE_LIVE = "live"
MODE_OFFLINE = "offline"
MODE_SELF_TEST = "self_test"
RUN_MODES = frozenset({MODE_LIVE, MODE_OFFLINE, MODE_SELF_TEST})
PAUSE_EXIT_CODE = 86

SELF_TEST_SCRIPTS = (
    ("keyword_configuration", "test_keywords_config.py"),
    ("standalone_trust_safeguards", "test_standalone_weekly_release.py"),
    ("routing_gates", "test_routing_gates.py"),
    ("manual_outreach_persistence", "test_outreach_persistence.py"),
    ("review_workbook_discovery", "test_launcher_review_xlsx_consistency.py"),
    ("tender_signal_routing", "test_tender_signal_routing.py"),
)

SELF_TEST_INTENTIONAL_EXCLUSIONS = (
    {
        "name": "live_tender_source_isolation",
        "status": "EXCLUDED_LIVE",
        "reason": "Self-Test is strictly offline; controlled live proof is a separate release gate.",
    },
    {
        "name": "legacy_surrey_clock_assertion",
        "status": "EXCLUDED_LEGACY",
        "reason": "Known stale hardcoded-date assertion, unrelated to the standalone workflow.",
    },
    {
        "name": "legacy_missing_eml_payload_checks",
        "status": "EXCLUDED_LEGACY",
        "reason": "Known checks require optional legacy .eml payloads absent from this package.",
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
    run_id: str = ""


@dataclass(frozen=True)
class RunPlan:
    run_id: str
    mode: str
    root: Path
    out_dir: Path
    state_root: Path
    review_xlsx: Path
    keywords_path: Path
    sources_path: Path
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
    package_root = detect_package_root(root).resolve()
    review = Path(request.review_xlsx).expanduser().resolve()
    if not review.exists():
        raise FileNotFoundError(f"review workbook not found: {review}")
    keywords = resolve_keywords_path(request.keywords_path, package_root)
    sources = resolve_registry_path(request.sources_path, package_root)
    # Strict preflight: no hardcoded or partial fallback is allowed.
    load_keywords_config(keywords, force_reload=True)
    load_source_rows(sources)

    run_id = request.run_id.strip() or new_run_id(mode)
    isolated_state = request.state_root
    if isolated_state is None:
        if mode == MODE_SELF_TEST:
            isolated_state = default_output_root() / "state" / MODE_SELF_TEST / run_id
        else:
            isolated_state = default_output_root() / "state" / mode
    paths = runtime_paths(isolated_state, mode=mode, package_root=package_root, create=True)
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
        "--sources-config", str(sources),
        "--state-root", str(paths.root),
        "--run-id", run_id,
    ]
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
        review_xlsx=review,
        keywords_path=keywords,
        sources_path=sources,
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
    else:
        state_root = default_output_root() / "state" / selected_mode
    script = package_root / "01 Code" / "CONNECTOR_SWEEP" / "tenderfinder_demo_three_buckets.py"
    sources = resolve_registry_path(None, package_root)
    command = [
        python_exe or sys.executable,
        "-u",
        str(script),
        "--review-xlsx", str(Path(review_xlsx).expanduser().resolve()),
        "--out-dir", str(Path(out_dir).expanduser().resolve()),
        "--sources-config", str(sources),
        "--state-root", str(state_root.resolve()),
        "--run-id", run_id,
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

    mode = MODE_OFFLINE if "--no-fetch" in values else MODE_LIVE
    run_id = option("--run-id") or new_run_id(mode)
    request = RunRequest(
        review_xlsx=Path(option("--review-xlsx")),
        out_dir=Path(option("--out-dir")),
        mode=mode,
        python_exe=values[0] if values else sys.executable,
        email_intake="--email-intake" in values,
        email_import_path=option("--email-import-path"),
        sources_path=Path(option("--sources-config")) if option("--sources-config") else None,
        state_root=Path(option("--state-root")) if option("--state-root") else None,
        run_id=run_id,
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


def _base_manifest(plan: RunPlan) -> dict[str, Any]:
    return {
        "schema_version": 1,
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
        "keywords_sha256": sha256_file(plan.keywords_path),
        "sources_csv": str(plan.sources_path),
        "sources_sha256": sha256_file(plan.sources_path),
        "source_registry": registry_summary(plan.sources_path),
        "state_root": str(plan.state_root),
        "out_dir": str(plan.out_dir),
        "artifacts": [],
    }


def run_plan(
    plan: RunPlan,
    *,
    on_line: Callable[[str], None] | None = None,
    started_callback: Callable[[subprocess.Popen[str]], None] | None = None,
) -> EngineRunResult:
    manifest = _base_manifest(plan)
    atomic_write_json(plan.manifest_path, manifest)
    log_path = plan.out_dir / "engine.log"
    env = os.environ.copy()
    env.update(
        {
            "PYTHONUTF8": "1",
            "TENDER_FINDER_DEMO_NO_OPEN": "1",
            RUN_MODE_ENV_VAR: plan.mode,
            STATE_ROOT_ENV_VAR: str(plan.state_root),
            "TENDER_FINDER_KEYWORDS_CONFIG": str(plan.keywords_path),
            "TENDER_FINDER_SOURCES_CONFIG": str(plan.sources_path),
        }
    )
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
    manifest.update(
        {
            "status": status,
            "finished_at": timestamp_now(),
            "return_code": return_code,
            "artifacts": list(artifacts),
            "log": str(log_path),
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
        ),
        root=package_root,
    )


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
    plan = prepare_self_test(root=root, output_root=output_root)
    all_lines: list[str] = []
    checks: list[dict[str, Any]] = []

    def emit(line: str) -> None:
        all_lines.append(line)
        if on_line:
            on_line(line)

    emit(f"SELF_TEST_RUN_ID: {plan.run_id}")
    emit("SELF_TEST_NETWORK_POLICY: OFFLINE_ONLY (--no-fetch; no live source test selected)")
    tests_dir = plan.root / "01 Code" / "CONNECTOR_SWEEP" / "tests"
    env = os.environ.copy()
    env.update(
        {
            "PYTHONUTF8": "1",
            "TENDER_FINDER_GUI_SKIP_E2E": "1",
            "TENDER_FINDER_OFFLINE_ONLY": "1",
            RUN_MODE_ENV_VAR: MODE_SELF_TEST,
            STATE_ROOT_ENV_VAR: str(plan.state_root),
            "TENDER_FINDER_KEYWORDS_CONFIG": str(plan.keywords_path),
            "TENDER_FINDER_SOURCES_CONFIG": str(plan.sources_path),
        }
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
        status = "PASS" if return_code == 0 else "FAIL"
        elapsed = round(time.perf_counter() - started, 3)
        checks.append(
            {
                "name": check_name,
                "script": str(script),
                "status": status,
                "return_code": return_code,
                "elapsed_seconds": elapsed,
                "output_tail": output_lines[-20:],
            }
        )
        emit(f"SELF_TEST_CHECK_{status}: {check_name} return_code={return_code} elapsed={elapsed:.3f}s")

    emit("SELF_TEST_CHECK_START: offline_end_to_end_pipeline")
    pipeline_result = run_plan(
        plan,
        on_line=emit,
        started_callback=started_callback,
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

    passed_count = sum(check["status"] == "PASS" for check in checks)
    failed_count = sum(check["status"] == "FAIL" for check in checks)
    skipped_count = 0
    excluded_count = len(SELF_TEST_INTENTIONAL_EXCLUSIONS)
    final_passed = failed_count == 0
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
                "checks": checks,
                "exclusions": list(SELF_TEST_INTENTIONAL_EXCLUSIONS),
            },
        }
    )
    self_test_log = plan.out_dir / "self_test.log"
    summary = (
        f"SELF_TEST_SUMMARY: passed={passed_count} failed={failed_count} "
        f"skipped={skipped_count} intentionally_excluded={excluded_count}"
    )
    verdict = "SELF_TEST: PASS" if final_passed else "SELF_TEST: FAIL"
    emit(summary)
    emit(verdict)
    self_test_log.write_text("\n".join(all_lines) + "\n", encoding="utf-8")
    artifacts = _artifact_list(plan.out_dir)
    manifest.update({"artifacts": list(artifacts), "self_test_log": str(self_test_log)})
    atomic_write_json(plan.manifest_path, manifest)
    return EngineRunResult(
        passed=final_passed,
        return_code=final_return_code,
        status="PASS" if final_passed else "FAIL",
        run_id=plan.run_id,
        out_dir=plan.out_dir,
        manifest_path=plan.manifest_path,
        artifacts=artifacts,
    )


def test_source_definition(
    source_id: str,
    *,
    root: Path | None = None,
    sources_path: Path | None = None,
    fixture_path: Path | None = None,
    allow_network: bool = False,
) -> dict[str, Any]:
    """Validate one canonical source and optionally perform one live probe.

    ``allow_network=False`` is a strict configuration-only check.  The GUI
    exposes live probing as a separate action so a source edit never causes an
    implicit request.
    """
    package_root = detect_package_root(root).resolve()
    sources_path = resolve_registry_path(sources_path, package_root)
    wanted = str(source_id).strip().casefold()
    rows = load_source_rows(sources_path)
    row = next((item for item in rows if item["source_id"] == wanted), None)
    if row is None:
        raise KeyError(f"source_id '{source_id}' was not found")
    readiness_errors = source_readiness_errors(row)
    result: dict[str, Any] = {
        "passed": True,
        "network_used": False,
        "source_id": wanted,
        "track": row["track"],
        "status": "PASS_CONFIG_ONLY",
        "details": "Canonical registry row is valid; no network request was made.",
    }
    if readiness_errors:
        custom_required = any("custom adapter required" in error for error in readiness_errors)
        result.update(
            {
                "passed": False,
                "status": "CUSTOM_ADAPTER_REQUIRED" if custom_required else "DRAFT_INCOMPLETE",
                "details": readiness_errors,
            }
        )
        return result
    if fixture_path is not None:
        fixture = Path(fixture_path).expanduser().resolve()
        if not fixture.is_file():
            raise FileNotFoundError(f"source-test fixture not found: {fixture}")
        if row["track"] != "tender" or row["adapter"] != "public_listing":
            return {
                **result,
                "passed": False,
                "status": "CUSTOM_ADAPTER_REQUIRED",
                "details": "Offline fixture preview currently supports the public_listing tender adapter.",
                "fixture": str(fixture),
            }
        import tenderfinder_demo_three_buckets as demo

        source = next(
            item for item in load_tender_sources(sources_path, active_only=False)
            if item["source_id"] == wanted
        )
        body = fixture.read_text(encoding="utf-8-sig")
        if body.lstrip().startswith("<") and any(
            marker in body[:1000].casefold() for marker in ("<rss", "<feed")
        ):
            candidates = demo.parse_rss(body, source, source["url"], source.get("rss") or source["url"])
            adapter_status = "PASS_FIXTURE_RSS"
        else:
            candidates = demo.parse_html_links(body, source, source["url"])
            adapter_status = "PASS_FIXTURE_HTML"
        preview = [asdict(candidate) for candidate in candidates[:5]]
        return {
            **result,
            "passed": bool(candidates),
            "status": adapter_status if candidates else "PARSE_ZERO_RECORDS",
            "details": "Offline fixture parsed through the configured public_listing adapter.",
            "fixture": str(fixture),
            "candidates": len(candidates),
            "normalized_preview": preview,
        }
    if not allow_network:
        return result

    probe_root = default_output_root() / "source_tests" / new_run_id("source_test")
    probe_root.mkdir(parents=True, exist_ok=True)
    result["network_used"] = True
    try:
        if row["track"] == "tender":
            source = next(
                item for item in load_tender_sources(sources_path, active_only=False)
                if item["source_id"] == wanted
            )
            import tenderfinder_demo_three_buckets as demo

            demo.configure_runtime_state(probe_root / "state", "source_test")
            sweep = demo.sweep_source(source)
            log = asdict(sweep.log)
            result.update(
                {
                    "status": log.get("status") or "UNKNOWN",
                    "passed": not bool(log.get("error")),
                    "details": log,
                    "candidates": len(sweep.candidates),
                }
            )
            resolved_endpoint = str(log.get("resolved_url") or "")
        else:
            import tenderfinder_raw_sweep as raw_sweep

            connector = raw_sweep.load_config(str(sources_path))[wanted]
            probe = raw_sweep.run_connector(
                connector,
                max_records=1,
                probe=True,
                raw_dir=str(probe_root),
            )
            status = str(probe.get("status") or ("ERROR" if probe.get("error") else "PROBE_COMPLETED"))
            result.update(
                {
                    "status": status,
                    "passed": not bool(probe.get("error")),
                    "details": probe,
                }
            )
            resolved_values = probe.get("resolved") or []
            resolved_endpoint = str(resolved_values[-1] if resolved_values else "")
    except Exception as exc:
        result.update({"passed": False, "status": "ERROR", "details": str(exc)})
        resolved_endpoint = ""

    updated = dict(row)
    updated["last_probe_status"] = str(result["status"])
    if result["passed"] and resolved_endpoint:
        updated["last_good_endpoint"] = resolved_endpoint
    upsert_source(updated, sources_path)
    result["probe_output"] = str(probe_root)
    return result


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

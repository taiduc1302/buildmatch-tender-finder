#!/usr/bin/env python3
"""TENDER_FINDER Tender Intelligence standalone Windows desktop launcher.

Tkinter owns only the presentation layer. Live/Offline runs, source tests,
configuration preflight, manifests, and the shared offline Self-Test all use
the display-agnostic :mod:`tenderfinder_engine` service boundary so the same
engine can later be called from a website without importing GUI widgets.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import queue
import re
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Callable

SCRIPT_DIR = Path(__file__).resolve().parent

sys.path.insert(0, str(SCRIPT_DIR))
# Small pure-stdlib helper (no pipeline imports) - the GUI still never
# imports the demo builder itself.
from tenderfinder_review_workbook import (  # noqa: E402
    discover_review_xlsx,
    missing_workbook_explanation,
    save_runtime_config,
)

# Legacy fallback only - the actual lookup happens through
# discover_review_xlsx() (env var -> saved config -> package-local inputs/
# -> this legacy path). Kept as a module constant because tests exercise
# the worker directly with it.
from tenderfinder_review_workbook import legacy_review_xlsx_path  # noqa: E402
from tenderfinder_email_intake import (  # noqa: E402
    connect_email_provider,
    current_email_import_folder,
    is_fixture_source_folder,
    load_email_provider_config,
    provider_display_name,
    reset_email_import_folder_to_default,
    test_email_intake,
)
from tenderfinder_package_paths import (  # noqa: E402
    config_root,
    detect_package_root,
    email_inbox_dir,
    email_processed_dir,
    email_rejected_dir,
    ensure_email_alert_dirs,
)
from tenderfinder_keywords_config import (  # noqa: E402
    KeywordConfigError,
    clear_keywords_cache,
    inspect_last_known_good,
    load_keywords_config,
    resolve_keywords_path,
    validation_summary,
)
from tenderfinder_engine import (  # noqa: E402
    build_command_for_paths,
    run_command as run_engine_command,
    run_self_test as run_engine_self_test,
    test_source_definition,
    validate_source_definition,
    validate_runtime_configuration,
)
from tenderfinder_source_registry import (  # noqa: E402
    DEVELOPMENT_ADAPTERS,
    SOURCE_COLUMNS,
    TENDER_ADAPTERS,
    SourceRegistryError,
    load_source_rows,
    registry_summary,
    resolve_registry_path,
    set_source_active,
    source_is_runtime_eligible,
    upsert_source,
)

ROOT_DIR = detect_package_root(SCRIPT_DIR)
DEMO_SCRIPT = SCRIPT_DIR / "tenderfinder_demo_three_buckets.py"

DEFAULT_REVIEW_XLSX, _ = discover_review_xlsx(ROOT_DIR)
if DEFAULT_REVIEW_XLSX is None:
    DEFAULT_REVIEW_XLSX = legacy_review_xlsx_path()

_configured_output_root = os.environ.get("TENDER_FINDER_OUTPUT_ROOT", "").strip()
if _configured_output_root:
    DEFAULT_OUTPUT_ROOT = Path(_configured_output_root).expanduser().resolve()
elif sys.platform.startswith("win"):
    DEFAULT_OUTPUT_ROOT = Path(r"C:\tenderfinder_out")
else:
    DEFAULT_OUTPUT_ROOT = Path.home() / "tenderfinder_out"

# demo_history/ is the internal snapshot archive the build script manages
# itself (archive_demo_history()); it is not meant to double as a live
# --out-dir target. Every prior patch's GUI-equivalent (.bat files) has
# used a folder under C:\tenderfinder_out, so the GUI defaults there too.

RUN_MODE_FULL = "Live Run (all enabled sources + BC Bid + email intake, ~2-3 min)"
RUN_MODE_FAST = "Offline/Test Run (no live fetch, local inputs only, ~1-2 min)"


def expected_source_status_lines(root: Path = ROOT_DIR) -> int:
    """Runtime-eligible tender sources plus internal email-intake status."""
    try:
        rows = load_source_rows(root=root, active_only=True, track="tender")
        return sum(source_is_runtime_eligible(row) for row in rows) + 1
    except SourceRegistryError:
        return 0


EXPECTED_SOURCE_STATUS_LINES = expected_source_status_lines()

# One GUI code path serves Windows and macOS; only fonts and the
# open-a-file mechanism differ per platform.
if sys.platform.startswith("win"):
    UI_FONT = "Segoe UI"
    LOG_FONT = ("Consolas", 9)
elif sys.platform == "darwin":
    UI_FONT = "Helvetica Neue"
    LOG_FONT = ("Menlo", 11)
else:
    UI_FONT = "Helvetica"
    LOG_FONT = ("Courier", 10)


def open_path_with_default_app(path: str) -> None:
    """Open a file or folder with the OS default application. os.startfile
    exists only on Windows; macOS uses `open`, other POSIX uses `xdg-open`."""
    if sys.platform.startswith("win"):
        os.startfile(path)  # noqa: PLW1509 - Windows branch only
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def keywords_folder(root: Path = ROOT_DIR) -> Path:
    """Return the package-local folder a founder opens to edit keywords."""
    return config_root(root)


RESCORE_ALWAYS_SUMMARY = (
    "Scores, gates, labels, and bucket routing always reflect current keywords.xlsx. "
    "Vancouver permit tiers are also recomputed when the persisted raw scoring snapshot is available."
)
RESCORE_ALWAYS_EXCEPTIONS = (
    "Explicit legacy exception: old Vancouver rows without a raw scoring snapshot keep their stored tier "
    "and are marked legacy_vancouver_scoring_text_unavailable. tenderfinder_agent2.py remains isolated/static; "
    "rows that were never persisted cannot be replayed."
)

KEYWORD_CATEGORY_LABELS = {
    "positive": "Positive fit",
    "negative": "Negative fit",
    "geography": "Geography",
    "client": "Known clients",
    "gate_include": "Civil include gate",
    "gate_exclude": "Exclusion gate",
    "gate_weak": "Weak terms",
    "gate_collision": "Collision protection",
    "label_civil": "Civil labels",
    "van_signal_primary": "Vancouver primary signals",
    "van_signal_secondary": "Vancouver secondary signals",
    "tender_match": "Tender language",
}
SOURCE_EDITABLE_OPERATIONAL_STATUSES = (
    "needs_configuration",
    "ready_for_live_test",
    "config_valid_only",
    "manual_only",
    "blocked",
    "wrong_source",
    "deprecated",
)


def validate_keywords_for_gui(root: Path = ROOT_DIR, *, force_reload: bool = True) -> dict[str, Any]:
    """Headless validation helper used by both the GUI and unit tests."""
    config = load_keywords_config(root=root, force_reload=force_reload)
    canonical_path = config.requested_path or resolve_keywords_path(root=root)
    return {
        "path": str(canonical_path),
        "effective_path": str(config.path),
        "present": canonical_path.exists(),
        "validation_status": (
            "VALID — canonical workbook"
            if config.source_kind == "canonical"
            else "WARNING — canonical invalid; verified last-known-good snapshot is in use"
        ),
        "source_kind": config.source_kind,
        "last_successful_load_time": config.loaded_at,
        "last_validation_time": config.last_validation_at,
        "company_name": config.company_name,
        "active_keyword_count": config.active_keyword_count,
        "inactive_keyword_count": config.inactive_keyword_count,
        "category_counts": config.category_counts,
        "category_labels": {
            category: KEYWORD_CATEGORY_LABELS.get(category, category)
            for category in config.category_counts
        },
        "last_known_good_status": config.last_known_good_status,
        "last_known_good_path": str(config.last_known_good_path or ""),
        "last_known_good_saved_at": config.last_known_good_saved_at,
        "validation_errors": list(config.validation_errors),
        "summary": validation_summary(config),
        "rescore_semantics": RESCORE_ALWAYS_SUMMARY,
        "rescore_exceptions": RESCORE_ALWAYS_EXCEPTIONS,
    }


def keyword_profile_status(root: Path = ROOT_DIR) -> str:
    try:
        return validate_keywords_for_gui(root, force_reload=False)["summary"]
    except KeywordConfigError as exc:
        return f"Keywords invalid: {exc.errors[0] if exc.errors else 'validation failed'}"


def classify_log_line(line: str) -> str:
    """Tag a build-log line for color coding in the GUI log pane. Pure
    function so it's directly testable: 'action' (a person must do
    something), 'error', 'stage' (progress milestone), or '' (routine)."""
    if (line.startswith("TENDER_FINDER_USER_ACTION_REQUIRED:")
            or "BC_BID_BLOCKED_BROWSER_CHECK_USER_ACTION_REQUIRED" in line
            or "BC_BID_USER_CHECK_NOT_COMPLETED" in line):
        return "action"
    if line.startswith(("ERROR", "Traceback")) or "USER_CANCELLED" in line or "USER_STOPPED" in line:
        return "error"
    if line.startswith("TENDER_FINDER_STAGE:") or line.startswith("DONE in"):
        return "stage"
    return ""


CONTINUE_SIGNAL_PREFIX = "TENDER_FINDER_CONTINUE_SIGNAL_FILE:"


def parse_continue_signal_file(line: str) -> str:
    """Extract the signal-file path the engine announces when it starts the
    BC Bid user-assisted wait; '' for any other line. Pure and testable."""
    if line.startswith(CONTINUE_SIGNAL_PREFIX):
        return line[len(CONTINUE_SIGNAL_PREFIX):].strip()
    return ""

DONE_SENTINEL = "__TENDER_FINDER_GUI_DONE__"
ERROR_SENTINEL = "__TENDER_FINDER_GUI_ERROR__"
CANCELLED_SENTINEL = "__TENDER_FINDER_GUI_CANCELLED__"
STOPPED_SENTINEL = "__TENDER_FINDER_GUI_STOPPED__"
PAUSED_SENTINEL = "__TENDER_FINDER_GUI_PAUSED__"

# Must match tenderfinder_demo_three_buckets.PAUSE_EXIT_CODE (the GUI deliberately
# never imports the pipeline module, so this is duplicated by design and
# pinned by tests).
PAUSE_EXIT_CODE = 86

# Duplicated (not imported) from tenderfinder_demo_three_buckets.bc_bid_status_note
# on purpose: the GUI only ever talks to the demo builder as a subprocess
# reading its output files, never by importing its pipeline code, so this
# small pure string-formatting helper is kept in sync by hand rather than
# adding a code dependency between the two. Wording must match exactly.
BC_BID_BLOCKED_STATUSES = {
    "BC_BID_BLOCKED_NO_PUBLIC_FEED",
    "BC_BID_BLOCKED_BROWSER_CHECK_USER_ACTION_REQUIRED",
    "BC_BID_USER_CHECK_NOT_COMPLETED",
}


def bc_bid_status_note(status: str) -> str:
    if status == "BC_BID_USER_CHECK_NOT_COMPLETED":
        return (
            "BC Bid: TENDER_FINDER opened a visible browser window for BC Bid's browser-check and "
            "waited, but the check was not completed before the time limit, so BC Bid was "
            "not read this run - this is NOT a genuine zero-result. Run TENDER_FINDER again when "
            "you can finish the check in that window (TENDER_FINDER never logs in or solves a "
            "CAPTCHA for you). Other tender sources above are unaffected."
        )
    if status == "BC_BID_BLOCKED_BROWSER_CHECK_USER_ACTION_REQUIRED":
        return (
            "BC Bid: needs a person to clear the site's browser-check/CAPTCHA page - "
            "TENDER_FINDER opened a visible browser window for this and does not log in or bypass "
            "CAPTCHA on your behalf. If that window is still open, allow the public "
            "Opportunities page to finish loading (solving any CAPTCHA yourself), then "
            "run TENDER_FINDER again. Other tender sources above are unaffected."
        )
    if status in BC_BID_BLOCKED_STATUSES:
        return (
            "BC Bid: temporarily blocked by the site's bot-check this run (this happens "
            "occasionally with live government sites and is not a TENDER_FINDER problem). Other "
            "tender sources above are unaffected. Try running again later, or check "
            "docs/BC_BID_NETWORK_AUDIT.md for details."
        )
    return ""


def default_output_dir(now: dt.datetime | None = None) -> Path:
    now = now or dt.datetime.now()
    return DEFAULT_OUTPUT_ROOT / f"weekly_run_{now.strftime('%Y%m%d_%H%M%S')}"


def build_demo_command(
    review_xlsx: Path,
    out_dir: Path,
    fast_mode: bool,
    email_import_path: str = "",
    python_exe: str | None = None,
) -> list[str]:
    """Prepare the display-agnostic engine command used by the GUI."""
    return build_command_for_paths(
        review_xlsx,
        out_dir,
        fast_mode=fast_mode,
        email_import_path=email_import_path,
        python_exe=python_exe or sys.executable,
        root=ROOT_DIR,
    )


def terminate_process_tree(proc: "subprocess.Popen[str]", grace_seconds: float = 3.0) -> bool:
    """Terminate proc and any child processes it spawned - specifically,
    the BC Bid step launches a real headless Chromium under the demo
    builder's python.exe, and on Windows proc.terminate()/proc.kill() only
    signal the immediate python.exe, leaving chromium.exe running orphaned
    after the GUI window closes. `taskkill /T /F` kills the whole process
    tree in one call, which is the reliable mechanism for this on Windows.
    Falls back to proc.terminate()/.kill() on non-Windows platforms or if
    taskkill is unavailable. Returns True if the process is confirmed no
    longer running (checked via proc.poll(), not just "a kill was issued")."""
    if proc.poll() is not None:
        return True
    if sys.platform.startswith("win"):
        try:
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                capture_output=True,
                timeout=grace_seconds + 5,
            )
        except Exception:
            pass
    else:
        try:
            proc.terminate()
        except Exception:
            pass
    try:
        proc.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        try:
            proc.kill()
            proc.wait(timeout=grace_seconds)
        except Exception:
            pass
    return proc.poll() is not None


def run_demo_build_subprocess(
    cmd: list[str],
    log_queue: "queue.Queue[str]",
    cwd: Path = ROOT_DIR,
    started_callback: "Callable[[subprocess.Popen[str]], None] | None" = None,
) -> int:
    """Run the demo builder as a subprocess, streaming each stdout/stderr
    line into log_queue as it arrives. Returns the process exit code, or
    -1 if the subprocess could not even be started (e.g. python missing).
    No Tkinter dependency - safe to call from a background thread or
    directly from a test. If started_callback is given, it's called with
    the live Popen object immediately after launch so a caller (e.g.
    DemoBuildWorker) can hold a reference to cancel the run mid-flight.
    """
    if "--review-xlsx" in cmd and "--out-dir" in cmd:
        try:
            result = run_engine_command(
                cmd,
                root=cwd,
                on_line=log_queue.put,
                started_callback=started_callback,
            )
            return result.return_code
        except Exception as exc:
            log_queue.put(f"ERROR: could not start engine run: {exc}")
            return -1

    # Small compatibility path for process-control unit tests that exercise
    # cancellation with a generic Python sleep command rather than a run plan.
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except Exception as exc:
        log_queue.put(f"ERROR: could not start TENDER_FINDER run: {exc}")
        return -1

    if started_callback is not None:
        started_callback(proc)

    assert proc.stdout is not None
    for line in proc.stdout:
        log_queue.put(line.rstrip("\n"))
    proc.wait()
    return proc.returncode


def parse_demo_build_report(text: str) -> dict[str, Any]:
    """Pull the headline numbers out of DEMO_BUILD_REPORT.md's Outputs
    section. Pure string parsing, no file I/O, so it's directly testable
    with a sample string."""
    result: dict[str, Any] = {}

    m = re.search(r"BID NOW total / civil / open civil:\s*([\d,]+)\s*/\s*([\d,]+)\s*/\s*([\d,]+)", text)
    if m:
        result["bid_now_total"] = m.group(1)
        result["bid_now_civil"] = m.group(2)
        result["bid_now_open_civil"] = m.group(3)

    m = re.search(r"BID LATER / WATCH / ANALYZED:\s*([\d,]+)\s*/\s*([\d,]+)\s*/\s*([\d,]+)", text)
    if m:
        result["bid_later"] = m.group(1)
        result["watchlist"] = m.group(2)
        result["analyzed"] = m.group(3)

    m = re.search(r"Total demo build time:\s*([\d.]+s)", text)
    if m:
        result["build_time"] = m.group(1)

    m = re.search(r"BC Bid status:\s*(\S+)", text)
    if m:
        result["bc_bid_status"] = m.group(1)

    patterns = {
        "email_files_seen": r"Email alert files seen:\s*([\d,]+)",
        "email_rows_parsed": r"Email tender rows parsed:\s*([\d,]+)",
        "email_bid_now_rows": r"Email BID NOW rows:\s*([\d,]+)",
        "email_non_actionable_rows": r"Email non-actionable/history rows:\s*([\d,]+)",
        "email_rejected_duplicate_files": r"Email rejected/duplicate files:\s*([\d,]+)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            result[key] = match.group(1)

    return result


def parse_email_state(demo_summary_text: str) -> str:
    m = re.search(r"TENDER_FINDER LIVE-TENDER EMAIL SETUP - status:\s*(\S+)", demo_summary_text)
    return m.group(1) if m else "UNKNOWN"


def read_run_results(out_dir: Path) -> dict[str, Any]:
    """Read and parse the build report + summary from a completed run's
    output folder. Returns an empty-ish dict if files are missing rather
    than raising, since this is called after a subprocess whose exact
    output layout we don't want to assume too strictly about."""
    result: dict[str, Any] = {"out_dir": str(out_dir)}
    report_path = out_dir / "DEMO_BUILD_REPORT.md"
    summary_path = out_dir / "demo_summary.txt"
    workbook_path = out_dir / "TENDER_FINDER_DEMO_Opportunities_Three_Buckets.xlsx"
    if report_path.exists():
        result.update(parse_demo_build_report(report_path.read_text(encoding="utf-8", errors="replace")))
    if summary_path.exists():
        result["email_state"] = parse_email_state(summary_path.read_text(encoding="utf-8", errors="replace"))
    result["workbook_path"] = str(workbook_path) if workbook_path.exists() else ""
    result["report_path"] = str(report_path) if report_path.exists() else ""
    result["summary_path"] = str(summary_path) if summary_path.exists() else ""
    return result


def build_completion_summary_lines(results: dict[str, Any], out_dir: Path) -> list[str]:
    """Pure formatting for the completion dialog - directly testable
    without a display. If BC Bid was blocked this run, that's surfaced as
    its own clearly-labeled line instead of only a "BID NOW open civil: 0"
    count that would look identical to BC Bid genuinely finding nothing."""
    lines = [
        f"BID LATER: {results.get('bid_later', '?')}",
        f"Watchlist: {results.get('watchlist', '?')}",
        f"Analyzed: {results.get('analyzed', '?')}",
        f"BID NOW open civil: {results.get('bid_now_open_civil', '?')}",
    ]
    note = bc_bid_status_note(results.get("bc_bid_status", ""))
    if note:
        lines.append(note)
    lines.extend([
        f"Build time: {results.get('build_time', '?')}",
        f"Email Alert Intake state: {results.get('email_state', '?')}",
        "",
        f"Output folder:\n{out_dir}",
    ])
    return lines


def shorten_display_path(path: str, max_chars: int = 64) -> str:
    text = str(path or "").strip()
    if len(text) <= max_chars:
        return text
    if max_chars < 12:
        return text[:max_chars]
    keep = max_chars - 3
    head = max(keep // 3, 10)
    tail = max(keep - head, 12)
    return f"{text[:head]}...{text[-tail:]}"


def should_auto_open_workbook(open_when_done: bool, workbook_path: str, env_no_open: str | None = None) -> bool:
    return bool(open_when_done and workbook_path and (env_no_open or "").strip() != "1")


def should_show_continue_button(signal_file: str, status_text: str = "") -> bool:
    if signal_file:
        return True
    low = (status_text or "").lower()
    return any(
        token in low
        for token in (
            "blocked_browser_check",
            "browser_check_needs_user",
            "user_assisted_browser_waiting",
        )
    )


def parse_source_status_line(line: str) -> dict[str, str] | None:
    match = re.match(r"^(?P<source_id>[\w_]+):\s+(?P<status>\S+)", line.strip())
    if not match:
        return None
    return match.groupdict()


def write_error_log(out_dir: Path, lines: list[str]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "gui_run_error.log"
    log_path.write_text("\n".join(lines), encoding="utf-8")
    return log_path


class _TeeQueue:
    """Duck-types queue.Queue's .put() so run_demo_build_subprocess can
    stream lines to the GUI while this also keeps its own copy for the
    error log, without monkeypatching the real queue."""

    def __init__(self, target: "queue.Queue[str]") -> None:
        self._target = target
        self.lines: list[str] = []

    def put(self, item: str) -> None:
        self.lines.append(item)
        self._target.put(item)


class DemoBuildWorker:
    """Wraps run_demo_build_subprocess in a background thread and reports
    progress/completion back through a queue. Kept separate from the
    Tkinter App class so the threading/queue wiring can be exercised
    without a GUI: construct one, call .start(), and drain .log_queue."""

    def __init__(self, cmd: list[str], out_dir: Path, cwd: Path = ROOT_DIR) -> None:
        self.cmd = cmd
        self.out_dir = out_dir
        self.cwd = cwd
        self.log_queue: "queue.Queue[str]" = queue.Queue()
        self.thread: threading.Thread | None = None
        self.return_code: int | None = None
        self.proc: "subprocess.Popen[str] | None" = None
        self.cancel_requested = False
        self.stop_requested = False
        self.tee: "_TeeQueue | None" = None
        self._log_written = False

    def start(self) -> None:
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def is_running(self) -> bool:
        return self.thread is not None and self.thread.is_alive()

    def cancel(self) -> bool:
        """Called from the GUI thread (e.g. the window-close handler) to
        stop an in-progress build. Terminates the subprocess and any child
        process it spawned (see terminate_process_tree) and marks the run
        as user-cancelled so the log reflects an intentional stop, not a
        crash. Returns True if the process is confirmed no longer running.

        Writes the cancellation note to the error log itself, synchronously,
        rather than leaving that to the background thread's own tail-end
        logic: self.thread is a daemon thread, so if the whole app process
        exits (e.g. right after this call, when the GUI closes the window)
        before that thread gets scheduled again, its own log write might
        never happen. Calling it here guarantees it runs before the caller
        (the close handler) proceeds to destroy the window."""
        self.cancel_requested = True
        terminated = True
        if self.proc is not None:
            terminated = terminate_process_tree(self.proc)
        if self.tee is not None and not self._log_written:
            self._log_written = True
            self.tee.put("USER_CANCELLED: the GUI window was closed while this build was "
                         "running; it was stopped intentionally, this is not a crash.")
            write_error_log(self.out_dir, self.tee.lines)
        return terminated

    def stop(self) -> bool:
        """Task E Stop button: like cancel(), but the window stays open and
        the log marker is USER_STOPPED (a deliberate stop of the build, as
        opposed to USER_CANCELLED which means the whole window was closed).
        Marks the output folder as partial if any files were produced."""
        self.stop_requested = True
        terminated = True
        if self.proc is not None:
            terminated = terminate_process_tree(self.proc)
        if self.tee is not None:
            if not self._log_written:
                self._log_written = True
                self.tee.put("USER_STOPPED: the Stop button was clicked; the build was "
                             "terminated intentionally, this is not a crash.")
            # Persist the stop log here (idempotent overwrite) BEFORE the
            # partial-marker check below. The worker thread's _run() may also
            # write it, so relying only on `_log_written` created a race where
            # stop() could reach the iterdir() check before the file existed and
            # skip the partial marker. Writing unconditionally makes the marker
            # deterministic regardless of which thread wins.
            write_error_log(self.out_dir, self.tee.lines)
        try:
            if self.out_dir.exists() and any(self.out_dir.iterdir()):
                (self.out_dir / "PARTIAL_OUTPUT_README.txt").write_text(
                    "This TENDER_FINDER run was STOPPED by the user before it finished.\n"
                    "Files in this folder may be incomplete - check "
                    "tenderfinder_stage_progress.json for the stages that completed.\n"
                    "Run TENDER_FINDER again for a full, consistent output set.\n",
                    encoding="utf-8",
                )
        except Exception:
            pass
        return terminated

    def _run(self) -> None:
        self.tee = _TeeQueue(self.log_queue)
        tee = self.tee
        try:
            code = run_demo_build_subprocess(
                self.cmd, tee, cwd=self.cwd,
                started_callback=lambda p: setattr(self, "proc", p),
            )
        except Exception as exc:
            code = -1
            tee.put(f"ERROR: unexpected exception in worker: {exc}")
        self.return_code = code
        if self.stop_requested:
            if not self._log_written:
                self._log_written = True
                tee.put("USER_STOPPED: the Stop button was clicked; the build was "
                         "terminated intentionally, this is not a crash.")
                write_error_log(self.out_dir, tee.lines)
            self.log_queue.put(f"{STOPPED_SENTINEL}:{code}")
        elif self.cancel_requested:
            if not self._log_written:
                self._log_written = True
                tee.put("USER_CANCELLED: the GUI window was closed while this build was running; "
                         "it was stopped intentionally, this is not a crash.")
                write_error_log(self.out_dir, tee.lines)
            self.log_queue.put(f"{CANCELLED_SENTINEL}:{code}")
        elif code == PAUSE_EXIT_CODE:
            # A requested stage-safe pause, not a failure - no error log.
            self.log_queue.put(f"{PAUSED_SENTINEL}:{code}")
        elif code != 0:
            write_error_log(self.out_dir, tee.lines)
            self.log_queue.put(f"{ERROR_SENTINEL}:{code}")
        else:
            self.log_queue.put(f"{DONE_SENTINEL}:{code}")


def _lazy_import_tk():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    return tk, ttk, filedialog, messagebox


class TenderFinderLauncherApp:
    """The actual Tkinter UI. Everything here is widget wiring; the real
    work happens in the module-level functions above."""

    def __init__(self) -> None:
        tk, ttk, filedialog, messagebox = _lazy_import_tk()
        self.tk = tk
        self.ttk = ttk
        self.filedialog = filedialog
        self.messagebox = messagebox

        self.root = tk.Tk()
        self.root.title("TENDER_FINDER Tender Intelligence")
        self.root.geometry("1100x720")
        self.root.minsize(1050, 700)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close_requested)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)

        self.worker: DemoBuildWorker | None = None
        self.last_results: dict[str, Any] = {}
        self.last_email_test_result: dict[str, Any] = {}
        self._continue_signal_file = ""
        self._last_cmd: list[str] | None = None
        self._last_out_dir: Path | None = None
        self._source_lines_seen: set[str] = set()
        self._email_dry_run_log_path = ""
        self._expected_source_status_lines = expected_source_status_lines(ROOT_DIR)
        self._self_test_queue: "queue.Queue[tuple[str, Any]]" = queue.Queue()
        self._self_test_running = False
        self._self_test_proc: subprocess.Popen[str] | None = None
        self._source_test_queue: "queue.Queue[tuple[str, Any]]" = queue.Queue()
        self._source_test_running = False

        self._build_widgets()

    def _build_widgets(self) -> None:
        tk, ttk = self.tk, self.ttk
        pad = 10

        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self.company_profile_var = tk.StringVar(value=keyword_profile_status(ROOT_DIR))
        header = ttk.Label(self.root, text="TENDER_FINDER Tender Intelligence", font=(UI_FONT, 16, "bold"))
        header.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 2))
        profile_header = ttk.Label(self.root, textvariable=self.company_profile_var, font=(UI_FONT, 9, "bold"))
        profile_header.grid(row=0, column=0, sticky="e", padx=12, pady=(12, 2))
        subtitle = ttk.Label(
            self.root,
            text="Compact launcher for the tender sweep, Email Alert Intake, source checks, and post-run results.",
            font=(UI_FONT, 9),
            wraplength=1040,
            justify="left",
        )
        subtitle.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))

        self.run_mode_var = tk.StringVar(value=RUN_MODE_FULL)
        self.out_dir_var = tk.StringVar(value=str(default_output_dir()))
        self.auto_open_workbook_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="Ready. Choose a mode and run TENDER_FINDER.")
        self.mode_summary_var = tk.StringVar(value="Current mode: Live Run")
        self.run_metrics_var = tk.StringVar(value="Build complete metrics will appear here after a run.")
        self.result_var = tk.StringVar(value="No build has run yet this session.")
        self.email_intake_var = tk.StringVar(value=self._email_intake_status_text())
        self.email_folder_var = tk.StringVar()
        self.email_folder_full_var = tk.StringVar()
        self.email_summary_var = tk.StringVar(value="Run Test Email Import to see dry-run counts, duplicate handling, and rejected-file reasons.")
        self.source_status_var = tk.StringVar(value="No source checks have run yet this session.")
        self.source_progress_var = tk.StringVar(value=f"Sources completed: 0 / {self._expected_source_status_lines}")
        self.bc_bid_summary_var = tk.StringVar(value="BC Bid status: not checked in this session.")
        self.output_folder_display_var = tk.StringVar()
        self.output_folder_full_var = tk.StringVar()
        self.result_paths_var = tk.StringVar(value="Workbook, report, summary, and output-folder paths will appear here after a run.")
        self.report_path_var = tk.StringVar(value="")
        self.summary_path_var = tk.StringVar(value="")
        self.workbook_path_var = tk.StringVar(value="")
        self.email_log_path_var = tk.StringVar(value="Dry-run log: not created yet")

        ensure_email_alert_dirs(ROOT_DIR)
        self._refresh_email_intake_status()
        self._refresh_output_path_display()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))

        self.run_tab = ttk.Frame(self.notebook, padding=pad)
        self.keywords_tab = ttk.Frame(self.notebook, padding=pad)
        self.email_tab = ttk.Frame(self.notebook, padding=pad)
        self.source_tab = ttk.Frame(self.notebook, padding=pad)
        self.results_tab = ttk.Frame(self.notebook, padding=pad)
        self.settings_tab = ttk.Frame(self.notebook, padding=pad)
        self.notebook.add(self.run_tab, text="Run")
        self.notebook.add(self.keywords_tab, text="Keywords")
        self.notebook.add(self.email_tab, text="Email Alerts")
        self.notebook.add(self.source_tab, text="Source Checks")
        self.notebook.add(self.results_tab, text="Results / Logs")
        self.notebook.add(self.settings_tab, text="Settings / Advanced")

        for tab in (
            self.run_tab,
            self.keywords_tab,
            self.email_tab,
            self.source_tab,
            self.results_tab,
            self.settings_tab,
        ):
            tab.columnconfigure(0, weight=1)

        self._build_run_tab()
        self._build_keywords_tab()
        self._build_email_tab()
        self._build_source_tab()
        self._build_results_tab()
        self._build_settings_tab()
        self._set_continue_button_visibility(False)

    def _build_run_tab(self) -> None:
        tk, ttk = self.tk, self.ttk

        actions = ttk.LabelFrame(self.run_tab, text="Run TENDER_FINDER")
        actions.grid(row=0, column=0, sticky="ew")
        for col in range(8):
            actions.columnconfigure(col, weight=1 if col in {0, 1, 2, 3, 4, 5, 6} else 0)

        self.run_full_button = ttk.Button(actions, text="Live Run", command=self._on_run_full_clicked)
        self.run_full_button.grid(row=0, column=0, sticky="ew", padx=(10, 6), pady=(10, 8))
        self.run_fast_button = ttk.Button(actions, text="Offline/Test Run", command=self._on_run_fast_clicked)
        self.run_fast_button.grid(row=0, column=1, sticky="ew", padx=6, pady=(10, 8))
        self.run_button = ttk.Button(actions, text="Run Selected Mode", command=self._on_run_clicked)
        self.run_button.grid(row=0, column=2, sticky="ew", padx=6, pady=(10, 8))
        self.self_test_button = ttk.Button(actions, text="Run Self-Test", command=self._on_self_test_clicked)
        self.self_test_button.grid(row=0, column=3, sticky="ew", padx=6, pady=(10, 8))
        self.pause_button = ttk.Button(actions, text="Pause", command=self._on_pause_clicked, state="disabled")
        self.pause_button.grid(row=0, column=4, sticky="ew", padx=6, pady=(10, 8))
        self.stop_button = ttk.Button(actions, text="Stop", command=self._on_stop_clicked, state="disabled")
        self.stop_button.grid(row=0, column=5, sticky="ew", padx=6, pady=(10, 8))
        self.resume_button = ttk.Button(actions, text="Resume", command=self._on_resume_clicked, state="disabled")
        self.resume_button.grid(row=0, column=6, sticky="ew", padx=6, pady=(10, 8))
        ttk.Checkbutton(actions, text="Open workbook automatically when build completes", variable=self.auto_open_workbook_var).grid(
            row=1, column=0, columnspan=4, sticky="w", padx=10, pady=(0, 8)
        )
        ttk.Label(actions, textvariable=self.mode_summary_var, font=(UI_FONT, 9)).grid(row=1, column=4, columnspan=2, sticky="e", padx=6, pady=(0, 8))
        self.progress = ttk.Progressbar(actions, mode="indeterminate")
        self.progress.grid(row=1, column=6, columnspan=2, sticky="ew", padx=(6, 10), pady=(0, 8))
        self.open_keywords_button = ttk.Button(actions, text="Open keywords folder", command=self._on_open_keywords_folder)
        self.open_keywords_button.grid(row=2, column=0, sticky="ew", padx=(10, 6), pady=(0, 10))
        self.validate_keywords_button = ttk.Button(actions, text="Validate keywords", command=self._on_validate_keywords)
        self.validate_keywords_button.grid(row=2, column=1, sticky="ew", padx=6, pady=(0, 10))
        ttk.Label(actions, text="Edit the live workbook, validate it, then run.", font=(UI_FONT, 9), justify="left").grid(
            row=2, column=2, columnspan=6, sticky="w", padx=(6, 10), pady=(0, 10)
        )

        output = ttk.LabelFrame(self.run_tab, text="Post-Run Actions")
        output.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        for col in range(5):
            output.columnconfigure(col, weight=1)
        self.open_workbook_button = ttk.Button(output, text="Open Workbook", command=self._open_workbook, state="disabled")
        self.open_workbook_button.grid(row=0, column=0, sticky="ew", padx=(10, 6), pady=(10, 8))
        self.open_folder_button = ttk.Button(output, text="Open Output Folder", command=self._open_output_folder, state="disabled")
        self.open_folder_button.grid(row=0, column=1, sticky="ew", padx=6, pady=(10, 8))
        self.open_report_button = ttk.Button(output, text="Open Report", command=self._open_report, state="disabled")
        self.open_report_button.grid(row=0, column=2, sticky="ew", padx=6, pady=(10, 8))
        self.open_summary_button = ttk.Button(output, text="Open Summary", command=self._open_summary, state="disabled")
        self.open_summary_button.grid(row=0, column=3, sticky="ew", padx=6, pady=(10, 8))
        self.copy_paths_button = ttk.Button(output, text="Copy Output Paths", command=self._copy_output_paths, state="disabled")
        self.copy_paths_button.grid(row=0, column=4, sticky="ew", padx=(6, 10), pady=(10, 8))

        status_frame = ttk.LabelFrame(self.run_tab, text="Current Step")
        status_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        status_frame.columnconfigure(1, weight=1)
        self.spinner_canvas = tk.Canvas(status_frame, width=64, height=64, highlightthickness=0, bg=self.root.cget("bg"))
        self.spinner_canvas.grid(row=0, column=0, rowspan=3, sticky="nw", padx=(10, 8), pady=10)
        self.spinner_canvas.create_oval(13, 13, 51, 51, outline="#1a2a5c", width=2)
        self.spinner_canvas.create_text(32, 32, text="TENDER_FINDER", fill="#1a2a5c", font=(UI_FONT, 8, "bold"))
        self.spinner_arcs = [
            self.spinner_canvas.create_arc(8, 8, 56, 56, start=0, extent=95, outline="#1a2a5c", width=3, style="arc"),
            self.spinner_canvas.create_arc(4, 4, 60, 60, start=180, extent=70, outline="#607090", width=2, style="arc"),
        ]
        self.spinner_angle = 0
        self.spinner_job: str | None = None
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, font=(UI_FONT, 10, "bold"), wraplength=930, justify="left")
        self.status_label.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=(10, 4))
        ttk.Label(status_frame, textvariable=self.run_metrics_var, font=(UI_FONT, 9), wraplength=930, justify="left").grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=2)
        ttk.Label(status_frame, textvariable=self.source_progress_var, font=(UI_FONT, 8), wraplength=930, justify="left").grid(row=2, column=1, sticky="ew", padx=(0, 10), pady=(2, 10))

        quick = ttk.LabelFrame(self.run_tab, text="Last Run Result")
        quick.grid(row=3, column=0, sticky="nsew", pady=(10, 0))
        self.run_tab.rowconfigure(3, weight=1)
        quick.columnconfigure(0, weight=1)
        ttk.Label(quick, textvariable=self.result_var, font=(UI_FONT, 9), wraplength=980, justify="left").grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        ttk.Label(quick, textvariable=self.result_paths_var, font=(UI_FONT, 8), wraplength=980, justify="left").grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

    def _build_keywords_tab(self) -> None:
        tk, ttk = self.tk, self.ttk
        self.keywords_path_var = tk.StringVar()
        self.keywords_presence_var = tk.StringVar()
        self.keywords_validation_status_var = tk.StringVar()
        self.keywords_times_var = tk.StringVar()
        self.keywords_counts_var = tk.StringVar()
        self.keywords_categories_var = tk.StringVar()
        self.keywords_lkg_var = tk.StringVar()
        self.keywords_effective_var = tk.StringVar()
        self.keywords_errors_var = tk.StringVar()

        overview = ttk.LabelFrame(self.keywords_tab, text="Founder-editable keyword scoring")
        overview.grid(row=0, column=0, sticky="ew")
        overview.columnconfigure(1, weight=1)
        labels = (
            ("Canonical workbook", self.keywords_path_var),
            ("Workbook state", self.keywords_presence_var),
            ("Validation", self.keywords_validation_status_var),
            ("Load / validation times", self.keywords_times_var),
            ("Rule counts", self.keywords_counts_var),
            ("Categories", self.keywords_categories_var),
            ("Last-known-good", self.keywords_lkg_var),
            ("Rules used by current runs", self.keywords_effective_var),
        )
        for row_index, (label, variable) in enumerate(labels):
            ttk.Label(overview, text=label, font=(UI_FONT, 9, "bold")).grid(
                row=row_index, column=0, sticky="nw", padx=(10, 12), pady=(8 if row_index == 0 else 4, 4)
            )
            ttk.Label(
                overview,
                textvariable=variable,
                wraplength=790,
                justify="left",
            ).grid(
                row=row_index, column=1, sticky="ew", padx=(0, 10), pady=(8 if row_index == 0 else 4, 4)
            )

        actions = ttk.Frame(overview)
        actions.grid(row=len(labels), column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 10))
        for column in range(5):
            actions.columnconfigure(column, weight=1)
        self.open_keywords_workbook_button = ttk.Button(
            actions, text="Open Keywords Workbook", command=self._on_open_keywords_workbook
        )
        self.open_keywords_workbook_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.open_keywords_folder_button = ttk.Button(
            actions, text="Open Keywords Folder", command=self._on_open_keywords_folder
        )
        self.open_keywords_folder_button.grid(row=0, column=1, sticky="ew", padx=4)
        self.keywords_validate_button = ttk.Button(
            actions, text="Validate Keywords", command=self._on_validate_keywords
        )
        self.keywords_validate_button.grid(row=0, column=2, sticky="ew", padx=4)
        self.reload_keywords_button = ttk.Button(
            actions, text="Reload Keywords", command=self._on_reload_keywords
        )
        self.reload_keywords_button.grid(row=0, column=3, sticky="ew", padx=4)
        self.view_keywords_instructions_button = ttk.Button(
            actions, text="View Instructions", command=self._on_view_keywords_instructions
        )
        self.view_keywords_instructions_button.grid(row=0, column=4, sticky="ew", padx=(4, 0))

        errors = ttk.LabelFrame(self.keywords_tab, text="Visible validation errors")
        errors.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        errors.columnconfigure(0, weight=1)
        ttk.Label(
            errors,
            textvariable=self.keywords_errors_var,
            wraplength=980,
            justify="left",
        ).grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        semantics = ttk.LabelFrame(self.keywords_tab, text="Scoring behavior")
        semantics.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
        self.keywords_tab.rowconfigure(2, weight=1)
        semantics.columnconfigure(0, weight=1)
        ttk.Label(
            semantics,
            text=RESCORE_ALWAYS_SUMMARY + "\n\n" + RESCORE_ALWAYS_EXCEPTIONS,
            wraplength=980,
            justify="left",
        ).grid(row=0, column=0, sticky="nw", padx=10, pady=10)
        self._refresh_keywords_tab(force_reload=False)

    def _build_email_tab(self) -> None:
        ttk = self.ttk

        summary = ttk.LabelFrame(self.email_tab, text="Email Alert Intake")
        summary.grid(row=0, column=0, sticky="ew")
        summary.columnconfigure(0, weight=1)
        ttk.Label(summary, textvariable=self.email_intake_var, wraplength=980, justify="left").grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))

        folder_row = ttk.Frame(summary)
        folder_row.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))
        folder_row.columnconfigure(0, weight=1)
        self.email_folder_label = ttk.Label(folder_row, textvariable=self.email_folder_var)
        self.email_folder_label.grid(row=0, column=0, sticky="w")
        ttk.Button(folder_row, text="Copy Path", command=self._copy_email_folder_path).grid(row=0, column=1, sticky="e", padx=(8, 0))

        primary = ttk.Frame(summary)
        primary.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 8))
        for col in range(3):
            primary.columnconfigure(col, weight=1)
        self.open_email_import_button = ttk.Button(primary, text="Open Email Import Folder", command=self._on_create_open_email_import_folder)
        self.open_email_import_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.test_email_import_button = ttk.Button(primary, text="Test Email Import", command=self._on_test_email_intake)
        self.test_email_import_button.grid(row=0, column=1, sticky="ew", padx=6)
        self.run_email_demo_button = ttk.Button(primary, text="Run With Email Alerts", command=self._on_run_demo_with_email_alerts)
        self.run_email_demo_button.grid(row=0, column=2, sticky="ew", padx=(6, 0))

        secondary = ttk.LabelFrame(summary, text="More Email Tools")
        secondary.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))
        for col in range(4):
            secondary.columnconfigure(col, weight=1)
        ttk.Button(secondary, text="Select Existing Email Folder", command=self._on_select_existing_email_folder).grid(row=0, column=0, sticky="ew", padx=(8, 6), pady=8)
        ttk.Button(secondary, text="Open Processed Folder", command=self._on_open_processed_folder).grid(row=0, column=1, sticky="ew", padx=6, pady=8)
        ttk.Button(secondary, text="Open Rejected Folder", command=self._on_open_rejected_folder).grid(row=0, column=2, sticky="ew", padx=6, pady=8)
        ttk.Button(secondary, text="Reset To Default Import Folder", command=self._on_reset_to_default_import_folder).grid(row=0, column=3, sticky="ew", padx=(6, 8), pady=8)

        results = ttk.LabelFrame(self.email_tab, text="Dry-Run Summary")
        results.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self.email_tab.rowconfigure(1, weight=1)
        results.columnconfigure(0, weight=1)
        ttk.Label(results, textvariable=self.email_summary_var, wraplength=980, justify="left").grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        row = ttk.Frame(results)
        row.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        row.columnconfigure(0, weight=1)
        ttk.Label(row, textvariable=self.email_log_path_var, wraplength=880, justify="left").grid(row=0, column=0, sticky="w")
        self.open_email_log_button = ttk.Button(row, text="Open Dry-Run Log", command=self._open_email_dry_run_log, state="disabled")
        self.open_email_log_button.grid(row=0, column=1, sticky="e", padx=(8, 0))

    def _build_source_tab(self) -> None:
        ttk = self.ttk

        panel = ttk.LabelFrame(self.source_tab, text="Source Checks")
        panel.grid(row=0, column=0, sticky="ew")
        panel.columnconfigure(0, weight=1)
        ttk.Label(
            panel,
            text="Use this tab for BC Bid public-access checks and live-source status context. The browser-check continuation control only appears when TENDER_FINDER is actively waiting for user action.",
            wraplength=980,
            justify="left",
        ).grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 8))

        row = ttk.Frame(panel)
        row.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))
        row.columnconfigure(1, weight=1)
        self.bc_bid_check_button = ttk.Button(row, text="Check BC Bid Public Access", command=self._on_check_bc_bid_public_access)
        self.bc_bid_check_button.grid(row=0, column=0, sticky="w")
        self.continue_button = ttk.Button(row, text="Continue After Browser Check", command=self._on_continue_clicked)
        self.continue_button.grid(row=0, column=1, sticky="e", padx=(8, 0))

        ttk.Label(panel, textvariable=self.bc_bid_summary_var, wraplength=980, justify="left").grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 4))
        ttk.Label(panel, textvariable=self.source_status_var, wraplength=980, justify="left").grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))

        manager = ttk.LabelFrame(self.source_tab, text="Canonical Source Manager — config/sources.csv")
        manager.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self.source_tab.rowconfigure(1, weight=1)
        manager.columnconfigure(0, weight=1)
        manager.rowconfigure(0, weight=1)

        columns = (
            "source_id", "name", "track", "active", "adapter",
            "operational_status", "last_test",
        )
        self.source_tree = ttk.Treeview(manager, columns=columns, show="headings", height=12, selectmode="browse")
        headings = {
            "source_id": "Source ID",
            "name": "Name",
            "track": "Track",
            "active": "Active",
            "adapter": "Adapter",
            "operational_status": "Operational Status",
            "last_test": "Last Test Result",
        }
        widths = {
            "source_id": 135, "name": 205, "track": 80, "active": 55,
            "adapter": 135, "operational_status": 145, "last_test": 180,
        }
        for column in columns:
            self.source_tree.heading(column, text=headings[column])
            self.source_tree.column(column, width=widths[column], minwidth=55, stretch=column in {"name", "last_test"})
        source_scroll = ttk.Scrollbar(manager, orient="vertical", command=self.source_tree.yview)
        self.source_tree.configure(yscrollcommand=source_scroll.set)
        self.source_tree.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=(10, 6))
        source_scroll.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=(10, 6))
        self.source_tree.bind("<Double-1>", lambda _event: self._on_edit_source())

        buttons = ttk.Frame(manager)
        buttons.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 6))
        for column in range(6):
            buttons.columnconfigure(column, weight=1)
        self.add_source_button = ttk.Button(buttons, text="Add Source", command=self._on_add_source)
        self.add_source_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.edit_source_button = ttk.Button(buttons, text="Edit Source", command=self._on_edit_source)
        self.edit_source_button.grid(row=0, column=1, sticky="ew", padx=4)
        self.toggle_source_button = ttk.Button(buttons, text="Enable / Disable", command=self._on_toggle_source)
        self.toggle_source_button.grid(row=0, column=2, sticky="ew", padx=4)
        self.validate_sources_button = ttk.Button(buttons, text="Validate Configuration", command=self._on_validate_sources)
        self.validate_sources_button.grid(row=0, column=3, sticky="ew", padx=4)
        self.test_source_offline_button = ttk.Button(buttons, text="Offline Parser Test", command=lambda: self._on_test_selected_source(False))
        self.test_source_offline_button.grid(row=0, column=4, sticky="ew", padx=4)
        self.test_source_live_button = ttk.Button(buttons, text="Live Source Test", command=lambda: self._on_test_selected_source(True))
        self.test_source_live_button.grid(row=0, column=5, sticky="ew", padx=(4, 0))
        self.source_manager_status_var = self.tk.StringVar(value="Loading canonical registry...")
        ttk.Label(manager, textvariable=self.source_manager_status_var, wraplength=980, justify="left").grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10)
        )
        self._refresh_source_registry()

    def _refresh_source_registry(self) -> None:
        try:
            rows = load_source_rows(root=ROOT_DIR)
            summary = registry_summary(root=ROOT_DIR)
        except SourceRegistryError as exc:
            self.source_manager_status_var.set(f"REGISTRY INVALID: {exc}")
            return
        for item in self.source_tree.get_children():
            self.source_tree.delete(item)
        for row in rows:
            self.source_tree.insert(
                "",
                "end",
                iid=row["source_id"],
                values=(
                    row["source_id"], row["name"], row["track"], row["active"],
                    row["adapter"], row["operational_status"],
                    row["last_test_result"] or "NOT TESTED",
                ),
            )
        runtime_tenders = sum(
            row["track"] == "tender" and source_is_runtime_eligible(row)
            for row in rows
        )
        self._expected_source_status_lines = runtime_tenders + 1
        self.source_manager_status_var.set(
            f"CONFIGURATION VALID — {summary['total']} configured; {summary['enabled']} enabled; "
            f"{summary['runtime_eligible']} runtime-eligible; {summary['verified_live']} verified live; "
            f"{summary['ready_for_live_test']} ready for live test; {summary['manual_only']} manual; "
            f"{summary['needs_configuration']} need configuration; {summary['blocked']} blocked; "
            f"{summary['wrong_source']} wrong source. "
            f"Runtime registry: {summary['path']}"
        )

    def _selected_source_row(self, *, warn: bool = True) -> dict[str, str] | None:
        selection = self.source_tree.selection()
        if not selection:
            if warn:
                self.messagebox.showwarning("Source Manager", "Select one source first.")
            return None
        source_id = str(selection[0])
        try:
            return next(row for row in load_source_rows(root=ROOT_DIR) if row["source_id"] == source_id)
        except (StopIteration, SourceRegistryError) as exc:
            if warn:
                self.messagebox.showerror("Source Manager", f"Could not load selected source:\n{exc}")
            return None

    def _open_source_editor(self, existing: dict[str, str] | None = None) -> None:
        tk, ttk = self.tk, self.ttk
        source = {column: "" for column in SOURCE_COLUMNS}
        source.update(
            {
                "track": "tender",
                "active": "N",
                "adapter": "public_listing",
                "no_retry": "N",
                "status": "ready_for_probe",
                "operational_status": "needs_configuration",
            }
        )
        if existing:
            source.update(existing)

        window = tk.Toplevel(self.root)
        window.title("Edit Source" if existing else "Add Source")
        window.geometry("800x690")
        window.minsize(700, 640)
        window.transient(self.root)
        window.grab_set()
        window.columnconfigure(1, weight=1)

        fields = (
            ("source_id", "Source ID"),
            ("name", "Display name"),
            ("track", "Track"),
            ("active", "Active"),
            ("adapter", "Adapter"),
            ("operational_status", "Operational status"),
            ("municipality", "Municipality"),
            ("url", "URL / dataset token"),
            ("endpoint", "Endpoint / item ID"),
            ("layer_index", "ArcGIS layer index (optional)"),
            ("layer_keywords", "Discovery keywords (; separated)"),
            ("test_query_where", "Live-test ArcGIS where (optional)"),
            ("test_query_order_by", "Live-test ArcGIS order by (optional)"),
            ("rss", "RSS URL (optional)"),
            ("url_variants", "URL variants (| separated)"),
            ("no_retry", "No retry"),
            ("tier", "Tier"),
            ("status", "Status"),
            ("notes", "Notes"),
        )
        variables = {key: tk.StringVar(value=source.get(key, "")) for key, _label in fields}
        widgets: dict[str, Any] = {}
        for row_index, (key, label) in enumerate(fields):
            ttk.Label(window, text=label).grid(row=row_index, column=0, sticky="w", padx=(12, 8), pady=3)
            if key == "track":
                widget = ttk.Combobox(window, textvariable=variables[key], values=("tender", "development"), state="readonly")
            elif key in {"active", "no_retry"}:
                widget = ttk.Combobox(window, textvariable=variables[key], values=("Y", "N"), state="readonly")
            elif key == "adapter":
                widget = ttk.Combobox(window, textvariable=variables[key], state="readonly")
            elif key == "operational_status":
                choices = list(SOURCE_EDITABLE_OPERATIONAL_STATUSES)
                if variables[key].get() and variables[key].get() not in choices:
                    choices.append(variables[key].get())
                widget = ttk.Combobox(
                    window,
                    textvariable=variables[key],
                    values=tuple(choices),
                    state="readonly",
                )
            else:
                widget = ttk.Entry(window, textvariable=variables[key])
                if key == "source_id" and existing:
                    widget.configure(state="readonly")
            widget.grid(row=row_index, column=1, sticky="ew", padx=(0, 12), pady=3)
            widgets[key] = widget

        adapter_widget = widgets["adapter"]

        def refresh_adapters(*_args: Any) -> None:
            choices = sorted(TENDER_ADAPTERS if variables["track"].get() == "tender" else DEVELOPMENT_ADAPTERS)
            adapter_widget.configure(values=choices)
            if variables["adapter"].get() not in choices:
                variables["adapter"].set(choices[0])

        variables["track"].trace_add("write", refresh_adapters)
        refresh_adapters()

        note = (
            "New sources start disabled for safety. Save validates the entire registry atomically. "
            "Use Offline Parser Test before enabling; Live Source Test is always a separate explicit action. "
            "Only a successful live parser test can assign verified_live."
        )
        ttk.Label(window, text=note, wraplength=740, justify="left").grid(
            row=len(fields), column=0, columnspan=2, sticky="ew", padx=12, pady=(8, 4)
        )
        actions = ttk.Frame(window)
        actions.grid(row=len(fields) + 1, column=0, columnspan=2, sticky="e", padx=12, pady=(6, 12))

        def save() -> None:
            updated = dict(source)
            for key, variable in variables.items():
                updated[key] = variable.get().strip()
            if updated["track"] == "development" and not updated["endpoint"]:
                updated["endpoint"] = updated["url"]
            updated["fetch_type"] = updated["fetch_type"] or updated["adapter"]
            try:
                upsert_source(updated, root=ROOT_DIR)
            except SourceRegistryError as exc:
                self.messagebox.showerror("Source validation failed", str(exc), parent=window)
                return
            window.destroy()
            self._refresh_source_registry()
            self.source_manager_status_var.set(
                f"Saved {updated['source_id']} atomically to {resolve_registry_path(root=ROOT_DIR)}"
            )

        ttk.Button(actions, text="Cancel", command=window.destroy).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(actions, text="Validate and Save", command=save).grid(row=0, column=1)
        widgets["name" if existing else "source_id"].focus_set()

    def _on_add_source(self) -> None:
        self._open_source_editor(None)

    def _on_edit_source(self) -> None:
        row = self._selected_source_row()
        if row:
            self._open_source_editor(row)

    def _on_toggle_source(self) -> None:
        row = self._selected_source_row()
        if not row:
            return
        try:
            set_source_active(row["source_id"], row["active"] != "Y", root=ROOT_DIR)
        except SourceRegistryError as exc:
            self.messagebox.showerror("Source validation failed", str(exc))
            return
        self._refresh_source_registry()
        new_state = "enabled" if row["active"] != "Y" else "disabled"
        self.source_manager_status_var.set(f"{row['source_id']} is now {new_state}.")

    def _on_validate_sources(self) -> None:
        try:
            summary = registry_summary(root=ROOT_DIR)
        except SourceRegistryError as exc:
            self.source_manager_status_var.set(f"REGISTRY INVALID: {exc}")
            self.messagebox.showerror("Source registry invalid", str(exc))
            return
        self._refresh_source_registry()
        selected = self._selected_source_row(warn=False)
        selected_text = ""
        if selected is not None:
            result = validate_source_definition(selected["source_id"], root=ROOT_DIR)
            selected_text = (
                f"\n\nSelected source: {result['source_id']}\n"
                f"Configuration: {result['status']}\n"
                f"Operational status: {result['operational_status']}\n"
                f"Runtime eligible: {'YES' if result['runtime_eligible'] else 'NO'}\n"
                f"Parser run: NO\nNetwork used: NO"
            )
        self.messagebox.showinfo(
            "Source configuration is valid",
            f"Configured: {summary['total']}\nEnabled: {summary['enabled']}\n"
            f"Runtime eligible: {summary['runtime_eligible']}\n"
            f"Verified live: {summary['verified_live']}\n"
            f"Ready for live test: {summary['ready_for_live_test']}\n"
            f"Manual / needs configuration / blocked / wrong source: "
            f"{summary['manual_only']} / {summary['needs_configuration']} / "
            f"{summary['blocked']} / {summary['wrong_source']}\n\n"
            "This action validates configuration only. It does not run a parser and does not prove a source works."
            f"{selected_text}\n\n{summary['path']}",
        )

    def _on_test_selected_source(self, allow_network: bool) -> None:
        if self._source_test_running:
            return
        row = self._selected_source_row()
        if not row:
            return
        if allow_network and not self.messagebox.askyesno(
            "Run live source test?",
            f"This will make live public-network requests for only:\n\n"
            f"{row['source_id']} — {row['name']}\n\n"
            "No login or credentials are used. Continue?",
        ):
            return
        self._source_test_running = True
        self.test_source_offline_button.configure(state="disabled")
        self.test_source_live_button.configure(state="disabled")
        mode = "LIVE" if allow_network else "OFFLINE"
        self.source_manager_status_var.set(f"{mode} test running for {row['source_id']}...")

        def work() -> None:
            try:
                result = test_source_definition(
                    row["source_id"],
                    root=ROOT_DIR,
                    allow_network=allow_network,
                    persist_result=True,
                )
                self._source_test_queue.put(("result", result))
            except Exception as exc:
                self._source_test_queue.put(("error", str(exc)))

        threading.Thread(target=work, daemon=True).start()
        self.root.after(100, self._poll_source_test_queue)

    def _poll_source_test_queue(self) -> None:
        try:
            kind, payload = self._source_test_queue.get_nowait()
        except queue.Empty:
            self.root.after(100, self._poll_source_test_queue)
            return
        self._source_test_running = False
        self.test_source_offline_button.configure(state="normal")
        self.test_source_live_button.configure(state="normal")
        if kind == "error":
            self.source_manager_status_var.set(f"SOURCE TEST FAIL: {payload}")
            self.messagebox.showerror("Source test failed", str(payload))
            return
        result = dict(payload)
        verdict = "PASS" if result.get("passed") else "FAIL"
        network = "live network used" if result.get("network_used") else "offline; no network"
        self._refresh_source_registry()
        self.source_manager_status_var.set(
            f"{verdict}: {result.get('source_id')} -> {result.get('status')} ({network}); "
            f"operational status={result.get('operational_status', 'unchanged')}"
        )
        details = json.dumps(result.get("details"), indent=2, ensure_ascii=False, default=str)
        raw_count = result.get("raw_candidate_count", result.get("candidate_count", 0))
        normalized_count = result.get("normalized_count", 0)
        parser_name = str(result.get("parser") or "").strip()
        parser_display = "YES" + (f" ({parser_name})" if parser_name else "") if result.get("parser_used") else "NO"
        message = (
            f"{verdict}: {result.get('source_id')}\nStatus: {result.get('status')}\n"
            f"Mode: {network}\nParser used: {parser_display}\n"
            f"Raw candidates: {raw_count}\nNormalized records: {normalized_count}\n"
            f"Operational status: {result.get('operational_status', 'unchanged')}\n\n{details[:1800]}"
        )
        if result.get("passed"):
            self.messagebox.showinfo("Source test complete", message)
        else:
            self.messagebox.showerror("Source test failed", message)

    def _build_results_tab(self) -> None:
        tk, ttk = self.tk, self.ttk

        self.results_notebook = ttk.Notebook(self.results_tab)
        self.results_notebook.grid(row=0, column=0, sticky="nsew")
        self.results_tab.rowconfigure(0, weight=1)

        current_tab = ttk.Frame(self.results_notebook, padding=10)
        log_tab = ttk.Frame(self.results_notebook, padding=10)
        last_tab = ttk.Frame(self.results_notebook, padding=10)
        email_tab = ttk.Frame(self.results_notebook, padding=10)
        source_tab = ttk.Frame(self.results_notebook, padding=10)
        self.results_notebook.add(current_tab, text="Current Status")
        self.results_notebook.add(log_tab, text="Build Log")
        self.results_notebook.add(last_tab, text="Last Run Result")
        self.results_notebook.add(email_tab, text="Email Import Summary")
        self.results_notebook.add(source_tab, text="Source Status")

        for tab in (current_tab, log_tab, last_tab, email_tab, source_tab):
            tab.columnconfigure(0, weight=1)
            tab.rowconfigure(0, weight=1)

        ttk.Label(current_tab, textvariable=self.status_var, wraplength=980, justify="left").grid(row=0, column=0, sticky="nw")
        ttk.Label(current_tab, textvariable=self.run_metrics_var, wraplength=980, justify="left").grid(row=1, column=0, sticky="nw", pady=(8, 0))

        log_body = ttk.Frame(log_tab)
        log_body.grid(row=0, column=0, sticky="nsew")
        log_body.columnconfigure(0, weight=1)
        log_body.rowconfigure(0, weight=1)
        self.log_text = tk.Text(log_body, height=12, wrap="none", state="disabled", font=LOG_FONT, bg="#f7f8fa", fg="#1f2937")
        log_yscroll = ttk.Scrollbar(log_body, orient="vertical", command=self.log_text.yview)
        log_xscroll = ttk.Scrollbar(log_body, orient="horizontal", command=self.log_text.xview)
        self.log_text.configure(yscrollcommand=log_yscroll.set, xscrollcommand=log_xscroll.set)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_yscroll.grid(row=0, column=1, sticky="ns")
        log_xscroll.grid(row=1, column=0, sticky="ew")
        self.log_text.tag_configure("stage", foreground="#17365D", font=LOG_FONT + ("bold",))
        self.log_text.tag_configure("action", foreground="#a43a1e", font=LOG_FONT + ("bold",))
        self.log_text.tag_configure("error", foreground="#b91c1c")

        ttk.Label(last_tab, textvariable=self.result_var, wraplength=980, justify="left").grid(row=0, column=0, sticky="nw")
        ttk.Label(last_tab, textvariable=self.result_paths_var, wraplength=980, justify="left").grid(row=1, column=0, sticky="nw", pady=(8, 0))

        ttk.Label(email_tab, textvariable=self.email_summary_var, wraplength=980, justify="left").grid(row=0, column=0, sticky="nw")
        ttk.Label(email_tab, textvariable=self.email_log_path_var, wraplength=980, justify="left").grid(row=1, column=0, sticky="nw", pady=(8, 0))

        ttk.Label(source_tab, textvariable=self.source_progress_var, wraplength=980, justify="left").grid(row=0, column=0, sticky="nw")
        ttk.Label(source_tab, textvariable=self.bc_bid_summary_var, wraplength=980, justify="left").grid(row=1, column=0, sticky="nw", pady=(8, 0))
        ttk.Label(source_tab, textvariable=self.source_status_var, wraplength=980, justify="left").grid(row=2, column=0, sticky="nw", pady=(8, 0))

    def _build_settings_tab(self) -> None:
        ttk = self.ttk

        panel = ttk.LabelFrame(self.settings_tab, text="Settings / Advanced")
        panel.grid(row=0, column=0, sticky="ew")
        panel.columnconfigure(1, weight=1)

        ttk.Label(panel, text="Output folder").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 6))
        ttk.Entry(panel, textvariable=self.out_dir_var).grid(row=0, column=1, sticky="ew", padx=6, pady=(10, 6))
        ttk.Button(panel, text="Browse...", command=self._browse_output_dir).grid(row=0, column=2, sticky="e", padx=(6, 10), pady=(10, 6))

        ttk.Label(panel, text="Display path").grid(row=1, column=0, sticky="w", padx=10, pady=6)
        ttk.Label(panel, textvariable=self.output_folder_display_var, wraplength=720, justify="left").grid(row=1, column=1, sticky="w", padx=6, pady=6)
        ttk.Button(panel, text="Copy Path", command=self._copy_output_folder_path).grid(row=1, column=2, sticky="e", padx=(6, 10), pady=6)

        ttk.Checkbutton(panel, text="Open workbook automatically when build completes", variable=self.auto_open_workbook_var).grid(
            row=2, column=0, columnspan=3, sticky="w", padx=10, pady=(6, 10)
        )

    def _browse_output_dir(self) -> None:
        chosen = self.filedialog.askdirectory(initialdir=str(DEFAULT_OUTPUT_ROOT))
        if chosen:
            self.out_dir_var.set(chosen)
            self._refresh_output_path_display()

    def _refresh_keywords_tab(
        self,
        *,
        force_reload: bool,
    ) -> tuple[dict[str, Any] | None, KeywordConfigError | None]:
        canonical = resolve_keywords_path(root=ROOT_DIR)
        self.keywords_path_var.set(str(canonical))
        self.keywords_presence_var.set("PRESENT" if canonical.exists() else "MISSING")
        try:
            result = validate_keywords_for_gui(ROOT_DIR, force_reload=force_reload)
        except KeywordConfigError as exc:
            lkg = inspect_last_known_good(root=ROOT_DIR)
            self.keywords_validation_status_var.set("INVALID — no usable rules loaded")
            self.keywords_times_var.set("Last validation: failed now")
            self.keywords_counts_var.set("Unavailable until a valid workbook or verified snapshot can load")
            self.keywords_categories_var.set("Unavailable")
            self.keywords_lkg_var.set(
                f"{str(lkg['status']).upper()} — {lkg['detail']}"
                + (f"; saved {lkg['saved_at']}" if lkg.get("saved_at") else "")
            )
            self.keywords_effective_var.set("NONE — runs are blocked before scoring")
            self.keywords_errors_var.set("\n".join(f"• {error}" for error in exc.errors))
            self.company_profile_var.set("Keywords invalid — run blocked")
            return None, exc

        categories = ", ".join(
            f"{result['category_labels'][category]}: {count}"
            for category, count in result["category_counts"].items()
        )
        self.keywords_validation_status_var.set(result["validation_status"])
        self.keywords_times_var.set(
            f"Last successful load: {result['last_successful_load_time']} | "
            f"Last validation: {result['last_validation_time']}"
        )
        self.keywords_counts_var.set(
            f"Active: {result['active_keyword_count']} | "
            f"Inactive: {result['inactive_keyword_count']}"
        )
        self.keywords_categories_var.set(categories or "No active categories")
        self.keywords_lkg_var.set(
            f"{result['last_known_good_status']}"
            + (f" | saved {result['last_known_good_saved_at']}" if result["last_known_good_saved_at"] else "")
            + (f" | {result['last_known_good_path']}" if result["last_known_good_path"] else "")
        )
        self.keywords_effective_var.set(
            ("CANONICAL" if result["source_kind"] == "canonical" else "LAST-KNOWN-GOOD FALLBACK")
            + f" — {result['effective_path']}"
        )
        self.keywords_errors_var.set(
            "None."
            if not result["validation_errors"]
            else "\n".join(f"• {error}" for error in result["validation_errors"])
        )
        self.company_profile_var.set(result["summary"])
        return result, None

    def _on_open_keywords_workbook(self) -> None:
        workbook = resolve_keywords_path(root=ROOT_DIR)
        if not workbook.exists():
            self.messagebox.showerror(
                "Keywords workbook missing",
                f"The canonical workbook is missing:\n{workbook}\n\nRestore it from keywords_template.xlsx or a trusted backup.",
            )
            return
        open_path_with_default_app(str(workbook))

    def _on_open_keywords_folder(self) -> None:
        folder = keywords_folder(ROOT_DIR)
        if not folder.exists():
            self.messagebox.showerror(
                "Keywords folder missing",
                f"The configuration folder is missing:\n{folder}\n\nRestore it from the package before running TENDER_FINDER.",
            )
            return
        open_path_with_default_app(str(folder))

    def _on_validate_keywords(self) -> None:
        result, error = self._refresh_keywords_tab(force_reload=True)
        if error is not None:
            self.messagebox.showerror("Keywords validation failed", str(error))
            return
        assert result is not None
        dialog = self.messagebox.showinfo if result["source_kind"] == "canonical" else self.messagebox.showwarning
        dialog(
            "Keywords validation complete",
            f"{result['summary']}\n\n{result['rescore_semantics']}\n\n"
            f"{result['rescore_exceptions']}\n\nCanonical workbook:\n{result['path']}\n\n"
            f"Effective workbook:\n{result['effective_path']}",
        )

    def _on_reload_keywords(self) -> None:
        clear_keywords_cache()
        result, error = self._refresh_keywords_tab(force_reload=True)
        if error is not None:
            self.messagebox.showerror("Keywords reload failed", str(error))
            return
        assert result is not None
        self.messagebox.showinfo(
            "Keywords reloaded",
            f"Reloaded {result['active_keyword_count']} active and "
            f"{result['inactive_keyword_count']} inactive rules from {result['source_kind']}.",
        )

    def _on_view_keywords_instructions(self) -> None:
        self.messagebox.showinfo(
            "How to edit keywords.xlsx",
            "Open the workbook and edit the Keywords sheet. Use match_type contains, exact, or regex; "
            "use whole-number weights; set active to Y or N; keep category IDs from the dropdown.\n\n"
            "Save the workbook, return here, choose Validate Keywords, then Reload Keywords. "
            "Every new run uses RESCORE_ALWAYS and writes Keyword_Change_Audit. Unsafe or invalid regex "
            "rules are rejected before scoring. The Instructions sheet in the workbook contains the full reference.",
        )

    def _selected_email_folder(self) -> Path:
        ensure_email_alert_dirs(ROOT_DIR)
        config = load_email_provider_config(ROOT_DIR)
        if config.import_path:
            return Path(config.import_path)
        return email_inbox_dir(ROOT_DIR)

    def _email_intake_status_text(self) -> str:
        ensure_email_alert_dirs(ROOT_DIR)
        config = load_email_provider_config(ROOT_DIR)
        connected = "YES" if config.connected else "NO"
        return f"Provider: {provider_display_name(config.provider)} | Mailbox connected: {connected}"

    def _refresh_output_path_display(self) -> None:
        path = self.out_dir_var.get().strip()
        self.output_folder_full_var.set(path)
        self.output_folder_display_var.set(shorten_display_path(path))

    def _refresh_email_intake_status(self) -> None:
        self.email_intake_var.set(self._email_intake_status_text())
        folder = str(self._selected_email_folder())
        self.email_folder_full_var.set(folder)
        label = f"Selected import folder: {shorten_display_path(folder)}"
        is_fixture = is_fixture_source_folder(folder)
        if is_fixture:
            label += "  [TEST ONLY - checked-in test fixtures, not a real inbox]"
        self.email_folder_var.set(label)
        # _refresh_email_intake_status() runs once during initial widget
        # setup, before _build_email_tab() has created this label - guard
        # against that first, label-less call.
        email_folder_label = getattr(self, "email_folder_label", None)
        if email_folder_label is not None:
            email_folder_label.configure(foreground="#a43a1e" if is_fixture else "")

    def _copy_to_clipboard(self, text: str) -> None:
        if not text:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()

    def _copy_output_folder_path(self) -> None:
        self._copy_to_clipboard(self.output_folder_full_var.get())

    def _copy_email_folder_path(self) -> None:
        self._copy_to_clipboard(self.email_folder_full_var.get())

    def _copy_output_paths(self) -> None:
        if not self.last_results:
            return
        text = "\n".join([
            f"Workbook: {self.last_results.get('workbook_path', '')}",
            f"Output folder: {self.last_results.get('out_dir', '')}",
            f"Report: {self.last_results.get('report_path', '')}",
            f"Summary: {self.last_results.get('summary_path', '')}",
        ])
        self._copy_to_clipboard(text)

    def _open_report(self) -> None:
        report_path = self.last_results.get("report_path")
        if report_path and os.path.exists(report_path):
            open_path_with_default_app(report_path)

    def _open_summary(self) -> None:
        summary_path = self.last_results.get("summary_path")
        if summary_path and os.path.exists(summary_path):
            open_path_with_default_app(summary_path)

    def _open_email_dry_run_log(self) -> None:
        if self._email_dry_run_log_path and os.path.exists(self._email_dry_run_log_path):
            open_path_with_default_app(self._email_dry_run_log_path)

    def _on_run_full_clicked(self) -> None:
        self.run_mode_var.set(RUN_MODE_FULL)
        self.mode_summary_var.set("Current mode: Live Run")
        self._on_run_clicked()

    def _on_run_fast_clicked(self) -> None:
        self.run_mode_var.set(RUN_MODE_FAST)
        self.mode_summary_var.set("Current mode: Offline/Test Run")
        self._on_run_clicked()

    def _on_self_test_clicked(self) -> None:
        if self._self_test_running or (self.worker is not None and self.worker.is_running()):
            return
        try:
            preflight = validate_runtime_configuration(root=ROOT_DIR)
            if not preflight.get("passed"):
                raise RuntimeError(f"Required offline review workbook is missing: {preflight.get('review_xlsx')}")
        except Exception as exc:
            self._set_status("Self-Test preflight failed.", urgent=True)
            self.messagebox.showerror("Self-Test FAIL", str(exc))
            return

        while True:
            try:
                self._self_test_queue.get_nowait()
            except queue.Empty:
                break
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self._self_test_running = True
        self._self_test_proc = None
        self._set_run_state("self_test")
        self.progress.start(12)
        self._start_spinner()
        self._set_status("Self-Test running offline in isolated state...")
        self.run_metrics_var.set("Self-Test uses --no-fetch, a unique state root, and the same engine/workbook validation as a real run.")
        self._append_log("SELF_TEST: starting offline end-to-end validation; no live source fetch is allowed.")

        def work() -> None:
            try:
                result = run_engine_self_test(
                    root=ROOT_DIR,
                    on_line=lambda line: self._self_test_queue.put(("line", line)),
                    started_callback=lambda proc: setattr(self, "_self_test_proc", proc),
                )
                self._self_test_queue.put(("result", result))
            except Exception as exc:
                self._self_test_queue.put(("error", str(exc)))

        threading.Thread(target=work, daemon=True).start()
        self.root.after(100, self._poll_self_test_queue)

    def _poll_self_test_queue(self) -> None:
        terminal: tuple[str, Any] | None = None
        try:
            while True:
                kind, payload = self._self_test_queue.get_nowait()
                if kind == "line":
                    self._append_log(str(payload))
                else:
                    terminal = (kind, payload)
                    break
        except queue.Empty:
            pass
        if terminal is None:
            self.root.after(100, self._poll_self_test_queue)
            return

        self._self_test_running = False
        self._self_test_proc = None
        self.progress.stop()
        self._stop_spinner()
        self._set_run_state("idle")
        kind, payload = terminal
        if kind == "error":
            self._set_status("Self-Test FAIL — preflight or engine error.", urgent=True)
            self.run_metrics_var.set(f"Self-Test FAIL: {payload}")
            self.messagebox.showerror("Self-Test FAIL", str(payload))
            return

        result = payload
        verdict = "PASS" if result.passed else "FAIL"
        self_test_counts: dict[str, Any] = {}
        try:
            self_test_counts = json.loads(result.manifest_path.read_text(encoding="utf-8")).get("self_test", {})
        except (OSError, ValueError):
            pass
        counts_text = (
            f"passed {self_test_counts.get('passed', '?')} | "
            f"failed {self_test_counts.get('failed', '?')} | "
            f"skipped {self_test_counts.get('skipped', '?')} | "
            f"intentionally excluded {self_test_counts.get('intentionally_excluded', '?')} | "
            f"not tested (no fixture) {self_test_counts.get('not_tested_fixture', '?')}"
        )
        self.last_results = read_run_results(result.out_dir)
        self.last_results["out_dir"] = str(result.out_dir)
        self.last_results["manifest_path"] = str(result.manifest_path)
        self.open_folder_button.configure(state="normal")
        if self.last_results.get("workbook_path"):
            self.open_workbook_button.configure(state="normal")
        self.result_paths_var.set(
            f"Self-Test manifest: {result.manifest_path}\nOutput folder: {result.out_dir}\n"
            f"Workbook: {self.last_results.get('workbook_path', '')}"
        )
        self.result_var.set(
            f"Self-Test {verdict} | {counts_text} | exit code {result.return_code} | "
            f"artifacts {len(result.artifacts)} | {result.manifest_path}"
        )
        self.run_metrics_var.set(
            f"Self-Test {verdict}: {counts_text}. Exit code: {result.return_code}. "
            "Manifest and isolated artifacts are available in the output folder."
        )
        self._set_status(f"Self-Test {verdict}." if result.passed else "Self-Test FAIL — inspect engine.log and manifest.", urgent=not result.passed)
        if result.passed:
            self.messagebox.showinfo(
                "Self-Test PASS",
                f"Offline self-test passed.\n{counts_text}\n\nManifest:\n{result.manifest_path}",
            )
        else:
            self.messagebox.showerror(
                "Self-Test FAIL",
                f"{counts_text}\nExit code: {result.return_code}\n\nManifest:\n{result.manifest_path}",
            )

    def _on_create_open_email_import_folder(self) -> None:
        paths = ensure_email_alert_dirs(ROOT_DIR)
        inbox = paths["inbox"]
        path = connect_email_provider(
            "manual_folder",
            account_label=provider_display_name("manual_folder"),
            import_path=str(inbox),
            root=ROOT_DIR,
        )
        self._refresh_email_intake_status()
        open_path_with_default_app(str(inbox))
        self.messagebox.showinfo(
            "Email Alert Intake",
            "\n".join([
                f"Email import folder: {inbox}",
                "",
                "Save or copy approved .eml alert files into this folder, then click Test Email Import.",
                "",
                f"Saved local config: {path}",
            ]),
        )

    def _on_select_existing_email_folder(self) -> None:
        ensure_email_alert_dirs(ROOT_DIR)
        chosen = self.filedialog.askdirectory(
            title="Choose local folder with .eml alerts",
            initialdir=str(self._selected_email_folder()),
        )
        if not chosen:
            return
        path = connect_email_provider(
            "manual_folder",
            account_label=provider_display_name("manual_folder"),
            import_path=chosen,
            root=ROOT_DIR,
        )
        self._refresh_email_intake_status()
        self.messagebox.showinfo(
            "Select Existing Email Folder",
            f"Saved selected folder to:\n{path}\n\nSelected email folder:\n{chosen}",
        )

    def _on_test_email_intake(self) -> None:
        ensure_email_alert_dirs(ROOT_DIR)
        config = load_email_provider_config(ROOT_DIR)
        result = test_email_intake(self._selected_email_folder(), provider_config=config, root=ROOT_DIR)
        self._refresh_email_intake_status()
        self._email_dry_run_log_path = result.log_path
        self.email_log_path_var.set(f"Dry-run log: {result.log_path or 'not written'}")
        if result.log_path:
            self.open_email_log_button.configure(state="normal")
        self.email_summary_var.set(
            "\n".join([
                f"Folder used: {result.selected_folder}",
                f".eml files found: {result.alert_emails_found}",
                f"Parsed rows: {result.tender_rows_parsed}",
                f"Civil-relevant rows: {result.civil_alerts_found}",
                f"BID NOW candidates: {result.open_actionable_rows}",
                f"Duplicates: {result.duplicate_emails_detected}",
                f"Rejected: {result.emails_rejected}",
                f"Rejected reasons: {result.rejected_reasons or {'none': 0}}",
            ])
        )
        self.messagebox.showinfo(
            "Test Email Import",
            "\n".join([
                f"Selected folder: {result.selected_folder}",
                f"Mailbox connected: {'YES' if result.mailbox_connected else 'NO'}",
                f".eml files found: {result.alert_emails_found}",
                f"Providers: {result.recognized_provider_counts}",
                f"Emails parsed successfully: {result.alerts_parsed}",
                f"Emails rejected: {result.emails_rejected}",
                f"Rejected reasons: {result.rejected_reasons}",
                f"Tender rows parsed: {result.tender_rows_parsed}",
                f"Civil-relevant rows: {result.civil_alerts_found}",
                f"Open/actionable rows: {result.open_actionable_rows}",
                f"Duplicate emails detected: {result.duplicate_emails_detected}",
                f"Dry-run log: {result.log_path}",
            ]),
        )

    def _on_run_demo_with_email_alerts(self) -> None:
        self._refresh_email_intake_status()
        self.notebook.select(self.run_tab)
        self._on_run_clicked()

    def _on_open_processed_folder(self) -> None:
        ensure_email_alert_dirs(ROOT_DIR)
        open_path_with_default_app(str(email_processed_dir(ROOT_DIR)))

    def _on_open_rejected_folder(self) -> None:
        ensure_email_alert_dirs(ROOT_DIR)
        open_path_with_default_app(str(email_rejected_dir(ROOT_DIR)))

    def _on_reset_to_default_import_folder(self) -> None:
        path = reset_email_import_folder_to_default(ROOT_DIR)
        self._refresh_email_intake_status()
        self.messagebox.showinfo(
            "Email Alert Intake",
            f"Reset the import folder to:\n{email_inbox_dir(ROOT_DIR)}\n\nConfig file:\n{path}",
        )

    def _on_check_bc_bid_public_access(self) -> None:
        self.bc_bid_summary_var.set("BC Bid status: manual preflight requested. Use a live sweep for parsed rows, pages fetched, and browser-check details.")
        self.messagebox.showinfo(
            "Check BC Bid Public Access",
            "\n".join([
                "OK_PUBLIC_ACCESS: run a Live Run and TENDER_FINDER will report rows parsed when the public page loads normally.",
                "BROWSER_CHECK_NEEDS_USER: TENDER_FINDER may open a visible browser and wait for you to clear the public browser-check yourself.",
                "BLOCKED: if BC Bid blocks the public session, TENDER_FINDER reports that honestly and does not ask for credentials.",
                "PARSED_ROWS / PAGES_FETCHED / HARD_CAP_REACHED are reported in the workbook and summary after the run.",
            ]),
        )

    def _append_log(self, line: str) -> None:
        tag = classify_log_line(line)
        self.log_text.configure(state="normal")
        if tag:
            self.log_text.insert("end", line + "\n", tag)
        else:
            self.log_text.insert("end", line + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _set_status(self, text: str, urgent: bool = False) -> None:
        self.status_var.set(text)
        try:
            self.status_label.configure(foreground="#a43a1e" if urgent else "#111827")
        except Exception:
            pass

    def _animate_spinner(self) -> None:
        self.spinner_angle = (self.spinner_angle + 12) % 360
        self.spinner_canvas.itemconfigure(self.spinner_arcs[0], start=self.spinner_angle)
        self.spinner_canvas.itemconfigure(self.spinner_arcs[1], start=360 - self.spinner_angle)
        self.spinner_job = self.root.after(80, self._animate_spinner)

    def _start_spinner(self) -> None:
        if self.spinner_job is None:
            self._animate_spinner()

    def _stop_spinner(self) -> None:
        if self.spinner_job is not None:
            self.root.after_cancel(self.spinner_job)
            self.spinner_job = None

    def _set_run_state(self, state: str) -> None:
        """One place for button enable/disable so no error path can leave
        the window in a dead state. States: idle, running, paused."""
        if state == "running":
            self.run_button.configure(state="disabled")
            self.run_full_button.configure(state="disabled")
            self.run_fast_button.configure(state="disabled")
            self.self_test_button.configure(state="disabled")
            self.pause_button.configure(state="normal")
            self.stop_button.configure(state="normal")
            self.resume_button.configure(state="disabled")
        elif state == "self_test":
            self.run_button.configure(state="disabled")
            self.run_full_button.configure(state="disabled")
            self.run_fast_button.configure(state="disabled")
            self.self_test_button.configure(state="disabled")
            self.pause_button.configure(state="disabled")
            self.stop_button.configure(state="disabled")
            self.resume_button.configure(state="disabled")
        elif state == "paused":
            self.run_button.configure(state="normal")
            self.run_full_button.configure(state="normal")
            self.run_fast_button.configure(state="normal")
            self.self_test_button.configure(state="normal")
            self.pause_button.configure(state="disabled")
            self.stop_button.configure(state="disabled")
            self.resume_button.configure(state="normal")
        else:  # idle
            self.run_button.configure(state="normal")
            self.run_full_button.configure(state="normal")
            self.run_fast_button.configure(state="normal")
            self.self_test_button.configure(state="normal")
            self.pause_button.configure(state="disabled")
            self.stop_button.configure(state="disabled")
            self.resume_button.configure(state="disabled")

    def _on_pause_clicked(self) -> None:
        """Task E: stage-safe pause. Touches the pause signal file; the
        engine stops at the NEXT safe stage boundary (never mid-write) and
        exits with the pause code."""
        if self.worker is None or not self.worker.is_running():
            return
        try:
            self.worker.out_dir.mkdir(parents=True, exist_ok=True)
            (self.worker.out_dir / "tenderfinder_pause.signal").write_text("pause", encoding="utf-8")
            self._append_log(
                "Pause requested - TENDER_FINDER will stop at the next safe checkpoint. "
                "Stages are never cut off mid-write, so this can take a moment."
            )
            self._set_status("Pausing at the next safe checkpoint...")
            self.pause_button.configure(state="disabled")
        except Exception as exc:
            self._append_log(f"WARNING: could not request a pause: {exc}")

    def _on_stop_clicked(self) -> None:
        if self.worker is None or not self.worker.is_running():
            return
        if not self.messagebox.askyesno(
            "Stop build",
            "Stop the running build? Output produced so far stays on disk "
            "and is marked as partial.",
        ):
            return
        self._append_log("Stop clicked - terminating the build and any browser it opened...")
        self.worker.stop()

    def _on_resume_clicked(self) -> None:
        """Task E: honest resume. This pipeline recomputes from its inputs,
        so resuming restarts the build from the beginning into the same
        output folder - stated plainly, never pretended otherwise."""
        if self._last_cmd is None or self._last_out_dir is None:
            return
        checkpoint = self._last_out_dir / "tenderfinder_checkpoint.json"
        stage = ""
        try:
            import json as _json
            if checkpoint.exists():
                stage = _json.loads(checkpoint.read_text(encoding="utf-8")).get("stage", "")
        except Exception:
            pass
        if stage:
            self._append_log(
                f"Resuming after pause at checkpoint '{stage}'. Stages before the "
                "workbook cannot skip ahead safely, so TENDER_FINDER restarts the build from "
                "the beginning into the same output folder."
            )
        else:
            self._append_log(
                "Resuming. TENDER_FINDER restarts the build from the beginning into the same "
                "output folder (no safe mid-run checkpoint was found to skip to)."
            )
        checkpoint.unlink(missing_ok=True)
        self._start_build(self._last_cmd, self._last_out_dir)

    def _on_continue_clicked(self) -> None:
        """Task D: the user says they finished BC Bid's browser check. Touch
        the signal file the engine announced; the engine re-checks the page
        immediately and either continues or prints an honest 'still on the
        check page' message."""
        if not self._continue_signal_file:
            return
        try:
            Path(self._continue_signal_file).write_text("continue", encoding="utf-8")
            self._append_log("Continue clicked - telling TENDER_FINDER to re-check the BC Bid page now...")
        except Exception as exc:
            self._append_log(f"WARNING: could not signal the build process: {exc}")

    def _status_from_log(self, line: str) -> tuple[str, bool]:
        """Returns (status_text, urgent). urgent=True means BC Bid needs a
        person to act in the browser window it opened - shown in a
        distinct color so it does not get lost among routine progress
        lines, and never collapsed into a plain "open civil 0" reading."""
        if line.startswith("TENDER_FINDER_USER_ACTION_REQUIRED:"):
            return "ACTION NEEDED: " + line.split(":", 1)[1].strip(), True
        if line.startswith("TENDER_FINDER_INFO:"):
            return line.split(":", 1)[1].strip(), False
        if "BC_BID_BLOCKED_BROWSER_CHECK_USER_ACTION_REQUIRED" in line:
            return "BC Bid needs a person to clear its browser-check page - see the log for details.", True
        if line.startswith("TENDER_FINDER_STAGE:"):
            return line.replace("TENDER_FINDER_STAGE:", "", 1).strip(), False
        low = line.lower()
        if line.startswith("future="):
            return "Track A loaded: future projects, watchlist, and analyzed rows are ready.", False
        if "surrey_bids_public" in low:
            return "Checking Surrey public tender pages and extracting status/date fields.", False
        if "bc_bid_public" in low or "bc bid" in low:
            return "Checking BC Bid public browse status and recording any blocker honestly.", False
        if line.startswith("Track B total time"):
            return "Live tender sweep finished; preparing workbook output.", False
        if line.startswith("DONE in"):
            return "Build finished. Opening the result workbook and output folder.", False
        return "", False

    def _on_run_clicked(self) -> None:
        out_dir = Path(self.out_dir_var.get().strip())
        fast_mode = self.run_mode_var.get() == RUN_MODE_FAST
        ensure_email_alert_dirs(ROOT_DIR)
        try:
            keyword_result = validate_keywords_for_gui(ROOT_DIR, force_reload=True)
        except KeywordConfigError as exc:
            self.company_profile_var.set(keyword_profile_status(ROOT_DIR))
            self._set_status("Run cancelled - keywords.xlsx did not pass validation.", urgent=True)
            self.messagebox.showerror("Keywords validation failed", str(exc))
            return
        self.company_profile_var.set(keyword_result["summary"])
        self._refresh_keywords_tab(force_reload=False)
        using_keyword_fallback = keyword_result["source_kind"] == "last_known_good"
        if using_keyword_fallback:
            self.messagebox.showwarning(
                "Using last-known-good keyword rules",
                "The canonical keywords.xlsx is invalid or missing. This run will use the verified "
                "last-known-good workbook snapshot shown on the Keywords tab. Canonical validation "
                "errors will remain visible and will be recorded in the run manifest.",
            )
        self.mode_summary_var.set("Current mode: Offline/Test Run" if fast_mode else "Current mode: Live Run")

        review_xlsx, review_source = discover_review_xlsx(ROOT_DIR)
        if review_xlsx is None:
            # Product rule: never dead-end on a missing workbook. Explain,
            # let the user browse for it, remember the choice, and continue.
            if not self.messagebox.askokcancel(
                "Review workbook needed", missing_workbook_explanation(ROOT_DIR),
            ):
                self._set_status("Run cancelled - the review workbook is required for Track A.", urgent=True)
                return
            chosen = self.filedialog.askopenfilename(
                title="Select the reviewed-leads workbook (all_live_review.xlsx)",
                filetypes=[("Excel workbook", "*.xlsx"), ("All files", "*.*")],
            )
            if not chosen:
                self._set_status("Run cancelled - no review workbook selected.", urgent=True)
                return
            review_xlsx = Path(chosen)
            review_source = "selected by you just now"
            try:
                save_runtime_config(ROOT_DIR, {"review_xlsx": str(review_xlsx)})
                self._append_log(f"Saved the review workbook path for future runs: {review_xlsx}")
            except Exception as exc:
                self._append_log(f"WARNING: could not save the workbook path for future runs: {exc}")

        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self._source_lines_seen.clear()
        self._expected_source_status_lines = expected_source_status_lines(ROOT_DIR)
        self.source_progress_var.set(f"Sources completed: 0 / {self._expected_source_status_lines}")
        self.source_status_var.set("No source statuses yet for this run.")
        self.bc_bid_summary_var.set("BC Bid status: waiting for this run.")
        self.run_metrics_var.set("Build in progress. TENDER_FINDER will keep the current step, source progress, and post-run actions updated here.")

        cmd = build_demo_command(
            review_xlsx,
            out_dir,
            fast_mode,
            email_import_path=str(self._selected_email_folder()),
        )
        self._append_log(f"Review workbook: {review_xlsx} (via {review_source})")
        if using_keyword_fallback:
            self._append_log(
                "WARNING: canonical keywords.xlsx is invalid; verified last-known-good snapshot is in use."
            )
        self._append_log(f"Running: {' '.join(cmd)}")
        if fast_mode:
            self._append_log("Mode explanation: Offline/Test Run skips every live tender site and rebuilds from local inputs.")
        else:
            self._append_log(
                "Mode explanation: Live Run reads local proven leads, then checks public "
                "tender pages and BC Bid public browse. BC Bid may open its own browser window if "
                "it needs a person to clear a browser-check/CAPTCHA page - TENDER_FINDER never logs in or "
                "solves a CAPTCHA on your behalf."
            )
        self._start_build(cmd, out_dir)

    def _start_build(self, cmd: list[str], out_dir: Path) -> None:
        """Shared by Run and Resume: launch the worker with clean button
        state and no stale pause signal left over from a prior run."""
        self._last_cmd = cmd
        self._last_out_dir = out_dir
        try:
            (out_dir / "tenderfinder_pause.signal").unlink(missing_ok=True)
        except Exception:
            pass
        self._set_run_state("running")
        self.open_folder_button.configure(state="disabled")
        self.open_workbook_button.configure(state="disabled")
        self.open_report_button.configure(state="disabled")
        self.open_summary_button.configure(state="disabled")
        self.copy_paths_button.configure(state="disabled")
        self.progress.start(12)
        self._set_status("Starting TENDER_FINDER build...")
        self._start_spinner()
        self.worker = DemoBuildWorker(cmd, out_dir)
        self.worker.start()
        self.root.after(100, self._poll_log_queue)

    def _set_continue_button_visibility(self, visible: bool) -> None:
        if visible:
            self.continue_button.configure(state="normal")
            self.continue_button.grid()
        else:
            self.continue_button.configure(state="disabled")
            self.continue_button.grid_remove()

    def _update_source_progress_from_line(self, line: str) -> None:
        parsed = parse_source_status_line(line)
        if not parsed:
            return
        source_id = parsed["source_id"]
        status = parsed["status"]
        self._source_lines_seen.add(source_id)
        self.source_progress_var.set(
            f"Sources completed: {len(self._source_lines_seen)} / {self._expected_source_status_lines}"
        )
        self.source_status_var.set(f"Last source status: {source_id} -> {status}")
        if source_id == "bc_bid_public":
            pages = ""
            pages_match = re.search(r"pages_fetched=(\d+)", line)
            cap_match = re.search(r"hard_cap=(\d+)", line)
            if pages_match:
                pages = f" | pages fetched: {pages_match.group(1)}"
            if cap_match:
                pages += f" | hard cap: {cap_match.group(1)}"
            self.bc_bid_summary_var.set(f"BC Bid status: {status}{pages}")
        elif source_id == "email_alert_intake":
            self.email_summary_var.set(line)

    def _poll_log_queue(self) -> None:
        assert self.worker is not None
        try:
            while True:
                line = self.worker.log_queue.get_nowait()
                if line.startswith(DONE_SENTINEL):
                    self._on_build_finished(success=True)
                    return
                if line.startswith(ERROR_SENTINEL):
                    self._on_build_finished(success=False)
                    return
                if line.startswith(PAUSED_SENTINEL):
                    self._on_build_paused()
                    return
                if line.startswith(STOPPED_SENTINEL):
                    self._on_build_stopped()
                    return
                if line.startswith(CANCELLED_SENTINEL):
                    # Only reachable if the queue is still being polled after
                    # a cancel - normally _on_close_requested destroys the
                    # window immediately, so this loop never runs again.
                    self.progress.stop()
                    self._stop_spinner()
                    self._set_status("Build cancelled.")
                    self._set_run_state("idle")
                    return
                signal_path = parse_continue_signal_file(line)
                if signal_path:
                    self._continue_signal_file = signal_path
                    self._set_continue_button_visibility(True)
                elif line.startswith("TENDER_FINDER_STAGE:") and self._continue_signal_file:
                    # The engine moved past the BC Bid wait - the button no
                    # longer has anything to signal.
                    self._continue_signal_file = ""
                    self._set_continue_button_visibility(False)
                status, urgent = self._status_from_log(line)
                if status:
                    self._set_status(status, urgent=urgent)
                self._update_source_progress_from_line(line)
                if should_show_continue_button(self._continue_signal_file, line):
                    self._set_continue_button_visibility(True)
                self._append_log(line)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_log_queue)

    def _on_close_requested(self) -> None:
        if self.worker is not None and self.worker.is_running():
            if not self.messagebox.askyesno(
                "Build in progress",
                "A build is in progress. Closing now will stop it. Close anyway?",
            ):
                return
            self._append_log("User closed the window while a build was running - stopping it now...")
            self.worker.cancel()
        elif self._self_test_running:
            if not self.messagebox.askyesno(
                "Self-Test in progress",
                "The offline Self-Test is still running. Closing now will stop it. Close anyway?",
            ):
                return
            if self._self_test_proc is not None:
                terminate_process_tree(self._self_test_proc)
        self.root.destroy()

    def _on_build_paused(self) -> None:
        """The engine exited at a safe checkpoint after a Pause request."""
        self.progress.stop()
        self._stop_spinner()
        self._continue_signal_file = ""
        self._set_continue_button_visibility(False)
        self._set_run_state("paused")
        assert self.worker is not None
        stage = ""
        try:
            import json as _json
            checkpoint = self.worker.out_dir / "tenderfinder_checkpoint.json"
            if checkpoint.exists():
                stage = _json.loads(checkpoint.read_text(encoding="utf-8")).get("stage", "")
        except Exception:
            pass
        stage_text = f" at safe checkpoint '{stage}'" if stage else ""
        self._set_status(f"Paused{stage_text}. Click Resume to continue, or Run TENDER_FINDER Sweep for a fresh run.")
        self.result_var.set(
            f"PAUSED{stage_text}. Output in {self.worker.out_dir} is consistent up to this stage - "
            "nothing was cut off mid-write. Resume restarts the build from the beginning into the "
            "same folder (stages before the workbook cannot skip ahead safely)."
        )
        self.run_metrics_var.set("Build paused safely. Use Resume to restart the run into the same output folder.")

    def _on_build_stopped(self) -> None:
        """The Stop button terminated the build intentionally."""
        self.progress.stop()
        self._stop_spinner()
        self._continue_signal_file = ""
        self._set_continue_button_visibility(False)
        self._set_run_state("idle")
        assert self.worker is not None
        out_dir = self.worker.out_dir
        self._set_status("Build stopped by you. Any output produced so far is marked as partial.", urgent=True)
        has_files = out_dir.exists() and any(out_dir.iterdir())
        if has_files:
            self.result_var.set(
                f"STOPPED by you. Partial output is in {out_dir} - see PARTIAL_OUTPUT_README.txt "
                "and tenderfinder_stage_progress.json there for exactly how far the build got."
            )
            self.last_results = {"out_dir": str(out_dir)}
            self.open_folder_button.configure(state="normal")
        else:
            self.result_var.set("STOPPED by you before any output was written.")
        self.run_metrics_var.set("Build stopped. Partial output may exist; use Open Output Folder for details.")

    def _on_build_finished(self, success: bool) -> None:
        self.progress.stop()
        self._stop_spinner()
        self._set_run_state("idle")
        self._continue_signal_file = ""
        self._set_continue_button_visibility(False)
        assert self.worker is not None
        out_dir = self.worker.out_dir

        if not success:
            self._set_status("Build failed. The error log path is shown below.", urgent=True)
            error_log = out_dir / "gui_run_error.log"
            self.result_var.set(
                f"Build FAILED (exit code {self.worker.return_code}). "
                f"Full output was saved to: {error_log}"
            )
            self.run_metrics_var.set(f"Build failed. Exit code: {self.worker.return_code}.")
            self.messagebox.showerror(
                "TENDER_FINDER build failed",
                f"The TENDER_FINDER run exited with an error (code {self.worker.return_code}).\n\n"
                f"Full output was written to:\n{error_log}",
            )
            return

        self._set_status("Build complete. Review the workbook, talk track, and report in the output folder.")
        self.last_results = read_run_results(out_dir)
        if self.last_results.get("workbook_path"):
            self.open_workbook_button.configure(state="normal")
        self.open_folder_button.configure(state="normal")
        self.open_report_button.configure(state="normal" if self.last_results.get("report_path") else "disabled")
        self.open_summary_button.configure(state="normal" if self.last_results.get("summary_path") else "disabled")
        self.copy_paths_button.configure(state="normal")

        summary_lines = build_completion_summary_lines(self.last_results, out_dir)
        email_rows = self.last_results.get("email_bid_now_rows", "?")
        self.run_metrics_var.set(
            f"Build complete. BID NOW: {self.last_results.get('bid_now_total', '?')} | "
            f"BID LATER: {self.last_results.get('bid_later', '?')} | "
            f"Email rows: {email_rows} | Build time: {self.last_results.get('build_time', '?')}"
        )
        self.result_var.set(" | ".join(
            l for l in summary_lines if l and not l.startswith("Output folder")
        ).replace("\n", " "))
        self.result_paths_var.set(
            "\n".join([
                f"Workbook: {self.last_results.get('workbook_path', '')}",
                f"Output folder: {self.last_results.get('out_dir', '')}",
                f"Report: {self.last_results.get('report_path', '')}",
                f"Summary: {self.last_results.get('summary_path', '')}",
            ])
        )
        self.bc_bid_summary_var.set(f"BC Bid status: {self.last_results.get('bc_bid_status', 'UNKNOWN')}")
        try:
            stage_path = Path(out_dir) / "tenderfinder_stage_progress.json"
            if stage_path.exists():
                payload = json.loads(stage_path.read_text(encoding="utf-8"))
                if "completed" not in payload.get("stages", []):
                    self.source_status_var.set("WARNING: build finished but stage progress is missing 'completed'.")
        except Exception:
            pass
        workbook_path = self.last_results.get("workbook_path", "")
        if should_auto_open_workbook(self.auto_open_workbook_var.get(), workbook_path, os.environ.get("TENDER_FINDER_DEMO_NO_OPEN")):
            try:
                open_path_with_default_app(workbook_path)
            except Exception as exc:
                self.messagebox.showwarning(
                    "Open Workbook",
                    f"Build succeeded but TENDER_FINDER could not open the workbook automatically.\n\n{workbook_path}\n\nReason: {exc}",
                )
        self.messagebox.showinfo("TENDER_FINDER build complete", "\n".join(summary_lines))

    def _open_output_folder(self) -> None:
        out_dir = self.last_results.get("out_dir")
        if out_dir and os.path.exists(out_dir):
            open_path_with_default_app(out_dir)

    def _open_workbook(self) -> None:
        workbook_path = self.last_results.get("workbook_path")
        if workbook_path and os.path.exists(workbook_path):
            open_path_with_default_app(workbook_path)

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    app = TenderFinderLauncherApp()
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

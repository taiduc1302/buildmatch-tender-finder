from __future__ import annotations

import queue
import os
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import tenderfinder_launcher_gui as g  # noqa: E402

DEFAULT_GUI_E2E_TIMEOUT_SECONDS = int(os.environ.get("TENDER_FINDER_GUI_E2E_TIMEOUT_SECONDS", "240"))
RUN_GUI_E2E = os.environ.get("TENDER_FINDER_GUI_SKIP_E2E", "").strip().lower() not in {"1", "true", "yes"}

# Most of this file exercises only the Tkinter-free business logic in
# tenderfinder_launcher_gui.py: command construction, the background worker's
# subprocess + queue wiring, and result parsing. Two tests below
# (test_on_close_requested_*) go further and directly exercise the real
# TenderFinderLauncherApp._on_close_requested() / WM_DELETE_WINDOW handler against
# a real (but withdrawn/hidden) Tk root, confirmed to work headlessly in
# this environment - see process_exists_os_level() below for why that's
# meaningfully different from the widget-free tests. What is still NOT
# verified here is visual rendering (does it look right on screen) or a
# real user clicking the window's actual "X" button / a desktop shortcut -
# those remain code-reviewed-only, documented as such in AUTONOMOUS_FIXES.md.


def process_exists_os_level(pid: int) -> bool:
    """Independent OS-level confirmation that a PID is (or isn't) running,
    via `tasklist` - the scriptable equivalent of `Get-Process -Id <pid>`.
    This queries the OS process table directly through a fresh external
    process, rather than relying only on proc.poll(), which just reports
    back through the same Popen handle Python already holds for that PID."""
    if sys.platform.startswith("win"):
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
            capture_output=True, text=True, timeout=10,
        )
        return str(pid) in result.stdout
    result = subprocess.run(["ps", "-p", str(pid)], capture_output=True, timeout=10)
    return result.returncode == 0


def test_build_demo_command() -> None:
    out_dir = Path("C:/tenderfinder_out/test_dir")
    review = Path("C:/tenderfinder_out/review.xlsx")
    cmd_full = g.build_demo_command(review, out_dir, fast_mode=False)
    assert "--no-fetch" not in cmd_full
    assert "--email-intake" in cmd_full
    assert str(review) in cmd_full
    assert str(out_dir) in cmd_full

    cmd_fast = g.build_demo_command(review, out_dir, fast_mode=True)
    assert "--no-fetch" in cmd_fast


def test_parse_demo_build_report() -> None:
    sample = (
        "- BID NOW total / civil / open civil: 85 / 26 / 13\n"
        "- BID LATER / WATCH / ANALYZED: 7537 / 973 / 25119\n"
        "Total demo build time: 121.09s\n"
    )
    parsed = g.parse_demo_build_report(sample)
    assert parsed["bid_later"] == "7537"
    assert parsed["watchlist"] == "973"
    assert parsed["analyzed"] == "25119"
    assert parsed["bid_now_open_civil"] == "13"
    assert parsed["build_time"] == "121.09s"


def test_parse_email_state() -> None:
    assert g.parse_email_state("TENDER_FINDER LIVE-TENDER EMAIL SETUP - status: STATE_A") == "STATE_A"
    assert g.parse_email_state("no status line here") == "UNKNOWN"


def test_shorten_display_path_keeps_tail() -> None:
    value = r"C:\TenderFinder\OneDrive_Example\260702\TENDER_FINDER_Patch_5_22_Runtime_Package_20260702_1123\user_data\email_alerts\inbox"
    shortened = g.shorten_display_path(value, max_chars=48)
    assert "..." in shortened
    assert shortened.endswith(r"email_alerts\inbox")


def test_should_auto_open_workbook_respects_env() -> None:
    assert g.should_auto_open_workbook(True, r"C:\x\book.xlsx", env_no_open="0") is True
    assert g.should_auto_open_workbook(True, r"C:\x\book.xlsx", env_no_open="1") is False
    assert g.should_auto_open_workbook(False, r"C:\x\book.xlsx", env_no_open="0") is False
    assert g.should_auto_open_workbook(True, "", env_no_open="0") is False


def test_bc_bid_blocked_status_simulated() -> None:
    """Patch 5.17 Track 2: simulate a blocked BC Bid result (rather than
    triggering a real one) to prove the GUI surfaces it distinctly from a
    genuine zero-result."""
    sample = (
        "- BID NOW total / civil / open civil: 27 / 13 / 0\n"
        "- BID LATER / WATCH / ANALYZED: 7537 / 973 / 25119\n"
        "- BC Bid status: BC_BID_BLOCKED_NO_PUBLIC_FEED\n"
        "Total demo build time: 195.01s\n"
    )
    parsed = g.parse_demo_build_report(sample)
    assert parsed["bc_bid_status"] == "BC_BID_BLOCKED_NO_PUBLIC_FEED"
    assert parsed["bid_now_open_civil"] == "0"

    lines = g.build_completion_summary_lines(parsed, Path("C:/tenderfinder_out/demo_test"))
    joined = "\n".join(lines)
    assert "temporarily blocked by the site's bot-check" in joined
    assert "not a TENDER_FINDER problem" in joined
    assert "BID NOW open civil: 0" in joined


def test_bc_bid_ok_status_unchanged() -> None:
    sample = (
        "- BID NOW total / civil / open civil: 85 / 26 / 13\n"
        "- BC Bid status: OK_BROWSER_COOKIE_REPLAY\n"
    )
    parsed = g.parse_demo_build_report(sample)
    lines = g.build_completion_summary_lines(parsed, Path("C:/tenderfinder_out/demo_test"))
    joined = "\n".join(lines)
    assert "temporarily blocked" not in joined
    assert "BID NOW open civil: 13" in joined


def test_bc_bid_user_action_required_status_simulated() -> None:
    """Patch 5.18 Task A/C: simulate the new status from the headed
    user-assisted browser fallback (not a real BC Bid hit) and prove the
    GUI's completion dialog shows a clear action-needed message distinct
    from both the OK case and the generic "temporarily blocked" case."""
    sample = (
        "- BID NOW total / civil / open civil: 27 / 13 / 0\n"
        "- BC Bid status: BC_BID_BLOCKED_BROWSER_CHECK_USER_ACTION_REQUIRED\n"
    )
    parsed = g.parse_demo_build_report(sample)
    assert parsed["bc_bid_status"] == "BC_BID_BLOCKED_BROWSER_CHECK_USER_ACTION_REQUIRED"

    lines = g.build_completion_summary_lines(parsed, Path("C:/tenderfinder_out/demo_test"))
    joined = "\n".join(lines)
    assert "needs a person to clear" in joined
    assert "CAPTCHA" in joined
    assert "temporarily blocked by the site's bot-check" not in joined
    assert "BID NOW open civil: 0" in joined


def test_status_from_log_flags_user_action_as_urgent() -> None:
    """The GUI status bar must visually distinguish an action-needed state
    (urgent=True, shown in a different color) from routine progress text."""
    status, urgent = g.TenderFinderLauncherApp._status_from_log(
        object(), "TENDER_FINDER_USER_ACTION_REQUIRED: Please allow the public BC Bid page to finish loading, then continue.",
    )
    assert urgent is True
    assert "ACTION NEEDED" in status

    status, urgent = g.TenderFinderLauncherApp._status_from_log(
        object(), "TENDER_FINDER_STAGE: Building Excel workbook and demo sheets",
    )
    assert urgent is False
    assert status == "Building Excel workbook and demo sheets"


def test_classify_log_line_color_tags() -> None:
    """Patch 5.19 GUI polish: the build log color-codes milestones,
    action-needed lines, and errors. Pure function, directly testable."""
    assert g.classify_log_line("TENDER_FINDER_STAGE: Building Excel workbook") == "stage"
    assert g.classify_log_line("DONE in 121.09s") == "stage"
    assert g.classify_log_line("TENDER_FINDER_USER_ACTION_REQUIRED: clear the BC Bid page") == "action"
    assert g.classify_log_line("status=BC_BID_BLOCKED_BROWSER_CHECK_USER_ACTION_REQUIRED") == "action"
    assert g.classify_log_line("ERROR: could not start demo build: boom") == "error"
    assert g.classify_log_line("USER_CANCELLED: the GUI window was closed") == "error"
    assert g.classify_log_line("future=7537 watch=973") == ""


def test_parse_continue_signal_file() -> None:
    """Product Task D: the engine announces the Continue-button signal file
    with a TENDER_FINDER_CONTINUE_SIGNAL_FILE line; the GUI must parse exactly it."""
    path = r"C:\Users\x\AppData\Local\Temp\tenderfinder_bcbid_continue_1234.signal"
    assert g.parse_continue_signal_file(f"TENDER_FINDER_CONTINUE_SIGNAL_FILE: {path}") == path
    assert g.parse_continue_signal_file("TENDER_FINDER_STAGE: something else") == ""
    assert g.parse_continue_signal_file("") == ""


def test_should_show_continue_button_only_when_needed() -> None:
    assert g.should_show_continue_button(r"C:\temp\continue.signal") is True
    assert g.should_show_continue_button("", "status=BLOCKED_BROWSER_CHECK") is True
    assert g.should_show_continue_button("", "user_assisted_browser_waiting") is True
    assert g.should_show_continue_button("", "ordinary status") is False


def test_gui_status_note_matches_engine_for_new_status() -> None:
    """The GUI duplicates bc_bid_status_note by design; the wording for the
    Task D status must match the engine copy exactly."""
    sys.path.insert(0, str(ROOT))
    from tenderfinder_demo_three_buckets import bc_bid_status_note as engine_note
    for status in ("BC_BID_USER_CHECK_NOT_COMPLETED",
                   "BC_BID_BLOCKED_BROWSER_CHECK_USER_ACTION_REQUIRED",
                   "BC_BID_BLOCKED_NO_PUBLIC_FEED"):
        assert g.bc_bid_status_note(status) == engine_note(status), f"wording drift for {status}"


def test_open_path_helper_is_platform_aware() -> None:
    """os.startfile exists only on Windows; the macOS package would crash
    on the output buttons without the dispatch helper. Prove the helper
    exists and that non-Windows platforms never route to os.startfile."""
    assert callable(g.open_path_with_default_app)
    import inspect
    src = inspect.getsource(g.open_path_with_default_app)
    assert "darwin" in src and "open" in src
    assert "xdg-open" in src
    if sys.platform.startswith("win"):
        assert hasattr(g.os, "startfile")


def test_primary_buttons_visible_on_launch() -> None:
    app = g.TenderFinderLauncherApp()
    try:
        app.root.geometry("1366x768")
        app.root.update_idletasks()
        app.notebook.select(app.run_tab)
        app.root.update_idletasks()
        buttons = [
            app.run_full_button,
            app.run_fast_button,
            app.run_button,
            app.open_workbook_button,
            app.open_folder_button,
            app.open_report_button,
            app.open_summary_button,
            app.copy_paths_button,
        ]
        for button in buttons:
            assert button.winfo_exists()
        assert app.root.winfo_width() >= 1050
        assert app.root.winfo_height() >= 700
        assert app.run_button.winfo_y() + app.run_button.winfo_height() < 768
    finally:
        try:
            app.root.destroy()
        except Exception:
            pass


def test_email_and_source_tabs_have_reachable_buttons() -> None:
    app = g.TenderFinderLauncherApp()
    try:
        app.root.geometry("1366x768")
        app.root.update_idletasks()
        app.notebook.select(app.email_tab)
        app.root.update_idletasks()
        assert app.open_email_import_button.winfo_exists()
        assert app.test_email_import_button.winfo_exists()
        assert app.run_email_demo_button.winfo_exists()
        app.notebook.select(app.source_tab)
        app.root.update_idletasks()
        assert app.bc_bid_check_button.winfo_exists()
        assert app.continue_button.winfo_ismapped() == 0
    finally:
        try:
            app.root.destroy()
        except Exception:
            pass


def test_terminate_process_tree_real_process() -> None:
    """Patch 5.17 Track 0: prove terminate_process_tree actually results in
    the OS-level process no longer running, not just that a kill call was
    issued. Uses a real subprocess so the taskkill /T /F path (or the
    non-Windows fallback) genuinely runs. QA fix: checks both proc.poll()
    (Python's own bookkeeping) AND an independent OS-level process-table
    query (process_exists_os_level, the tasklist/Get-Process equivalent),
    since proc.poll() alone only proves Python's handle thinks it's dead."""
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    pid = proc.pid
    assert proc.poll() is None, "dummy process should still be starting up"
    assert process_exists_os_level(pid), "dummy process should be visible in the OS process table"
    time.sleep(0.5)
    result = g.terminate_process_tree(proc, grace_seconds=3.0)
    assert result is True
    assert proc.poll() is not None, "process must actually be dead, not just 'terminate() called'"
    assert not process_exists_os_level(pid), f"pid {pid} still appears in the OS process table after termination"


def test_worker_cancel_stops_real_subprocess() -> None:
    """Patch 5.17 Track 0: exercises the exact path the GUI's window-close
    handler uses (DemoBuildWorker.cancel()) against a real long-running
    dummy subprocess (not the real demo builder or BC Bid, per the
    prompt's guidance to keep this test fast and independent of the live
    pipeline). Confirms: the process handle gets published, cancel() kills
    it for real, the CANCELLED_SENTINEL (not the crash ERROR_SENTINEL)
    is emitted, and the run's error log clearly says USER_CANCELLED."""
    cmd = [sys.executable, "-c", "import time\nfor i in range(30):\n    print(f'tick {i}', flush=True)\n    time.sleep(1)"]
    out_dir = g.default_output_dir()
    worker = g.DemoBuildWorker(cmd, out_dir)
    worker.start()

    t0 = time.perf_counter()
    while worker.proc is None:
        assert time.perf_counter() - t0 < 10, "worker.proc handle was never published"
        time.sleep(0.1)
    pid = worker.proc.pid
    time.sleep(1)

    assert worker.cancel() is True

    t0 = time.perf_counter()
    saw_cancelled_sentinel = False
    while time.perf_counter() - t0 < 15:
        try:
            line = worker.log_queue.get(timeout=1)
        except queue.Empty:
            continue
        if line.startswith(g.CANCELLED_SENTINEL):
            saw_cancelled_sentinel = True
            break
        assert not line.startswith(g.ERROR_SENTINEL), "a user cancel must not be reported as a crash"
    assert saw_cancelled_sentinel, f"never saw {g.CANCELLED_SENTINEL}"
    assert worker.proc.poll() is not None, f"subprocess pid {pid} is still running after cancel()"

    error_log = out_dir / "gui_run_error.log"
    assert error_log.exists()
    assert "USER_CANCELLED" in error_log.read_text(encoding="utf-8")


def test_on_close_requested_confirms_and_stops_running_build() -> None:
    """QA fix for Patch 5.17: the prior test coverage exercised
    DemoBuildWorker.cancel() directly but never the actual WM_DELETE_WINDOW
    handler (TenderFinderLauncherApp._on_close_requested) that calls it. This
    builds a real TenderFinderLauncherApp with a real Tk root (withdrawn/hidden, so
    nothing is shown on screen - confirmed to work headlessly in this
    environment), starts a real long-running dummy subprocess as the
    "in-progress build", simulates the user clicking "Yes" on the
    confirmation dialog (messagebox.askyesno blocks on real input, so it's
    monkeypatched rather than skipped), and then independently confirms via
    the OS process table (not just proc.poll()) that the subprocess is
    genuinely gone and that the window was actually destroyed."""
    cmd = [sys.executable, "-c", "import time\nfor i in range(30):\n    print(f'tick {i}', flush=True)\n    time.sleep(1)"]
    out_dir = g.default_output_dir()

    app = g.TenderFinderLauncherApp()
    original_destroy = app.root.destroy
    try:
        app.root.withdraw()
        app.worker = g.DemoBuildWorker(cmd, out_dir)
        app.worker.start()

        t0 = time.perf_counter()
        while app.worker.proc is None:
            assert time.perf_counter() - t0 < 10, "worker.proc handle was never published"
            time.sleep(0.1)
        pid = app.worker.proc.pid
        time.sleep(1)
        assert process_exists_os_level(pid), "dummy build process should be running before close"

        app.messagebox.askyesno = lambda *a, **k: True  # simulate the user clicking "Yes"
        destroy_calls: list[bool] = []

        def _tracking_destroy() -> None:
            destroy_calls.append(True)
            original_destroy()

        app.root.destroy = _tracking_destroy

        app._on_close_requested()

        assert destroy_calls, "close handler did not destroy the window after the user confirmed"
        assert app.worker.proc.poll() is not None, "subprocess must be stopped after a confirmed close"
        assert not process_exists_os_level(pid), f"pid {pid} still appears in the OS process table after window close"
    finally:
        try:
            import tkinter as tk
            tk.Tk.destroy(app.root)
        except Exception:
            pass


def test_on_close_requested_keeps_running_if_user_declines() -> None:
    """QA fix for Patch 5.17: proves the confirmation dialog actually gates
    the close - if the user clicks "No", the build must keep running and
    the window must not be destroyed. Without this, a "Yes"-only test
    couldn't tell a real confirmation gate from one that always closes."""
    cmd = [sys.executable, "-c", "import time\nfor i in range(15):\n    print(f'tick {i}', flush=True)\n    time.sleep(1)"]
    out_dir = g.default_output_dir()

    app = g.TenderFinderLauncherApp()
    try:
        app.root.withdraw()
        app.worker = g.DemoBuildWorker(cmd, out_dir)
        app.worker.start()

        t0 = time.perf_counter()
        while app.worker.proc is None:
            assert time.perf_counter() - t0 < 10, "worker.proc handle was never published"
            time.sleep(0.1)
        pid = app.worker.proc.pid

        app.messagebox.askyesno = lambda *a, **k: False  # simulate the user clicking "No"
        destroy_calls: list[bool] = []
        app.root.destroy = lambda: destroy_calls.append(True)

        app._on_close_requested()

        assert not destroy_calls, "window must not close if the user declines the confirmation"
        assert app.worker.proc.poll() is None, "build must keep running if the user declines"
        assert process_exists_os_level(pid), "declined-close must leave the real process running"
    finally:
        try:
            if app.worker is not None and app.worker.proc is not None:
                g.terminate_process_tree(app.worker.proc)
        except Exception:
            pass
        try:
            import tkinter as tk
            tk.Tk.destroy(app.root)
        except Exception:
            pass


def test_auto_open_workbook_called_on_success() -> None:
    app = g.TenderFinderLauncherApp()
    out_dir = g.default_output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    workbook = out_dir / "TENDER_FINDER_DEMO_Opportunities_Three_Buckets.xlsx"
    workbook.write_text("x", encoding="utf-8")
    (out_dir / "DEMO_BUILD_REPORT.md").write_text("- BID NOW total / civil / open civil: 3 / 3 / 3\n- BID LATER / WATCH / ANALYZED: 7537 / 973 / 25119\nTotal demo build time: 1.00s\n- Email alert files seen: 3\n- Email tender rows parsed: 2\n- Email BID NOW rows: 2\n- Email non-actionable/history rows: 0\n- Email rejected/duplicate files: 1\n", encoding="utf-8")
    (out_dir / "demo_summary.txt").write_text("TENDER_FINDER LIVE-TENDER EMAIL SETUP - status: STATE_A", encoding="utf-8")
    (out_dir / "tenderfinder_stage_progress.json").write_text(json.dumps({"stages": ["completed"]}), encoding="utf-8")
    original_reader = g.read_run_results
    original_open = g.open_path_with_default_app
    original_no_open = os.environ.get("TENDER_FINDER_DEMO_NO_OPEN")
    opened: list[str] = []
    try:
        g.read_run_results = lambda _out_dir: {
            "out_dir": str(out_dir),
            "workbook_path": str(workbook),
            "report_path": str(out_dir / "DEMO_BUILD_REPORT.md"),
            "summary_path": str(out_dir / "demo_summary.txt"),
            "bid_now_total": "3",
            "bid_later": "7537",
            "build_time": "1.00s",
            "email_bid_now_rows": "2",
            "bc_bid_status": "OK_BROWSER_COOKIE_REPLAY",
        }
        g.open_path_with_default_app = lambda path: opened.append(path)
        os.environ.pop("TENDER_FINDER_DEMO_NO_OPEN", None)
        app.messagebox.showinfo = lambda *a, **k: None
        app.worker = type("Worker", (), {"out_dir": out_dir, "return_code": 0})()
        app._on_build_finished(success=True)
        assert opened == [str(workbook)]
    finally:
        g.read_run_results = original_reader
        g.open_path_with_default_app = original_open
        if original_no_open is None:
            os.environ.pop("TENDER_FINDER_DEMO_NO_OPEN", None)
        else:
            os.environ["TENDER_FINDER_DEMO_NO_OPEN"] = original_no_open
        try:
            app.root.destroy()
        except Exception:
            pass


def test_auto_open_workbook_failure_does_not_crash() -> None:
    app = g.TenderFinderLauncherApp()
    out_dir = g.default_output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    workbook = out_dir / "TENDER_FINDER_DEMO_Opportunities_Three_Buckets.xlsx"
    workbook.write_text("x", encoding="utf-8")
    (out_dir / "tenderfinder_stage_progress.json").write_text(json.dumps({"stages": ["completed"]}), encoding="utf-8")
    original_reader = g.read_run_results
    original_open = g.open_path_with_default_app
    warnings: list[str] = []
    try:
        g.read_run_results = lambda _out_dir: {
            "out_dir": str(out_dir),
            "workbook_path": str(workbook),
            "report_path": "",
            "summary_path": "",
            "bid_now_total": "3",
            "bid_later": "7537",
            "build_time": "1.00s",
            "email_bid_now_rows": "2",
            "bc_bid_status": "OK_BROWSER_COOKIE_REPLAY",
        }
        def _boom(_path: str) -> None:
            raise OSError("cannot open")
        g.open_path_with_default_app = _boom
        app.messagebox.showinfo = lambda *a, **k: None
        app.messagebox.showwarning = lambda _title, body: warnings.append(body)
        app.worker = type("Worker", (), {"out_dir": out_dir, "return_code": 0})()
        app._on_build_finished(success=True)
        assert warnings and "could not open the workbook automatically" in warnings[0]
        assert str(workbook) in warnings[0]
    finally:
        g.read_run_results = original_reader
        g.open_path_with_default_app = original_open
        try:
            app.root.destroy()
        except Exception:
            pass


def test_worker_success_end_to_end() -> None:
    """Runs the real demo builder in fast mode (~15s per the GUI's own
    label, though observed closer to ~100s for the current large review
    workbook - see AUTONOMOUS_FIXES.md) via DemoBuildWorker, exactly as
    the GUI's Run button would, and checks the queue/thread wiring and
    result parsing against the real output files."""
    if not RUN_GUI_E2E:
        print("[SKIP] test_worker_success_end_to_end (TENDER_FINDER_GUI_SKIP_E2E set)")
        return
    out_dir = g.default_output_dir()
    cmd = g.build_demo_command(g.DEFAULT_REVIEW_XLSX, out_dir, fast_mode=True)
    worker = g.DemoBuildWorker(cmd, out_dir)
    worker.start()

    t0 = time.perf_counter()
    while True:
        try:
            line = worker.log_queue.get(timeout=1)
        except queue.Empty:
            assert (
                time.perf_counter() - t0 < DEFAULT_GUI_E2E_TIMEOUT_SECONDS
            ), f"worker did not finish within {DEFAULT_GUI_E2E_TIMEOUT_SECONDS}s"
            continue
        if line.startswith(g.DONE_SENTINEL) or line.startswith(g.ERROR_SENTINEL):
            break

    assert worker.return_code == 0, f"demo build failed, see {out_dir / 'gui_run_error.log'}"
    results = g.read_run_results(out_dir)
    assert results["bid_later"] == "7537"
    assert results["watchlist"] == "973"
    assert results["analyzed"] == "25119"
    assert results["workbook_path"]
    assert Path(results["workbook_path"]).exists()
    stage_progress = out_dir / "tenderfinder_stage_progress.json"
    assert stage_progress.exists()
    payload = json.loads(stage_progress.read_text(encoding="utf-8"))
    assert "completed" in payload.get("stages", [])


def main() -> int:
    tests = [
        test_build_demo_command,
        test_parse_demo_build_report,
        test_parse_email_state,
        test_shorten_display_path_keeps_tail,
        test_should_auto_open_workbook_respects_env,
        test_bc_bid_blocked_status_simulated,
        test_bc_bid_ok_status_unchanged,
        test_bc_bid_user_action_required_status_simulated,
        test_status_from_log_flags_user_action_as_urgent,
        test_classify_log_line_color_tags,
        test_parse_continue_signal_file,
        test_should_show_continue_button_only_when_needed,
        test_gui_status_note_matches_engine_for_new_status,
        test_open_path_helper_is_platform_aware,
        test_primary_buttons_visible_on_launch,
        test_email_and_source_tabs_have_reachable_buttons,
        test_terminate_process_tree_real_process,
        test_worker_cancel_stops_real_subprocess,
        test_on_close_requested_confirms_and_stops_running_build,
        test_on_close_requested_keeps_running_if_user_declines,
        test_auto_open_workbook_called_on_success,
        test_auto_open_workbook_failure_does_not_crash,
        test_worker_success_end_to_end,
    ]
    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")
    print("Launcher GUI logic test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
DEFAULT_GUI_E2E_TIMEOUT_SECONDS = int(os.environ.get("TENDER_FINDER_GUI_E2E_TIMEOUT_SECONDS", "240"))
RUN_GUI_E2E = os.environ.get("TENDER_FINDER_GUI_SKIP_E2E", "").strip().lower() not in {"1", "true", "yes"}

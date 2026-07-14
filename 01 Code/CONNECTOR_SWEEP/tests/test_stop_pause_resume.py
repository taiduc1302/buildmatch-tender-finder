from __future__ import annotations

import json
import queue
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import tenderfinder_launcher_gui as g  # noqa: E402

# Product Task E: Stop / Pause / Resume. Stop must genuinely kill the
# process tree and mark output partial; Pause must stop only at safe stage
# boundaries via the engine's checkpoint mechanism (exit code 86, never
# reported as a crash); Resume is honestly a restart - these tests pin the
# sentinels and files each path produces so the GUI can never confuse
# stopped/paused/crashed/completed.


def _drain_for_sentinel(worker: "g.DemoBuildWorker", sentinel: str, timeout: float = 20.0) -> bool:
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < timeout:
        try:
            line = worker.log_queue.get(timeout=1)
        except queue.Empty:
            continue
        if line.startswith(sentinel):
            return True
        for other in (g.DONE_SENTINEL, g.ERROR_SENTINEL, g.CANCELLED_SENTINEL,
                      g.STOPPED_SENTINEL, g.PAUSED_SENTINEL):
            if other != sentinel and line.startswith(other):
                raise AssertionError(f"expected {sentinel}, got {line}")
    return False


def test_pause_exit_code_constants_match() -> None:
    """The GUI never imports the pipeline, so the pause exit code is
    duplicated by design - this pins the two copies together."""
    import ast
    engine_src = (ROOT / "tenderfinder_demo_three_buckets.py").read_text(encoding="utf-8")
    tree = ast.parse(engine_src)
    engine_value = None
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "PAUSE_EXIT_CODE"):
            engine_value = node.value.value
    assert engine_value == g.PAUSE_EXIT_CODE, (
        f"engine PAUSE_EXIT_CODE={engine_value} but GUI expects {g.PAUSE_EXIT_CODE}"
    )


def test_record_stage_and_maybe_pause_checkpoint() -> None:
    from tenderfinder_demo_three_buckets import (
        PAUSE_EXIT_CODE,
        maybe_pause_at_checkpoint,
        record_stage,
    )

    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp)
        record_stage(out_dir, "track_a_loaded")
        record_stage(out_dir, "bc_bid_done_or_skipped")
        record_stage(out_dir, "track_a_loaded")  # no duplicates
        progress = json.loads((out_dir / "tenderfinder_stage_progress.json").read_text(encoding="utf-8"))
        assert progress["stages"] == ["track_a_loaded", "bc_bid_done_or_skipped"]

        # No signal file -> no pause, returns silently.
        maybe_pause_at_checkpoint(out_dir, "track_a_loaded")

        (out_dir / "tenderfinder_pause.signal").write_text("pause", encoding="utf-8")
        try:
            maybe_pause_at_checkpoint(out_dir, "bc_bid_done_or_skipped")
            raise AssertionError("expected SystemExit at checkpoint with signal present")
        except SystemExit as exc:
            assert exc.code == PAUSE_EXIT_CODE
        assert not (out_dir / "tenderfinder_pause.signal").exists(), "signal must be consumed"
        checkpoint = json.loads((out_dir / "tenderfinder_checkpoint.json").read_text(encoding="utf-8"))
        assert checkpoint["stage"] == "bc_bid_done_or_skipped"
        assert "restart" in checkpoint["resume_note"].lower() or "beginning" in checkpoint["resume_note"].lower()


def test_worker_stop_kills_process_and_marks_partial() -> None:
    cmd = [sys.executable, "-c", "import time\nfor i in range(30):\n    print(f'tick {i}', flush=True)\n    time.sleep(1)"]
    out_dir = g.default_output_dir()
    worker = g.DemoBuildWorker(cmd, out_dir)
    worker.start()
    t0 = time.perf_counter()
    while worker.proc is None:
        assert time.perf_counter() - t0 < 10
        time.sleep(0.1)
    time.sleep(1)

    assert worker.stop() is True
    assert _drain_for_sentinel(worker, g.STOPPED_SENTINEL), "never saw STOPPED sentinel"
    assert worker.proc.poll() is not None, "process must actually be dead after Stop"

    error_log = out_dir / "gui_run_error.log"
    assert error_log.exists()
    log_text = error_log.read_text(encoding="utf-8")
    assert "USER_STOPPED" in log_text
    assert "USER_CANCELLED" not in log_text, "Stop and window-close cancel must stay distinct"
    partial = out_dir / "PARTIAL_OUTPUT_README.txt"
    assert partial.exists(), "stopped run with files must be marked partial"
    assert "STOPPED" in partial.read_text(encoding="utf-8")


def test_worker_pause_exit_code_reports_paused_not_error() -> None:
    from tenderfinder_demo_three_buckets import PAUSE_EXIT_CODE
    cmd = [sys.executable, "-c", f"import sys; print('pausing', flush=True); sys.exit({PAUSE_EXIT_CODE})"]
    out_dir = g.default_output_dir()
    worker = g.DemoBuildWorker(cmd, out_dir)
    worker.start()
    assert _drain_for_sentinel(worker, g.PAUSED_SENTINEL), "never saw PAUSED sentinel"
    assert worker.return_code == PAUSE_EXIT_CODE
    assert not (out_dir / "gui_run_error.log").exists(), "a pause is not an error and must not write the crash log"


def test_engine_pause_at_first_checkpoint_real_run() -> None:
    """Runs the REAL engine (fast mode) with a pause signal pre-placed:
    the engine must load Track A, then stop at the track_a_loaded
    checkpoint with exit code 86, a checkpoint file, and NO workbook -
    proving pause never leaves a half-built output."""
    from tenderfinder_review_workbook import discover_review_xlsx
    from tenderfinder_demo_three_buckets import PAUSE_EXIT_CODE

    review, _ = discover_review_xlsx(ROOT.parents[1])
    if review is None:
        print("  (review workbook not found on this machine - skipping the live engine pause test)")
        return
    out_dir = g.default_output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "tenderfinder_pause.signal").write_text("pause", encoding="utf-8")
    cmd = g.build_demo_command(review, out_dir, fast_mode=True)
    proc = subprocess.run(cmd, cwd=str(ROOT.parents[1]), capture_output=True, text=True, timeout=400)
    assert proc.returncode == PAUSE_EXIT_CODE, (
        f"expected pause exit {PAUSE_EXIT_CODE}, got {proc.returncode}\n{proc.stdout[-2000:]}"
    )
    assert "TENDER_FINDER_PAUSED" in proc.stdout
    checkpoint = json.loads((out_dir / "tenderfinder_checkpoint.json").read_text(encoding="utf-8"))
    assert checkpoint["stage"] == "track_a_loaded"
    progress = json.loads((out_dir / "tenderfinder_stage_progress.json").read_text(encoding="utf-8"))
    assert "track_a_loaded" in progress["stages"]
    assert not (out_dir / "TENDER_FINDER_DEMO_Opportunities_Three_Buckets.xlsx").exists(), (
        "pause at track_a_loaded must happen BEFORE any workbook is written"
    )


def main() -> int:
    tests = [
        test_pause_exit_code_constants_match,
        test_record_stage_and_maybe_pause_checkpoint,
        test_worker_stop_kills_process_and_marks_partial,
        test_worker_pause_exit_code_reports_paused_not_error,
        test_engine_pause_at_first_checkpoint_real_run,
    ]
    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")
    print("Stop/Pause/Resume test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

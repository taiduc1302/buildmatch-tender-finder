from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import replace
from pathlib import Path


CODE_DIR = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = CODE_DIR.parents[1]
sys.path.insert(0, str(CODE_DIR))

from tenderfinder_engine import (  # noqa: E402
    MODE_OFFLINE,
    RunRequest,
    prepare_run,
    run_plan,
)
from tenderfinder_source_registry import load_tender_sources  # noqa: E402


def _review_workbook() -> Path:
    path = PACKAGE_ROOT / "inputs" / "all_live_review.xlsx"
    assert path.exists(), path
    return path


def test_request_and_result_are_json_serializable_and_gui_independent() -> None:
    engine_source = (CODE_DIR / "tenderfinder_engine.py").read_text(encoding="utf-8")
    assert "import tkinter" not in engine_source
    source_id = load_tender_sources(root=PACKAGE_ROOT, active_only=True)[0]["source_id"]

    with tempfile.TemporaryDirectory() as temp:
        folder = Path(temp)
        request = RunRequest(
            review_xlsx=_review_workbook(),
            out_dir=folder / "out",
            mode=MODE_OFFLINE,
            state_root=folder / "state",
            run_id="engine_contract_fixture",
            source_ids=(source_id,),
            offline=True,
        )
        json.dumps(request.to_dict())
        plan = prepare_run(request, root=PACKAGE_ROOT)
        assert plan.offline is True
        assert plan.self_test is False
        assert plan.source_ids == (source_id,)
        assert plan.keywords_source_kind == "canonical"
        assert "--source-id" in plan.command
        assert "--keywords-config" in plan.command

        fixture_command = (
            sys.executable,
            "-c",
            "print('- BID NOW total / civil / open civil: 4 / 3 / 2'); "
            "print('- BID LATER / WATCH / ANALYZED: 7 / 5 / 16')",
        )
        result = run_plan(replace(plan, command=fixture_command))
        payload = result.to_dict()
        json.dumps(payload)
        assert result.passed
        assert result.status == "PASS"
        assert result.source_counts["selected"] == 1
        assert result.record_counts["bid_now_total"] == 4
        assert result.record_counts["analyzed"] == 16
        assert result.score_bucket_summaries == {
            "bid_now": 4,
            "bid_later": 7,
            "watchlist": 5,
        }
        assert result.started_at and result.finished_at
        assert result.output_paths["manifest"] == str(result.manifest_path)

        manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
        assert manifest["schema_version"] == 2
        assert manifest["request"] == {
            "offline": True,
            "self_test": False,
            "mode": MODE_OFFLINE,
        }
        assert manifest["keywords_source_kind"] == "canonical"


def test_request_rejects_conflicting_flags_and_unknown_sources() -> None:
    with tempfile.TemporaryDirectory() as temp:
        folder = Path(temp)
        base = dict(
            review_xlsx=_review_workbook(),
            out_dir=folder / "out",
            mode=MODE_OFFLINE,
            state_root=folder / "state",
        )
        try:
            prepare_run(RunRequest(**base, offline=False), root=PACKAGE_ROOT)
        except ValueError as exc:
            assert "conflicts" in str(exc)
        else:
            raise AssertionError("conflicting offline flag was accepted")

        try:
            prepare_run(
                RunRequest(**base, offline=True, source_ids=("missing_source",)),
                root=PACKAGE_ROOT,
            )
        except ValueError as exc:
            assert "unknown source selection" in str(exc)
        else:
            raise AssertionError("unknown source selection was accepted")


def main() -> int:
    tests = [
        test_request_and_result_are_json_serializable_and_gui_independent,
        test_request_rejects_conflicting_flags_and_unknown_sources,
    ]
    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")
    print(f"Engine contract tests: {len(tests)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

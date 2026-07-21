"""Tests for the display-agnostic GUI helper functions that wire the launcher
to the Build Week controllers (Phase 2/6 GUI). These need no Tk display.

Runs under pytest and as a script.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
REPO_ROOT = ROOT.parents[1]

import tenderfinder_launcher_gui as g  # noqa: E402
import tenderfinder_snapshot as snap  # noqa: E402
import tenderfinder_ai_analysis as ai  # noqa: E402


class _FakeClient:
    def __init__(self, payload):
        self._payload = payload

    class _Resp:
        def __init__(self, text):
            self.status = "completed"
            self.output_text = text
            self.output = []

    @property
    def responses(self):
        outer = self

        class _R:
            @staticmethod
            def create(**kwargs):
                return _FakeClient._Resp(json.dumps(outer._payload))

        return _R()


def _payload(record_id, action="BID_LATER"):
    return {
        "record_id": record_id, "project_summary": "A civil servicing project.",
        "match_assessment": "STRONG", "recommended_action": action,
        "positive_factors": [{"factor": "civil", "evidence_field": "scope_summary", "evidence_value": "watermain"}],
        "negative_factors": [], "eligibility_uncertainties": [],
        "missing_information": ["closing date"], "potential_scope": [], "next_steps": ["confirm scope"],
        "confidence": "MEDIUM", "limitations": [],
    }


def test_data_mode_banner_defaults_to_synthetic() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        banner = g.current_data_mode_banner(state_root=tmp, package_root=REPO_ROOT)
    assert "SYNTHETIC DEMO DATA" in banner


def test_data_mode_banner_reflects_promoted_snapshot() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        snap.promote_snapshot(state_root=tmp, root=REPO_ROOT)
        banner = g.current_data_mode_banner(state_root=tmp, package_root=REPO_ROOT)
    assert banner.startswith("PUBLIC SNAPSHOT — captured")


def test_preset_choices() -> None:
    choices = dict(g.preset_choices())
    assert choices["civil_contractor"] == "Civil Contractor"
    assert "multifamily_residential" in choices


def test_top_ranked_opportunity_from_snapshot() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        snap.promote_snapshot(state_root=tmp, root=REPO_ROOT)
        record, evidence = g.top_ranked_opportunity(
            state_root=tmp, preset_id="civil_contractor", package_root=REPO_ROOT
        )
    assert record is not None
    assert evidence["fit_score"] >= 60
    assert evidence["routing_bucket"] == "Future_Projects"
    assert evidence["matched_positive_terms"]


def test_top_ranked_opportunity_none_when_no_dataset() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        record, evidence = g.top_ranked_opportunity(state_root=tmp, package_root=REPO_ROOT)
    assert record is None and evidence is None


# --------------------------------------------------------------------------- #
# Ranked-opportunity selection (Gap B fix): the AI action must analyze the
# opportunity the user actually selected in the ranked list, never an
# auto-picked record silently substituted for "selected".
# --------------------------------------------------------------------------- #


def test_ranked_opportunities_default_excludes_terminal_stages() -> None:
    """By default (include_terminal_stages=False), records whose application
    stage is finished (Concluded/Closed/Cancelled/...) are excluded - they
    are not opportunities anyone can still pursue."""
    with tempfile.TemporaryDirectory() as tmp:
        snap.promote_snapshot(state_root=tmp, root=REPO_ROOT)
        ranked = g.ranked_opportunities(state_root=tmp, preset_id="civil_contractor", package_root=REPO_ROOT)
        records, _manifest = snap.load_snapshot(REPO_ROOT)
    terminal_count = sum(1 for r in records if g._is_terminal_stage(r))
    assert terminal_count > 0  # the fixture snapshot actually contains finished records
    assert len(ranked) == len(records) - terminal_count
    assert all(not g._is_terminal_stage(item["record"]) for item in ranked)
    fits = [item["evidence"]["fit_score"] for item in ranked]
    assert fits == sorted(fits, reverse=True)  # default sort: fit score descending
    ranks = [item["rank"] for item in ranked]
    assert ranks == list(range(1, len(ranked) + 1))


def test_ranked_opportunities_include_terminal_stages_restores_full_list() -> None:
    """The "Include finished applications" option (include_terminal_stages=True)
    must restore the records excluded by the default filter."""
    with tempfile.TemporaryDirectory() as tmp:
        snap.promote_snapshot(state_root=tmp, root=REPO_ROOT)
        ranked = g.ranked_opportunities(
            state_root=tmp, preset_id="civil_contractor", package_root=REPO_ROOT,
            include_terminal_stages=True,
        )
        records, _manifest = snap.load_snapshot(REPO_ROOT)
    assert len(ranked) == len(records)  # the full snapshot, not a truncated top-N preview
    fits = [item["evidence"]["fit_score"] for item in ranked]
    assert fits == sorted(fits, reverse=True)  # default sort: fit score descending
    ranks = [item["rank"] for item in ranked]
    assert ranks == list(range(1, len(ranked) + 1))


def test_ranked_opportunities_empty_without_active_dataset() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ranked = g.ranked_opportunities(state_root=tmp, package_root=REPO_ROOT)
    assert ranked == []


def test_resolve_selected_opportunity_maps_correct_record() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        snap.promote_snapshot(state_root=tmp, root=REPO_ROOT)
        ranked = g.ranked_opportunities(state_root=tmp, preset_id="civil_contractor", package_root=REPO_ROOT)
    # select rank 3 specifically - must return exactly that record, not rank 1.
    third_record_id = ranked[2]["record"]["record_id"]
    record, evidence = g.resolve_selected_opportunity(ranked, 3)
    assert record is not None
    assert record["record_id"] == third_record_id
    assert evidence["fit_score"] == ranked[2]["evidence"]["fit_score"]
    # the top-ranked (rank 1) record must NOT have been silently substituted
    assert record["record_id"] != ranked[0]["record"]["record_id"] or third_record_id == ranked[0]["record"]["record_id"]


def test_resolve_selected_opportunity_no_selection_returns_none() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        snap.promote_snapshot(state_root=tmp, root=REPO_ROOT)
        ranked = g.ranked_opportunities(state_root=tmp, preset_id="civil_contractor", package_root=REPO_ROOT)
    record, evidence = g.resolve_selected_opportunity(ranked, None)
    assert record is None and evidence is None


def test_resolve_selected_opportunity_stale_rank_returns_none_not_a_substitute() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        snap.promote_snapshot(state_root=tmp, root=REPO_ROOT)
        ranked = g.ranked_opportunities(state_root=tmp, preset_id="civil_contractor", package_root=REPO_ROOT)
    # a rank that doesn't exist in the current list (e.g. stale selection after
    # a refresh shrank the list) must resolve to nothing, never a fallback pick.
    record, evidence = g.resolve_selected_opportunity(ranked, 9999)
    assert record is None and evidence is None


def test_opportunity_row_values_shape() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        snap.promote_snapshot(state_root=tmp, root=REPO_ROOT)
        ranked = g.ranked_opportunities(state_root=tmp, preset_id="civil_contractor", package_root=REPO_ROOT)
    row = g.opportunity_row_values(ranked[0])
    assert len(row) == 9
    assert row[0] == 1  # rank
    assert isinstance(row[1], int)  # fit score
    assert row[2] in ("Future_Projects", "Run_Queue", "Rejected_Archive")


def test_ai_analysis_uses_selected_record_not_top_ranked() -> None:
    """The core Gap-B assertion: analyzing a user-selected (non-top) record must
    send THAT record's evidence to the AI service, not the top-ranked one's."""
    with tempfile.TemporaryDirectory() as tmp:
        snap.promote_snapshot(state_root=tmp, root=REPO_ROOT)
        ranked = g.ranked_opportunities(state_root=tmp, preset_id="civil_contractor", package_root=REPO_ROOT)
        # find a rank that is NOT the top-ranked one and has a distinct record_id
        chosen = next(item for item in ranked if item["rank"] != 1)
        record, evidence = g.resolve_selected_opportunity(ranked, chosen["rank"])
        assert record["record_id"] != ranked[0]["record"]["record_id"]

        captured = {}
        view = g.analyze_record_headless(
            record, "civil_contractor", evidence, state_root=tmp, package_root=REPO_ROOT,
            client_factory=lambda: _FakeClient(_payload(record["record_id"])),
        )
    assert view["record_id"] == record["record_id"]
    assert view["record_id"] != ranked[0]["record"]["record_id"]


def test_analyze_record_headless_preserves_deterministic() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        record = {"record_id": "R1", "scope_summary": "watermain and sanitary sewer servicing"}
        evidence = {"fit_score": 82, "routing_bucket": "Future_Projects",
                    "matched_positive_terms": ["watermain"], "matched_negative_terms": []}
        view = g.analyze_record_headless(
            record, "civil_contractor", evidence, state_root=tmp, package_root=REPO_ROOT,
            client_factory=lambda: _FakeClient(_payload("R1")),
        )
    assert view["deterministic_section"]["fit_score"] == 82
    assert view["ai_section"]["match_assessment"] == "STRONG"


def test_ai_status_line_setup_required() -> None:
    saved = os.environ.pop(ai.API_KEY_ENV, None)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            record = {"record_id": "R1", "scope_summary": "watermain"}
            view = g.analyze_record_headless(
                record, "civil_contractor",
                {"fit_score": 50, "routing_bucket": "Run_Queue"},
                state_root=tmp, package_root=REPO_ROOT,  # no client_factory, no key
            )
        assert view["status"] == "SETUP_REQUIRED"
        assert "OPENAI_API_KEY" in g.format_ai_status_line(view)
        dialog = g.format_ai_view_for_dialog(view)
        assert "DETERMINISTIC RESULT" in dialog
        assert "Fit score: 50" in dialog
    finally:
        if saved is not None:
            os.environ[ai.API_KEY_ENV] = saved


def test_ai_dialog_shows_disagreement() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        record = {"record_id": "R1", "scope_summary": "watermain servicing"}
        evidence = {"fit_score": 82, "routing_bucket": "Future_Projects"}
        view = g.analyze_record_headless(
            record, "civil_contractor", evidence, state_root=tmp, package_root=REPO_ROOT,
            client_factory=lambda: _FakeClient(_payload("R1", action="SKIP")),
        )
    assert view["disagreement"] is not None
    dialog = g.format_ai_view_for_dialog(view)
    assert "DISAGREEMENT" in dialog


def main() -> int:
    tests = [value for name, value in sorted(globals().items())
             if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")
    print(f"Build Week GUI-helper tests: {len(tests)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

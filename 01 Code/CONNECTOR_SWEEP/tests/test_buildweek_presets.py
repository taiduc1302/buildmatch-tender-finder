"""Tests for contractor profile presets (Build Week Phase 5).

Proves the Civil preset is unchanged, the Residential preset does not penalize
interior/mechanical/electrical/HVAC/suite scope, the General Contractor preset
differs in intended ways, preset switching works, user customization is
preserved, and preset identity is available for manifests.

Runs under pytest and as a plain script (for the offline Self-Test).
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
REPO_ROOT = ROOT.parents[1]

import tenderfinder_presets as presets  # noqa: E402
import tenderfinder_guards as G  # noqa: E402
from tenderfinder_keywords_config import clear_keywords_cache  # noqa: E402

CIVIL_TEXT = "Watermain and sanitary sewer site servicing for a new subdivision, grading and roadworks"
RESIDENTIAL_TEXT = "Apartment building interior fit-out including mechanical, electrical, HVAC and suite alteration work"


def _score(preset_id: str, text: str) -> int:
    clear_keywords_cache()
    os.environ["TENDER_FINDER_KEYWORDS_CONFIG"] = str(
        presets.resolve_preset_keywords_path(preset_id, root=REPO_ROOT)
    )
    try:
        return G.score_civil_fit(text)
    finally:
        os.environ.pop("TENDER_FINDER_KEYWORDS_CONFIG", None)
        clear_keywords_cache()


def test_three_presets_are_registered_with_stable_ids_and_versions() -> None:
    ids = {p.preset_id for p in presets.list_presets()}
    assert ids == {"civil_contractor", "multifamily_residential", "general_contractor"}
    for p in presets.list_presets():
        assert p.version and p.display_name and p.description
    assert presets.get_preset("civil_contractor").display_name == "Civil Contractor"


def test_all_preset_workbooks_load_and_validate() -> None:
    for p in presets.list_presets():
        cfg = presets.load_preset_config(p.preset_id, root=REPO_ROOT)
        assert cfg.active_keyword_count > 0
        assert cfg.company_name


def test_civil_preset_behaviour_is_stable() -> None:
    # Civil preset must reproduce the original scoring exactly.
    cfg = presets.load_preset_config("civil_contractor", root=REPO_ROOT)
    assert cfg.company_name == "Meridian Civil Works"
    assert len(cfg.rules_for("negative")) == 15  # all civil penalties active
    assert _score("civil_contractor", CIVIL_TEXT) == 100
    # a vertical/interior record is strongly penalized under Civil
    assert _score("civil_contractor", RESIDENTIAL_TEXT) == 0


def test_residential_preset_does_not_penalize_residential_scope() -> None:
    cfg = presets.load_preset_config("multifamily_residential", root=REPO_ROOT)
    negatives = {r.keyword.casefold() for r in cfg.rules_for("negative")}
    for term in ("interior", "mechanical", "electrical", "hvac", "suite"):
        assert term not in negatives, f"{term} must not penalize the residential preset"
    residential_score = _score("multifamily_residential", RESIDENTIAL_TEXT)
    civil_score = _score("civil_contractor", RESIDENTIAL_TEXT)
    assert residential_score > civil_score
    assert residential_score >= 35  # not driven below the neutral base by penalties


def test_general_contractor_preset_differs_in_intended_ways() -> None:
    # GC values both civil site work and vertical building scope.
    assert _score("general_contractor", CIVIL_TEXT) == 100
    gc_vertical = _score("general_contractor", RESIDENTIAL_TEXT)
    civil_vertical = _score("civil_contractor", RESIDENTIAL_TEXT)
    assert gc_vertical > civil_vertical
    # GC is broader than the residential preset on a commercial/institutional record
    commercial = "New institutional commercial building with structural steel and mechanical systems"
    assert _score("general_contractor", commercial) > _score("civil_contractor", commercial)


def test_preset_switching_changes_active_config() -> None:
    civil = presets.load_preset_config("civil_contractor", root=REPO_ROOT)
    residential = presets.load_preset_config("multifamily_residential", root=REPO_ROOT)
    assert civil.company_name != residential.company_name
    assert len(civil.rules_for("negative")) != len(residential.rules_for("negative"))


def test_apply_preset_to_copy_preserves_user_customization() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "my_keywords.xlsx"
        applied = presets.apply_preset_to_copy("multifamily_residential", dest, root=REPO_ROOT)
        assert applied.exists()
        # a second apply without overwrite must refuse (never clobber user edits)
        try:
            presets.apply_preset_to_copy("civil_contractor", dest, root=REPO_ROOT)
        except presets.PresetError:
            pass
        else:  # pragma: no cover
            raise AssertionError("apply_preset_to_copy overwrote an existing workbook")
        # overwrite=True is allowed
        presets.apply_preset_to_copy("civil_contractor", dest, root=REPO_ROOT, overwrite=True)


def test_preset_identity_and_manifest_fields() -> None:
    path = presets.resolve_preset_keywords_path("general_contractor", root=REPO_ROOT)
    identified = presets.identify_preset(path, root=REPO_ROOT)
    assert identified is not None and identified.preset_id == "general_contractor"
    fields = presets.preset_manifest_fields(identified)
    assert fields["preset_id"] == "general_contractor"
    assert fields["preset_version"] == "1.0.0"
    # a non-preset workbook is not identified as a preset
    assert presets.identify_preset(REPO_ROOT / "config" / "keywords.xlsx", root=REPO_ROOT) is None


def test_unknown_preset_raises() -> None:
    try:
        presets.get_preset("nope")
    except presets.PresetError:
        return
    raise AssertionError("unknown preset must raise PresetError")


def main() -> int:
    tests = [value for name, value in sorted(globals().items())
             if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")
    print(f"Build Week presets tests: {len(tests)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

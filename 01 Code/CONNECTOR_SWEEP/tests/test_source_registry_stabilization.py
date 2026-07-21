from __future__ import annotations

import csv
import hashlib
import os
import shutil
import sys
import tempfile
from pathlib import Path


CODE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = CODE_DIR.parents[1]
sys.path.insert(0, str(CODE_DIR))

import tenderfinder_raw_sweep as raw_sweep  # noqa: E402
from tenderfinder_engine import (  # noqa: E402
    _assess_development_live_sample,
    test_source_definition,
    validate_source_definition,
)
from tenderfinder_runtime import STATE_ROOT_ENV_VAR  # noqa: E402
from tenderfinder_source_registry import (  # noqa: E402
    OPERATIONAL_STATUSES,
    SOURCE_COLUMNS,
    SourceRegistryError,
    load_source_rows,
    registry_summary,
    source_is_runtime_eligible,
    source_skip_reason,
    update_source_test_metadata,
    upsert_source,
    write_source_rows,
)
from tenderfinder_source_testing import (  # noqa: E402
    ADAPTER_FIXTURES,
    NO_FIXTURE_STATUS,
    run_offline_adapter_fixture,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_canonical_status_classification_is_truthful() -> None:
    summary = registry_summary(root=REPO_ROOT)
    assert summary["total"] == 39
    assert summary["enabled"] == 39
    assert summary["verified_live"] == 1
    assert summary["ready_for_live_test"] == 26
    assert summary["manual_only"] == 4
    assert summary["needs_configuration"] == 3
    assert summary["blocked"] == 1
    assert summary["wrong_source"] == 4
    assert summary["runtime_eligible"] == 27
    assert sum(summary[status] for status in OPERATIONAL_STATUSES) == summary["total"]

    rows = {row["source_id"]: row for row in load_source_rows(root=REPO_ROOT)}
    assert rows["surrey_futureworks"]["operational_status"] == "blocked"
    assert "operational_status=blocked" in source_skip_reason(rows["surrey_futureworks"])
    assert rows["new_west_currentdev"]["operational_status"] == "wrong_source"
    assert rows["surrey_bids_public"]["operational_status"] == "ready_for_live_test"
    assert source_is_runtime_eligible(rows["surrey_bids_public"])


def test_non_operational_connector_is_skipped_before_network() -> None:
    row = next(
        item for item in load_source_rows(root=REPO_ROOT)
        if item["source_id"] == "surrey_futureworks"
    )
    row["runtime_skip_reason"] = source_skip_reason(row)
    old_http = raw_sweep.http_get
    raw_sweep.http_get = lambda *_args, **_kwargs: (_ for _ in ()).throw(
        AssertionError("network helper must not be called")
    )
    try:
        result = raw_sweep.run_connector(row, 5, probe=False)
    finally:
        raw_sweep.http_get = old_http
    assert result["status"] == "skipped_source_status"
    assert result["records_pulled"] == 0
    assert result["next_action"]


def _add_unknown_column(path: Path) -> None:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    fields.append("founder_history_note")
    for row in rows:
        row["founder_history_note"] = "keep this historical note"
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_atomic_write_backup_unknown_columns_and_failed_write_restore() -> None:
    canonical = REPO_ROOT / "config" / "sources.csv"
    with tempfile.TemporaryDirectory() as temp:
        temp_root = Path(temp)
        registry = temp_root / "sources.csv"
        backups = temp_root / "backups"
        shutil.copy2(canonical, registry)
        _add_unknown_column(registry)
        before = registry.read_bytes()
        rows = load_source_rows(registry)
        rows[0]["notes"] += " | atomic-write test"
        write_source_rows(rows, registry, backup_root=backups)

        with registry.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            assert "founder_history_note" in (reader.fieldnames or [])
            assert all(row["founder_history_note"] == "keep this historical note" for row in reader)
        backup_files = list(backups.glob("sources_*.csv.bak"))
        assert len(backup_files) == 1
        assert backup_files[0].read_bytes() == before
        assert not list(temp_root.glob(".*.tmp"))

        stable = registry.read_bytes()
        broken = load_source_rows(registry)
        broken[1]["source_id"] = broken[0]["source_id"]
        try:
            write_source_rows(broken, registry, backup_root=backups)
        except SourceRegistryError as exc:
            assert "duplicate source_id" in str(exc)
        else:
            raise AssertionError("invalid registry was written")
        assert registry.read_bytes() == stable
        assert len(list(backups.glob("sources_*.csv.bak"))) == 1
        assert not list(temp_root.glob(".*.tmp"))


def test_private_and_duplicate_runnable_endpoints_are_rejected() -> None:
    canonical = REPO_ROOT / "config" / "sources.csv"
    with tempfile.TemporaryDirectory() as temp:
        temp_root = Path(temp)
        registry = temp_root / "sources.csv"
        backups = temp_root / "backups"
        shutil.copy2(canonical, registry)
        template = next(
            row for row in load_source_rows(registry)
            if row["source_id"] == "abbotsford_devapps"
        )

        private = dict(template)
        private["source_id"] = "private_endpoint_test"
        private["name"] = "Private endpoint test"
        private["url"] = "http://10.0.0.1/rest/services/private"
        private["endpoint"] = private["url"]
        private["last_good_endpoint"] = ""
        private["operational_status"] = "ready_for_live_test"
        try:
            upsert_source(private, registry, backup_root=backups)
        except SourceRegistryError as exc:
            assert "non-public address" in str(exc)
        else:
            raise AssertionError("private development endpoint was accepted")

        duplicate = dict(template)
        duplicate["source_id"] = "duplicate_endpoint_test"
        duplicate["name"] = "Duplicate endpoint test"
        duplicate["operational_status"] = "ready_for_live_test"
        try:
            upsert_source(duplicate, registry, backup_root=backups)
        except SourceRegistryError as exc:
            assert "duplicate runnable endpoint" in str(exc)
        else:
            raise AssertionError("duplicate runnable endpoint was accepted")


def test_every_supported_adapter_has_a_passing_offline_fixture() -> None:
    canonical_before = sha256(REPO_ROOT / "config" / "sources.csv")
    rows = load_source_rows(root=REPO_ROOT)
    representative = {}
    for row in rows:
        representative.setdefault(row["adapter"], row)
    assert set(ADAPTER_FIXTURES) == set(representative)
    for adapter, row in representative.items():
        result = run_offline_adapter_fixture(row, root=REPO_ROOT)
        assert result["network_used"] is False
        assert result["passed"] is True, (adapter, result)
        assert result["parser_used"] is True, (adapter, result)
        assert result["parser"]
        assert result["candidate_count"] > 0
        assert result["normalized_count"] > 0
        assert result["status_code"] == "PASS_ADAPTER_FIXTURE"
    assert sha256(REPO_ROOT / "config" / "sources.csv") == canonical_before


def test_no_fixture_is_not_reported_as_pass() -> None:
    row = {column: "" for column in SOURCE_COLUMNS}
    row.update(
        source_id="custom_fixture_test",
        name="Custom fixture test",
        track="tender",
        active="N",
        adapter="custom_future_adapter",
        url="https://public.example.org/source",
        operational_status="config_valid_only",
    )
    result = run_offline_adapter_fixture(row, root=REPO_ROOT)
    assert result["passed"] is False
    assert result["parser_used"] is False
    assert result["status"] == NO_FIXTURE_STATUS
    assert result["status_code"] == "NOT_TESTED_NO_FIXTURE"


def test_validation_fixture_and_live_operations_are_distinct() -> None:
    config = validate_source_definition("surrey_bids_public", root=REPO_ROOT)
    fixture = test_source_definition("surrey_bids_public", root=REPO_ROOT, allow_network=False)
    assert config["passed"] is True and config["parser_used"] is False
    assert config["status_code"] == "CONFIG_VALID"
    assert fixture["passed"] is True and fixture["network_used"] is False
    assert fixture["status_code"] == "PASS_ADAPTER_FIXTURE"
    assert fixture["normalized_count"] > 0


def test_fixture_result_metadata_persists_only_to_selected_registry() -> None:
    canonical = REPO_ROOT / "config" / "sources.csv"
    canonical_before = sha256(canonical)
    previous_state = os.environ.get(STATE_ROOT_ENV_VAR)
    with tempfile.TemporaryDirectory() as temp:
        temp_root = Path(temp)
        registry = temp_root / "sources.csv"
        shutil.copy2(canonical, registry)
        os.environ[STATE_ROOT_ENV_VAR] = str(temp_root / "state")
        try:
            result = test_source_definition(
                "surrey_bids_public",
                root=REPO_ROOT,
                sources_path=registry,
                allow_network=False,
                persist_result=True,
            )
        finally:
            if previous_state is None:
                os.environ.pop(STATE_ROOT_ENV_VAR, None)
            else:
                os.environ[STATE_ROOT_ENV_VAR] = previous_state
        assert result["passed"] is True
        row = next(item for item in load_source_rows(registry) if item["source_id"] == "surrey_bids_public")
        assert row["operational_status"] == "adapter_fixture_pass"
        assert row["last_test_type"] == "offline_fixture"
        assert row["last_test_result"] == "PASS_ADAPTER_FIXTURE"
        assert int(row["last_candidate_count"]) > 0
        assert int(row["last_normalized_count"]) > 0
    assert sha256(canonical) == canonical_before


def test_development_live_sample_requires_meaningful_relevant_project() -> None:
    source = {
        "source_id": "surrey_devapps_v2",
        "name": "Surrey Development Applications",
    }
    result = _assess_development_live_sample(
        source,
        [
            {
                "project_id": "SURREY-19032200",
                "app_no": "19-0322-00",
                "municipality": "Surrey",
                "scope_summary": (
                    "Rezoning and development permit for three industrial lots "
                    "and a new industrial building."
                ),
                "fit_score": 70,
                "source_url": "https://example.org/public/project/19032200",
            }
        ],
    )
    assert result["passed"] is True
    assert result["meaningful_count"] == 1
    assert result["relevant_count"] == 1
    assert result["warnings"] == []
    assert result["normalized_preview"][0]["signal_quality"] == "HIGH"
    assert result["normalized_preview"][0]["route"] == "Future_Projects"


def test_development_live_sample_rejects_thin_low_fit_layer_rows() -> None:
    source = {
        "source_id": "abbotsford_devapps",
        "name": "Abbotsford Development Applications",
    }
    result = _assess_development_live_sample(
        source,
        [
            {
                "project_id": "ABBOTSFORD-PRJ21209",
                "app_no": "PRJ21-209",
                "municipality": "Abbotsford",
                "title": "Abbotsford",
                "scope_summary": "",
                "fit_score": 35,
                "source_url": "https://example.org/public/layer/6",
            }
        ],
    )
    assert result["passed"] is False
    assert result["meaningful_count"] == 0
    assert result["relevant_count"] == 0
    assert len(result["warnings"]) == 2
    assert result["normalized_preview"][0]["signal_quality"] == "LOW"
    assert result["normalized_preview"][0]["route"] == "Run_Queue"


def test_live_persistence_keeps_base_endpoint_separate_from_request_audit_url() -> None:
    canonical = REPO_ROOT / "config" / "sources.csv"
    previous_state = os.environ.get(STATE_ROOT_ENV_VAR)
    original_run_connector = raw_sweep.run_connector
    with tempfile.TemporaryDirectory() as temp:
        temp_root = Path(temp)
        registry = temp_root / "sources.csv"
        shutil.copy2(canonical, registry)
        base_url = "https://public.example.org/FeatureServer/0"
        request_url = base_url + "/query?where=1%3D1&resultRecordCount=5&f=json"

        def fake_run_connector(*_args, **_kwargs):
            return {
                "records_pulled": 1,
                "leads": [
                    {
                        "project_id": "SURREY-TEST-1",
                        "municipality": "Surrey",
                        "scope_summary": "Rezoning and subdivision for a new industrial development.",
                        "fit_score": 70,
                        "source_url": "https://public.example.org/project/1",
                    }
                ],
                "rejected": [],
                "error": "",
                "status": "live",
                "http_status": 200,
                "resolved_endpoint": base_url,
                "final_validated_url": request_url,
            }

        raw_sweep.run_connector = fake_run_connector
        os.environ[STATE_ROOT_ENV_VAR] = str(temp_root / "state")
        try:
            result = test_source_definition(
                "surrey_devapps_v2",
                root=REPO_ROOT,
                sources_path=registry,
                allow_network=True,
                persist_result=True,
            )
        finally:
            raw_sweep.run_connector = original_run_connector
            if previous_state is None:
                os.environ.pop(STATE_ROOT_ENV_VAR, None)
            else:
                os.environ[STATE_ROOT_ENV_VAR] = previous_state

        persisted = next(
            item for item in load_source_rows(registry)
            if item["source_id"] == "surrey_devapps_v2"
        )
        assert result["passed"] is True
        assert result["final_validated_url"] == request_url
        assert persisted["last_good_endpoint"] == base_url
        assert persisted["last_good_endpoint"] != result["final_validated_url"]


def main() -> int:
    tests = [
        test_canonical_status_classification_is_truthful,
        test_non_operational_connector_is_skipped_before_network,
        test_atomic_write_backup_unknown_columns_and_failed_write_restore,
        test_private_and_duplicate_runnable_endpoints_are_rejected,
        test_every_supported_adapter_has_a_passing_offline_fixture,
        test_no_fixture_is_not_reported_as_pass,
        test_validation_fixture_and_live_operations_are_distinct,
        test_fixture_result_metadata_persists_only_to_selected_registry,
        test_development_live_sample_requires_meaningful_relevant_project,
        test_development_live_sample_rejects_thin_low_fit_layer_rows,
        test_live_persistence_keeps_base_endpoint_separate_from_request_audit_url,
    ]
    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")
    print(f"Source registry stabilization tests: {len(tests)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

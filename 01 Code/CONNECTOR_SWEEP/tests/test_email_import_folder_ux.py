from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tenderfinder_email_intake import (  # noqa: E402
    connect_email_provider,
    current_email_import_folder,
    evaluate_email_folder,
    load_email_provider_config,
    run_email_intake,
    test_email_intake,
)
from tenderfinder_package_paths import (  # noqa: E402
    detect_package_root,
    email_inbox_dir,
    email_import_state_path,
    ensure_email_alert_dirs,
    tenderfinder_user_config_path,
)


def build_fake_package_root(root: Path) -> Path:
    (root / "run_tenderfinder_demo.bat").write_text("@echo off\n", encoding="utf-8")
    (root / "verify_package.bat").write_text("@echo off\n", encoding="utf-8")
    (root / "inputs").mkdir(parents=True, exist_ok=True)
    (root / "01 Code" / "CONNECTOR_SWEEP").mkdir(parents=True, exist_ok=True)
    return root


def main() -> int:
    fixtures = Path(__file__).resolve().parent / "fixtures" / "email_alerts"
    with tempfile.TemporaryDirectory() as tmp:
        root = build_fake_package_root(Path(tmp))
        nested = root / "01 Code" / "CONNECTOR_SWEEP" / "nested" / "script.py"
        nested.parent.mkdir(parents=True, exist_ok=True)
        nested.write_text("pass", encoding="utf-8")

        detected = detect_package_root(nested)
        assert detected == root

        dirs = ensure_email_alert_dirs(root)
        for key in ("inbox", "processed", "rejected", "logs"):
            assert dirs[key].exists(), f"missing {key}"
            assert (dirs[key] / "README.md").exists(), f"missing {key} README"

        chosen = root / "OneDrive Test" / "Email notifications for test"
        chosen.mkdir(parents=True, exist_ok=True)
        config_path = connect_email_provider("manual_folder", import_path=str(chosen), root=root)
        assert config_path == tenderfinder_user_config_path(root)
        config = load_email_provider_config(root)
        assert config.import_path == str(chosen)
        assert current_email_import_folder(root) == chosen

        working = root / "work_emails"
        shutil.copytree(fixtures, working)
        before = sorted(p.name for p in working.glob("*.eml"))
        result = test_email_intake(working, provider_config=config, root=root)
        after = sorted(p.name for p in working.glob("*.eml"))
        assert before == after, "dry-run moved or modified email files"
        assert result.alert_emails_found >= 6
        assert result.log_path and Path(result.log_path).exists()

        out_dir = root / "email_out"
        status1, rows1, report1 = run_email_intake(out_dir, working, dry_run=False, provider_config=config, root=root)
        assert status1 == "EMAIL_INTAKE_PARSED_ROWS"
        assert rows1, "expected parsed rows on first run"
        assert email_import_state_path(root).exists(), "import state not written"

        status2, rows2, report2 = run_email_intake(out_dir, working, dry_run=False, provider_config=config, root=root)
        assert status2 in {"EMAIL_INTAKE_REJECTED_FILES", "EMAIL_INTAKE_PARSE_ZERO_ROWS"}
        assert not rows2, "duplicate run should not emit new rows"
        assert report2.duplicate_emails_detected >= 1

        print("Email import folder UX tests: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import os
import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import tenderfinder_launcher_gui as g  # noqa: E402
from tenderfinder_runtime import STATE_ROOT_ENV_VAR  # noqa: E402


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        package_root = base / "package"
        state_root = base / "state"
        package_root.mkdir(parents=True, exist_ok=True)
        (package_root / "run_tenderfinder_demo.bat").write_text("@echo off\n", encoding="utf-8")
        (package_root / "verify_package.bat").write_text("@echo off\n", encoding="utf-8")
        (package_root / "inputs").mkdir(parents=True, exist_ok=True)
        (package_root / "01 Code" / "CONNECTOR_SWEEP").mkdir(parents=True, exist_ok=True)

        old_root = g.ROOT_DIR
        old_state = os.environ.get(STATE_ROOT_ENV_VAR)
        os.environ[STATE_ROOT_ENV_VAR] = str(state_root)
        opened: list[str] = []
        try:
            g.ROOT_DIR = package_root
            app = g.TenderFinderLauncherApp()
            app.root.withdraw()
            app.messagebox.showinfo = lambda *a, **k: None
            original_open = g.open_path_with_default_app
            g.open_path_with_default_app = lambda path: opened.append(path)
            app._on_create_open_email_import_folder()
            inbox = state_root / "settings" / "email_alerts" / "inbox"
            assert inbox.exists()
            assert opened and opened[-1] == str(inbox)
            assert "Selected import folder:" in app.email_folder_var.get()
        finally:
            g.ROOT_DIR = old_root
            if old_state is None:
                os.environ.pop(STATE_ROOT_ENV_VAR, None)
            else:
                os.environ[STATE_ROOT_ENV_VAR] = old_state
            try:
                g.open_path_with_default_app = original_open
            except Exception:
                pass
            try:
                import tkinter as tk
                tk.Tk.destroy(app.root)
            except Exception:
                pass
    print("Email import GUI folder action tests: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

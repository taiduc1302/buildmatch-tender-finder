# Change Index

Branch: `claude/buildmatch-tender-finder-completion-03pg2w` (base: `main`).

## Recovery

No prior Codex commit `cc03740…` existed on the remote or locally, and the
branch was identical to `origin/main` — **Case C** (previous changes did not
exist). All Build Week work below was implemented fresh from repository evidence
and the specification; no existing work was discarded.

## Product code

- `tenderfinder_data_modes.py` (new) — data modes, provenance, metrics, pointer.
- `tenderfinder_presets.py` (new) — contractor-profile presets.
- `tenderfinder_refresh_service.py` (new) — development-refresh orchestration.
- `tenderfinder_ai_analysis.py` (new) — OpenAI analysis service.
- `tenderfinder_ai_controller.py` (new) — AI render/export controller.
- `tenderfinder_snapshot.py` (new) — public-snapshot loader/validator/promoter.
- `tenderfinder_launcher_gui.py` (edit) — data-mode banner, preset selector,
  Refresh + AI buttons, display-agnostic helpers, deterministic Stop-log fix.
- `tenderfinder_engine.py` (edit) — `test_source_definition.__test__ = False`.

## Tests

- `tests/test_buildweek_data_modes.py` (new, 17)
- `tests/test_buildweek_presets.py` (new, 9)
- `tests/test_buildweek_refresh_service.py` (new, 8)
- `tests/test_buildweek_ai_analysis.py` (new, 23 + 1 opt-in live)
- `tests/test_buildweek_gui_helpers.py` (new, 8)
- `tests/test_buildweek_snapshot.py` (new, 6)
- `tests/test_launcher_gui.py` (edit) — portable paths, truthful counts, Tk skip.
- `tests/test_source_registry_stabilization.py` (edit) — portable temp dirs.
- `tests/test_surrey_tender_status.py` (edit) — dynamic future date.

## Fixtures

- `tests/fixtures/email_alerts/*.eml` (new, 6 sanitized synthetic) + generator.

## Configuration

- `config/presets/*.xlsx` (new, 3 preset workbooks) + `generate_presets.py`.

## Data

- `demo_data/public_snapshot/development_snapshot.csv` + `snapshot_manifest.json`
  + `generate_snapshot.py` (new, sanitized PUBLIC_SNAPSHOT demo).

## CI / packaging

- `scripts/build_clean_release.py` (edit) — exclude forbidden-suffix fixtures;
  ship presets, snapshot, and Build Week tests.
- `scripts/windows_acceptance.ps1` (new) — automated Windows acceptance.
- `.gitignore` / `.gitattributes` (edit) — track sanitized `.eml` fixtures with
  stable bytes.

## Documentation

- `docs/buildweek/00…10` (new) — this set.
- `README.md`, `ENTRY_POINTS.md` (edit).

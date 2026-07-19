# BuildMatch Tender Finder — Windows automated acceptance script.
#
# Runs every headless-verifiable acceptance check on Windows. Interactive GUI
# steps, live public-network refresh, and live OpenAI calls remain manual and
# are listed in docs/buildweek/08_WINDOWS_ACCEPTANCE.md.
#
# Usage (from the repository root, in PowerShell):
#   .\scripts\windows_acceptance.ps1
#
# Exit code 0 = all automated checks passed.

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

function Section($name) { Write-Host "`n=== $name ===" -ForegroundColor Cyan }

# Resolve the venv python if present, else system python.
$py = Join-Path $repo ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }
$code = Join-Path $repo "01 Code\CONNECTOR_SWEEP"

Section "1. Offline CI check"
& $py "scripts\offline_ci_check.py"

Section "2. Full offline pytest suite"
Push-Location $code
& $py -m pytest tests\ -q
$pytestExit = $LASTEXITCODE
Pop-Location
if ($pytestExit -ne 0) { throw "pytest failed" }

Section "3. Authoritative offline Self-Test"
& $py -c "import sys; sys.path.insert(0, r'$code'); from tenderfinder_engine import run_self_test; r = run_self_test(); print('SELF_TEST passed:', r.passed, r.test_totals); sys.exit(0 if r.passed else 1)"

Section "4. Package audit"
& $py "scripts\package_audit.py" --mode repo .

Section "5. Build clean release"
$rel = Join-Path $env:TEMP "tf_release"
& $py "scripts\build_clean_release.py" --output-dir $rel

Section "6. Verify clean release"
$zip = Get-ChildItem -Path $rel -Filter *.zip | Select-Object -First 1
& $py "scripts\verify_clean_release.py" $zip.FullName

Section "7. Public Snapshot validation + scoring acceptance"
Push-Location $code
& $py -m pytest tests\test_buildweek_snapshot.py -q
Pop-Location

Section "8. Contractor presets"
Push-Location $code
& $py -m pytest tests\test_buildweek_presets.py -q
Pop-Location

Section "9. Mocked OpenAI GUI flow + missing-key + cache"
Push-Location $code
& $py -m pytest tests\test_buildweek_ai_analysis.py tests\test_buildweek_gui_helpers.py -q
Pop-Location

Section "10. Refresh orchestration + rollback + truthful metrics"
Push-Location $code
& $py -m pytest tests\test_buildweek_refresh_service.py tests\test_buildweek_data_modes.py -q
Pop-Location

Write-Host "`nALL AUTOMATED WINDOWS ACCEPTANCE CHECKS PASSED." -ForegroundColor Green
Write-Host "Remaining manual checks: interactive GUI, live public-network refresh, live OpenAI key." -ForegroundColor Yellow

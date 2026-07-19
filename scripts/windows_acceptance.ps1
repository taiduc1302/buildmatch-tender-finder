# BuildMatch Tender Finder — Windows automated acceptance script.
#
# Runs every headless-verifiable acceptance check on Windows. Interactive GUI
# steps, live public-network refresh, and live OpenAI calls remain manual and
# are listed in docs/buildweek/08_WINDOWS_ACCEPTANCE.md.
#
# Usage (from the repository root, in PowerShell):
#   powershell -ExecutionPolicy Bypass -File .\scripts\windows_acceptance.ps1
#
# Exit code 0 = every step below genuinely passed. IMPORTANT: PowerShell's
# $ErrorActionPreference = "Stop" does NOT turn a non-zero exit code from an
# external process (python.exe, pytest) into a terminating error — only
# PowerShell cmdlet errors trigger that. Every step below is therefore run
# through Invoke-Step, which explicitly checks $LASTEXITCODE and aborts the
# whole script immediately on the first real failure, so a later "ALL PASSED"
# banner can never print while an earlier step silently failed.

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

function Section($name) { Write-Host "`n=== $name ===" -ForegroundColor Cyan }

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Command
    )
    Section $Name
    & $Command
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`nFAILED: $Name (exit code $LASTEXITCODE)" -ForegroundColor Red
        throw "Windows acceptance step failed: $Name"
    }
}

# Resolve the venv python if present (created by setup_tenderfinder_environment.bat
# / Launch_TENDER_FINDER_GUI.bat), else fall back to system python.
$py = Join-Path $repo ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "No .venv found at $py - falling back to system 'python'. Run " -ForegroundColor Yellow -NoNewline
    Write-Host "Launch_TENDER_FINDER_GUI.bat once first for a reproducible environment." -ForegroundColor Yellow
    $py = "python"
}
$code = Join-Path $repo "01 Code\CONNECTOR_SWEEP"

Section "0. Python environment"
& $py --version
if ($LASTEXITCODE -ne 0) { throw "Could not resolve a working Python interpreter at '$py'." }
Write-Host "Using interpreter: $py"

Invoke-Step "1. Offline CI check (syntax, imports, zero-network guard)" {
    & $py "scripts\offline_ci_check.py"
}

Invoke-Step "2. Full offline pytest suite" {
    Push-Location $code
    try { & $py -m pytest tests\ -q } finally { Pop-Location }
}

Invoke-Step "3. Authoritative offline Self-Test" {
    & $py -c "import sys; sys.path.insert(0, r'$code'); from tenderfinder_engine import run_self_test; r = run_self_test(); print('SELF_TEST passed:', r.passed, r.test_totals); sys.exit(0 if r.passed else 1)"
}

Invoke-Step "4. Package audit" {
    & $py "scripts\package_audit.py" --mode repo .
}

$rel = Join-Path $env:TEMP ("tf_release_" + [System.Guid]::NewGuid().ToString("N").Substring(0, 8))
Invoke-Step "5. Build clean release" {
    & $py "scripts\build_clean_release.py" --output-dir $rel
}

Invoke-Step "6. Verify clean release" {
    $zip = Get-ChildItem -Path $rel -Filter *.zip | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $zip) { throw "No release zip found under $rel after the build step." }
    & $py "scripts\verify_clean_release.py" $zip.FullName
}

Invoke-Step "7. Public Snapshot validation + scoring acceptance" {
    Push-Location $code
    try { & $py -m pytest tests\test_buildweek_snapshot.py -q } finally { Pop-Location }
}

Invoke-Step "8. Contractor presets (Civil / Multi-Family Residential / General)" {
    Push-Location $code
    try { & $py -m pytest tests\test_buildweek_presets.py -q } finally { Pop-Location }
}

Invoke-Step "9. Mocked OpenAI analysis + GUI helpers (missing-key, cache, disagreement)" {
    Push-Location $code
    try { & $py -m pytest tests\test_buildweek_ai_analysis.py tests\test_buildweek_gui_helpers.py -q } finally { Pop-Location }
}

Invoke-Step "10. Refresh orchestration (full sweep, rollback, truthful metrics)" {
    Push-Location $code
    try { & $py -m pytest tests\test_buildweek_refresh_service.py tests\test_buildweek_data_modes.py -q } finally { Pop-Location }
}

Write-Host "`nALL AUTOMATED WINDOWS ACCEPTANCE CHECKS PASSED." -ForegroundColor Green
Write-Host "Release artifact: $rel" -ForegroundColor Green
Write-Host "Remaining manual/interactive checks (see docs\buildweek\08_WINDOWS_ACCEPTANCE.md):" -ForegroundColor Yellow
Write-Host "  - Interactive GUI: layout, ranked-opportunity selection, dialogs, workbook opening" -ForegroundColor Yellow
Write-Host "  - A real live public-network 'Refresh Development Data' run" -ForegroundColor Yellow
Write-Host "  - A real live OpenAI analysis with your own OPENAI_API_KEY" -ForegroundColor Yellow

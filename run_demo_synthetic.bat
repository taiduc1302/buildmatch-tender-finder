@echo off
setlocal

REM ============================================================
REM Tender Finder - OFFLINE SYNTHETIC DEMO
REM Added by the sanitized portable package.
REM
REM Uses only synthetic data shipped with the package:
REM   inputs\all_live_review.xlsx        (12 fictitious records)
REM   demo_data\email_alerts\*.eml       (3 fictitious tender alerts)
REM No network access is performed (--no-fetch).
REM
REM EXPECTED RESULT: the three-bucket workbook builds successfully
REM (BID NOW=2, BID LATER=6, WATCH=2, ANALYZED=5). The final
REM "user master" stage then reports Overall: FAIL - that is the
REM anti-fixture production guard correctly refusing synthetic
REM rows. It is NOT a bug. See README.md / RUNBOOK.md.
REM ============================================================

cd /d "%~dp0"

set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

set "OUT_DIR=%~dp0demo_out_synthetic"

%PYTHON_EXE% "01 Code\CONNECTOR_SWEEP\tenderfinder_demo_three_buckets.py" ^
  --review-xlsx "inputs\all_live_review.xlsx" ^
  --out-dir "%OUT_DIR%" ^
  --no-fetch ^
  --email-intake ^
  --email-import-path "demo_data\email_alerts"

echo.
echo ============================================================
echo Synthetic demo finished.
echo Workbook: "%OUT_DIR%\TENDER_FINDER_DEMO_Opportunities_Three_Buckets.xlsx"
echo Reminder: "final-review verification reported FAIL" is the
echo expected anti-fixture guard result on synthetic data.
echo ============================================================
if /I not "%TENDER_FINDER_DEMO_NO_PAUSE%"=="1" pause
exit /b 0

@echo off
setlocal

REM ============================================================
REM TENDER_FINDER Fast Demo Launcher - Patch 5.23
REM Uses --no-fetch for bad wifi. Track A, Action Center, and
REM the intake plan still build instantly.
REM
REM Patch 5.18 fix: this used to point at the stale
REM live_outputs_p54\all17_live_review.xlsx (2026-06-25 snapshot),
REM which produces different Track A totals (BID LATER/WATCH/ANALYZED
REM = 5393/999/12766) than run_tenderfinder_demo.bat and the GUI, both of
REM which already use the corrected, current review workbook below
REM (7537/973/25119). Fast mode and full mode must never silently
REM disagree on Track A just because of a stale hardcoded path.
REM ============================================================
REM Review workbook lookup order (added 5.20, same as run_tenderfinder_demo.bat):
REM   1. TENDER_FINDER_REVIEW_XLSX environment variable
REM   2. package-local inputs\all_live_review.xlsx
set "REVIEW_XLSX=%~dp0inputs\all_live_review.xlsx"
if defined TENDER_FINDER_REVIEW_XLSX set "REVIEW_XLSX=%TENDER_FINDER_REVIEW_XLSX%"
set "OUT_DIR=C:\tenderfinder_out\demo_p523_fast"

set "SCRIPT=01 Code\CONNECTOR_SWEEP\tenderfinder_demo_three_buckets.py"
set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
set "WORKBOOK=%OUT_DIR%\TENDER_FINDER_DEMO_Opportunities_Three_Buckets.xlsx"
set "SUMMARY=%OUT_DIR%\demo_summary.txt"

cd /d "%~dp0"

if not exist "%SCRIPT%" (
  echo ERROR: Demo builder not found: "%SCRIPT%"
  pause
  exit /b 1
)

if not exist "%REVIEW_XLSX%" (
  echo ERROR: Review workbook not found: "%REVIEW_XLSX%"
  echo Edit REVIEW_XLSX at the top of this launcher.
  pause
  exit /b 1
)

if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"
%PYTHON_EXE% "%SCRIPT%" --review-xlsx "%REVIEW_XLSX%" --out-dir "%OUT_DIR%" --email-intake --no-fetch
if errorlevel 1 (
  echo ERROR: TENDER_FINDER fast demo build failed.
  pause
  exit /b 1
)

if /I not "%TENDER_FINDER_DEMO_NO_OPEN%"=="1" (
  if exist "%OUT_DIR%" start "" "%OUT_DIR%"
  if exist "%WORKBOOK%" start "" "%WORKBOOK%"
)

if exist "%SUMMARY%" (
  type "%SUMMARY%"
) else (
  echo ============================================================
  echo TENDER_FINDER FAST DEMO COMPLETE - summary file missing.
  echo Workbook: "%WORKBOOK%"
  echo ============================================================
)

if /I "%TENDER_FINDER_DEMO_NO_PAUSE%"=="1" exit /b 0
pause
exit /b 0

@echo off
setlocal
cd /d "%~dp0"

set "ROOT=%~dp0"
set "PY=%ROOT%.venv\Scripts\python.exe"
set "SELF_TEST=%ROOT%01 Code\CONNECTOR_SWEEP\tenderfinder_self_test.py"

echo ============================================================
echo TENDER_FINDER shared offline package Self-Test
echo ============================================================

if not exist "%SELF_TEST%" (
  echo ERROR: Missing shared Self-Test runner:
  echo   "%SELF_TEST%"
  exit /b 1
)

if not exist "%PY%" (
  echo TENDER_FINDER environment is missing. Running one-time setup...
  call "%ROOT%setup_tenderfinder_environment.bat"
  if errorlevel 1 exit /b 1
)

if not exist "%PY%" (
  echo ERROR: Setup did not create "%PY%"
  exit /b 1
)

"%PY%" -u "%SELF_TEST%" --root "%ROOT%"
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" (
  echo VERIFY_PACKAGE: FAIL
  exit /b %RESULT%
)

echo VERIFY_PACKAGE: PASS
exit /b 0

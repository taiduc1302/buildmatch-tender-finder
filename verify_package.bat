@echo off
setlocal
cd /d "%~dp0"

set "ROOT=%~dp0"
set "ROOT_NORM=%ROOT:~0,-1%"
set "SCRIPT_DIR=%ROOT%01 Code\CONNECTOR_SWEEP"
set "PY=%ROOT%.venv\Scripts\python.exe"

if not exist "%PY%" (
  where python >nul 2>&1
  if %errorlevel%==0 (
    set "PY=python"
  ) else (
    where py >nul 2>&1
    if %errorlevel%==0 (
      set "PY=py -3"
    )
  )
)

echo ============================================================
echo TENDER_FINDER package verification
echo ============================================================

if not exist "%SCRIPT_DIR%\tenderfinder_demo_three_buckets.py" (
  echo ERROR: Missing demo builder under "%SCRIPT_DIR%"
  exit /b 1
)

for %%F in (
  "run_tenderfinder_demo.bat"
  "run_tenderfinder_demo_fast.bat"
  "Launch_TENDER_FINDER_GUI.bat"
  "setup_venv.bat"
  "README_QUICKSTART.md"
  "README_INSTALL.md"
  "PATCH_NOTES.md"
  "KNOWN_LIMITATIONS.md"
  "Email_Setup_Guide.md"
  "PACKAGE_MANIFEST.md"
) do (
  if not exist "%ROOT%%%~F" (
    echo ERROR: Missing required file %%~F
    exit /b 1
  )
)

for %%D in (
  "user_data\email_alerts\inbox\README.md"
  "user_data\email_alerts\processed\README.md"
  "user_data\email_alerts\rejected\README.md"
  "user_data\email_alerts\logs\README.md"
) do (
  if not exist "%ROOT%%%~D" (
    echo ERROR: Missing required placeholder %%~D
    exit /b 1
  )
)

echo [1/4] Package-root and empty-folder email check
%PY% -c "import sys; from pathlib import Path; sys.path.insert(0, str(Path(r'%SCRIPT_DIR%'))); from tenderfinder_package_paths import ensure_email_alert_dirs, detect_package_root; from tenderfinder_email_intake import test_email_intake, EmailProviderConfig; root=detect_package_root(Path(r'%ROOT_NORM%')); ensure_email_alert_dirs(root); inbox=root/'user_data'/'email_alerts'/'inbox'; result=test_email_intake(inbox, EmailProviderConfig(provider='manual_folder', connected=True, import_path=str(inbox)), root=root); print(f'EMPTY_EMAIL_TEST files={result.alert_emails_found} parsed={result.tender_rows_parsed}'); assert result.alert_emails_found == 0"
if errorlevel 1 exit /b 1

echo [2/4] Synthetic email fixture parser checks
%PY% "%SCRIPT_DIR%\tests\test_email_intake.py"
if errorlevel 1 exit /b 1
%PY% "%SCRIPT_DIR%\tests\test_email_intake_provider_neutral.py"
if errorlevel 1 exit /b 1

echo [3/4] Email folder UX and routing checks
%PY% "%SCRIPT_DIR%\tests\test_email_import_folder_ux.py"
if errorlevel 1 exit /b 1
%PY% "%SCRIPT_DIR%\tests\test_email_import_gui_folder_actions.py"
if errorlevel 1 exit /b 1
%PY% "%SCRIPT_DIR%\tests\test_tender_signal_routing.py"
if errorlevel 1 exit /b 1

echo [4/4] Launcher safe-path checks
set "TENDER_FINDER_GUI_SKIP_E2E=1"
%PY% "%SCRIPT_DIR%\tests\test_launcher_gui.py"
if errorlevel 1 exit /b 1

echo VERIFY_PACKAGE: PASS
exit /b 0

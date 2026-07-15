@echo off
setlocal
cd /d "%~dp0"
set "GUI_SCRIPT=%~dp001 Code\CONNECTOR_SWEEP\tenderfinder_launcher_gui.py"
set "PY=%~dp0.venv\Scripts\python.exe"
set "PYW=%~dp0.venv\Scripts\pythonw.exe"

if not exist "%GUI_SCRIPT%" (
  echo ERROR: GUI launcher script not found:
  echo   "%GUI_SCRIPT%"
  pause
  exit /b 1
)

set "NEEDS_SETUP=0"
if not exist "%PY%" set "NEEDS_SETUP=1"
if not exist "%PYW%" set "NEEDS_SETUP=1"
if "%NEEDS_SETUP%"=="0" (
  "%PY%" -c "import tkinter, openpyxl, bs4, playwright, pandas, pdfplumber, requests, yaml, regex" >nul 2>&1
  if errorlevel 1 set "NEEDS_SETUP=1"
)

if "%NEEDS_SETUP%"=="1" (
  echo TENDER_FINDER first-run setup is preparing its private Python environment.
  echo This happens once and may take several minutes.
  call "%~dp0setup_tenderfinder_environment.bat"
  if errorlevel 1 (
    echo.
    echo ERROR: TENDER_FINDER setup did not complete. Review the messages above.
    pause
    exit /b 1
  )
)

if not exist "%PY%" (
  echo ERROR: Setup finished without creating:
  echo   "%PY%"
  pause
  exit /b 1
)
if not exist "%PYW%" (
  echo ERROR: Setup finished without creating:
  echo   "%PYW%"
  pause
  exit /b 1
)

"%PY%" -c "import tkinter, openpyxl, bs4, playwright, pandas, pdfplumber, requests, yaml, regex" >nul 2>&1
if errorlevel 1 (
  echo ERROR: Setup completed, but required Python dependencies still cannot be imported.
  echo Re-run setup_tenderfinder_environment.bat and review its first ERROR message.
  pause
  exit /b 1
)

start "" "%PYW%" "%GUI_SCRIPT%"
exit /b 0

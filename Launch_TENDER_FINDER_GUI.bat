@echo off
setlocal
cd /d "%~dp0"
set "GUI_SCRIPT=%~dp001 Code\CONNECTOR_SWEEP\tenderfinder_launcher_gui.py"
set "PYW=%~dp0.venv\Scripts\pythonw.exe"

if not exist "%GUI_SCRIPT%" (
  echo ERROR: GUI launcher script not found:
  echo   "%GUI_SCRIPT%"
  pause
  exit /b 1
)

if not exist "%PYW%" (
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

if not exist "%PYW%" (
  echo ERROR: Setup finished without creating:
  echo   "%PYW%"
  pause
  exit /b 1
)

start "" "%PYW%" "%GUI_SCRIPT%"
exit /b 0

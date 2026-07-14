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

if exist "%PYW%" (
  start "" "%PYW%" "%GUI_SCRIPT%"
  exit /b 0
)

where python >nul 2>&1
if %errorlevel%==0 (
  start "" pythonw "%GUI_SCRIPT%"
  exit /b 0
)

where py >nul 2>&1
if %errorlevel%==0 (
  start "" pyw -3 "%GUI_SCRIPT%"
  exit /b 0
)

echo ERROR: Python was not found. Run setup_venv.bat first.
pause
exit /b 1

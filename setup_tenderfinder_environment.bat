@echo off
setlocal enabledelayedexpansion

REM ============================================================
REM TENDER_FINDER Tender Intelligence - One-Time Environment Setup
REM Patch 5.16
REM
REM Run this ONCE. It creates a local virtual environment,
REM installs the Python packages TENDER_FINDER needs, downloads the
REM Playwright Chromium browser (used by the BC Bid connector),
REM and creates a "TENDER_FINDER Tender Intelligence" shortcut on your
REM Desktop that launches the GUI. After this finishes, use that
REM shortcut any time you want to run TENDER_FINDER - no command line
REM needed.
REM ============================================================

cd /d "%~dp0"
set "ROOT=%~dp0"
set "VENV_DIR=%ROOT%.venv"
set "GUI_SCRIPT=%ROOT%01 Code\CONNECTOR_SWEEP\tenderfinder_launcher_gui.py"
set "REQUIREMENTS=%ROOT%requirements.txt"

echo ============================================================
echo TENDER_FINDER Tender Intelligence - Environment Setup
echo ============================================================
echo.

REM --- Step 1: find Python -----------------------------------
echo [1/5] Checking for Python...
call "%ROOT%_python_bootstrap.bat"
if errorlevel 1 (
    echo ERROR: Python 3.11 or newer is required; environment setup cannot continue.
    exit /b 1
)
echo   Found Python: %PY_LAUNCHER%
echo.

REM --- Step 2: create/reuse virtual environment ----------------
echo [2/5] Setting up the local virtual environment...
if exist "%VENV_DIR%\Scripts\python.exe" (
    echo   Existing environment found at "%VENV_DIR%" - reusing it.
) else (
    %PY_LAUNCHER% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to create the virtual environment.
        echo See the message above for details.
        pause
        exit /b 1
    )
    echo   Created "%VENV_DIR%".
)
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "VENV_PYW=%VENV_DIR%\Scripts\pythonw.exe"
echo.

REM --- Step 3: install Python packages -------------------------
echo [3/5] Installing required Python packages...
if not exist "%REQUIREMENTS%" (
    echo.
    echo ERROR: Could not find requirements.txt at:
    echo   "%REQUIREMENTS%"
    pause
    exit /b 1
)
"%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 (
    echo.
    echo ERROR: pip itself could not be prepared. Check internet/proxy access and retry setup.
    exit /b 1
)
"%VENV_PY%" -m pip install -r "%REQUIREMENTS%"
if errorlevel 1 (
    echo.
    echo ERROR: pip install failed. See the message above for details.
    exit /b 1
)
echo   Packages installed.
echo.

REM --- Step 4: install Playwright's Chromium browser ------------
echo [4/5] Installing the Playwright Chromium browser...
echo   This step downloads roughly 300MB and can take a few minutes
echo   the first time. This only happens once - future setup runs
echo   will skip it if it is already installed.
"%VENV_PY%" -m playwright install chromium
if errorlevel 1 (
    echo.
    echo ERROR: Playwright Chromium installation failed.
    echo   Live BC Bid testing requires this browser. Retry with:
    echo   "%VENV_PY%" -m playwright install chromium
    exit /b 1
)
echo.

REM --- Step 5: create launchers ----------------------------------
echo [5/5] Creating launchers...
set "SHORTCUT_NAME=TENDER_FINDER Tender Intelligence"

REM 5a. The checked-in repo-relative launcher is canonical. Setup must never
REM rewrite it with machine-specific absolute paths.
set "ROOT_LAUNCHER=%ROOT%Launch_TENDER_FINDER_GUI.bat"
if exist "%ROOT_LAUNCHER%" (
    echo   Canonical launcher preserved: "%ROOT_LAUNCHER%"
) else (
    echo ERROR: canonical launcher is missing:
    echo   "%ROOT_LAUNCHER%"
    exit /b 1
)

REM 5b. Best-effort Desktop .lnk shortcut. Ask Windows for the real Desktop
REM path because OneDrive and managed profiles may redirect it away from
REM %%USERPROFILE%%\Desktop. Shortcut creation runs in a subroutine so cmd.exe
REM never mis-parses PowerShell/VB-style parentheses inside this IF block.
set "DESKTOP_DIR="
for /f "usebackq delims=" %%D in (`powershell.exe -NoProfile -NonInteractive -Command "[Environment]::GetFolderPath('Desktop')" 2^>nul`) do set "DESKTOP_DIR=%%D"
if not defined DESKTOP_DIR set "DESKTOP_DIR=%USERPROFILE%\Desktop"
set "SHORTCUT_LNK=!DESKTOP_DIR!\%SHORTCUT_NAME%.lnk"
set "DESKTOP_OK=0"
if exist "!DESKTOP_DIR!\" (
    set "TENDER_FINDER_SHORTCUT_LNK=!SHORTCUT_LNK!"
    set "TENDER_FINDER_SHORTCUT_TARGET=%ROOT_LAUNCHER%"
    set "TENDER_FINDER_SHORTCUT_WORKDIR=%ROOT%"
    set "TENDER_FINDER_SHORTCUT_ICON=%VENV_PYW%"
    call :CREATE_DESKTOP_SHORTCUT
    if exist "%SHORTCUT_LNK%" (
        echo   Desktop shortcut created: "%SHORTCUT_LNK%"
        set "DESKTOP_OK=1"
    ) else (
        echo   Could not create a .lnk shortcut - trying a .bat fallback instead.
        set "SHORTCUT_BAT=!DESKTOP_DIR!\%SHORTCUT_NAME%.bat"
        > "!SHORTCUT_BAT!" echo @echo off
        >> "!SHORTCUT_BAT!" echo call "%ROOT_LAUNCHER%"
        if exist "!SHORTCUT_BAT!" (
            echo   Desktop fallback shortcut created: "!SHORTCUT_BAT!"
            set "DESKTOP_OK=1"
        ) else (
            echo   Could not write to the Desktop folder either.
        )
    )
) else (
    echo   No usable Desktop folder found for this profile - skipping the Desktop shortcut.
)
echo.

echo ============================================================
if "%DESKTOP_OK%"=="1" (
    echo Setup complete. Use the TENDER_FINDER Tender Intelligence shortcut on
    echo your Desktop to run TENDER_FINDER.
) else (
    echo Setup complete. No Desktop shortcut could be created on this
    echo computer, but you can always run TENDER_FINDER by double-clicking:
    echo   %ROOT_LAUNCHER%
)
echo ============================================================
exit /b 0

:CREATE_DESKTOP_SHORTCUT
powershell.exe -NoProfile -NonInteractive -Command "$ws=New-Object -ComObject WScript.Shell; $link=$ws.CreateShortcut($env:TENDER_FINDER_SHORTCUT_LNK); $link.TargetPath=$env:TENDER_FINDER_SHORTCUT_TARGET; $link.Arguments=''; $link.WorkingDirectory=$env:TENDER_FINDER_SHORTCUT_WORKDIR; $link.IconLocation=$env:TENDER_FINDER_SHORTCUT_ICON; $link.Description='Run the TENDER_FINDER tender/lead sweep'; $link.Save()" >nul 2>&1
exit /b 0

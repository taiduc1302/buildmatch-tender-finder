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
set "REQUIREMENTS=%ROOT%01 Code\CONNECTOR_SWEEP\requirements.txt"

echo ============================================================
echo TENDER_FINDER Tender Intelligence - Environment Setup
echo ============================================================
echo.

REM --- Step 1: find Python -----------------------------------
echo [1/5] Checking for Python...
set "PY_LAUNCHER="
where python >nul 2>&1
if %errorlevel%==0 (
    set "PY_LAUNCHER=python"
) else (
    where py >nul 2>&1
    if %errorlevel%==0 (
        set "PY_LAUNCHER=py -3"
    )
)

if "%PY_LAUNCHER%"=="" (
    echo.
    echo ERROR: Python was not found on this computer.
    echo.
    echo TENDER_FINDER needs Python 3.10 or newer. Download and install it from:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANT: on the Python installer's first screen, check the box
    echo that says "Add python.exe to PATH" before clicking Install.
    echo.
    echo After installing Python, run this setup script again.
    echo ============================================================
    pause
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
"%VENV_PY%" -m pip install --upgrade pip >nul
"%VENV_PY%" -m pip install -r "%REQUIREMENTS%"
if errorlevel 1 (
    echo.
    echo ERROR: pip install failed. See the message above for details.
    pause
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
    echo WARNING: Playwright browser install did not finish cleanly.
    echo   The BC Bid connector needs this browser; other TENDER_FINDER features
    echo   will still work. You can retry later with:
    echo   "%VENV_PY%" -m playwright install chromium
    echo.
)
echo.

REM --- Step 5: create launchers ----------------------------------
echo [5/5] Creating launchers...
set "SHORTCUT_NAME=TENDER_FINDER Tender Intelligence"

REM 5a. Always create a repo-root launcher. This does not depend on a
REM Desktop folder existing (some managed/redirected profiles don't have
REM one) so it is the one guaranteed-to-work double-click entry point.
set "ROOT_LAUNCHER=%ROOT%Launch_TENDER_FINDER_GUI.bat"
> "%ROOT_LAUNCHER%" echo @echo off
>> "%ROOT_LAUNCHER%" echo cd /d "%%~dp0"
>> "%ROOT_LAUNCHER%" echo start "" "%VENV_PYW%" "%GUI_SCRIPT%"
if exist "%ROOT_LAUNCHER%" (
    echo   Launcher created: "%ROOT_LAUNCHER%"
) else (
    echo   WARNING: could not write "%ROOT_LAUNCHER%".
)

REM 5b. Best-effort Desktop .lnk shortcut via a small VBScript helper
REM ^(cmd.exe cannot create .lnk files directly^). Not all environments
REM have a Desktop folder ^(e.g. some redirected/managed profiles^), so
REM this is allowed to fail - the repo-root launcher above always works.
set "SHORTCUT_LNK=%USERPROFILE%\Desktop\%SHORTCUT_NAME%.lnk"
set "DESKTOP_OK=0"
if exist "%USERPROFILE%\Desktop" (
    set "VBS_TEMP=%TEMP%\tenderfinder_make_shortcut_%RANDOM%.vbs"
    > "!VBS_TEMP!" echo Set oWS = WScript.CreateObject("WScript.Shell")
    >> "!VBS_TEMP!" echo sLinkFile = "%SHORTCUT_LNK%"
    >> "!VBS_TEMP!" echo Set oLink = oWS.CreateShortcut(sLinkFile)
    >> "!VBS_TEMP!" echo oLink.TargetPath = "%VENV_PYW%"
    >> "!VBS_TEMP!" echo oLink.Arguments = """%GUI_SCRIPT%"""
    >> "!VBS_TEMP!" echo oLink.WorkingDirectory = "%ROOT%"
    >> "!VBS_TEMP!" echo oLink.IconLocation = "%VENV_PYW%"
    >> "!VBS_TEMP!" echo oLink.Description = "Run the TENDER_FINDER tender/lead sweep"
    >> "!VBS_TEMP!" echo oLink.Save
    cscript //nologo "!VBS_TEMP!" >nul 2>&1
    del "!VBS_TEMP!" >nul 2>&1

    if exist "%SHORTCUT_LNK%" (
        echo   Desktop shortcut created: "%SHORTCUT_LNK%"
        set "DESKTOP_OK=1"
    ) else (
        echo   Could not create a .lnk shortcut - trying a .bat fallback instead.
        set "SHORTCUT_BAT=%USERPROFILE%\Desktop\%SHORTCUT_NAME%.bat"
        > "!SHORTCUT_BAT!" echo @echo off
        >> "!SHORTCUT_BAT!" echo cd /d "%ROOT%"
        >> "!SHORTCUT_BAT!" echo start "" "%VENV_PYW%" "%GUI_SCRIPT%"
        if exist "!SHORTCUT_BAT!" (
            echo   Desktop fallback shortcut created: "!SHORTCUT_BAT!"
            set "DESKTOP_OK=1"
        ) else (
            echo   Could not write to the Desktop folder either.
        )
    )
) else (
    echo   No Desktop folder found for this profile - skipping the Desktop shortcut.
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
pause
exit /b 0

@echo off
setlocal enabledelayedexpansion

REM ============================================================
REM TENDER_FINDER Tender Intelligence - Setup + Launch
REM
REM Creates/reuses a local Python virtual environment, installs
REM the required packages, then opens the TENDER_FINDER Tender Intelligence
REM desktop launcher (GUI). Use the GUI's "Run Full Live Sweep"
REM button for a full live run, or "Run Fast Mode" for a quick
REM no-fetch structure check - you do not need to type any commands.
REM
REM Prefer the command line instead? Run TENDER_FINDER directly with:
REM   ".venv\Scripts\python.exe" "01 Code\CONNECTOR_SWEEP\tenderfinder_demo_three_buckets.py" ^
REM     --review-xlsx "inputs\all_live_review.xlsx" --out-dir "C:\tenderfinder_out\demo_live_run" --email-intake
REM (add --no-fetch to skip live web fetching)
REM ============================================================

cd /d "%~dp0"
set "ROOT=%~dp0"
set "VENV_DIR=%ROOT%.venv"
set "GUI_SCRIPT=%ROOT%01 Code\CONNECTOR_SWEEP\tenderfinder_launcher_gui.py"
set "REQUIREMENTS=%ROOT%01 Code\CONNECTOR_SWEEP\requirements.txt"
set "REVIEW_XLSX=%ROOT%inputs\all_live_review.xlsx"

echo ============================================================
echo TENDER_FINDER Tender Intelligence - Setup + Launch
echo ============================================================
echo.
echo This will:
echo   1. Find (or help you install) a working Python
echo   2. Set up a local Python environment (first run only)
echo   3. Open the TENDER_FINDER Tender Intelligence launcher window
echo.
echo From the launcher window you can run a full live sweep or a
echo fast no-fetch test, open results, and manage Email Alert Intake
echo - no typed commands needed.
echo.

REM --- Step 1: find/bootstrap a working Python --------------------
echo [1/5] Checking for Python...
call "%ROOT%_python_bootstrap.bat"
if errorlevel 1 (
    echo.
    echo Setup stopped - no working Python is available yet. Run this
    echo file again after installing Python.
    pause
    exit /b 1
)
echo.

REM --- Step 2: create/reuse virtual environment --------------------
echo [2/5] Setting up the local virtual environment...
if exist "%VENV_DIR%\Scripts\python.exe" (
    echo   Existing environment found at "%VENV_DIR%" - reusing it.
) else (
    %PY_LAUNCHER% -m venv "%VENV_DIR%" 2>"%TEMP%\tenderfinder_venv_error.tmp"
    if errorlevel 1 (
        echo   Normal setup failed - retrying without bundled pip...
        %PY_LAUNCHER% -m venv --without-pip "%VENV_DIR%"
        if errorlevel 1 (
            echo.
            echo ERROR: Could not create a Python virtual environment on this
            echo   computer, even without bundled pip. Details below:
            echo ------------------------------------------------------------
            type "%TEMP%\tenderfinder_venv_error.tmp" 2>nul
            echo ------------------------------------------------------------
            echo.
            echo The usual fix: install Python 3.11 or newer from
            echo https://www.python.org/downloads/ using the official
            echo installer ^(check "Add python.exe to PATH"^), then rerun
            echo this file.
            del "%TEMP%\tenderfinder_venv_error.tmp" 2>nul
            pause
            exit /b 1
        )
        echo   Created "%VENV_DIR%" without bundled pip - installing pip now...
        "%VENV_DIR%\Scripts\python.exe" -m ensurepip --upgrade
        if errorlevel 1 (
            echo.
            echo ERROR: Could not install pip into the new virtual environment.
            echo The usual fix: install Python 3.11 or newer from
            echo https://www.python.org/downloads/ using the official
            echo installer ^(check "Add python.exe to PATH"^), then rerun
            echo this file.
            pause
            exit /b 1
        )
    ) else (
        echo   Created "%VENV_DIR%".
    )
    del "%TEMP%\tenderfinder_venv_error.tmp" 2>nul
)
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "VENV_PYW=%VENV_DIR%\Scripts\pythonw.exe"
if not exist "%VENV_PY%" (
    echo.
    echo ERROR: Virtual environment setup did not produce a usable Python
    echo   at "%VENV_PY%". Install Python 3.11 or newer from
    echo   https://www.python.org/downloads/ and rerun this file.
    pause
    exit /b 1
)
echo.

REM --- Step 3: install Python packages -----------------------------
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

REM --- Step 4: Playwright browser (best-effort) ---------------------
echo [4/5] Installing the Playwright Chromium browser...
echo   This is used by the BC Bid connector. It downloads roughly
echo   300MB and can take a few minutes the first time only.
"%VENV_PY%" -m playwright install chromium
if errorlevel 1 (
    echo.
    echo   WARNING: Playwright browser install did not finish cleanly.
    echo   TENDER_FINDER will still run - the BC Bid connector may just fall back
    echo   to a simpler check for this run. You can retry later with:
    echo   "%VENV_PY%" -m playwright install chromium
)
echo.

REM --- Step 5: open the TENDER_FINDER launcher window ------------------------
echo [5/5] Opening the TENDER_FINDER Tender Intelligence launcher window...
if not exist "%GUI_SCRIPT%" (
    echo.
    echo WARNING: Could not find the launcher window program at:
    echo   "%GUI_SCRIPT%"
    echo Falling back to running TENDER_FINDER directly on the command line instead.
    echo.
    if not exist "%REVIEW_XLSX%" (
        echo ERROR: Required input file not found:
        echo   "%REVIEW_XLSX%"
        pause
        exit /b 1
    )
    "%VENV_PY%" "%ROOT%01 Code\CONNECTOR_SWEEP\tenderfinder_demo_three_buckets.py" --review-xlsx "%REVIEW_XLSX%" --out-dir "C:\tenderfinder_out\demo_live_run" --email-intake
    set "RUN_RESULT=!errorlevel!"
    pause
    exit /b !RUN_RESULT!
)

if exist "%VENV_PYW%" (
    start "" "%VENV_PYW%" "%GUI_SCRIPT%"
) else (
    start "" "%VENV_PY%" "%GUI_SCRIPT%"
)
echo.
echo ============================================================
echo The TENDER_FINDER Tender Intelligence launcher window should now be
echo open (check your taskbar if you do not see it right away).
echo.
echo In that window:
echo   - Click "Run Full Live Sweep" for current live opportunities.
echo   - Click "Run Fast Mode" for a quick no-fetch structure check.
echo   - Use "Open Output Folder" / "Open Workbook" after it finishes.
echo.
echo This command window can be closed - it is not needed once the
echo launcher window is open.
echo ============================================================
exit /b 0

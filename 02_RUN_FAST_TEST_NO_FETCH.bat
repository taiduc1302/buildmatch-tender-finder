@echo off
setlocal enabledelayedexpansion

REM ============================================================
REM TENDER_FINDER Tender Intelligence - FAST TEST (no live web fetch)
REM
REM This is a standalone quick test: it sets up its own local
REM Python environment if needed (same preflight-checked bootstrap
REM as 01_SETUP_AND_RUN_LIVE.bat) but skips the Playwright browser
REM download and skips live web fetching, so it finishes much
REM faster. Use it to confirm the program runs correctly on this
REM computer before doing a full live run, or any time you just
REM want to re-check the program structure quickly.
REM
REM This runs the command line directly (no GUI window) so it can
REM double as a scriptable/CI-style smoke test. For the graphical
REM launcher, use 01_SETUP_AND_RUN_LIVE.bat instead.
REM ============================================================

cd /d "%~dp0"
set "ROOT=%~dp0"
set "VENV_DIR=%ROOT%.venv"
set "SCRIPT=%ROOT%01 Code\CONNECTOR_SWEEP\tenderfinder_demo_three_buckets.py"
set "REQUIREMENTS=%ROOT%01 Code\CONNECTOR_SWEEP\requirements.txt"
set "REVIEW_XLSX=%ROOT%inputs\all_live_review.xlsx"
set "OUT_DIR=C:\tenderfinder_out\demo_fast_test"

echo ============================================================
echo TENDER_FINDER Tender Intelligence - FAST TEST (no live web fetch)
echo ============================================================
echo.
echo IMPORTANT: This mode skips live web fetching. It only proves
echo the program runs correctly on this computer - it is NOT a
echo live current-opportunities run. Use 01_SETUP_AND_RUN_LIVE.bat
echo for real current data.
echo.

REM --- Step 1: find/bootstrap a working Python ---------------------
echo [1/5] Checking for Python...
call "%ROOT%_python_bootstrap.bat"
if errorlevel 1 (
    echo.
    echo Fast test stopped - no working Python is available yet. Run
    echo this file again after installing Python.
    pause
    exit /b 1
)
echo.

REM --- Step 2: create/reuse virtual environment ----------------
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
if not exist "%VENV_PY%" (
    echo.
    echo ERROR: Virtual environment setup did not produce a usable Python
    echo   at "%VENV_PY%". Install Python 3.11 or newer from
    echo   https://www.python.org/downloads/ and rerun this file.
    pause
    exit /b 1
)
echo.

REM --- Step 3: install Python packages -------------------------
echo [3/5] Installing required Python packages...
echo   (Playwright's browser is skipped in fast-test mode - it is
echo   only needed for live web fetching.)
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

REM --- Step 4/5: run the fast/no-fetch version ---------------------
echo [4/5] Running the fast structure test (no live fetch)...
echo.
if not exist "%REVIEW_XLSX%" (
    echo ERROR: Required input file not found:
    echo   "%REVIEW_XLSX%"
    pause
    exit /b 1
)

"%VENV_PY%" "%SCRIPT%" --review-xlsx "%REVIEW_XLSX%" --out-dir "%OUT_DIR%" --email-intake --no-fetch
set "RUN_RESULT=%errorlevel%"

echo.
echo [5/5] Done.
echo ============================================================
if "%RUN_RESULT%"=="0" (
    echo FAST TEST FINISHED
    echo.
    echo Scroll up and check the "FINAL USER MASTER CHECK" section
    echo above. Look for "Overall: PASS".
    echo.
    echo REMINDER: this was a structure test only - not live current
    echo data. For real current opportunities, run:
    echo   01_SETUP_AND_RUN_LIVE.bat
) else (
    echo FAST TEST FAILED
    echo.
    echo Scroll up for the error message. If Excel has either output file
    echo open, close it and run this again. See the README.txt
    echo Troubleshooting section for other common fixes.
)
echo ============================================================
pause
exit /b %RUN_RESULT%

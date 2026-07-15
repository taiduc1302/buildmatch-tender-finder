@echo off
REM ============================================================
REM TENDER_FINDER Tender Intelligence - shared Python bootstrap helper
REM
REM Called with `call "%%~dp0_python_bootstrap.bat"` from both
REM 01_SETUP_AND_RUN_LIVE.bat and 02_RUN_FAST_TEST_NO_FETCH.bat.
REM Deliberately has NO setlocal of its own, so PY_LAUNCHER (and
REM any PATH change made here) is still visible to the caller
REM after `call` returns - only `if errorlevel N (...)` (the
REM runtime-evaluated form) is used for control flow here, never
REM `%%errorlevel%%` inside a nested parenthesized block, which
REM cmd.exe expands at parse time and would silently read a stale
REM value (this exact bug was found and fixed elsewhere in this
REM package - see the Python-detection blocks in the two callers).
REM
REM On success: sets PY_LAUNCHER to a working Python command and
REM returns errorlevel 0. The caller should use %%PY_LAUNCHER%%
REM (it may contain a space, e.g. "py -3", so always call it
REM unquoted: %%PY_LAUNCHER%% -m venv ...).
REM
REM On failure (user chooses Exit, or all install attempts are
REM exhausted): returns errorlevel 1. The caller must check
REM `if errorlevel 1 exit /b 1` immediately after the call.
REM
REM No admin rights are required anywhere in this flow: the
REM bundled-python check, the winget --scope user install, and the
REM official python.org installer (when the user selects "Install
REM Now" / "Just for me") are all per-user operations.
REM ============================================================

set "PY_LAUNCHER="
set "TENDER_FINDER_BOOTSTRAP_ROOT=%~dp0"

:DETECT
REM Never prepend every discovered Python directory to PATH here. A stale
REM Python 3.10 install can otherwise hide a supported Python 3.11+ that the
REM user deliberately placed first on PATH. Check explicit/current commands
REM first, then probe common install locations one executable at a time.

REM --- Step 1: bundled/local Python, if a maintainer drops a
REM portable Python under tools\python\ next to this file ---------
if exist "%TENDER_FINDER_BOOTSTRAP_ROOT%tools\python\python.exe" (
    "%TENDER_FINDER_BOOTSTRAP_ROOT%tools\python\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info.major == 3 and sys.version_info.minor not in range(0,11) else 1)" >nul 2>&1
    if not errorlevel 1 set "PY_LAUNCHER=%TENDER_FINDER_BOOTSTRAP_ROOT%tools\python\python.exe"
)

REM --- Step 2: the "py" launcher (py -3) --------------------------
if "%PY_LAUNCHER%"=="" (
    where py >nul 2>&1
    if not errorlevel 1 (
        py -3 -c "import sys; raise SystemExit(0 if sys.version_info.major == 3 and sys.version_info.minor not in range(0,11) else 1)" >nul 2>&1
        if not errorlevel 1 set "PY_LAUNCHER=py -3"
    )
)

REM --- Step 3: plain "python" on PATH ------------------------------
if "%PY_LAUNCHER%"=="" (
    where python >nul 2>&1
    if not errorlevel 1 (
        python -c "import sys; raise SystemExit(0 if sys.version_info.major == 3 and sys.version_info.minor not in range(0,11) else 1)" >nul 2>&1
        if not errorlevel 1 set "PY_LAUNCHER=python"
    )
)

REM --- Step 3b: plain "python3" on PATH -----------------------------
if "%PY_LAUNCHER%"=="" (
    where python3 >nul 2>&1
    if not errorlevel 1 (
        python3 -c "import sys; raise SystemExit(0 if sys.version_info.major == 3 and sys.version_info.minor not in range(0,11) else 1)" >nul 2>&1
        if not errorlevel 1 set "PY_LAUNCHER=python3"
    )
)

REM --- Step 3c: common install folders, without changing PATH ------
if "%PY_LAUNCHER%"=="" (
    for /d %%V in ("%LocalAppData%\Programs\Python\Python3*") do call :TRY_CANDIDATE "%%~fV\python.exe"
    for /d %%V in ("%ProgramFiles%\Python3*") do call :TRY_CANDIDATE "%%~fV\python.exe"
    for /d %%V in ("%ProgramFiles(x86)%\Python3*") do call :TRY_CANDIDATE "%%~fV\python.exe"
)

if not "%PY_LAUNCHER%"=="" goto :FOUND

REM --- Step 4: Python missing - offer a per-user auto-install ------
if defined TENDER_FINDER_BOOTSTRAP_INSTALL_ATTEMPTED goto :GUIDE
set "TENDER_FINDER_BOOTSTRAP_INSTALL_ATTEMPTED=1"

where winget >nul 2>&1
if errorlevel 1 goto :GUIDE

echo.
echo No working Python installation was found on this computer.
echo TENDER_FINDER can try to install Python for your user account only
echo (no admin rights, no changes for other users) using winget,
echo the package installer built into Windows 10/11.
echo.
choice /C YN /N /M "Try an automatic per-user Python install now? [Y/N] "
if errorlevel 2 goto :GUIDE

echo.
echo Installing Python 3.12 for your user account only via winget...
echo (This does not require admin rights and does not affect other
echo user accounts on this computer.)
winget install --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements
echo.
echo Install step finished - re-checking for Python...
goto :DETECT

:GUIDE
echo.
echo ============================================================
echo TENDER_FINDER needs Python 3.11 or newer and could not find or install
echo it automatically on this computer.
echo.
echo Please install it yourself - this takes about a minute and
echo does NOT require admin rights:
echo   1. TENDER_FINDER is opening the official download page for you now:
echo        https://www.python.org/downloads/
echo   2. Click "Download Python" and run the installer.
echo   3. On the installer's FIRST screen:
echo        - Choose "Install Now" / "Just for me"
echo        - Check the box "Add python.exe to PATH"
echo   4. When the install finishes, come back to this window and
echo      choose Retry below.
echo.
echo (If Retry still does not find Python right after installing,
echo close this window and double-click this file again - that
echo always picks up a fresh install.)
echo ============================================================
if not defined TENDER_FINDER_BOOTSTRAP_BROWSER_OPENED (
    set "TENDER_FINDER_BOOTSTRAP_BROWSER_OPENED=1"
    start "" "https://www.python.org/downloads/"
)
echo.
choice /C RE /N /M "Press R to Retry the Python check, or E to Exit. [R/E] "
if errorlevel 2 (
    echo.
    echo Exiting. Run this file again after installing Python.
    exit /b 1
)
goto :DETECT

:FOUND
echo   Found Python: %PY_LAUNCHER%
%PY_LAUNCHER% --version
exit /b 0

:TRY_CANDIDATE
if not "%PY_LAUNCHER%"=="" exit /b 0
if not exist "%~1" exit /b 0
"%~1" -c "import sys; raise SystemExit(0 if sys.version_info.major == 3 and sys.version_info.minor not in range(0,11) else 1)" >nul 2>&1
if not errorlevel 1 set "PY_LAUNCHER=%~1"
exit /b 0

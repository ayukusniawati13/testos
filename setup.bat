@echo off
REM ======================================================================
REM Spectrum Lyric Video Maker - Windows setup script
REM
REM Creates a local virtual environment in .venv, upgrades pip, and
REM installs every dependency from requirements.txt. Run this once after
REM cloning the repository, then use run.bat to launch the app.
REM ======================================================================

setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo.
echo === Spectrum Lyric Video Maker - setup ===
echo.

REM ---- 1. Locate Python ------------------------------------------------
set "PYTHON_EXE="
where py >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_EXE=py -3"
) else (
    where python >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_EXE=python"
    )
)

if "%PYTHON_EXE%"=="" (
    echo [ERROR] Python 3.11+ was not found on PATH.
    echo         Install it from https://www.python.org/downloads/ and re-run setup.bat.
    pause
    exit /b 1
)

echo Using Python launcher: %PYTHON_EXE%
%PYTHON_EXE% --version

REM ---- 2. Create venv --------------------------------------------------
if not exist ".venv\Scripts\python.exe" (
    echo.
    echo Creating virtual environment in .venv ...
    %PYTHON_EXE% -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create the virtual environment.
        pause
        exit /b 1
    )
) else (
    echo Re-using existing virtual environment in .venv
)

REM ---- 3. Upgrade pip + install requirements ---------------------------
echo.
echo Upgrading pip ...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERROR] pip upgrade failed.
    pause
    exit /b 1
)

echo.
echo Installing requirements (this may take several minutes the first time) ...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] requirements install failed.
    pause
    exit /b 1
)

REM ---- 4. FFmpeg check (informational only) ----------------------------
echo.
where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo [WARN] FFmpeg was not found on PATH.
    echo        The app can auto-download a static build the first time you
    echo        open the FFmpeg dialog, but you can also install it manually
    echo        from https://www.gyan.dev/ffmpeg/builds/ and add it to PATH.
) else (
    echo FFmpeg is on PATH:
    ffmpeg -version 2>nul | findstr /C:"ffmpeg version"
)

echo.
echo === Setup complete ===
echo Run the app with: run.bat
echo.
pause
endlocal

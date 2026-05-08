@echo off
REM ======================================================================
REM Spectrum Lyric Video Maker - Windows launcher
REM
REM Activates the local .venv (created by setup.bat) and runs run.py.
REM If .venv does not exist yet, point the user at setup.bat first.
REM ======================================================================

setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] No virtual environment found at .venv
    echo         Please run setup.bat first.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" run.py %*
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo Application exited with code %EXIT_CODE%.
    pause
)

endlocal & exit /b %EXIT_CODE%

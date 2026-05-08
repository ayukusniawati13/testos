@echo off
title Music Spectrum Lyrics Studio
echo ========================================
echo  Music Spectrum Lyrics Studio
echo ========================================
echo.

REM Check venv
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run setup.bat first.
    echo.
    pause
    exit /b 1
)

REM Activate venv
call venv\Scripts\activate.bat

REM Run application
echo Starting Music Spectrum Lyrics Studio...
echo.
python main.py

echo.
if errorlevel 1 (
    echo [ERROR] Application exited with an error.
    echo Check the logs folder for details.
) else (
    echo Application closed.
)
echo.
echo Check logs\app.log and logs\crash.log for details if something went wrong.
echo.
pause

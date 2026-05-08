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

if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with an error.
    echo Check the logs folder for details.
    echo.
    pause
)

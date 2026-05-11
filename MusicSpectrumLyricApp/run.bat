@echo off
title Music Spectrum Lyric Video Maker

:: Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found.
    echo Please run setup.bat first to install dependencies.
    echo.
    pause
    exit /b 1
)

:: Check if dependencies are installed
call venv\Scripts\activate.bat
python -c "import PySide6" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Dependencies not installed.
    echo Please run setup.bat first to install dependencies.
    echo.
    pause
    exit /b 1
)

:: Run the application
echo Starting Music Spectrum Lyric Video Maker...
python app\main.py
if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with an error.
    pause
)

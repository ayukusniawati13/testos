@echo off
title Music Spectrum Lyrics Studio - Setup
echo ========================================
echo  Music Spectrum Lyrics Studio - Setup
echo ========================================
echo.

REM Check Python
echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)
python --version
echo [OK] Python found.
echo.

REM Create virtual environment
echo [2/6] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo [OK] Virtual environment created.
) else (
    echo [OK] Virtual environment already exists.
)
echo.

REM Activate venv
echo [3/6] Activating virtual environment...
call venv\Scripts\activate.bat
echo [OK] Virtual environment activated.
echo.

REM Upgrade pip
echo [4/6] Upgrading pip...
python -m pip install --upgrade pip
echo [OK] pip upgraded.
echo.

REM Install requirements
echo [5/6] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [WARNING] Some dependencies may have failed to install.
    echo The application may still work with limited features.
)
echo [OK] Dependencies installed.
echo.

REM Check FFmpeg
echo [6/6] Checking FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] FFmpeg not found!
    echo.
    echo FFmpeg is required for video rendering.
    echo.
    echo Attempting to install via winget...
    winget install --id Gyan.FFmpeg -e --accept-package-agreements --accept-source-agreements >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Automatic install failed.
        echo.
        echo Please install FFmpeg manually:
        echo   1. Download from https://ffmpeg.org/download.html
        echo   2. Extract to a folder (e.g., C:\ffmpeg)
        echo   3. Add the bin folder to your PATH environment variable
        echo.
    ) else (
        echo [OK] FFmpeg installed via winget.
    )
) else (
    echo [OK] FFmpeg found.
)

echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo To run the application:
echo   run.bat
echo.
echo Or manually:
echo   venv\Scripts\activate
echo   python main.py
echo.
pause

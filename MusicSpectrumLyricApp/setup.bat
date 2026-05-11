@echo off
title Music Spectrum Lyric Video Maker - Setup
echo ========================================
echo  Music Spectrum Lyric Video Maker
echo  Setup Script
echo ========================================
echo.

:: Check Python
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)
python --version
echo Python found!
echo.

:: Create virtual environment
echo [2/4] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)
echo.

:: Install dependencies
echo [3/4] Installing dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo Dependencies installed successfully!
echo.

:: Check FFmpeg
echo [4/4] Checking FFmpeg...
where ffmpeg >nul 2>&1
if errorlevel 1 (
    if exist "tools\ffmpeg" (
        echo FFmpeg found in local tools folder.
    ) else (
        echo [WARNING] FFmpeg not found.
        echo.
        echo You can install FFmpeg in two ways:
        echo   1. Use the "Install FFmpeg Online" button in the app
        echo   2. Download manually from https://ffmpeg.org/download.html
        echo      and extract to the tools\ffmpeg\ folder
        echo.
        set /p INSTALL_FFMPEG="Would you like to download FFmpeg now? (y/n): "
        if /i "%INSTALL_FFMPEG%"=="y" (
            echo.
            echo FFmpeg will be downloaded when you launch the application.
            echo Use the "Install FFmpeg Online" button in the app.
        )
    )
) else (
    echo FFmpeg found in system PATH.
    ffmpeg -version 2>&1 | findstr /i "version"
)
echo.

echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo To run the application:
echo   1. Double-click run.bat
echo   2. Or run: venv\Scripts\activate.bat ^&^& python app\main.py
echo.
pause

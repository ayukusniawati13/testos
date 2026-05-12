@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

if not exist .venv\Scripts\activate.bat (
    echo Virtual environment belum dibuat. Jalankan setup.bat terlebih dahulu.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
python -m app.main

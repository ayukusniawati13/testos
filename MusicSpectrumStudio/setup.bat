@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo === Music Spectrum Studio - Setup ===
echo.

REM --- Cek Python ---
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python belum terdeteksi di PATH.
    echo Silakan install Python 3.10+ dari https://www.python.org/downloads/
    echo dan centang opsi "Add Python to PATH" saat instalasi.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo Python terdeteksi: %PYVER%

REM --- Virtualenv ---
if not exist .venv (
    echo [1/4] Membuat virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Gagal membuat virtualenv.
        pause
        exit /b 1
    )
) else (
    echo [1/4] Virtualenv .venv sudah ada.
)

call .venv\Scripts\activate.bat

echo [2/4] Update pip...
python -m pip install --upgrade pip wheel setuptools

echo [3/4] Install dependency dari requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Gagal install dependency.
    pause
    exit /b 1
)

echo [4/4] Mengecek FFmpeg...
python -c "from app.core.ffmpeg_check import check_ffmpeg; s=check_ffmpeg(); print('OK' if s.available else 'BELUM'); print(s.path or '')"
if errorlevel 1 (
    echo (info) Periksa langsung di aplikasi - tombol Install FFmpeg tersedia di UI.
)

echo.
echo === Setup selesai. Jalankan run.bat untuk membuka aplikasi. ===
pause

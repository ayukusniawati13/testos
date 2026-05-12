@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================
echo   Music Spectrum Studio - Setup
echo ============================================
echo.

set "PY_CMD="

REM --- 1. Cari Python di PATH ---
where python >nul 2>nul
if not errorlevel 1 (
    for /f "tokens=*" %%v in ('python --version 2^>^&1') do set "PYVER=%%v"
    echo [INFO] Python ditemukan via 'python': !PYVER!
    set "PY_CMD=python"
    goto :have_python
)

REM --- 2. Coba Python launcher 'py' (Windows Python launcher) ---
where py >nul 2>nul
if not errorlevel 1 (
    for /f "tokens=*" %%v in ('py -3 --version 2^>^&1') do set "PYVER=%%v"
    echo [INFO] Python ditemukan via 'py -3': !PYVER!
    set "PY_CMD=py -3"
    goto :have_python
)

echo [ERROR] Python 3.10+ tidak ditemukan di PATH.
echo.
echo Silakan install Python dari https://www.python.org/downloads/windows/
echo PASTIKAN centang opsi "Add Python to PATH" saat instalasi.
echo Setelah instalasi, tutup dan buka ulang setup.bat ini.
echo.
goto :end_error

:have_python
echo.

REM --- 3. Buat virtualenv ---
if not exist ".venv" (
    echo [1/4] Membuat virtual environment .venv ...
    %PY_CMD% -m venv .venv
    if errorlevel 1 (
        echo.
        echo [ERROR] Gagal membuat virtualenv.
        echo Coba install ulang Python atau jalankan: %PY_CMD% -m pip install --upgrade pip
        goto :end_error
    )
) else (
    echo [1/4] Virtual environment .venv sudah ada.
)

REM --- 4. Aktifkan venv ---
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] File .venv\Scripts\activate.bat tidak ditemukan.
    echo Hapus folder .venv lalu jalankan setup.bat lagi.
    goto :end_error
)
call ".venv\Scripts\activate.bat"

REM --- 5. Upgrade pip ---
echo.
echo [2/4] Upgrade pip, wheel, setuptools ...
python -m pip install --upgrade pip wheel setuptools
if errorlevel 1 (
    echo.
    echo [ERROR] Gagal upgrade pip.
    goto :end_error
)

REM --- 6. Install dependency ---
echo.
echo [3/4] Install dependency dari requirements.txt ...
echo (Ini bisa memakan waktu beberapa menit, terutama untuk PySide6 dan librosa)
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Gagal install dependency.
    echo Periksa koneksi internet, atau coba jalankan ulang setup.bat.
    goto :end_error
)

REM --- 7. Cek FFmpeg ---
echo.
echo [4/4] Mengecek FFmpeg ...
python -c "from app.core.ffmpeg_check import check_ffmpeg; s = check_ffmpeg(); print('FFmpeg:', 'TERINSTAL' if s.available else 'BELUM TERINSTAL'); print('Path  :', s.path or '(akan diunduh otomatis dari aplikasi)')"
if errorlevel 1 (
    echo (info) Status FFmpeg bisa juga dicek dari dalam aplikasi.
)

echo.
echo ============================================
echo   Setup SELESAI. Jalankan run.bat untuk membuka aplikasi.
echo ============================================
echo.
goto :end_ok

:end_error
echo.
echo ============================================
echo   Setup GAGAL. Lihat pesan error di atas.
echo ============================================
echo.

:end_ok
echo Tekan tombol apa saja untuk menutup jendela ini...
pause >nul
endlocal

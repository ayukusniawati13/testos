@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo ============================================
    echo   Virtual environment belum dibuat.
    echo   Jalankan setup.bat terlebih dahulu.
    echo ============================================
    echo.
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"
python -m app.main %*

if errorlevel 1 (
    echo.
    echo Aplikasi keluar dengan error. Lihat pesan di atas.
    pause
)

endlocal

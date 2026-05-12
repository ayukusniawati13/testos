#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=== Music Spectrum Studio - Setup ==="

if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] python3 tidak tersedia di PATH." >&2
    exit 1
fi

python3 --version

if [ ! -d ".venv" ]; then
    echo "[1/4] Membuat virtualenv..."
    python3 -m venv .venv
else
    echo "[1/4] Virtualenv sudah ada."
fi

# shellcheck source=/dev/null
source .venv/bin/activate

echo "[2/4] Upgrade pip..."
python -m pip install --upgrade pip wheel setuptools

echo "[3/4] Install dependency..."
pip install -r requirements.txt

echo "[4/4] Cek FFmpeg..."
python - <<'PY'
from app.core.ffmpeg_check import check_ffmpeg
s = check_ffmpeg()
print("FFmpeg:", "OK" if s.available else "BELUM")
print("Path :", s.path or "(tidak ada)")
PY

echo "=== Setup selesai. Jalankan ./run.sh untuk membuka aplikasi. ==="

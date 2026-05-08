#!/usr/bin/env bash
# ======================================================================
# Spectrum Lyric Video Maker - Linux/macOS setup script
#
# Creates a local virtual environment in .venv, upgrades pip, and
# installs every dependency from requirements.txt. Run this once after
# cloning the repository, then use ./run.sh to launch the app.
# ======================================================================
set -euo pipefail

cd "$(dirname "$0")"

echo
echo "=== Spectrum Lyric Video Maker - setup ==="
echo

# ---- 1. Locate Python -------------------------------------------------
PYTHON_BIN=""
for candidate in python3.12 python3.11 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        PYTHON_BIN="$candidate"
        break
    fi
done

if [[ -z "$PYTHON_BIN" ]]; then
    echo "[ERROR] Python 3.11+ was not found on PATH." >&2
    echo "        Install it (e.g. 'sudo apt install python3.11 python3.11-venv') and re-run." >&2
    exit 1
fi

echo "Using Python: $PYTHON_BIN ($($PYTHON_BIN --version 2>&1))"

# ---- 2. Create venv ---------------------------------------------------
if [[ ! -x ".venv/bin/python" ]]; then
    echo
    echo "Creating virtual environment in .venv ..."
    "$PYTHON_BIN" -m venv .venv
else
    echo "Re-using existing virtual environment in .venv"
fi

# ---- 3. Upgrade pip + install requirements ---------------------------
echo
echo "Upgrading pip ..."
.venv/bin/python -m pip install --upgrade pip

echo
echo "Installing requirements (this may take several minutes the first time) ..."
.venv/bin/python -m pip install -r requirements.txt

# ---- 4. FFmpeg check (informational only) ----------------------------
echo
if command -v ffmpeg >/dev/null 2>&1; then
    echo "FFmpeg is on PATH:"
    ffmpeg -version | head -n 1
else
    echo "[WARN] FFmpeg was not found on PATH."
    echo "       The app can auto-download a static build the first time you"
    echo "       open the FFmpeg dialog, or install it via your package manager"
    echo "       (e.g. 'sudo apt install ffmpeg' / 'brew install ffmpeg')."
fi

echo
echo "=== Setup complete ==="
echo "Run the app with: ./run.sh"
echo

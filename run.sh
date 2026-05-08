#!/usr/bin/env bash
# ======================================================================
# Spectrum Lyric Video Maker - Linux/macOS launcher
#
# Activates the local .venv (created by setup.sh) and runs run.py.
# ======================================================================
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -x ".venv/bin/python" ]]; then
    echo "[ERROR] No virtual environment found at .venv" >&2
    echo "        Please run ./setup.sh first." >&2
    exit 1
fi

exec .venv/bin/python run.py "$@"

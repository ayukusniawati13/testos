#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "Virtualenv belum dibuat. Jalankan ./setup.sh dulu." >&2
    exit 1
fi

# shellcheck source=/dev/null
source .venv/bin/activate
python -m app.main "$@"

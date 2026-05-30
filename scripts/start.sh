#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$ROOT/ams_dashboard.log"
PID_FILE="$ROOT/.ams_dashboard.pid"

echo "[AMS Intelligence] Starting dashboard..."

# Kill any existing instance
if [[ -f "$PID_FILE" ]]; then
    OLD_PID=$(cat "$PID_FILE")
    kill "$OLD_PID" 2>/dev/null && echo "Stopped previous instance (PID $OLD_PID)" || true
    rm -f "$PID_FILE"
fi

# Activate venv if present
if [[ -f "$ROOT/.venv/bin/activate" ]]; then
    source "$ROOT/.venv/bin/activate"
fi

# Launch
PYTHONPATH="$ROOT/src" streamlit run "$ROOT/src/dashboard/app.py" \
    --server.port 8502 \
    --server.headless true \
    >> "$LOG" 2>&1 &

DASHBOARD_PID=$!
echo "$DASHBOARD_PID" > "$PID_FILE"
echo "[AMS Intelligence] Dashboard PID $DASHBOARD_PID — http://localhost:8502"
echo "[AMS Intelligence] Log: $LOG"

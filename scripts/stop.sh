#!/usr/bin/env bash
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="$ROOT/.ams_dashboard.pid"

if [[ -f "$PID_FILE" ]]; then
    PID=$(cat "$PID_FILE")
    kill "$PID" 2>/dev/null && echo "[AMS Intelligence] Stopped PID $PID" || echo "Already stopped."
    rm -f "$PID_FILE"
else
    pkill -f "streamlit run.*ams" 2>/dev/null && echo "Stopped." || echo "Not running."
fi

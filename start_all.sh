#!/usr/bin/env bash
# One-button launcher for WebSocketSDK (Linux/macOS)
cd "$(dirname "$0")"

# Use venv python if available
if [ -f "venv/bin/python" ]; then
    PYTHON="venv/bin/python"
else
    PYTHON="python3"
fi

exec "$PYTHON" start_all.py "$@"

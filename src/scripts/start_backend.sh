#!/usr/bin/env bash
# Start GridMind backend (idempotent, nohup-detached)
set -e
pkill -f "uvicorn backend.main" 2>/dev/null || true
sleep 1
nohup python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 \
  > /tmp/gridmind-uvicorn.log 2>&1 < /dev/null &
disown || true
echo "started pid $!"
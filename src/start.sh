#!/bin/bash
# Bottleneck AI - Start Script
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "⚡ Bottleneck AI v2.0 - Starting..."
echo ""

kill $(lsof -t -i:8000 2>/dev/null) 2>/dev/null || true
kill $(lsof -t -i:5173 2>/dev/null) 2>/dev/null || true
sleep 1

# Start backend
echo "  → Backend: http://localhost:8000"
setsid python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 < /dev/null > /tmp/gm_backend.log 2>&1 &
sleep 3

if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
  echo "    ✅ Backend running"
else
  echo "    ❌ Backend failed"
  cat /tmp/gm_backend.log | tail -5
  exit 1
fi

# Start frontend
echo "  → Frontend: http://localhost:5173"
cd frontend
setsid npx vite --host 0.0.0.0 --port 5173 < /dev/null > /tmp/gm_frontend.log 2>&1 &
cd ..
sleep 3

echo "    ✅ Frontend running"
echo ""
echo "════════════════════════════════════════════════"
echo "  Bottleneck AI is ready!"
echo ""
echo "  Frontend:   http://localhost:5173"
echo "  Backend:    http://localhost:8000"
echo "  API Docs:   http://localhost:8000/docs"
echo ""
echo "  Demo login: demo@bottleneck.com / demo123"
echo "  (or create a new account on the login page)"
echo ""
echo "  Stop: kill \$(lsof -t -i:8000) \$(lsof -t -i:5173)"
echo "════════════════════════════════════════════════"

#!/usr/bin/env bash

# ======================================================================
#       PulseGuardian AI - Universal Launcher (Linux / macOS)
# ======================================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "======================================================================"
echo "             PulseGuardian AI - Smart Health System"
echo "               Universal Launcher (Linux / macOS)"
echo "======================================================================"
echo ""

# Check prerequisites and trigger setup if needed
if [ ! -d "$ROOT_DIR/backend/.venv" ] || [ ! -d "$ROOT_DIR/frontend/node_modules" ]; then
    echo "[*] First-time setup detected. Running setup.sh..."
    bash "$ROOT_DIR/setup.sh"
fi

# Cleanup background processes on exit (Ctrl+C)
cleanup() {
    echo ""
    echo "[*] Gracefully stopping PulseGuardian services..."
    if [ -n "$BACKEND_PID" ]; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    echo "[OK] All services stopped."
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# 1. Start Backend API
echo "[*] Starting FastAPI Backend on http://localhost:8000 ..."
cd "$ROOT_DIR/backend"
source .venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# 2. Start Frontend Dev Server
echo "[*] Starting React Frontend on http://localhost:5173 ..."
cd "$ROOT_DIR/frontend"
npm run dev -- --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!

echo ""
echo "======================================================================"
echo "              PulseGuardian AI is running!"
echo "======================================================================"
echo "  Web Application:   http://localhost:5173"
echo "  API Documentation: http://localhost:8000/docs"
echo ""
echo "  DEMO LOGIN CREDENTIALS:"
echo "  ------------------------------------------------------------------"
echo "  Role                 Email                            Password"
echo "  ------------------------------------------------------------------"
echo "  1. Patient           monisha@pulseguardian.ai         Password@123"
echo "  2. Family Caregiver  caregiver@pulseguardian.ai       Password@123"
echo "  3. Attending Doctor  dr.sunita@pulseguardian.ai       Password@123"
echo "  4. Emergency EMS     ems.rajesh@pulseguardian.ai      Password@123"
echo ""
echo "  Default Patient ID:  PT-2026-000001"
echo "======================================================================"
echo "Press Ctrl+C to stop all services."
echo ""

# Attempt to open browser on macOS (open) or Linux (xdg-open)
if command -v xdg-open >/dev/null 2>&1; then
    (sleep 3 && xdg-open "http://localhost:5173") &
elif command -v open >/dev/null 2>&1; then
    (sleep 3 && open "http://localhost:5173") &
fi

wait

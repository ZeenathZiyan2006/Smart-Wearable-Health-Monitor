#!/usr/bin/env bash
set -e

# ======================================================================
#       PulseGuardian AI - Cross-Platform Automated Setup (Linux / macOS)
# ======================================================================

echo "======================================================================"
echo "      PulseGuardian AI - Automated Setup (Linux / macOS)"
echo "======================================================================"
echo ""

# Get script root directory
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. Check Python installation
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "[ERROR] Python 3 is not installed or not in your PATH."
    echo "Please install Python 3.10+ from https://www.python.org/downloads/ or your package manager."
    exit 1
fi
echo "[OK] Found $($PYTHON_CMD --version)"

# 2. Check Node.js and npm
if ! command -v node >/dev/null 2>&1; then
    echo "[ERROR] Node.js is not installed or not in your PATH."
    echo "Please install Node.js 18+ from https://nodejs.org/ or your package manager (nvm, brew, apt)."
    exit 1
fi
echo "[OK] Found Node.js $(node --version)"

if ! command -v npm >/dev/null 2>&1; then
    echo "[ERROR] npm is not installed."
    exit 1
fi

echo ""
echo "----------------------------------------------------------------------"
echo "[1/4] Setting up Backend Virtual Environment & Dependencies..."
echo "----------------------------------------------------------------------"
cd "$ROOT_DIR/backend"

if [ ! -d ".venv" ]; then
    echo "[*] Creating Python virtual environment in backend/.venv..."
    $PYTHON_CMD -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip --quiet
echo "[*] Installing backend dependencies from requirements.txt..."
pip install -r requirements.txt --quiet

# Prepare backend .env if missing
if [ ! -f ".env" ]; then
    echo "[*] Creating backend/.env from template..."
    cp .env.example .env
fi

# Seed database
echo "[*] Initializing SQLite database and creating baseline demo accounts..."
python -c "from app.core.database import engine, Base; from app.scripts.seed_demo_data import seed_database; Base.metadata.create_all(bind=engine); seed_database(clean=False); print('[OK] Database and baseline accounts seeded successfully.')"

echo ""
echo "----------------------------------------------------------------------"
echo "[2/4] Setting up Frontend Node Packages..."
echo "----------------------------------------------------------------------"
cd "$ROOT_DIR/frontend"

if [ ! -f ".env" ]; then
    echo "[*] Creating frontend/.env from template..."
    cp .env.example .env
fi

echo "[*] Installing frontend npm packages..."
npm install --silent

cd "$ROOT_DIR"
echo ""
echo "======================================================================"
echo "[SUCCESS] Setup completed successfully!"
echo ""
echo "Ready to launch! Run:"
echo "  ./run.sh"
echo "======================================================================"

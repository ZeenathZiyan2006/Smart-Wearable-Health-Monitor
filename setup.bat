@echo off
setlocal enabledelayedexpansion

echo ======================================================================
echo       PulseGuardian AI - Cross-Platform Automated Setup (Windows)
echo ======================================================================
echo.

:: 1. Check Python installation
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in your system PATH.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo [OK] Found %%i

:: 2. Check Node.js installation
node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js is not installed or not in your system PATH.
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version') do echo [OK] Found Node.js %%i

echo.
echo ----------------------------------------------------------------------
echo [1/4] Setting up Backend Virtual Environment & Dependencies...
echo ----------------------------------------------------------------------
cd /d "%~dp0backend"

if not exist ".venv" (
    echo [*] Creating Python virtual environment in backend\.venv...
    python -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
echo [*] Installing backend dependencies from requirements.txt...
pip install -r requirements.txt --quiet

:: 3. Prepare backend .env
if not exist ".env" (
    echo [*] Creating backend\.env from template...
    copy .env.example .env >nul
)

:: 4. Seed database
echo [*] Initializing SQLite database and creating baseline demo accounts...
python -c "import sys; from app.core.database import engine, Base; from app.scripts.seed_demo_data import seed_database; Base.metadata.create_all(bind=engine); seed_database(clean=False); print('[OK] Database and baseline accounts seeded successfully.')"

cd /d "%~dp0frontend"
echo.
echo ----------------------------------------------------------------------
echo [2/4] Setting up Frontend Node Packages...
echo ----------------------------------------------------------------------

if not exist ".env" (
    echo [*] Creating frontend\.env from template...
    copy .env.example .env >nul
)

echo [*] Installing frontend npm packages (this may take a moment)...
call npm install --silent

cd /d "%~dp0"
echo.
echo ======================================================================
echo [SUCCESS] Setup completed successfully!
echo.
echo Ready to launch! Double-click 'run.bat' or run:
echo   .\run.bat
echo ======================================================================
echo.
pause

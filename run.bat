@echo off
setlocal enabledelayedexpansion

echo ======================================================================
echo                PulseGuardian AI - Smart Health System
echo                  Universal Launcher (Windows)
echo ======================================================================
echo.

set ROOT_DIR=%~dp0

:: Check if setup has been performed
if not exist "%ROOT_DIR%backend\.venv" (
    echo [*] First-time setup detected. Running setup.bat...
    call "%ROOT_DIR%setup.bat"
)

if not exist "%ROOT_DIR%frontend\node_modules" (
    echo [*] Frontend dependencies not found. Running setup.bat...
    call "%ROOT_DIR%setup.bat"
)

echo [*] Starting FastAPI Backend on http://localhost:8000 ...
start "PulseGuardian Backend API" cmd /k "cd /d ""%ROOT_DIR%backend"" && call .venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [*] Starting React Frontend on http://localhost:5173 ...
start "PulseGuardian Frontend UI" cmd /k "cd /d ""%ROOT_DIR%frontend"" && npm run dev -- --host 0.0.0.0 --port 5173"

echo.
echo ======================================================================
echo              PulseGuardian AI is running!
echo ======================================================================
echo  Web Application:   http://localhost:5173
echo  API Documentation: http://localhost:8000/docs
echo.
echo  DEMO LOGIN CREDENTIALS:
echo  ------------------------------------------------------------------
echo  Role                 Email                            Password
echo  ------------------------------------------------------------------
echo  1. Patient           monisha@pulseguardian.ai         Password@123
echo  2. Family Caregiver  caregiver@pulseguardian.ai       Password@123
echo  3. Attending Doctor  dr.sunita@pulseguardian.ai       Password@123
echo  4. Emergency EMS     ems.rajesh@pulseguardian.ai      Password@123
echo.
echo  Default Patient ID:  PT-2026-000001
echo ======================================================================
echo.
echo [*] Opening application in your default browser in 4 seconds...
timeout /t 4 /nobreak >nul
start http://localhost:5173

echo Press any key to stop this launcher window (backend and frontend windows will remain open).
pause >nul

@echo off
title HFR MOCT - Local Launcher
echo.
echo ==========================================
echo       MOCT Cyrillic Font Matcher
echo        Local Version Launcher
echo ==========================================
echo.

cd /d "%~dp0"

set PY_CMD=py -3
where py >nul 2>nul
if %errorlevel% neq 0 (
    set PY_CMD=python
)

REM 1. Stop old backend instances and start FastAPI Backend
echo [1/2] Checking and restarting Backend on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo Stopping old backend process, PID %%a...
    taskkill /f /pid %%a >nul 2>nul
)
start "MOCT-Backend" cmd /k "cd /d %~dp0 && %PY_CMD% -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"
echo Waiting for backend to initialize 5s...
ping 127.0.0.1 -n 6 >nul

REM 2. Check and start Vite Frontend
netstat -ano | findstr :5188 >nul
if %errorlevel% equ 0 (
    echo [OK] Frontend is already running on port 5188.
) else (
    echo [2/2] Starting Frontend on port 5188...
    start "MOCT-Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
    echo Waiting for frontend to initialize 3s...
    ping 127.0.0.1 -n 4 >nul
)

REM 3. Open in browser
echo.
echo [OK] Opening local site in browser...
start http://127.0.0.1:5188/

echo.
echo Launcher finished successfully!
echo You can close this window now.
echo.

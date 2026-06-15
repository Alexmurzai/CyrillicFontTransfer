@echo off
setlocal enabledelayedexpansion
title HFR MOCT - Local Mobile Launcher
echo.
echo ==========================================================
echo       MOCT Cyrillic Font Matcher
echo       Local Mobile (Wi-Fi) Version Launcher
echo ==========================================================
echo.

cd /d "%~dp0"

set PY_CMD=py -3
where py >nul 2>nul
if %errorlevel% neq 0 (
    set PY_CMD=python
)

REM 1. Get local IP address using Python
for /f "usebackq tokens=*" %%a in (`%PY_CMD% -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('8.8.8.8', 80)); print(s.getsockname()[0]); s.close()"`) do (
    set LOCAL_IP=%%a
)

if not defined LOCAL_IP (
    echo [ERROR] Could not detect local IP address.
    pause
    exit /b
)

echo [OK] Detected PC Local IP: %LOCAL_IP%
echo.

REM 2. Stop old backend instances and start FastAPI Backend
echo [1/3] Checking and restarting Backend on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo Stopping old backend process, PID %%a...
    taskkill /f /pid %%a >nul 2>nul
)
start "MOCT-Backend" cmd /k "cd /d %~dp0 && %PY_CMD% -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"
echo Waiting for backend to initialize 5s...
ping 127.0.0.1 -n 6 >nul

REM 3. Start Vite Frontend with host binding
echo [2/3] Checking and starting Vite Frontend on port 5188 (exposing to LAN)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5188 ^| findstr LISTENING') do (
    echo Stopping old frontend process, PID %%a...
    taskkill /f /pid %%a >nul 2>nul
)
start "MOCT-Frontend" cmd /k "cd /d %~dp0frontend && npm run dev -- --host 0.0.0.0"
echo Waiting for frontend to initialize 3s...
ping 127.0.0.1 -n 4 >nul

REM 4. Generate URL and QR Code
set MOBILE_URL=http://%LOCAL_IP%:5188/?api_url=http://%LOCAL_IP%:8000

echo.
echo ==========================================================
echo.
echo  DESKTOP: Open http://localhost:5188/ to view on PC.
echo.
echo  MOBILE:  1. Connect your phone to the SAME Wi-Fi network.
echo           2. Scan the QR code opened on your PC.
echo              (Or type manually: %MOBILE_URL%)
echo.
echo ==========================================================
echo.

echo Generating QR code for mobile access...
%PY_CMD% scripts\show_qr.py "%MOBILE_URL%"

echo Keep this window open while testing.
pause

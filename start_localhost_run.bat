@echo off
setlocal enabledelayedexpansion
title HFR MOCT - Localhost.run Launcher
echo.
echo ==========================================================
echo       MOCT Cyrillic Font Matcher
echo      Localhost.run (SSH) Launcher
echo ==========================================================
echo.

cd /d "%~dp0"

set PY_CMD=py -3
where py >nul 2>nul
if %errorlevel% neq 0 (
    set PY_CMD=python
)

REM 0. Check SSH availability
where ssh >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] SSH client not found in your system.
    echo Please use start_localtunnel.bat instead.
    echo.
    pause
    exit /b
)

REM 1. Check and start FastAPI Backend
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo [OK] Backend is already running on port 8000.
) else (
    echo [1/3] Starting FastAPI Backend on port 8000...
    start "MOCT-Backend" cmd /k "cd /d %~dp0 && %PY_CMD% -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"
    echo Waiting for backend neural network initialization on RTX 3090...
    ping 127.0.0.1 -n 6 >nul
)

REM 2. Start SSH tunnel in the background
echo [2/3] Starting SSH Tunnel via localhost.run...
set LOG_FILE=%temp%\localhost_run.log
del /f /q "%LOG_FILE%" >nul 2>nul

start /b "" ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=10 -R 80:localhost:8000 localhost.run > "%LOG_FILE%" 2>&1

echo Waiting for tunnel URL generation...

REM Use PowerShell to extract the URL
set PS_CMD=PowerShell -NoProfile -ExecutionPolicy Bypass -Command "$url = ''; for ($i=0; $i -lt 15; $i++) { Start-Sleep -Seconds 1; if (Test-Path '%LOG_FILE%') { $c = Get-Content '%LOG_FILE%' -Raw; if ($c -match 'https://[a-zA-Z0-9\-]+\.lhr\.life') { $url = $matches[0]; break; } } }; if ($url) { Write-Output $url; } else { Write-Output 'FAIL'; }"

for /f "usebackq tokens=*" %%a in (`%PS_CMD%`) do (
    set TUNNEL_URL=%%a
)

if "%TUNNEL_URL%"=="FAIL" (
    echo.
    echo [ERROR] Failed to establish localhost.run tunnel.
    echo Log output:
    type "%LOG_FILE%"
    echo.
    pause
    exit /b
)
if not defined TUNNEL_URL (
    echo.
    echo [ERROR] Timeout waiting for localhost.run URL.
    echo Log output:
    type "%LOG_FILE%"
    echo.
    pause
    exit /b
)

echo.
echo [OK] Tunnel created successfully: %TUNNEL_URL%

REM Build frontend URL
set GITHUB_URL=https://alexmurzai.github.io/CyrillicFontTransfer/?api_url=%TUNNEL_URL%

REM Copy link to clipboard
PowerShell -NoProfile -ExecutionPolicy Bypass -Command "Set-Clipboard -Value '%GITHUB_URL%'"
echo [OK] Public URL copied to Windows Clipboard!
echo.

REM 3. Open site on PC
echo [3/3] Opening GitHub Pages app...
start "" "%GITHUB_URL%"

echo.
echo ==========================================================
echo.
echo  DESKTOP: Browser opened automatically.
echo.
echo  MOBILE:  Open this link on your phone:
echo.
echo  %GITHUB_URL%
echo.
echo ==========================================================
echo.

REM 4. Generate QR code for mobile
echo Generating QR code for mobile access...
%PY_CMD% scripts\show_qr.py "%GITHUB_URL%"

echo.
echo ==========================================================
echo Keep this window open while using the website.
echo To close the tunnel, press Ctrl+C or close this window.
echo ==========================================================
echo.

:loop
ping 127.0.0.1 -n 5 >nul
tasklist /fi "imagename eq ssh.exe" | findstr ssh.exe >nul
if %errorlevel% equ 0 goto loop

echo.
echo [WARNING] SSH tunnel has stopped!
pause

@echo off
title HFR MOCT - GitHub Launcher
echo.
echo ==========================================
echo       MOCT Cyrillic Font Matcher
echo        GitHub Version Launcher
echo ==========================================
echo.

cd /d "%~dp0"

set PY_CMD=py -3
where py >nul 2>nul
if %errorlevel% neq 0 (
    set PY_CMD=python
)

REM 1. Check and start FastAPI Backend
netstat -ano | findstr :8000 >nul
if %errorlevel% equ 0 (
    echo [OK] Backend is already running on port 8000.
) else (
    echo [1/3] Starting Backend on port 8000...
    start "MOCT-Backend" cmd /k "cd /d %~dp0 && %PY_CMD% -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"
    echo Waiting for backend to initialize 5s...
    ping 127.0.0.1 -n 6 >nul
)

REM 2. Stop old tunnel instances
taskkill /f /im cloudflared.exe >nul 2>nul

REM 3. Start Cloudflare Tunnel
echo [2/3] Starting Cloudflare Tunnel...
set LOG_FILE=%temp%\cloudflared.log
del /f /q "%LOG_FILE%" >nul 2>nul
start /b "" cloudflared.exe tunnel --url http://localhost:8000 --protocol http2 --edge-ip-version 4 > "%LOG_FILE%" 2>&1

echo Waiting for tunnel connection and URL generation...

REM Call PowerShell to extract URL
set PS_CMD=PowerShell -NoProfile -ExecutionPolicy Bypass -Command "$url = ''; for ($i=0; $i -lt 15; $i++) { Start-Sleep -Seconds 1; if (Test-Path '%LOG_FILE%') { $c = Get-Content '%LOG_FILE%' -Raw; if ($c -match 'https://[a-zA-Z0-9\-]+\.trycloudflare\.com') { $url = $matches[0]; break; } } }; if ($url) { Set-Clipboard -Value $url; Write-Output $url; } else { Write-Output 'FAIL'; }"

for /f "usebackq tokens=*" %%a in (`%PS_CMD%`) do (
    set TUNNEL_URL=%%a
)

if "%TUNNEL_URL%"=="FAIL" (
    echo.
    echo [ERROR] Failed to get Cloudflare tunnel URL.
    echo Log:
    type "%LOG_FILE%"
    echo.
    pause
    exit /b
)
if not defined TUNNEL_URL (
    echo.
    echo [ERROR] Tunnel URL generation timed out.
    echo Log:
    type "%LOG_FILE%"
    echo.
    pause
    exit /b
)

echo.
echo [OK] Tunnel created successfully: %TUNNEL_URL%
echo [OK] Public URL has been copied to your Windows Clipboard!
echo.
echo [3/3] Opening GitHub Pages site...
start https://alexmurzai.github.io/CyrillicFontTransfer/
echo.
echo ==========================================================
echo  INSTRUCTIONS:
echo  1. On the web page, click API Settings gear icon, bottom-left.
echo  2. Paste the copied URL from clipboard - press Ctrl+V.
echo  3. The website will connect to your local RTX 3090 GPU!
echo ==========================================================
echo.
echo Keep this window open while using the website.
echo To close the tunnel, press Ctrl+C here or close this window.
echo.

:loop
ping 127.0.0.1 -n 5 >nul
tasklist /fi "imagename eq cloudflared.exe" | findstr cloudflared.exe >nul
if %errorlevel% equ 0 goto loop

echo Tunnel was stopped.
pause

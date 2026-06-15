@echo off
setlocal enabledelayedexpansion

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   HFR — Hierarchical Font Recognition   ║
echo  ║   STABLE Server + Cloudflare Tunnel     ║
echo  ╚══════════════════════════════════════════╝
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
start "HFR-Backend" cmd /k "cd /d %~dp0 && %PY_CMD% -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"

echo       Ожидание загрузки backend (5 сек)...
ping 127.0.0.1 -n 6 >nul

REM 2. Запуск Cloudflare Tunnel с авто-рестартом
echo [2/2] Запуск стабильного туннеля (Cloudflare)...
echo.
echo ВНИМАНИЕ: Ищите строку "https://[случайный-текст].tryflare.com"
echo Это будет ваша новая ссылка для фронтенда.
echo.

:restart_tunnel
echo [%time%] Запуск туннеля...
set GODEBUG=netdns=go
.\cloudflared.exe tunnel --url http://127.0.0.1:8000 --protocol http2 --edge-ip-version 4
echo.
echo [%time%] ВНИМАНИЕ: Тоннель прерван! Перезапуск через 5 секунд...
ping 127.0.0.1 -n 6 >nul
goto restart_tunnel

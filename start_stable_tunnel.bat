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

REM 1. Запуск FastAPI backend (в новом окне)
echo [1/2] Запуск FastAPI backend на порту 8000...
start "HFR-Backend" cmd /k "cd /d %~dp0 && %PY_CMD% -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"

echo       Ожидание загрузки backend (5 сек)...
timeout /t 5 /nobreak >nul

REM 2. Запуск Cloudflare Tunnel с авто-рестартом
echo [2/2] Запуск стабильного туннеля (Cloudflare)...
echo.
echo ВНИМАНИЕ: Ищите строку "https://[случайный-текст].tryflare.com"
echo Это будет ваша новая ссылка для фронтенда.
echo.

:restart_tunnel
echo [%time%] Запуск туннеля...
.\cloudflared.exe tunnel --url http://127.0.0.1:8000
echo.
echo [%time%] ВНИМАНИЕ: Тоннель прерван! Перезапуск через 5 секунд...
timeout /t 5
goto restart_tunnel

@echo off
REM ═══════════════════════════════════════════
REM  HFR — Start Backend + Cloudflare Tunnel
REM  Запуск FastAPI и публичный доступ через Cloudflare
REM ═══════════════════════════════════════════

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   HFR — Hierarchical Font Recognition   ║
echo  ║   Backend + Cloudflare Tunnel Launcher   ║
echo  ╚══════════════════════════════════════════╝
echo.

cd /d "%~dp0"

set PY_CMD=py -3
where py >nul 2>nul
if %errorlevel% neq 0 (
    set PY_CMD=python
)

REM 1. Запуск FastAPI backend
echo [1/2] Запуск FastAPI backend на порту 8000...
start "HFR-Backend" cmd /k "cd /d %~dp0 && %PY_CMD% -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

REM Ждём 5 секунд, чтобы backend успел загрузить модель
echo       Ожидание загрузки ML-модели (5 сек)...
ping 127.0.0.1 -n 6 >nul

REM 2. Запуск Cloudflare Tunnel
echo [2/2] Запуск Cloudflare Tunnel...
echo       Публичный URL появится ниже:
echo.

set GODEBUG=netdns=go
cloudflared.exe tunnel --url http://127.0.0.1:8000 --protocol http2 --edge-ip-version 4

echo.
echo Туннель закрыт. Не забудьте закрыть окно backend.
pause

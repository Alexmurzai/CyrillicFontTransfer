@echo off
setlocal enabledelayedexpansion

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   HFR — Hierarchical Font Recognition   ║
echo  ║   STABLE Server + Pinggy (SSH Tunnel)   ║
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
ping 127.0.0.1 -n 6 >nul

REM 2. Запуск Pinggy с авто-рестартом
echo [2/2] Запуск стабильного туннеля (Pinggy)...
echo.
echo ВНИМАНИЕ: Ссылка появится в выводе ниже (ищите "https://...pinggy.link").
echo Если появится вопрос про "fingerprint" - введите "yes".
echo.

:restart_tunnel
echo [%time%] Запуск туннеля через SSH (port 443)...
REM Используем пользователя 'qr' для автоматического входа без пароля
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -p 443 -R 80:localhost:8000 qr@a.pinggy.io
echo.
echo [%time%] ВНИМАНИЕ: Соединение прервано! Перезапуск через 5 секунд...
ping 127.0.0.1 -n 6 >nul
goto restart_tunnel

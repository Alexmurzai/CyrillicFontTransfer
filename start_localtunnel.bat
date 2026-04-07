@echo off
echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   HFR — Hierarchical Font Recognition   ║
echo  ║   Backend + Localtunnel Launcher        ║
echo  ╚══════════════════════════════════════════╝
echo.

cd /d "%~dp0"

REM 1. Запуск FastAPI backend (в новом окне)
echo [1/2] Запуск FastAPI backend на порту 8000...
start "HFR-Backend" cmd /k "cd /d %~dp0 && py -3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

REM Ждём 5 секунд
echo       Ожидание загрузки (5 сек)...
timeout /t 5 /nobreak >nul

REM 2. Запуск Localtunnel
echo [2/2] Запуск Localtunnel...
echo.
echo ВНИМАНИЕ: Когда откроете ссылку, введите свой IP с сайта 2ip.ru
echo.
npx -y localtunnel --port 8000

echo.
echo Туннель закрыт.
pause

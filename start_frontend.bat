@echo off
REM ═══════════════════════════════════════════
REM  HFR — Start Frontend Developer Server
REM  Запуск Vite сервера для локальной разработки
REM ═══════════════════════════════════════════

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   HFR — Hierarchical Font Recognition   ║
echo  ║      Vite Frontend Server Launcher       ║
echo  ╚══════════════════════════════════════════╝
echo.

cd /d "%~dp0frontend"

echo [1/1] Установка зависимостей (на случай новых пакетов)...
call npm install --legacy-peer-deps

echo.
echo [2/2] Запуск Vite frontend dev-сервера...
echo       Откройте в браузере: http://localhost:5173
echo.

npm run dev

echo.
pause

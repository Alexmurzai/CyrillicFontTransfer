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

if not exist node_modules (
    echo [1/2] Установка зависимостей (node_modules не найден)...
    call npm install --legacy-peer-deps
) else (
    echo [1/2] node_modules найден. Пропуск установки зависимостей.
)

echo.
echo [2/2] Запуск Vite frontend dev-сервера...
echo       Откройте в браузере: http://localhost:5173
echo.

npm run dev

echo.
pause

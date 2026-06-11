@echo off
title HFR MOCT — Local Version Launcher
chcp 65001 >nul

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║          MOCT Cyrillic Font Matcher          ║
echo  ║         Локальная Версия — Launcher          ║
echo  ╚══════════════════════════════════════════╝
echo.

cd /d "%~dp0"

set PY_CMD=py -3
where py >nul 2>nul
if %errorlevel% neq 0 (
    set PY_CMD=python
)

REM 1. Проверка и запуск FastAPI Backend
netstat -ano | findstr :8000 >nul
if %errorlevel% equ 0 (
    echo [OK] Бэкенд уже запущен на порту 8000.
) else (
    echo [1/2] Запуск бэкенда на порту 8000...
    start "MOCT-Backend" cmd /k "cd /d %~dp0 && %PY_CMD% -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"
    
    echo       Ожидание инициализации бэкенда (5 сек)...
    ping 127.0.0.1 -n 6 >nul
)

REM 2. Проверка и запуск Vite Frontend
netstat -ano | findstr :5173 >nul
if %errorlevel% equ 0 (
    echo [OK] Фронтенд dev-сервер уже запущен на порту 5173.
) else (
    echo [2/2] Запуск фронтенда на порту 5173...
    start "MOCT-Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
    
    echo       Ожидание инициализации фронтенда (3 сек)...
    ping 127.0.0.1 -n 4 >nul
)

REM 3. Открытие в браузере
echo.
echo [OK] Открытие локального сайта в браузере...
start http://localhost:5173/

echo.
echo Запуск завершен. Окна терминалов бэкенда и фронтенда работают в фоне.
echo Чтобы выключить систему, просто закройте открывшиеся окна терминалов.
echo.
pause

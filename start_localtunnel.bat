@echo off
title HFR Master Launcher
setlocal
cd /d "%~dp0"

:: Настройка цветов (голубой текст на черном)
color 0B

echo ======================================================
echo   HFR - Hierarchical Font Recognition Launcher
echo ======================================================
echo.

:: 1. Проверка, не запущен ли уже сервер
netstat -ano | findstr :8000 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [!] Порт 8000 уже занят. Возможно, бэкенд уже запущен.
    echo     Пробую запустить туннель напрямую...
    goto start_tunnel
)

:: 2. Запуск бэкенда в фоновом (минимизированном) окне
echo [*] Запуск FastAPI Backend (в новом окне)...
start "HFR-Backend-Server" /min cmd /c "py -3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"

:: 3. Ожидание готовности API (особенно важно для CUDA)
echo [*] Ожидание инициализации нейросети (загрузка весов на RTX 3090)...
:wait_loop
timeout /t 2 /nobreak >nul
curl -s http://localhost:8000/api/health | findstr "ok" >nul
if %errorlevel% neq 0 (
    echo     . . . API еще не отвечает
    goto wait_loop
)

echo [+] Бэкенд онлайн!
echo.

:start_tunnel
:: 4. Запуск туннеля
echo [*] Активация туннеля: https://hfr-alex-font.loca.lt
echo [!] ВНИМАНИЕ: Если спросят пароль - введи свой IP с сайта 2ip.ru
echo.
npx -y localtunnel --port 8000 --subdomain hfr-alex-font

pause

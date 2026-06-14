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

:: 1. Проверка и перезапуск бэкенда на порту 8000
echo [*] Проверка и перезапуск бэкенда на порту 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo Stopping old backend process (PID %%a)...
    taskkill /f /pid %%a >nul 2>nul
)

:: 2. Запуск бэкенда в фоновом (минимизированном) окне
echo [*] Запуск FastAPI Backend (в новом окне)...
set PY_CMD=py -3
where py >nul 2>nul
if %errorlevel% neq 0 set PY_CMD=python
start "HFR-Backend-Server" /min cmd /c "%PY_CMD% -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"

:: 3. Ожидание готовности API (особенно важно для CUDA)
echo [*] Ожидание инициализации нейросети (загрузка весов на RTX 3090)...
set /a retry_count=0
:wait_loop
set /a retry_count+=1
if %retry_count% gtr 30 (
    echo [!] Ошибка: Сервер не ответил за 60 секунд. Проверьте окно бэкенда на наличие ошибок!
    pause
    exit /b 1
)
ping 127.0.0.1 -n 3 >nul
curl -s http://localhost:8000/api/health | findstr "ok" >nul
if %errorlevel% neq 0 (
    echo     . . . API еще не отвечает (попытка %retry_count%/30)
    goto wait_loop
)

echo [+] Бэкенд онлайн!
echo.

:start_tunnel
echo [*] Активация туннеля: https://hfr-alex-font-v2.loca.lt
echo [!] ВНИМАНИЕ: Если спросят пароль - введи свой IP с сайта 2ip.ru
echo.
npx -y localtunnel --port 8000 --subdomain hfr-alex-font-v2

pause

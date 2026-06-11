@echo off
title HFR MOCT — GitHub Version Launcher
chcp 65001 >nul

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║          MOCT Cyrillic Font Matcher          ║
echo  ║         Версия на GitHub — Launcher          ║
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
    echo [1/3] Запуск бэкенда на порту 8000...
    start "MOCT-Backend" cmd /k "cd /d %~dp0 && %PY_CMD% -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"
    
    echo       Ожидание инициализации бэкенда (5 сек)...
    ping 127.0.0.1 -n 6 >nul
)

REM 2. Очистка старых процессов туннеля
taskkill /f /im cloudflared.exe >nul 2>nul

REM 3. Запуск Cloudflare Tunnel
echo [2/3] Запуск Cloudflare Tunnel...
set LOG_FILE=%temp%\cloudflared.log
del /f /q "%LOG_FILE%" >nul 2>nul
start /b "" cloudflared.exe tunnel --url http://localhost:8000 --protocol http2 --edge-ip-version 4 > "%LOG_FILE%" 2>&1

echo       Ожидание подключения и генерации URL...

REM Вызов PowerShell для ожидания и извлечения URL
set PS_CMD=PowerShell -NoProfile -ExecutionPolicy Bypass -Command "$url = ''; for ($i=0; $i -lt 15; $i++) { Start-Sleep -Seconds 1; if (Test-Path '%LOG_FILE%') { $c = Get-Content '%LOG_FILE%' -Raw; if ($c -match 'https://[a-zA-Z0-9\-]+\.trycloudflare\.com') { $url = $matches[0]; break; } } }; if ($url) { Set-Clipboard -Value $url; Write-Output $url; } else { Write-Output 'FAIL'; }"

for /f "usebackq tokens=*" %%a in (`%PS_CMD%`) do (
    set TUNNEL_URL=%%a
)

if "%TUNNEL_URL%"=="FAIL" (
    echo.
    echo [Ошибка] Не удалось получить URL туннеля. Проверьте подключение к Интернету.
    echo Лог ошибки:
    type "%LOG_FILE%"
    echo.
    pause
    exit /b
)
if not defined TUNNEL_URL (
    echo.
    echo [Ошибка] Не удалось получить URL туннеля (таймаут).
    echo Лог ошибки:
    type "%LOG_FILE%"
    echo.
    pause
    exit /b
)

echo.
echo [OK] Успешно! Создан туннель: %TUNNEL_URL%
echo [OK] URL скопирован в буфер обмена Windows.
echo.
echo [3/3] Открытие сайта на GitHub в браузере...
start https://alexmurzai.github.io/CyrillicFontTransfer/
echo.
echo ──────────────────────────────────────────────────────────
echo  ИНСТРУКЦИЯ:
echo  1. На открывшейся странице сайта нажмите «Настройки API» (шестеренка слева внизу).
echo  2. Вставьте скопированный URL (нажав Ctrl+V) в текстовое поле.
echo  3. Сайт автоматически подключится к вашей локальной видеокарте RTX 3090!
echo ──────────────────────────────────────────────────────────
echo.
echo Не закрывайте это окно терминала, пока пользуетесь сайтом (в нем работает туннель).
echo Для завершения работы нажмите Ctrl+C здесь или просто закройте это окно.
echo.

REM Ожидание закрытия туннеля (держим скрипт активным, чтобы туннель не умер)
:loop
ping 127.0.0.1 -n 5 >nul
tasklist /fi "imagename eq cloudflared.exe" | findstr cloudflared.exe >nul
if %errorlevel% equ 0 goto loop

echo Туннель был принудительно остановлен.
pause

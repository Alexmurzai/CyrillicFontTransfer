@echo off
title HFR MOCT - Font Collection Manager
echo.
echo ==================================================
echo         MOCT Cyrillic Font Matcher
echo         Font Collection Manager
echo ==================================================
echo.

cd /d "%~dp0"

set PY_CMD=py -3
where py >nul 2>nul
if %errorlevel% neq 0 (
    set PY_CMD=python
)

REM Запуск python скрипта управления коллекцией
%PY_CMD% scripts\manage_collection.py

echo.
echo ==================================================
echo Менеджер коллекции завершил работу.
echo Нажмите любую клавишу для закрытия окна.
echo ==================================================
pause >nul

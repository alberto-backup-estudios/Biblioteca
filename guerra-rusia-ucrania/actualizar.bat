@echo off
chcp 65001 > nul
title Monitor de Guerra Rusia-Ucrania
echo ============================================================
echo   Actualizando Monitor de Inteligencia Rusia-Ucrania
echo ============================================================
echo.
cd /d "%~dp0"
python build_monitor.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Hubo un problema ejecutando build_monitor.py
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [OK] Monitor actualizado. Abriendo en el navegador...
start "" "%~dp0index.html"
timeout /t 3 > nul

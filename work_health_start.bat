@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PYTHON=C:\Users\13410\.conda\envs\work_health\python.exe"

echo ========================================================
echo   Health Assistant - Work Health
echo   Python: %PYTHON%
echo ========================================================

if not exist "%PYTHON%" (
    echo [ERROR] work_health conda env not found:
    echo   %PYTHON%
    echo.
    echo Please create it first:
    echo   conda create -n work_health python=3.10
    echo   conda install -n work_health -c conda-forge pystray pillow
    pause
    exit /b 1
)

"%PYTHON%" src\main.py
if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with code %errorlevel%
    echo Check app.log for details.
    pause
)

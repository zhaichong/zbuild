@echo off
setlocal
cd /d "%~dp0"

if exist "%~dp0scripts\start_web.py" (
    set "TARGET_DIR=%~dp0"
) else if exist "%~dp0..\scripts\start_web.py" (
    set "TARGET_DIR=%~dp0..\"
) else (
    echo [ERROR] Cannot find scripts\start_web.py
    pause
    exit /b 1
)

cd /d "%TARGET_DIR%"

py scripts\start_web.py --open
if %ERRORLEVEL% NEQ 0 (
    python scripts\start_web.py --open
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Web server stopped with error.
    pause
)

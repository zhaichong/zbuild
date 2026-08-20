@echo off
setlocal EnableExtensions
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

set "ZBUILD_RESOURCES_DIR=%TARGET_DIR%"
set "PYTHONUTF8=1"
set "PATH=%TARGET_DIR%runtime\git\cmd;%TARGET_DIR%runtime\git\bin;%TARGET_DIR%runtime\svn\bin;%TARGET_DIR%runtime\node;%PATH%"

if exist "%TARGET_DIR%runtime\python\python.exe" (
    "%TARGET_DIR%runtime\python\python.exe" scripts\start_web.py --open %*
) else (
    py scripts\start_web.py --open %*
    if %ERRORLEVEL% NEQ 0 (
        python scripts\start_web.py --open %*
    )
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Web server stopped with error.
    pause
)

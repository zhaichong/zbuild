@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0.."

echo ===================================================
echo   zbuild 一键更新并解决冲突工具
echo ===================================================
echo.

rem 加载内建与系统 Git 路径
set "PATH=%CD%\runtime\git\cmd;%CD%\runtime\git\bin;%PATH%"

where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 未检测到 Git 命令行工具，请确保已安装 Git。
    pause
    exit /b 1
)

echo [1/4] 正在中止冲突中的合并或变基状态...
git merge --abort 2>nul
git rebase --abort 2>nul

echo [2/4] 正在获取远程最新代码 (fetch origin)...
git fetch origin web2.0 2>nul || git fetch origin

echo [3/4] 正在强制对齐远程 web2.0 分支最新代码...
git reset --hard origin/web2.0 2>nul || git reset --hard @{u}

echo [4/4] 正在清理未跟踪的临时改动...
git clean -fd

echo.
echo ===================================================
echo   代码同步成功！本地冲突已自动彻底解决！
echo ===================================================
echo.
echo 当前分支已对齐远程最新版本。
echo.
pause

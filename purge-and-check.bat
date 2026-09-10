@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [1/3] 删除 Electron 残留...
py -3 tools\purge_electron.py
if errorlevel 1 (
  echo 删除脚本失败，请确认已安装 Python。
  pause
  exit /b 1
)
echo [2/3] npm install...
call npm install
if errorlevel 1 (
  echo npm install 失败。
  pause
  exit /b 1
)
echo [3/3] npm run typecheck...
call npm run typecheck
echo.
echo 完成。把上面的 typecheck 结果发回对话即可收口。
pause

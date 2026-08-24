# setup_runtime.ps1
# ---------------------------------------------------------------
# 下载 Python 3.11 embeddable 并安装必要依赖到 runtime/python/
# 运行完毕后执行 npm run dist 打包，Python 会自动随安装包分发。
#
# 用法：
#   在项目根目录运行:  .\tools\setup_runtime.ps1
# ---------------------------------------------------------------

param(
    [string]$PyVersion = "3.11.9"
)

$ErrorActionPreference = "Stop"

# PS5 compatible path construction (Join-Path only takes 2 args in PS5)
$ROOT        = (Get-Item (Join-Path $PSScriptRoot "..")).FullName
$RUNTIME_DIR = "$ROOT\runtime\python"
New-Item -ItemType Directory -Force -Path $RUNTIME_DIR | Out-Null
$RUNTIME_DIR = (Get-Item $RUNTIME_DIR).FullName
$TEMP_ZIP    = "$env:TEMP\zbuild-python-embed.zip"
$PY_EXE      = "$RUNTIME_DIR\python.exe"
$PY_URL      = "https://www.python.org/ftp/python/$PyVersion/python-$PyVersion-embed-amd64.zip"

Write-Host ""
Write-Host "=== zbuild Python Runtime Setup ===" -ForegroundColor Cyan
Write-Host "Python version : $PyVersion"
Write-Host "Target dir     : $RUNTIME_DIR"
Write-Host ""

# ── 1. 下载 embeddable zip ────────────────────────────────────────────────────
Write-Host "[1/4] Downloading Python $PyVersion embeddable ..." -ForegroundColor Yellow
if (Test-Path $PY_EXE) {
    Write-Host "      Already exists, skipping download." -ForegroundColor DarkGray
} else {
    try {
        Invoke-WebRequest -Uri $PY_URL -OutFile $TEMP_ZIP -UseBasicParsing
    } catch {
        Write-Host "ERROR: Download failed: $_" -ForegroundColor Red
        Write-Host "Please download manually from: $PY_URL" -ForegroundColor Red
        Write-Host "and extract to: $RUNTIME_DIR" -ForegroundColor Red
        exit 1
    }

    # ── 2. 解压 ────────────────────────────────────────────────────────────────
    Write-Host "[2/4] Extracting ..." -ForegroundColor Yellow
    Expand-Archive -Path $TEMP_ZIP -DestinationPath $RUNTIME_DIR -Force
    Remove-Item $TEMP_ZIP -Force
}

# ── 3. 启用 site-packages ────────────────────────────────────────────────────
# 必须在安装 pip 之前完成，否则 -m pip 找不到已安装的模块。
# embeddable Python 的 pth 文件名形如 python311._pth（注意下划线）。
Write-Host "[3/4] Enabling site-packages ..." -ForegroundColor Yellow
$pthFiles = Get-ChildItem "$RUNTIME_DIR" -Filter "python3*._pth" -ErrorAction SilentlyContinue
if (-not $pthFiles) {
    # 兜底：扫描所有 ._pth 文件
    $pthFiles = Get-ChildItem "$RUNTIME_DIR" -Filter "*._pth" -ErrorAction SilentlyContinue
}
if ($pthFiles) {
    foreach ($pthFile in $pthFiles) {
        $content = Get-Content $pthFile.FullName -Raw -Encoding Ascii
        if ($content -match '#import site') {
            $content = $content -replace '#import site', 'import site'
            Set-Content -Path $pthFile.FullName -Value $content -Encoding Ascii -NoNewline
            Write-Host "      Patched: $($pthFile.Name)" -ForegroundColor Green
        } else {
            Write-Host "      Already enabled: $($pthFile.Name)" -ForegroundColor DarkGray
        }
    }
} else {
    Write-Host "      WARNING: No ._pth file found in $RUNTIME_DIR" -ForegroundColor DarkYellow
    Get-ChildItem $RUNTIME_DIR | Select-Object Name | ForEach-Object { Write-Host "        $($_.Name)" }
}

# ── 4. 安装 pip + 依赖包 ──────────────────────────────────────────────────────
Write-Host "[4/4] Installing pip and required packages ..." -ForegroundColor Yellow

# 检查 pip 是否已安装。PowerShell 在 ErrorActionPreference=Stop 时会把
# ``python -m pip`` 的首次失败当作脚本异常，因此直接检查安装目录。
$hasPip = Test-Path "$RUNTIME_DIR\Lib\site-packages\pip"
if (-not $hasPip) {
    $getPipPath = Join-Path $env:TEMP "get-pip.py"
    Write-Host "      Downloading get-pip.py ..." -ForegroundColor DarkGray
    Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $getPipPath -UseBasicParsing
    & $PY_EXE $getPipPath --no-warn-script-location 2>&1 | Write-Host
    Remove-Item $getPipPath -Force -ErrorAction SilentlyContinue
}

# 安装运行时依赖。aiohttp 是 Web 服务启动所必需的，不能只存在于开发机。
Write-Host "      Installing packages: aiohttp openpyxl paramiko pymysql ..." -ForegroundColor DarkGray
& $PY_EXE -m pip install aiohttp openpyxl paramiko pymysql --no-warn-script-location 2>&1 | Write-Host

if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Some packages may not have installed correctly." -ForegroundColor DarkYellow
    Write-Host "         Try running manually: $PY_EXE -m pip install openpyxl paramiko" -ForegroundColor DarkYellow
}

# ── 5. 准备 Node 14 + npm 运行时 ──────────────────────────────────────────────
Write-Host ""
Write-Host "[5/5] Checking Node.js 14 runtime ..." -ForegroundColor Yellow
$NODE_DIR = "$ROOT\runtime\node"
$NODE_EXE = "$NODE_DIR\node.exe"
$NPM_CLI  = "$NODE_DIR\node_modules\npm\bin\npm-cli.js"

if ((Test-Path $NODE_EXE) -and (Test-Path $NPM_CLI)) {
    Write-Host "      Node 14 runtime is complete at $NODE_DIR" -ForegroundColor DarkGray
} else {
    $NODE_VERSION = "14.21.3"
    $NODE_ZIP = "$env:TEMP\node-v$NODE_VERSION-win-x64.zip"
    $NODE_EXTRACT = "$env:TEMP\node-v$NODE_VERSION"
    $NODE_URL = "https://npmmirror.com/mirrors/node/v$NODE_VERSION/node-v$NODE_VERSION-win-x64.zip"

    Write-Host "      Downloading Node $NODE_VERSION ..." -ForegroundColor DarkGray
    try {
        Invoke-WebRequest -Uri $NODE_URL -OutFile $NODE_ZIP -UseBasicParsing
    } catch {
        Write-Host "      Fallback to official nodejs.org..." -ForegroundColor DarkGray
        Invoke-WebRequest -Uri "https://nodejs.org/dist/v$NODE_VERSION/node-v$NODE_VERSION-win-x64.zip" -OutFile $NODE_ZIP -UseBasicParsing
    }

    Write-Host "      Extracting Node 14 ..." -ForegroundColor DarkGray
    Remove-Item $NODE_EXTRACT -Recurse -Force -ErrorAction SilentlyContinue
    Expand-Archive -Path $NODE_ZIP -DestinationPath $NODE_EXTRACT -Force
    New-Item -ItemType Directory -Force -Path $NODE_DIR | Out-Null
    Copy-Item "$NODE_EXTRACT\node-v$NODE_VERSION-win-x64\*" $NODE_DIR -Recurse -Force
    Remove-Item $NODE_EXTRACT -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $NODE_ZIP -Force -ErrorAction SilentlyContinue
    Write-Host "      Node 14 runtime ready at: $NODE_DIR" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host "Python runtime: $RUNTIME_DIR"
Write-Host "Node runtime  : $NODE_DIR"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  npm run dist    -- build and package the installer"
Write-Host ""


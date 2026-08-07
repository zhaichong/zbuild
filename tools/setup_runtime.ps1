# setup_runtime.ps1
# ---------------------------------------------------------------
# 构建带锁定依赖的 Python 3.11 预制运行环境 ZIP，并同步到 runtime/python/
#
# 用法：
#   在项目根目录运行:  .\tools\setup_runtime.ps1
#   可选参数:
#     -PyVersion 3.11.9
#     -PrimaryUrl https://...
#     -BackupUrl  https://...
#     -SkipManifestFill   仅构建 ZIP，不回填 manifest
#
# 产物：
#   - runtime/python/           开发模式使用（与打包一致，已裁剪）
#   - release/zbuild-python-<version>-win-x64.zip   预制 ZIP（含 SHA256）
#   - electron/runtime-manifest.json  回填 python.sha256 / size（及可选 URL）
# ---------------------------------------------------------------

param(
    [string]$PyVersion = "3.11.9",
    [string]$PrimaryUrl = "",
    [string]$BackupUrl = "",
    [switch]$SkipManifestFill
)

$ErrorActionPreference = "Stop"

# 精确锁定（与 pyproject.toml 保持一致）— 必须用数组，避免作为单一参数传给 pip
$PINNED_PKGS = @("openpyxl==3.1.5", "paramiko==5.0.0")

# PS5 compatible path construction
$ROOT        = (Get-Item (Join-Path $PSScriptRoot "..")).FullName
$RUNTIME_DIR = "$ROOT\runtime\python"
$BUILD_DIR   = "$ROOT\tools\build-runtime\python"
$TEMP_ZIP    = "$env:TEMP\zbuild-python-embed.zip"
$OUT_ZIP     = "$ROOT\release\zbuild-python-$PyVersion-win-x64.zip"
$PY_URL      = "https://www.python.org/ftp/python/$PyVersion/python-$PyVersion-embed-amd64.zip"

function Remove-Tree($path) {
    if (Test-Path $path) { Remove-Item -LiteralPath $path -Recurse -Force -ErrorAction SilentlyContinue }
}

Write-Host ""
Write-Host "=== zbuild Python Runtime Setup ===" -ForegroundColor Cyan
Write-Host "Python version : $PyVersion"
Write-Host "Pinned packages: $($PINNED_PKGS -join ' ')"
Write-Host "Output ZIP     : $OUT_ZIP"
Write-Host ""

# ── 1. 下载 embeddable zip ────────────────────────────────────────────────────
Write-Host "[1/7] Downloading Python $PyVersion embeddable ..." -ForegroundColor Yellow
if (-not (Test-Path $TEMP_ZIP)) {
    try {
        Invoke-WebRequest -Uri $PY_URL -OutFile $TEMP_ZIP -UseBasicParsing
    } catch {
        Write-Host "ERROR: Download failed: $_" -ForegroundColor Red
        Write-Host "Please download manually from: $PY_URL" -ForegroundColor Red
        Write-Host "and save to: $TEMP_ZIP" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "      Using cached $TEMP_ZIP" -ForegroundColor DarkGray
}

# ── 2. 解压到 staging ────────────────────────────────────────────────────────
Write-Host "[2/7] Extracting to staging ..." -ForegroundColor Yellow
Remove-Tree $BUILD_DIR
New-Item -ItemType Directory -Force -Path $BUILD_DIR | Out-Null
Expand-Archive -Path $TEMP_ZIP -DestinationPath $BUILD_DIR -Force
$PY_EXE = "$BUILD_DIR\python.exe"

# ── 3. 启用 site-packages ────────────────────────────────────────────────────
Write-Host "[3/7] Enabling site-packages ..." -ForegroundColor Yellow
$pthFiles = Get-ChildItem "$BUILD_DIR" -Filter "python3*._pth" -ErrorAction SilentlyContinue
if (-not $pthFiles) { $pthFiles = Get-ChildItem "$BUILD_DIR" -Filter "*._pth" -ErrorAction SilentlyContinue }
if ($pthFiles) {
    foreach ($pthFile in $pthFiles) {
        $content = Get-Content $pthFile.FullName -Raw -Encoding Ascii
        if ($content -match '#import site') {
            $content = $content -replace '#import site', 'import site'
            Set-Content -Path $pthFile.FullName -Value $content -Encoding Ascii -NoNewline
            Write-Host "      Patched: $($pthFile.Name)" -ForegroundColor Green
        }
    }
} else {
    throw "No ._pth file found in $BUILD_DIR"
}

# ── 4. 安装 pip + 锁定依赖 ──────────────────────────────────────────────────
Write-Host "[4/7] Installing pip and pinned packages ..." -ForegroundColor Yellow
# embeddable Python has no pip; stderr would abort under ErrorActionPreference=Stop
$prevEap = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
& $PY_EXE -m pip --version 2>&1 | Out-Null
$hasPip = ($LASTEXITCODE -eq 0)
$ErrorActionPreference = $prevEap
if (-not $hasPip) {
    $getPipPath = Join-Path $env:TEMP "get-pip.py"
    Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $getPipPath -UseBasicParsing
    $ErrorActionPreference = 'Continue'
    & $PY_EXE $getPipPath --no-warn-script-location 2>&1 | Write-Host
    $getPipExit = $LASTEXITCODE
    $ErrorActionPreference = $prevEap
    Remove-Item $getPipPath -Force -ErrorAction SilentlyContinue
    if ($getPipExit -ne 0) { throw "get-pip.py failed with exit $getPipExit" }
}
$ErrorActionPreference = 'Continue'
& $PY_EXE -m pip install @PINNED_PKGS --no-warn-script-location 2>&1 | Write-Host
$pipExit = $LASTEXITCODE
$ErrorActionPreference = $prevEap
if ($pipExit -ne 0) { throw "pip install failed for: $($PINNED_PKGS -join ' ')" }

# ── 5. 裁剪（与打包后状态一致）───────────────────────────────────────────────
Write-Host "[5/7] Pruning pip/setuptools/wheel/Scripts/__pycache__ ..." -ForegroundColor Yellow
$sp = "$BUILD_DIR\Lib\site-packages"
foreach ($p in @("pip", "setuptools", "wheel", "pkg_resources", "_distutils_hack")) {
    Remove-Tree (Join-Path $sp $p)
}
Get-ChildItem $sp -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '^(pip|setuptools|wheel)-' } |
    ForEach-Object { Remove-Tree $_.FullName }
# leftover .pth from setuptools causes stderr noise and can break embeddable site
Get-ChildItem $sp -Filter "*.pth" -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match 'distutils|setuptools|pip|wheel' } |
    ForEach-Object { Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue }
Remove-Tree "$BUILD_DIR\Scripts"
Get-ChildItem $BUILD_DIR -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
    ForEach-Object { Remove-Tree $_.FullName }

# ── 6. 健康检查（含精确版本）──────────────────────────────────────────────────
Write-Host "[6/7] Health check (openpyxl==3.1.5, paramiko==5.0.0) ..." -ForegroundColor Yellow
$prevEap = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
$health = & $PY_EXE -c "import openpyxl, paramiko; assert openpyxl.__version__=='3.1.5', openpyxl.__version__; assert paramiko.__version__=='5.0.0', paramiko.__version__; print('OK', openpyxl.__version__, paramiko.__version__)" 2>&1
$healthExit = $LASTEXITCODE
$ErrorActionPreference = $prevEap
if ($healthExit -ne 0) { throw "Health check failed: $health" }
Write-Host "      $health" -ForegroundColor Green

# ── 7. 同步 dev runtime + 生成预制 ZIP + 回填 manifest ────────────────────────
Write-Host "[7/7] Syncing dev runtime and building ZIP ..." -ForegroundColor Yellow
Remove-Tree $RUNTIME_DIR
New-Item -ItemType Directory -Force -Path "$ROOT\runtime" | Out-Null
Move-Item $BUILD_DIR $RUNTIME_DIR

New-Item -ItemType Directory -Force -Path "$ROOT\release" | Out-Null
Remove-Item $OUT_ZIP -Force -ErrorAction SilentlyContinue
Compress-Archive -Path "$RUNTIME_DIR\*" -DestinationPath $OUT_ZIP -CompressionLevel Optimal -Force

$fileInfo = Get-Item $OUT_ZIP
$hash = (Get-FileHash $OUT_ZIP -Algorithm SHA256).Hash.ToLower()
$sizeMB = [math]::Round($fileInfo.Length / 1MB, 2)

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host "Dev runtime : $RUNTIME_DIR"
Write-Host "Runtime ZIP : $OUT_ZIP ($sizeMB MB)"
Write-Host "SHA256      : $hash"
Write-Host ""

if (-not $SkipManifestFill) {
    $fillArgs = @("tools/fill-runtime-manifest.cjs", "--python-zip", $OUT_ZIP)
    if ($PrimaryUrl) { $fillArgs += @("--primary", $PrimaryUrl) }
    if ($BackupUrl)  { $fillArgs += @("--backup", $BackupUrl) }
    Write-Host "Filling electron/runtime-manifest.json ..." -ForegroundColor Yellow
    & node @fillArgs
    if ($LASTEXITCODE -ne 0) { throw "fill-runtime-manifest.cjs failed" }
    Write-Host "Manifest updated." -ForegroundColor Green
} else {
    Write-Host "SkipManifestFill set — remember to fill python.sha256/size/primary/backup before release." -ForegroundColor Yellow
}
Write-Host ""

# Build a self-contained zbuild Web Server folder for a Windows machine with no runtimes installed.
param(
    [string]$OutputDir = "",
    [string]$GitSource = "D:\application\Git",
    [string]$SvnSource = "C:\Program Files\SlikSvn"
)

$ErrorActionPreference = "Stop"
$ROOT = (Get-Item (Join-Path $PSScriptRoot "..")).FullName
if (-not $OutputDir) {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $OutputDir = Join-Path $ROOT "release\zbuild-web-server-$stamp"
}
$OutputDir = [System.IO.Path]::GetFullPath($OutputDir)

if (Test-Path $OutputDir) { throw "Output directory already exists: $OutputDir" }
if (-not (Test-Path "$GitSource\cmd\git.exe")) { throw "Git executable not found: $GitSource\cmd\git.exe" }
if (-not (Test-Path "$SvnSource\bin\svn.exe")) { throw "SVN executable not found: $SvnSource\bin\svn.exe" }

Write-Host "[1/5] Build frontend..." -ForegroundColor Cyan
Push-Location $ROOT
try { & npm.cmd run build } finally { Pop-Location }
if ($LASTEXITCODE -ne 0) { throw "Frontend build failed" }

Write-Host "[2/5] Prepare embedded Python dependencies..." -ForegroundColor Cyan
& powershell -ExecutionPolicy Bypass -File "$ROOT\tools\setup_runtime.ps1"
if ($LASTEXITCODE -ne 0) { throw "Python runtime setup failed" }

Write-Host "[3/5] Assemble package..." -ForegroundColor Cyan
New-Item -ItemType Directory -Path $OutputDir | Out-Null
foreach ($name in @("dist", "scripts", "references", "runtime")) {
    Copy-Item -Recurse -Force "$ROOT\$name" (Join-Path $OutputDir $name)
}
Copy-Item -Force "$ROOT\tools\start_web.bat" (Join-Path $OutputDir "Start-Web.bat")
Copy-Item -Recurse -Force $GitSource (Join-Path $OutputDir "runtime\git")
Copy-Item -Recurse -Force $SvnSource (Join-Path $OutputDir "runtime\svn")
Get-ChildItem -Path "$OutputDir\scripts" -Directory -Filter "__pycache__" -Recurse | Remove-Item -Recurse -Force
Get-ChildItem -Path "$OutputDir\scripts" -File -Filter "*.pyc" -Recurse | Remove-Item -Force

$readme = "zbuild Web Server deployment package`r`n`r`n" +
    "1. Copy this folder to the server, for example D:\zbuild-web-server.`r`n" +
    "2. Run Start-Web.bat. It creates .zbuild-data\web-config.json on first start.`r`n" +
    "3. Configure project root, SVN URL and personal SVN credentials in the browser settings.`r`n" +
    "4. Allow TCP 8000 in Windows Firewall if LAN users cannot connect.`r`n`r`n" +
    "The package includes Python, Node, Git and SVN. Project repositories must still be reachable from the server."
Set-Content -Path (Join-Path $OutputDir "DEPLOYMENT.txt") -Value $readme -Encoding utf8

Write-Host "[4/5] Verify package runtime..." -ForegroundColor Cyan
$env:ZBUILD_RESOURCES_DIR = $OutputDir
$env:PATH = "$OutputDir\runtime\git\cmd;$OutputDir\runtime\git\bin;$OutputDir\runtime\svn\bin;$OutputDir\runtime\node;$env:PATH"
& "$OutputDir\runtime\python\python.exe" -c "import aiohttp; print('aiohttp', aiohttp.__version__)"
if ($LASTEXITCODE -ne 0) { throw "Bundled Python cannot import aiohttp" }
& "$OutputDir\runtime\git\cmd\git.exe" --version
& "$OutputDir\runtime\svn\bin\svn.exe" --version --quiet
& "$OutputDir\runtime\node\node.exe" --version
if ($LASTEXITCODE -ne 0) { throw "Bundled Node verification failed" }

Write-Host "[5/5] Complete" -ForegroundColor Green
Write-Host "Package: $OutputDir" -ForegroundColor Green

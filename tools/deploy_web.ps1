[CmdletBinding()]
param(
    [string]$HostAddress = '0.0.0.0',
    [ValidateRange(1, 65535)]
    [int]$Port = 8000,
    [switch]$SkipPull,
    [switch]$NoStart
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot

function Stop-Deployment {
    param([string]$Message)

    Write-Host "`n部署已停止：$Message" -ForegroundColor Red
    exit 1
}

function Invoke-Step {
    param(
        [string]$Title,
        [string]$Command,
        [string[]]$Arguments = @()
    )

    Write-Host "`n==> $Title" -ForegroundColor Cyan
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        Stop-Deployment "$Title 失败（退出码：$LASTEXITCODE）。"
    }
}

function Require-Command {
    param([string]$Name)

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        Stop-Deployment "未找到 $Name，请先安装并加入 PATH。"
    }
}

Set-Location $repoRoot

if (-not (Test-Path (Join-Path $repoRoot '.git'))) {
    Stop-Deployment '当前目录不是 Git 仓库。请将脚本放在 zbuild 项目中执行。'
}

if (-not (Test-Path (Join-Path $repoRoot 'package-lock.json'))) {
    Stop-Deployment '未找到 package-lock.json，无法执行可重复的 npm 安装。'
}

Require-Command 'git'
Require-Command 'node'
Require-Command 'npm'

$pythonCommand = if (Get-Command 'py' -ErrorAction SilentlyContinue) {
    'py'
} elseif (Get-Command 'python' -ErrorAction SilentlyContinue) {
    'python'
} else {
    Stop-Deployment '未找到 py 或 python，请先安装 Python 并加入 PATH。'
}

Write-Host "部署目录：$repoRoot" -ForegroundColor DarkGray

if (-not $SkipPull) {
    $changes = & git status --porcelain
    if ($LASTEXITCODE -ne 0) {
        Stop-Deployment '无法读取 Git 工作区状态。'
    }
    if ($changes) {
        Stop-Deployment '检测到未提交的本地改动。为避免覆盖服务器修改，脚本不会拉取代码；请先提交、暂存或清理改动。'
    }

    Invoke-Step '拉取最新代码' 'git' @('pull', '--ff-only')
} else {
    Write-Host "`n==> 跳过拉取代码" -ForegroundColor Yellow
}

Invoke-Step '安装 Python 服务依赖' $pythonCommand @('-m', 'pip', 'install', '-e', '.')
Invoke-Step '安装前端依赖' 'npm' @('ci')
Invoke-Step '构建前端 dist' 'npm' @('run', 'build')

if ($NoStart) {
    Write-Host "`n构建完成，未启动 Web 服务（-NoStart）。" -ForegroundColor Green
    exit 0
}

Write-Host "`n构建完成，Web 服务即将启动：http://localhost:$Port" -ForegroundColor Green
Write-Host '按 Ctrl+C 可停止服务。' -ForegroundColor DarkGray
Invoke-Step '启动 Web 服务' $pythonCommand @('scripts/start_web.py', '--host', $HostAddress, '--port', $Port)

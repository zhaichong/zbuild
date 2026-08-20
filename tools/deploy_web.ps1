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

    Write-Host "`nDeployment stopped: $Message" -ForegroundColor Red
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
        Stop-Deployment "$Title failed (exit code: $LASTEXITCODE)."
    }
}

function Require-Command {
    param([string]$Name)

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        Stop-Deployment "$Name was not found. Install it and add it to PATH."
    }
}

Set-Location $repoRoot

if (-not (Test-Path (Join-Path $repoRoot '.git'))) {
    Stop-Deployment 'This directory is not a Git repository. Run the script from the zbuild project.'
}

if (-not (Test-Path (Join-Path $repoRoot 'package-lock.json'))) {
    Stop-Deployment 'package-lock.json was not found; npm ci cannot run safely.'
}

Require-Command 'git'
Require-Command 'node'
Require-Command 'npm'

$pythonCommand = if (Get-Command 'py' -ErrorAction SilentlyContinue) {
    'py'
} elseif (Get-Command 'python' -ErrorAction SilentlyContinue) {
    'python'
} else {
    Stop-Deployment 'Neither py nor python was found. Install Python and add it to PATH.'
}

Write-Host "Project directory: $repoRoot" -ForegroundColor DarkGray

if (-not $SkipPull) {
    $changes = & git status --porcelain
    if ($LASTEXITCODE -ne 0) {
        Stop-Deployment 'Cannot read Git working tree status.'
    }
    if ($changes) {
        Stop-Deployment 'Uncommitted local changes detected. To protect server changes, the script will not pull code. Commit, stash, or clean them first.'
    }

    Invoke-Step 'Pull latest code' 'git' @('pull', '--ff-only')
} else {
    Write-Host "`n==> Skip code pull" -ForegroundColor Yellow
}

Invoke-Step 'Install Python service dependencies' $pythonCommand @('-m', 'pip', 'install', '-e', '.')
Invoke-Step 'Install frontend dependencies' 'npm' @('ci')
Invoke-Step 'Build frontend dist' 'npm' @('run', 'build')

if ($NoStart) {
    Write-Host "`nBuild complete; Web service was not started (-NoStart)." -ForegroundColor Green
    exit 0
}

Write-Host "`nBuild complete. Starting Web service: http://localhost:$Port" -ForegroundColor Green
Write-Host 'Press Ctrl+C to stop the service.' -ForegroundColor DarkGray
Invoke-Step 'Start Web service' $pythonCommand @('scripts/start_web.py', '--host', $HostAddress, '--port', $Port)

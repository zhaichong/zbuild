# check_svn.ps1
# ---------------------------------------------------------------
# Check whether zbuild can detect an SVN command-line client.
#
# Uses the project's own detection (tools.detect.find_tool), which
# covers, in order:
#   1. tools.svn configured in .zbuild-data\tool-config.json
#   2. common Windows install paths (SlikSvn / TortoiseSVN)
#   3. system PATH
#   4. bundled copy at runtime\svn\bin (packaged distribution)
#
# Usage: .\tools\check_svn.ps1
# Expected last line: SVN detection OK: <svn path> (version xxx)
# ---------------------------------------------------------------

$ErrorActionPreference = "Stop"

$ROOT           = (Get-Item (Join-Path $PSScriptRoot "..")).FullName
$RUNTIME_SVN    = Join-Path $ROOT "runtime\svn\bin\svn.exe"
$SLIKSVN_SYS    = "C:\Program Files\SlikSvn\bin\svn.exe"
$TORTOISE_SYS   = "C:\Program Files\TortoiseSVN\bin\svn.exe"

Write-Host ""
Write-Host "=== zbuild SVN Runtime Check ===" -ForegroundColor Cyan

$env:PYTHONPATH = Join-Path $ROOT "scripts"
$env:ZBUILD_DATA_DIR = Join-Path $ROOT ".zbuild-data"

# 1) Project detection logic (authoritative)
$code = @"
import sys
sys.path.insert(0, r'$env:PYTHONPATH')
from tools.bundled import bundled_svn
from tools.detect import find_tool, detect_tools
bs = bundled_svn()
ft = find_tool('svn')
print('bundled_svn =', bs)
print('find_tool   =', ft)
d = detect_tools().get('svn', {})
print('version     =', d.get('version'))
if bs or ft:
    print('SVN detection OK')
else:
    print('SVN detection FAILED')
    sys.exit(1)
"@
py -c $code
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=== SVN detection OK; restart the zbuild web service and the WARN is gone ===" -ForegroundColor Green
    exit 0
}

# 2) Diagnostics when detection fails
Write-Host ""
Write-Host "[FAIL] SVN not detected by the project." -ForegroundColor Red
foreach ($cand in @($RUNTIME_SVN, $SLIKSVN_SYS, $TORTOISE_SYS)) {
    if (Test-Path $cand) {
        Write-Host "       candidate exists but was not picked up: $cand" -ForegroundColor Yellow
        Write-Host "       check tools.svn in .zbuild-data\tool-config.json" -ForegroundColor Yellow
    }
}
Write-Host ""
Write-Host "How to install SVN:" -ForegroundColor Cyan
Write-Host "  A. System-wide: install SlikSvn (C:\Program Files\SlikSvn\bin\svn.exe)" -ForegroundColor Gray
Write-Host "  B. Project-local: copy svn.exe + all dlls into $RUNTIME_SVN" -ForegroundColor Gray
Write-Host "     (see runtime\svn\README.txt)" -ForegroundColor Gray
exit 1

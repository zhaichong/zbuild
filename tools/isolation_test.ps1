# isolation_test.ps1  (PS5 compatible, simplified)
param()
$ErrorActionPreference = "Continue"

# ── 根目录 ────────────────────────────────────────────────────────────────────
$ROOT = (Get-Item (Join-Path $PSScriptRoot "..")).FullName
$SCRIPTS = "$ROOT\scripts"
$RUNNER  = "$SCRIPTS\electron_runner.py"

Write-Host ""
Write-Host "=== Isolation Test ===" -ForegroundColor Cyan
Write-Host "Root: $ROOT"

$PASS = 0; $FAIL = 0

# ── 找到 runtime 里的 Python ──────────────────────────────────────────────────
$BUNDLED_PY   = "$ROOT\runtime\python\python.exe"
$USE_PY_ARGS  = $false

if (Test-Path $BUNDLED_PY) {
    Write-Host "[OK]   Bundled Python : $BUNDLED_PY" -ForegroundColor Green
} else {
    Write-Host "[SKIP] runtime\python\python.exe not found -- using system py" -ForegroundColor Yellow
    $BUNDLED_PY  = "py"
    $USE_PY_ARGS = $true
}

# ── runtime/node ─────────────────────────────────────────────────────────────
$RUNTIME_NODE = "$ROOT\runtime\node"
if (Test-Path $RUNTIME_NODE) {
    Write-Host "[OK]   Bundled Node   : $RUNTIME_NODE" -ForegroundColor Green
} else {
    Write-Host "[WARN] runtime\node not found" -ForegroundColor Yellow
    $RUNTIME_NODE = ""
}

# ── 清洁 PATH（剥除系统 python/git/svn/node 路径）────────────────────────────
$cleanList = @()
foreach ($seg in ($env:PATH -split ';')) {
    if ($seg -and $seg -notmatch '(?i)(python|\\git|git\\|tortoiseSVN|sliksvn|\\svn|nodejs|\\node)') {
        $cleanList += $seg
    }
}
if ($RUNTIME_NODE) { $cleanList = @($RUNTIME_NODE) + $cleanList }
$CLEAN_PATH = $cleanList -join ';'

Write-Host "PATH   : system python/git/svn/node stripped, bundled node prepended"
Write-Host ""

# ── 运行单个命令 ──────────────────────────────────────────────────────────────
function Run-Cmd {
    param([string]$Label, [string]$Cmd, [string]$StdinJson = "{}")

    Write-Host "  > $Label" -ForegroundColor Cyan

    # 构造参数列表
    if ($script:USE_PY_ARGS) {
        $argList = @("-3", $script:RUNNER, $Cmd)
    } else {
        $argList = @($script:RUNNER, $Cmd)
    }

    # 启动进程
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName               = $script:BUNDLED_PY
    $psi.Arguments              = ($argList | ForEach-Object { "`"$_`"" }) -join " "
    $psi.UseShellExecute        = $false
    $psi.RedirectStandardInput  = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.WorkingDirectory       = $script:ROOT

    # 隔离环境变量
    $psi.EnvironmentVariables["PATH"]                 = $script:CLEAN_PATH
    $psi.EnvironmentVariables["PYTHONUTF8"]           = "1"
    $psi.EnvironmentVariables["ZBUILD_DATA_DIR"]      = "$env:APPDATA\zbuild-isolation-test"
    $psi.EnvironmentVariables["ZBUILD_RESOURCES_DIR"] = "$script:ROOT\runtime"
    # 清除 venv/conda 干扰
    foreach ($k in @("VIRTUAL_ENV","CONDA_DEFAULT_ENV","PYTHONPATH","CONDA_PREFIX")) {
        if ($psi.EnvironmentVariables.ContainsKey($k)) {
            $psi.EnvironmentVariables.Remove($k)
        }
    }

    $proc = [System.Diagnostics.Process]::Start($psi)
    $proc.StandardInput.WriteLine($StdinJson)
    $proc.StandardInput.Close()
    $stdout = $proc.StandardOutput.ReadToEnd()
    $stderr = $proc.StandardError.ReadToEnd()
    $proc.WaitForExit()
    $code = $proc.ExitCode

    if ($code -eq 0) {
        Write-Host "    PASS (exit 0)" -ForegroundColor Green
        $script:PASS++
    } else {
        Write-Host "    FAIL (exit $code)" -ForegroundColor Red
        $script:FAIL++
    }

    ($stdout -split "`n") | Where-Object {$_.Trim()} | Select-Object -Last 4 | ForEach-Object {
        Write-Host "    OUT: $_" -ForegroundColor DarkGray
    }
    if ($stderr.Trim()) {
        ($stderr -split "`n") | Select-Object -First 6 | ForEach-Object {
            Write-Host "    ERR: $_" -ForegroundColor DarkYellow
        }
    }
    return $stdout
}

# ── 测试 1: import 检查 ───────────────────────────────────────────────────────
Write-Host "  > [1] syntax + import check" -ForegroundColor Cyan
$importScript = @"
import sys
sys.path.insert(0, r'$SCRIPTS')
import runner.commands
import tools.detect
import tools.bundled
import core.config
import workflow.pipeline
print('imports OK')
"@
$tmpPy = [System.IO.Path]::GetTempFileName() + ".py"
[System.IO.File]::WriteAllText($tmpPy, $importScript, [System.Text.Encoding]::UTF8)

if ($USE_PY_ARGS) { $impArgs = "-3 `"$tmpPy`"" } else { $impArgs = "`"$tmpPy`"" }

$r = Start-Process -FilePath $BUNDLED_PY -ArgumentList $impArgs `
    -NoNewWindow -Wait -PassThru `
    -RedirectStandardOutput "$env:TEMP\iso_out.txt" `
    -RedirectStandardError "$env:TEMP\iso_err.txt"

$impOut = Get-Content "$env:TEMP\iso_out.txt" -ErrorAction SilentlyContinue
$impErr = Get-Content "$env:TEMP\iso_err.txt" -ErrorAction SilentlyContinue
Remove-Item $tmpPy,"$env:TEMP\iso_out.txt","$env:TEMP\iso_err.txt" -ErrorAction SilentlyContinue

if ($r.ExitCode -eq 0) {
    Write-Host "    PASS  $impOut" -ForegroundColor Green; $PASS++
} else {
    Write-Host "    FAIL" -ForegroundColor Red
    $impErr | Select-Object -First 5 | ForEach-Object { Write-Host "    ERR: $_" -ForegroundColor DarkYellow }
    $FAIL++
}

# ── 测试 2-5: IPC 命令 ────────────────────────────────────────────────────────
Run-Cmd "[2] config"       "config"       | Out-Null
Run-Cmd "[3] detect-tools" "detect-tools" | Out-Null
Run-Cmd "[4] history-list" "history-list" | Out-Null

$discPayload = '{"root_path":"' + $ROOT.Replace('\','\\') + '"}'
$detectOut = Run-Cmd "[5] discover" "discover" $discPayload

# ── 解析 detect-tools 工具路径 ────────────────────────────────────────────────
$detectRaw = Run-Cmd "[6] detect-tools (detail)" "detect-tools" "{}"
$resultLine = ($detectRaw -split "`n") | Where-Object { $_ -match '"type".*result' } | Select-Object -Last 1
if ($resultLine) {
    try {
        $obj = ConvertFrom-Json $resultLine
        if ($obj.tools) {
            Write-Host ""
            Write-Host "  Tool detection results:" -ForegroundColor Cyan
            foreach ($t in $obj.tools.PSObject.Properties) {
                $p = $t.Value.path
                if ($p) {
                    Write-Host ("    FOUND   {0,-6} {1}" -f $t.Name, $p) -ForegroundColor Green
                } else {
                    Write-Host ("    MISSING {0}" -f $t.Name) -ForegroundColor DarkYellow
                }
            }
        }
    } catch {}
}

# ── 结果 ─────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
if ($FAIL -eq 0) {
    Write-Host "  ALL PASSED ($PASS tests)" -ForegroundColor Green
} else {
    Write-Host "  PASSED $PASS  /  FAILED $FAIL" -ForegroundColor Red
}
Write-Host "================================" -ForegroundColor Cyan
if ($FAIL -gt 0) { exit 1 }

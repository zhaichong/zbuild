# verify-packaged-runtime.ps1
# ---------------------------------------------------------------
# 校验本地 electron-builder 产物是否符合「去内置 runtime」发布要求。
#
# 用法（项目根目录）：
#   .\tools\verify-packaged-runtime.ps1
#   .\tools\verify-packaged-runtime.ps1 -AppOutDir release\win-unpacked
# ---------------------------------------------------------------

param(
    [string]$AppOutDir = ""
)

$ErrorActionPreference = "Stop"
$ROOT = (Get-Item (Join-Path $PSScriptRoot "..")).FullName

if (-not $AppOutDir) {
    $AppOutDir = Join-Path $ROOT "release\win-unpacked"
}
if (-not (Test-Path $AppOutDir)) {
    throw "AppOutDir missing: $AppOutDir (run pack/dist first)"
}
$AppOutDir = (Resolve-Path $AppOutDir).Path

Write-Host "=== verify-packaged-runtime ===" -ForegroundColor Cyan
Write-Host "AppOutDir: $AppOutDir"

# Delegate structured checks to Node (reliable asar read via npx asar).
$script = @'
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const appOut = process.argv[2];
const resources = path.join(appOut, 'resources');
const asarPath = path.join(resources, 'app.asar');
const failed = [];

function ok(msg) { console.log('OK: ' + msg); }
function fail(msg) { failed.push('FAIL: ' + msg); console.error('FAIL: ' + msg); }

if (!fs.existsSync(resources)) {
  fail('resources dir missing');
  process.exit(1);
}

if (fs.existsSync(path.join(resources, 'runtime'))) {
  fail('resources\\runtime still exists (must not be bundled)');
} else {
  ok('no resources\\runtime');
}

if (!fs.existsSync(asarPath)) {
  fail('app.asar missing');
  process.exit(1);
}
const sizeMB = (fs.statSync(asarPath).size / (1024 * 1024)).toFixed(2);
ok('app.asar present (' + sizeMB + ' MB)');

function runAsar(args) {
  return spawnSync('npx', ['--yes', 'asar', ...args], {
    encoding: 'utf8',
    shell: true,
    windowsHide: true,
  });
}

const list = runAsar(['list', asarPath]);
if (list.status !== 0) {
  fail('asar list failed: ' + (list.stderr || list.stdout || list.status));
  process.exit(1);
}
const listing = String(list.stdout || '');
const need = [
  'electron/runtime-manifest.json',
  'electron/preload-setup.js',
  'electron/runtime-setup.js',
  'dist/setup.html',
  'dist/recovery.html',
];
for (const n of need) {
  const slash = n.replace(/\\/g, '/');
  const back = n.replace(/\//g, '\\');
  if (!listing.includes(slash) && !listing.includes(back) && !listing.includes('\\' + back) && !listing.includes('/' + slash)) {
    // asar list often prints \electron\runtime-manifest.json
    const needle = back.startsWith('\\') ? back : '\\' + back;
    if (!listing.includes(needle) && !listing.toLowerCase().includes(n.split('/').pop().toLowerCase() === 'runtime-manifest.json' ? 'runtime-manifest' : n)) {
      // looser check
      const base = path.posix.basename(slash);
      if (!listing.includes(base)) fail('asar missing ' + n);
      else ok('asar has ' + n);
    } else {
      ok('asar has ' + n);
    }
  } else {
    ok('asar has ' + n);
  }
}

// Extract manifest via full extract of a temp dir (extract-file path quirks on Windows)
const tmp = fs.mkdtempSync(path.join(require('os').tmpdir(), 'zbuild-asar-'));
const extract = runAsar(['extract', asarPath, tmp]);
if (extract.status !== 0) {
  fail('asar extract failed: ' + (extract.stderr || extract.stdout || extract.status));
  process.exit(1);
}
const manifestPath = path.join(tmp, 'electron', 'runtime-manifest.json');
if (!fs.existsSync(manifestPath)) {
  fail('extracted manifest missing at electron/runtime-manifest.json');
} else {
  const m = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  const py = m.resources && m.resources.python;
  const node = m.resources && m.resources.node;
  if (!py || !/^[a-f0-9]{64}$/i.test(py.sha256 || '')) fail('packed python.sha256 empty/invalid');
  else ok('python.sha256 locked');
  if (!py || !/^https:\/\//i.test(py.primary || '')) fail('packed python.primary must be HTTPS');
  else ok('python.primary HTTPS');
  if (!node || !/^[a-f0-9]{64}$/i.test(node.sha256 || '')) fail('packed node.sha256 empty/invalid');
  else ok('node.sha256 locked');
}
try { fs.rmSync(tmp, { recursive: true, force: true }); } catch (_) {}

if (failed.length) {
  console.error('\n=== VERIFY FAILED ===');
  process.exit(1);
}
console.log('\n=== VERIFY PASSED ===');
process.exit(0);
'@

$tmpJs = Join-Path $env:TEMP ("verify-packaged-runtime-" + [guid]::NewGuid().ToString() + ".js")
Set-Content -Path $tmpJs -Value $script -Encoding UTF8
try {
    & node $tmpJs $AppOutDir
    $code = $LASTEXITCODE
} finally {
    Remove-Item $tmpJs -Force -ErrorAction SilentlyContinue
}
exit $code

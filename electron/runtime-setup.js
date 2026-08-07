'use strict';
// Runtime on-demand setup.
//
// Downloads a pinned + SHA256-verified runtime ZIP to the per-user runtime root,
// verifies it, extracts via PowerShell Expand-Archive (after ZIP safety scan),
// runs a health check, then atomically swaps the final directory and writes a
// completion marker.
//
// Pure Node (no Electron dependency) so it can be unit-tested with `node --test`.

const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');
const https = require('https');
const http = require('http');
const { spawnSync } = require('child_process');

const READY_FILE = '.ready.json';
const LOCK_STALE_MS = 15 * 60 * 1000;
const MAX_REDIRECTS = 5;
const SOCKET_TIMEOUT_MS = 30000;
const IDLE_TIMEOUT_MS = 60000;
const HEALTH_TIMEOUT_MS = 60000;
const EXTRACT_TIMEOUT_MS = 5 * 60 * 1000;
const MAX_ZIP_ENTRIES = 50000;
const MAX_UNCOMPRESSED_BYTES = 800 * 1024 * 1024; // 800 MB
const SIZE_SLACK = 1.05; // allow 5% over declared Content-Length / size

function sleepSync(ms) {
  const sab = new Int32Array(new SharedArrayBuffer(4));
  Atomics.wait(sab, 0, 0, ms);
}

function abortedError() {
  const e = new Error('安装已取消');
  e.code = 'ABORTED';
  return e;
}

function throwIfAborted(signal) {
  if (signal && signal.aborted) throw abortedError();
}

// ---- Paths / config ------------------------------------------------------

function defaultRuntimeRoot(env = process.env) {
  const local = env.LOCALAPPDATA;
  if (local) return path.join(local, 'zbuild', 'runtime');
  return path.join(os.homedir(), 'zbuild-runtime');
}

function getRuntimeRoot(env = process.env) {
  return env.ZBUILD_RUNTIME_ROOT || defaultRuntimeRoot(env);
}

function runtimeConfigPath(env = process.env) {
  return path.join(path.dirname(getRuntimeRoot(env)), 'runtime-config.json');
}

function loadRuntimeConfig(env = process.env) {
  const cfg = { mirrorBase: null, overridePython: null, overrideNode: null };
  if (env.ZBUILD_RUNTIME_MIRROR && /^https:\/\//i.test(env.ZBUILD_RUNTIME_MIRROR)) {
    cfg.mirrorBase = env.ZBUILD_RUNTIME_MIRROR;
  }
  try {
    const parsed = JSON.parse(fs.readFileSync(runtimeConfigPath(env), 'utf8'));
    if (parsed && typeof parsed.mirrorBase === 'string' && /^https:\/\//i.test(parsed.mirrorBase)) {
      cfg.mirrorBase = parsed.mirrorBase;
    }
    if (parsed && typeof parsed.overridePython === 'string') cfg.overridePython = parsed.overridePython;
    if (parsed && typeof parsed.overrideNode === 'string') cfg.overrideNode = parsed.overrideNode;
  } catch (_) {}
  return cfg;
}

function writeRuntimeConfig(patch, env = process.env) {
  const file = runtimeConfigPath(env);
  let cfg = {};
  try { cfg = JSON.parse(fs.readFileSync(file, 'utf8')); } catch (_) {}
  Object.assign(cfg, patch);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const tmp = file + '.tmp-' + process.pid + '-' + Date.now();
  fs.writeFileSync(tmp, JSON.stringify(cfg, null, 2), 'utf8');
  try {
    fs.renameSync(tmp, file);
  } catch (err) {
    // Windows: target may exist; replace via unlink + rename
    try { fs.unlinkSync(file); } catch (_) {}
    fs.renameSync(tmp, file);
  }
  return cfg;
}

// ---- Manifest ------------------------------------------------------------

function loadManifest(manifestPath) {
  const raw = fs.readFileSync(manifestPath, 'utf8');
  const m = JSON.parse(raw);
  if (!m.resources || typeof m.resources !== 'object') throw new Error('manifest 缺少 resources');
  return m;
}

function isAllowedDownloadUrl(urlString, { allowHttpLocalhost = true } = {}) {
  let u;
  try { u = new URL(urlString); } catch (_) { return false; }
  if (u.protocol === 'https:') return true;
  if (
    allowHttpLocalhost &&
    u.protocol === 'http:' &&
    (u.hostname === '127.0.0.1' || u.hostname === 'localhost' || u.hostname === '::1')
  ) {
    return true;
  }
  return false;
}

function validateResource(resource, options = {}) {
  if (!resource || !resource.file) throw new Error('manifest 资源缺少 file');
  if (!/^[a-f0-9]{64}$/i.test(resource.sha256 || '')) {
    throw new Error(`资源 ${resource.file} 未锁定 SHA256，已拒绝下载`);
  }
  if (!Array.isArray(resource.healthCheck) || resource.healthCheck.length === 0) {
    throw new Error(`资源 ${resource.file} 缺少健康检查命令`);
  }
  const primaryOk = resource.primary && isAllowedDownloadUrl(resource.primary, options);
  const backupOk = resource.backup && isAllowedDownloadUrl(resource.backup, options);
  if (!primaryOk && !backupOk) {
    throw new Error(`资源 ${resource.file} 缺少可用的 HTTPS 下载源`);
  }
  if (resource.primary && !isAllowedDownloadUrl(resource.primary, options)) {
    throw new Error(`资源 ${resource.file} primary 必须为 HTTPS`);
  }
  if (resource.backup && !isAllowedDownloadUrl(resource.backup, options)) {
    throw new Error(`资源 ${resource.file} backup 必须为 HTTPS`);
  }
}

function resolveDownloadUrls(resource, cfg) {
  const urls = [];
  if (cfg.mirrorBase && resource.path) {
    const base = cfg.mirrorBase.replace(/\/+$/, '');
    if (isAllowedDownloadUrl(base + '/')) urls.push(base + '/' + resource.path);
  }
  if (resource.primary) urls.push(resource.primary);
  if (resource.backup) urls.push(resource.backup);
  return urls;
}

// ---- Download ------------------------------------------------------------

function downloadFile(url, destPath, options = {}) {
  const {
    onProgress,
    redirectLimit = MAX_REDIRECTS,
    timeoutMs = SOCKET_TIMEOUT_MS,
    idleTimeoutMs = IDLE_TIMEOUT_MS,
    maxBytes = null,
    signal = null,
    allowHttpLocalhost = true,
  } = options;

  return new Promise((resolve, reject) => {
    if (signal && signal.aborted) { reject(abortedError()); return; }
    if (!isAllowedDownloadUrl(url, { allowHttpLocalhost })) {
      reject(new Error('仅允许 HTTPS 下载（localhost 测试除外）: ' + url));
      return;
    }
    let parsed;
    try { parsed = new URL(url); } catch (err) { reject(new Error('无效的下载地址: ' + err.message)); return; }
    const mod = parsed.protocol === 'https:' ? https : http;

    let settled = false;
    let idleTimer = null;
    let req = null;
    let ws = null;

    const cleanup = () => {
      if (idleTimer) { clearTimeout(idleTimer); idleTimer = null; }
      if (signal) signal.removeEventListener('abort', onAbort);
    };
    const fail = (err) => {
      if (settled) return;
      settled = true;
      cleanup();
      try { if (req) req.destroy(); } catch (_) {}
      try { if (ws) ws.destroy(); } catch (_) {}
      try { fs.unlinkSync(destPath); } catch (_) {}
      reject(err);
    };
    const succeed = (value) => {
      if (settled) return;
      settled = true;
      cleanup();
      resolve(value);
    };
    const onAbort = () => fail(abortedError());
    if (signal) signal.addEventListener('abort', onAbort, { once: true });

    const resetIdle = () => {
      if (idleTimer) clearTimeout(idleTimer);
      idleTimer = setTimeout(() => fail(new Error('下载空闲超时')), idleTimeoutMs);
    };

    req = mod.get(url, (res) => {
      const status = res.statusCode || 0;
      if (status >= 300 && status < 400) {
        res.resume();
        req.destroy();
        if (redirectLimit <= 0) { fail(new Error('重定向次数过多')); return; }
        const loc = res.headers.location;
        if (!loc) { fail(new Error('重定向缺少 Location')); return; }
        let next;
        try {
          next = new URL(loc, url).toString();
        } catch (_) { fail(new Error('不允许的重定向目标')); return; }
        // Forbid HTTPS → HTTP downgrade (and any non-allowed scheme).
        if (!isAllowedDownloadUrl(next, { allowHttpLocalhost })) {
          fail(new Error('禁止重定向到非 HTTPS 地址: ' + next));
          return;
        }
        cleanup();
        if (signal) signal.removeEventListener('abort', onAbort);
        downloadFile(next, destPath, {
          onProgress, redirectLimit: redirectLimit - 1, timeoutMs, idleTimeoutMs, maxBytes, signal, allowHttpLocalhost,
        }).then(succeed, fail);
        return;
      }
      if (status !== 200) {
        res.resume();
        fail(new Error(`下载失败: HTTP ${status}`));
        return;
      }
      const total = Number(res.headers['content-length']) || 0;
      const hardMax = maxBytes != null
        ? maxBytes
        : (total > 0 ? Math.ceil(total * SIZE_SLACK) : null);
      let received = 0;
      req.setTimeout(0);
      resetIdle();
      ws = fs.createWriteStream(destPath);
      res.on('error', (err) => fail(err));
      res.on('data', (chunk) => {
        received += chunk.length;
        if (hardMax != null && received > hardMax) {
          fail(new Error(`下载超过大小限制 (${hardMax} bytes)`));
          return;
        }
        resetIdle();
        if (onProgress) onProgress({ downloaded: received, total: total || (maxBytes || 0) });
      });
      res.pipe(ws);
      ws.on('error', (err) => fail(err));
      ws.on('finish', () => {
        if (settled) return;
        cleanup();
        ws.close(() => succeed({ downloaded: received, total }));
      });
    });
    req.setTimeout(timeoutMs, () => fail(new Error('下载超时')));
    req.on('error', (err) => fail(err));
  });
}

// ---- Verification / extract / health -------------------------------------

function computeSha256(filePath) {
  const hash = crypto.createHash('sha256');
  const fd = fs.openSync(filePath, 'r');
  const buf = Buffer.alloc(1024 * 1024);
  let bytes;
  try {
    while ((bytes = fs.readSync(fd, buf, 0, buf.length, null)) > 0) hash.update(buf.subarray(0, bytes));
  } finally {
    fs.closeSync(fd);
  }
  return hash.digest('hex');
}

/**
 * Inspect a ZIP for path traversal and zip-bomb indicators before Expand-Archive.
 * Uses PowerShell + System.IO.Compression (available on Windows).
 */
function inspectZip(zipPath, options = {}) {
  const maxEntries = options.maxEntries || MAX_ZIP_ENTRIES;
  const maxUncompressed = options.maxUncompressed || MAX_UNCOMPRESSED_BYTES;
  const script = `
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zipPath = '${String(zipPath).replace(/'/g, "''")}'
$maxEntries = ${maxEntries}
$maxUncompressed = ${maxUncompressed}
$zip = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
try {
  $count = 0
  $total = [int64]0
  foreach ($e in $zip.Entries) {
    $count++
    if ($count -gt $maxEntries) { throw "ZIP entry count exceeds limit ($maxEntries)" }
    $name = $e.FullName -replace '\\\\','/'
    if ($name -match '(^|/|\\\\)\\.\\.(/|\\\\|$)' -or $name -match '^[A-Za-z]:' -or $name.StartsWith('/') -or $name.StartsWith('\\\\')) {
      throw "ZIP path traversal rejected: $name"
    }
    $total += [int64]$e.Length
    if ($total -gt $maxUncompressed) { throw "ZIP uncompressed size exceeds limit ($maxUncompressed)" }
  }
  Write-Output ("OK entries=" + $count + " bytes=" + $total)
} finally {
  $zip.Dispose()
}
`.trim();
  const r = spawnSync('powershell.exe', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', script], {
    windowsHide: true,
    timeout: EXTRACT_TIMEOUT_MS,
    encoding: 'utf8',
  });
  if (r.error) throw new Error('ZIP 检查失败: ' + r.error.message);
  if (r.status !== 0) throw new Error('ZIP 检查失败: ' + String(r.stderr || r.stdout || 'exit ' + r.status).trim());
  return String(r.stdout || '').trim();
}

function extractZip(zipPath, destDir, options = {}) {
  if (options.skipInspect !== true) {
    inspectZip(zipPath, options);
  }
  fs.mkdirSync(destDir, { recursive: true });
  const script = "$ErrorActionPreference='Stop'; " +
    "Expand-Archive -LiteralPath '" + String(zipPath).replace(/'/g, "''") +
    "' -DestinationPath '" + String(destDir).replace(/'/g, "''") + "' -Force";
  const r = spawnSync('powershell.exe', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', script], {
    windowsHide: true,
    timeout: EXTRACT_TIMEOUT_MS,
    encoding: 'utf8',
  });
  if (r.error) throw new Error('解压失败: ' + r.error.message);
  if (r.status !== 0) throw new Error('解压失败: ' + String(r.stderr || r.stdout || 'exit ' + r.status).trim());
}

function runHealthCheck(dir, healthCheck) {
  const [exeRel, ...args] = healthCheck;
  const exePath = path.join(dir, ...String(exeRel).split('/'));
  if (!fs.existsSync(exePath)) return { ok: false, error: '缺少 ' + exeRel };
  // Resolve relative CLI args (e.g. node_modules/npm/bin/npm-cli.js) against the
  // install dir, because spawnSync runs with the caller's cwd, not the exe's.
  // Only resolve when the joined path actually exists on disk — flags like /D must
  // not be mangled.
  const resolvedArgs = args.map((a) => {
    const s = String(a);
    if (!s.includes('/') && !s.includes('\\')) return s;
    const joined = path.join(dir, ...s.split(/[\\/]+/));
    return fs.existsSync(joined) ? joined : s;
  });
  const r = spawnSync(exePath, resolvedArgs, { windowsHide: true, timeout: HEALTH_TIMEOUT_MS, encoding: 'utf8' });
  if (r.error) return { ok: false, error: r.error.message };
  if (r.status !== 0) return { ok: false, error: String(r.stderr || r.stdout || 'exit ' + r.status).trim() };
  return { ok: true, output: String(r.stdout || '').trim() };
}

function checkVersion(dir, healthVersion, expectedVersion) {
  if (!expectedVersion || !Array.isArray(healthVersion)) return { ok: true };
  const [exeRel, ...args] = healthVersion;
  const exePath = path.join(dir, ...String(exeRel).split('/'));
  if (!fs.existsSync(exePath)) return { ok: false, error: '缺少 ' + exeRel };
  const r = spawnSync(exePath, args, { windowsHide: true, timeout: HEALTH_TIMEOUT_MS, encoding: 'utf8' });
  if (r.status !== 0) return { ok: false, error: String(r.stderr || r.stdout || 'version check failed').trim() };
  const match = String(r.stdout || '').match(/\d+\.\d+\.\d+/);
  if (!match) return { ok: false, error: '无法识别版本: ' + String(r.stdout || r.stderr).trim() };
  if (!String(expectedVersion).startsWith(match[0])) {
    return { ok: false, error: `版本不匹配: 期望 ${expectedVersion}, 实际 ${match[0]}` };
  }
  return { ok: true, version: match[0] };
}

// ---- Lock ----------------------------------------------------------------

function isPidRunning(pid) {
  if (!Number.isInteger(pid) || pid <= 0) return false;
  const r = spawnSync('tasklist', ['/FI', `PID eq ${pid}`, '/FO', 'CSV', '/NH'], {
    windowsHide: true,
    encoding: 'utf8',
    timeout: 10000,
  });
  // If tasklist itself fails, treat as "unknown / still held" (do not steal).
  if (r.error || r.status !== 0) return true;
  return String(r.stdout).includes(`"${pid}"`);
}

function acquireLock(root, name, options = {}) {
  const { timeoutMs = 60 * 1000, now = Date.now, pid = process.pid } = options;
  const token = crypto.randomBytes(16).toString('hex');
  fs.mkdirSync(root, { recursive: true });
  const lockPath = path.join(root, `.install-${name}.lock`);
  const start = now();
  for (;;) {
    try {
      const fd = fs.openSync(lockPath, 'wx');
      try {
        fs.writeSync(fd, JSON.stringify({ pid, token, at: new Date(now()).toISOString() }));
      } finally {
        fs.closeSync(fd);
      }
      return { path: lockPath, pid, token };
    } catch (err) {
      if (err.code !== 'EEXIST') throw err;
      let stale = false;
      try {
        const st = fs.statSync(lockPath);
        const content = JSON.parse(fs.readFileSync(lockPath, 'utf8'));
        const ageStale = (now() - st.mtimeMs) > LOCK_STALE_MS;
        const ownerRunning = Number.isInteger(content.pid) && isPidRunning(content.pid);
        // Only steal when clearly stale by age, or owner PID is not running.
        // When tasklist fails, isPidRunning returns true → do not steal.
        stale = ageStale || !ownerRunning;
      } catch (_) {
        stale = true;
      }
      if (stale) {
        // Best-effort steal: rename away then create. Not fully atomic on all FS,
        // but reduces the unlink-then-create race window.
        const stalePath = lockPath + '.stale-' + now() + '-' + pid;
        try {
          fs.renameSync(lockPath, stalePath);
          try { fs.unlinkSync(stalePath); } catch (_) {}
        } catch (_) {
          try { fs.unlinkSync(lockPath); } catch (_) {}
        }
        continue;
      }
      if (now() - start > timeoutMs) {
        const e = new Error('另一个运行时安装正在进行，请稍后重试');
        e.code = 'LOCK_TIMEOUT';
        throw e;
      }
      sleepSync(500);
    }
  }
}

function releaseLock(lockInfo) {
  if (!lockInfo || !lockInfo.path) return;
  try {
    const raw = fs.readFileSync(lockInfo.path, 'utf8');
    const content = JSON.parse(raw);
    // Only release if we still own the lock (token match). Prevents a late
    // release from deleting a lock taken by a newer installer after PID reuse.
    if (lockInfo.token && content.token && content.token !== lockInfo.token) return;
    if (lockInfo.pid && content.pid && content.pid !== lockInfo.pid) return;
  } catch (_) {
    // If we cannot read/parse, still try to remove only when path was ours.
  }
  try { fs.unlinkSync(lockInfo.path); } catch (_) {}
}

// ---- Install steps -------------------------------------------------------

/**
 * Marker + executable presence. Does NOT run health check (fast path).
 * Use isRuntimeReady for full validation including health.
 */
function isInstalled(root, name, resource) {
  let marker = null;
  try { marker = JSON.parse(fs.readFileSync(path.join(root, name, READY_FILE), 'utf8')); } catch (_) {}
  if (!marker) return false;
  if (marker.version !== resource.version) return false;
  if (String(marker.sha256 || '').toLowerCase() !== String(resource.sha256 || '').toLowerCase()) return false;
  const [exeRel] = resource.healthCheck || [];
  if (!exeRel) return false;
  return fs.existsSync(path.join(root, name, ...String(exeRel).split('/')));
}

/**
 * Full readiness: marker matches manifest, executable exists, health + version pass.
 * Prevents forged .ready.json + placeholder exe from skipping reinstall.
 */
function isRuntimeReady(root, name, resource, deps = {}) {
  if (!isInstalled(root, name, resource)) return false;
  const health = deps.runHealthCheck || runHealthCheck;
  const versionCheck = deps.checkVersion || checkVersion;
  const dir = path.join(root, name);
  const hc = health(dir, resource.healthCheck);
  if (!hc.ok) return false;
  const vc = versionCheck(dir, resource.healthVersion, resource.version);
  return !!vc.ok;
}

function atomicInstall(stagingDir, finalDir) {
  fs.mkdirSync(path.dirname(finalDir), { recursive: true });
  const backupDir = finalDir + '.old-' + Date.now();
  let movedOld = false;
  if (fs.existsSync(finalDir)) {
    fs.renameSync(finalDir, backupDir);
    movedOld = true;
  }
  try {
    fs.renameSync(stagingDir, finalDir);
  } catch (err) {
    if (movedOld && fs.existsSync(backupDir) && !fs.existsSync(finalDir)) {
      try { fs.renameSync(backupDir, finalDir); } catch (_) {}
    }
    throw err;
  }
  if (movedOld) {
    try { fs.rmSync(backupDir, { recursive: true, force: true }); } catch (_) {}
  }
}

function writeReady(root, name, resource) {
  const dir = path.join(root, name);
  fs.mkdirSync(dir, { recursive: true });
  const marker = {
    name,
    version: resource.version,
    sha256: resource.sha256,
    installedAt: new Date().toISOString(),
  };
  const file = path.join(dir, READY_FILE);
  const tmp = file + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(marker, null, 2), 'utf8');
  try {
    fs.renameSync(tmp, file);
  } catch (_) {
    try { fs.unlinkSync(file); } catch (_) {}
    fs.renameSync(tmp, file);
  }
  return marker;
}

function cleanupDir(dir) {
  if (!dir) return;
  try { fs.rmSync(dir, { recursive: true, force: true }); } catch (_) {}
}

// Some official ZIPs (e.g. node-v14.21.3-win-x64.zip) extract into a single
// top-level versioned folder. Move its contents up so the install layout is flat
// (install-dir\node.exe), matching what the resolution layers expect.
function flattenTopLevelDir(dir) {
  let entries = [];
  try { entries = fs.readdirSync(dir); } catch (_) { return; }
  if (entries.length !== 1) return;
  const only = path.join(dir, entries[0]);
  let st = null;
  try { st = fs.statSync(only); } catch (_) { return; }
  if (!st.isDirectory()) return;
  let files = [];
  try { files = fs.readdirSync(only); } catch (_) { return; }
  for (const f of files) {
    fs.renameSync(path.join(only, f), path.join(dir, f));
  }
  try { fs.rmdirSync(only); } catch (_) {}
}

// ---- Orchestrator --------------------------------------------------------

async function ensureRuntime(name, options = {}) {
  const {
    manifestPath,
    root,
    env = process.env,
    onProgress,
    deps = {},
    lockTimeoutMs = 60 * 1000,
    signal = null,
  } = options;
  throwIfAborted(signal);
  const manifest = loadManifest(manifestPath);
  const resource = manifest.resources[name];
  if (!resource) throw new Error('未知运行时: ' + name);
  validateResource(resource);

  const runtimeRoot = root || getRuntimeRoot(env);
  const emit = (phase, data = {}) => {
    if (onProgress) onProgress({ name, phase, resource: resource.file, label: resource.label, ...data });
  };

  const healthFn = deps.runHealthCheck || runHealthCheck;
  const versionFn = deps.checkVersion || checkVersion;

  // Full readiness: marker + health. Reinstall on version/hash/health mismatch.
  if (isRuntimeReady(runtimeRoot, name, resource, { runHealthCheck: healthFn, checkVersion: versionFn })) {
    emit('done', { path: path.join(runtimeRoot, name) });
    return { ok: true, path: path.join(runtimeRoot, name), skipped: true };
  }

  const download = deps.downloadFile || downloadFile;
  const extract = deps.extractZip || extractZip;
  const sha256 = deps.computeSha256 || computeSha256;
  const acquire = deps.acquireLock || acquireLock;
  const release = deps.releaseLock || releaseLock;

  emit('starting');
  const cfg = loadRuntimeConfig(env);
  let lockInfo = null;
  try {
    lockInfo = acquire(runtimeRoot, name, { timeoutMs: lockTimeoutMs });
  } catch (err) {
    release(lockInfo);
    throw err;
  }

  // Another installer may have finished while we waited for the lock.
  if (isRuntimeReady(runtimeRoot, name, resource, { runHealthCheck: healthFn, checkVersion: versionFn })) {
    release(lockInfo);
    emit('done', { path: path.join(runtimeRoot, name) });
    return { ok: true, path: path.join(runtimeRoot, name), skipped: true };
  }

  const stagingDir = path.join(runtimeRoot, `.staging-${name}-${process.pid}-${Date.now()}`);
  const zipPath = stagingDir + '.zip';
  const finalDir = path.join(runtimeRoot, name);

  try {
    throwIfAborted(signal);
    fs.mkdirSync(runtimeRoot, { recursive: true });
    fs.mkdirSync(stagingDir, { recursive: true });

    const urls = resolveDownloadUrls(resource, cfg).filter((u) => isAllowedDownloadUrl(u));
    if (!urls.length) throw new Error('没有可用的下载源');

    const maxBytes = resource.size
      ? Math.ceil(Number(resource.size) * SIZE_SLACK)
      : MAX_UNCOMPRESSED_BYTES;

    let lastErr = null;
    let downloaded = false;
    for (const url of urls) {
      throwIfAborted(signal);
      emit('downloading', { url });
      try {
        await download(url, zipPath, {
          signal,
          maxBytes,
          onProgress: (p) => emit('downloading', {
            url,
            downloaded: p.downloaded,
            total: p.total || resource.size || 0,
          }),
        });
        downloaded = true;
        break;
      } catch (err) {
        if (err && err.code === 'ABORTED') throw err;
        lastErr = err;
        cleanupDir(zipPath);
        emit('retry-source', { url, error: err.message });
      }
    }
    if (!downloaded) {
      throw new Error('所有下载源均失败: ' + ((lastErr && lastErr.message) || ''));
    }

    throwIfAborted(signal);
    emit('verifying');
    const actual = sha256(zipPath);
    if (String(actual).toLowerCase() !== String(resource.sha256).toLowerCase()) {
      throw new Error(`SHA256 校验失败: 期望 ${resource.sha256}, 实际 ${actual}`);
    }

    throwIfAborted(signal);
    emit('extracting');
    extract(zipPath, stagingDir, deps.extractOptions || {});
    cleanupDir(zipPath);
    flattenTopLevelDir(stagingDir);

    throwIfAborted(signal);
    emit('health-check');
    const healthResult = healthFn(stagingDir, resource.healthCheck);
    if (!healthResult.ok) throw new Error('运行环境健康检查失败: ' + healthResult.error);
    const verResult = versionFn(stagingDir, resource.healthVersion, resource.version);
    if (!verResult.ok) throw new Error('运行环境版本校验失败: ' + verResult.error);

    throwIfAborted(signal);
    emit('installing');
    atomicInstall(stagingDir, finalDir);
    writeReady(runtimeRoot, name, resource);
    emit('done', { path: finalDir });
    return { ok: true, path: finalDir };
  } finally {
    cleanupDir(stagingDir);
    cleanupDir(zipPath);
    release(lockInfo);
  }
}

module.exports = {
  ensureRuntime,
  isInstalled,
  isRuntimeReady,
  loadManifest,
  validateResource,
  resolveDownloadUrls,
  downloadFile,
  computeSha256,
  extractZip,
  inspectZip,
  runHealthCheck,
  checkVersion,
  acquireLock,
  releaseLock,
  atomicInstall,
  writeReady,
  flattenTopLevelDir,
  getRuntimeRoot,
  defaultRuntimeRoot,
  runtimeConfigPath,
  loadRuntimeConfig,
  writeRuntimeConfig,
  isAllowedDownloadUrl,
  READY_FILE,
  LOCK_STALE_MS,
};

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const http = require('http');
const crypto = require('crypto');
const {
  ensureRuntime,
  resolveDownloadUrls,
  validateResource,
  downloadFile,
  computeSha256,
  acquireLock,
  releaseLock,
  isInstalled,
  isRuntimeReady,
  atomicInstall,
  isAllowedDownloadUrl,
  validateOverrideExecutable,
  writeRuntimeConfig,
  loadRuntimeConfig,
  runtimeConfigPath,
} = require('./runtime-setup');

function tmpDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'zbuild-setup-test-'));
}

function makeManifest(resource) {
  return {
    version: 1,
    platform: 'win32-x64',
    resources: {
      node: {
        label: 'Node.js',
        version: '14.21.3',
        file: 'node.zip',
        size: null,
        sha256: '0'.repeat(64),
        path: 'node/node.zip',
        primary: 'http://127.0.0.1:1/nope.zip',
        backup: 'http://127.0.0.1:1/nope.zip',
        healthCheck: ['node.exe', '--version'],
        healthVersion: ['node.exe', '--version'],
        ...resource,
      },
    },
  };
}

function startServer(buildResponse) {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      const r = buildResponse(req.url);
      res.writeHead(r.status, r.headers || {});
      if (r.body) res.write(r.body);
      res.end();
    });
    server.listen(0, '127.0.0.1', () => resolve(server));
  });
}

function okDeps() {
  return {
    extractZip: (_zip, dir) => {
      fs.mkdirSync(dir, { recursive: true });
      fs.writeFileSync(path.join(dir, 'node.exe'), 'fake');
    },
    runHealthCheck: () => ({ ok: true }),
    checkVersion: () => ({ ok: true }),
  };
}

function writeManifest(root, manifest) {
  const file = path.join(root, 'runtime-manifest.json');
  fs.writeFileSync(file, JSON.stringify(manifest));
  return file;
}

test('resolveDownloadUrls: mirror base first, then primary, then backup', () => {
  const urls = resolveDownloadUrls(
    { path: 'node/v14/node.zip', primary: 'https://p/node.zip', backup: 'https://b/node.zip' },
    { mirrorBase: 'https://mirror.example.com/' },
  );
  assert.deepEqual(urls, [
    'https://mirror.example.com/node/v14/node.zip',
    'https://p/node.zip',
    'https://b/node.zip',
  ]);
});

test('resolveDownloadUrls de-dupes identical primary and backup', () => {
  const urls = resolveDownloadUrls(
    { path: 'p.zip', primary: 'https://same/x.zip', backup: 'https://same/x.zip' },
    {},
  );
  assert.deepEqual(urls, ['https://same/x.zip']);
});

test('validateOverrideExecutable rejects missing path', () => {
  const r = validateOverrideExecutable('python', 'C:\\no\\such\\python.exe', '3.11.9');
  assert.equal(r.ok, false);
});

test('validateOverrideExecutable accepts real dev python when present', () => {
  const py = path.join(__dirname, '..', 'runtime', 'python', 'python.exe');
  if (!fs.existsSync(py)) return;
  const r = validateOverrideExecutable('python', py, '3.11.9');
  assert.equal(r.ok, true, r.error);
});

test('validateResource rejects a resource without a locked SHA256', () => {
  assert.throws(
    () => validateResource({ file: 'x.zip', healthCheck: ['x'], primary: 'https://a/x', backup: 'https://b/x' }),
    /未锁定 SHA256/,
  );
});

test('validateResource rejects missing download sources', () => {
  assert.throws(
    () => validateResource({ file: 'x.zip', sha256: 'a'.repeat(64), healthCheck: ['x'] }),
    /缺少可用的 HTTPS/,
  );
});

test('validateResource rejects non-HTTPS primary', () => {
  assert.throws(
    () => validateResource({
      file: 'x.zip', sha256: 'a'.repeat(64), healthCheck: ['x'],
      primary: 'http://evil.example/x.zip', backup: '',
    }),
    /缺少可用的 HTTPS|必须为 HTTPS/,
  );
});

test('isAllowedDownloadUrl allows https and localhost http only', () => {
  assert.equal(isAllowedDownloadUrl('https://cdn.example/a.zip'), true);
  assert.equal(isAllowedDownloadUrl('http://127.0.0.1:9/a.zip'), true);
  assert.equal(isAllowedDownloadUrl('http://evil.example/a.zip'), false);
  assert.equal(isAllowedDownloadUrl('ftp://x/a'), false);
});

test('downloadFile follows redirects and writes bytes', async () => {
  const body = Buffer.from('hello-runtime');
  const server = await startServer((url) => {
    if (url === '/start') return { status: 302, headers: { location: '/file' } };
    return { status: 200, body };
  });
  try {
    const dest = path.join(tmpDir(), 'out.zip');
    const res = await downloadFile(`http://127.0.0.1:${server.address().port}/start`, dest);
    assert.equal(fs.readFileSync(dest, 'utf8'), 'hello-runtime');
    assert.equal(res.downloaded, body.length);
  } finally {
    server.close();
  }
});

test('downloadFile rejects HTTPS→HTTP downgrade', async () => {
  // Simulate by pointing an http localhost redirect target that claims to be
  // absolute http to a non-localhost host — use custom Location.
  const server = await startServer(() => ({
    status: 302,
    headers: { location: 'http://evil.example.com/payload.zip' },
  }));
  try {
    await assert.rejects(
      downloadFile(`http://127.0.0.1:${server.address().port}/start`, path.join(tmpDir(), 'o.zip')),
      /禁止重定向到非 HTTPS|仅允许 HTTPS/,
    );
  } finally {
    server.close();
  }
});

test('downloadFile enforces maxBytes', async () => {
  const body = Buffer.alloc(1000, 1);
  const server = await startServer(() => ({ status: 200, body }));
  try {
    await assert.rejects(
      downloadFile(`http://127.0.0.1:${server.address().port}/x`, path.join(tmpDir(), 'o.zip'), { maxBytes: 100 }),
      /大小限制/,
    );
  } finally {
    server.close();
  }
});

test('downloadFile rejects on non-200', async () => {
  const server = await startServer(() => ({ status: 404 }));
  try {
    await assert.rejects(
      downloadFile(`http://127.0.0.1:${server.address().port}/x`, path.join(tmpDir(), 'o.zip')),
      /HTTP 404/,
    );
  } finally {
    server.close();
  }
});

test('downloadFile aborts when signal fires', async () => {
  const server = await startServer(() => ({ status: 200, body: Buffer.alloc(10 * 1024 * 1024) }));
  try {
    const ac = new AbortController();
    const p = downloadFile(
      `http://127.0.0.1:${server.address().port}/big`,
      path.join(tmpDir(), 'o.zip'),
      { signal: ac.signal },
    );
    ac.abort();
    await assert.rejects(p, (err) => err.code === 'ABORTED');
  } finally {
    server.close();
  }
});

test('computeSha256 matches crypto', () => {
  const f = path.join(tmpDir(), 'f');
  fs.writeFileSync(f, 'zbuild');
  assert.equal(computeSha256(f), crypto.createHash('sha256').update('zbuild').digest('hex'));
});

test('ensureRuntime installs, verifies, and writes a marker', async () => {
  const body = crypto.randomBytes(2048);
  const sha = crypto.createHash('sha256').update(body).digest('hex');
  const manifest = makeManifest({ sha256: sha });
  const root = tmpDir();
  const server = await startServer(() => ({ status: 200, body }));
  try {
    const phases = [];
    const res = await ensureRuntime('node', {
      manifestPath: writeManifest(root, manifest),
      root,
      onProgress: (s) => phases.push(s.phase),
      deps: {
        ...okDeps(),
        downloadFile: (u, dest) => { fs.writeFileSync(dest, body); return { downloaded: body.length }; },
      },
    });
    assert.equal(res.ok, true);
    assert.ok(fs.existsSync(path.join(root, 'node', 'node.exe')));
    assert.ok(fs.existsSync(path.join(root, 'node', '.ready.json')));
    assert.ok(isInstalled(root, 'node', manifest.resources.node));
    assert.ok(phases.includes('downloading'));
    assert.ok(phases.includes('verifying'));
    assert.ok(phases.includes('done'));
  } finally {
    server.close();
  }
});

test('ensureRuntime falls back to the backup source when primary fails', async () => {
  const body = Buffer.from('backup-bytes');
  const sha = crypto.createHash('sha256').update(body).digest('hex');
  const manifest = makeManifest({
    sha256: sha,
    primary: 'http://127.0.0.1:1/down.zip',
    backup: 'http://BACKUP',
  });
  // backup host is not localhost — filter will drop it unless we use localhost.
  // Use two localhost ports instead.
  const goodServer = await startServer(() => ({ status: 200, body }));
  const goodUrl = `http://127.0.0.1:${goodServer.address().port}/ok.zip`;
  const root = tmpDir();
  try {
    const result = await ensureRuntime('node', {
      manifestPath: writeManifest(root, makeManifest({
        sha256: sha,
        primary: 'http://127.0.0.1:1/down.zip',
        backup: goodUrl,
      })),
      root,
      deps: okDeps(),
    });
    assert.equal(result.ok, true);
    assert.ok(isInstalled(root, 'node', makeManifest({ sha256: sha }).resources.node));
  } finally {
    goodServer.close();
  }
});

test('ensureRuntime rejects on SHA256 mismatch and cleans staging', async () => {
  const body = Buffer.from('tampered');
  const manifest = makeManifest({ sha256: '0'.repeat(64) });
  const root = tmpDir();
  await assert.rejects(
    ensureRuntime('node', {
      manifestPath: writeManifest(root, manifest),
      root,
      deps: {
        ...okDeps(),
        downloadFile: (u, dest) => { fs.writeFileSync(dest, body); return { downloaded: body.length }; },
      },
    }),
    /SHA256 校验失败/,
  );
  const leftovers = fs.readdirSync(root).filter((f) => f.includes('.staging-node-') || f.includes('.zip'));
  assert.deepEqual(leftovers, []);
  assert.equal(isInstalled(root, 'node', manifest.resources.node), false);
});

test('ensureRuntime skips download when fully ready (marker + health)', async () => {
  const manifest = makeManifest({});
  const root = tmpDir();
  const nodeDir = path.join(root, 'node');
  fs.mkdirSync(nodeDir, { recursive: true });
  fs.writeFileSync(path.join(nodeDir, 'node.exe'), 'fake');
  fs.writeFileSync(path.join(nodeDir, '.ready.json'), JSON.stringify({
    name: 'node', version: '14.21.3', sha256: '0'.repeat(64),
  }));
  const phases = [];
  let downloadCalls = 0;
  const res = await ensureRuntime('node', {
    manifestPath: writeManifest(root, manifest),
    root,
    onProgress: (s) => phases.push(s.phase),
    deps: { ...okDeps(), downloadFile: () => { downloadCalls++; } },
  });
  assert.equal(res.ok, true);
  assert.equal(downloadCalls, 0);
  assert.ok(!phases.includes('downloading'));
});

test('ensureRuntime reinstalls when health check fails despite marker', async () => {
  const body = Buffer.from('reinstall-health');
  const sha = crypto.createHash('sha256').update(body).digest('hex');
  const manifest = makeManifest({ sha256: sha });
  const root = tmpDir();
  const nodeDir = path.join(root, 'node');
  fs.mkdirSync(nodeDir, { recursive: true });
  fs.writeFileSync(path.join(nodeDir, 'node.exe'), 'broken');
  fs.writeFileSync(path.join(nodeDir, '.ready.json'), JSON.stringify({
    name: 'node', version: '14.21.3', sha256: sha,
  }));
  let healthCalls = 0;
  const res = await ensureRuntime('node', {
    manifestPath: writeManifest(root, manifest),
    root,
    deps: {
      ...okDeps(),
      runHealthCheck: () => {
        healthCalls++;
        // First call (isRuntimeReady skip check) fails; later install health succeeds.
        return healthCalls === 1 ? { ok: false, error: 'broken' } : { ok: true };
      },
      downloadFile: (u, dest) => { fs.writeFileSync(dest, body); return { downloaded: body.length }; },
    },
  });
  assert.equal(res.ok, true);
  assert.ok(healthCalls >= 2);
});

test('ensureRuntime reinstalls when marker version mismatches (upgrade)', async () => {
  const body = Buffer.from('upgrade-me');
  const sha = crypto.createHash('sha256').update(body).digest('hex');
  const manifest = makeManifest({ sha256: sha, version: '14.21.3' });
  const root = tmpDir();
  const nodeDir = path.join(root, 'node');
  fs.mkdirSync(nodeDir, { recursive: true });
  fs.writeFileSync(path.join(nodeDir, 'node.exe'), 'old');
  fs.writeFileSync(path.join(nodeDir, '.ready.json'), JSON.stringify({
    name: 'node', version: '14.0.0', sha256: sha,
  }));
  let downloadCalls = 0;
  const res = await ensureRuntime('node', {
    manifestPath: writeManifest(root, manifest),
    root,
    deps: {
      ...okDeps(),
      downloadFile: (u, dest) => {
        downloadCalls++;
        fs.writeFileSync(dest, body);
        return { downloaded: body.length };
      },
    },
  });
  assert.equal(res.ok, true);
  assert.equal(downloadCalls, 1);
  const marker = JSON.parse(fs.readFileSync(path.join(root, 'node', '.ready.json'), 'utf8'));
  assert.equal(marker.version, '14.21.3');
});

test('ensureRuntime reinstalls when the completion marker is corrupted', async () => {
  const body = Buffer.from('reinstall-me');
  const sha = crypto.createHash('sha256').update(body).digest('hex');
  const manifest = makeManifest({ sha256: sha });
  const root = tmpDir();
  const nodeDir = path.join(root, 'node');
  fs.mkdirSync(nodeDir, { recursive: true });
  fs.writeFileSync(path.join(nodeDir, '.ready.json'), 'garbage-not-json');
  const res = await ensureRuntime('node', {
    manifestPath: writeManifest(root, manifest),
    root,
    deps: {
      ...okDeps(),
      downloadFile: (u, dest) => { fs.writeFileSync(dest, body); return { downloaded: body.length }; },
    },
  });
  assert.equal(res.ok, true);
  assert.ok(isInstalled(root, 'node', manifest.resources.node));
});

test('isRuntimeReady is false when only a forged marker + exe exist without health', () => {
  const root = tmpDir();
  const nodeDir = path.join(root, 'node');
  fs.mkdirSync(nodeDir, { recursive: true });
  fs.writeFileSync(path.join(nodeDir, 'node.exe'), 'fake');
  fs.writeFileSync(path.join(nodeDir, '.ready.json'), JSON.stringify({
    name: 'node', version: '14.21.3', sha256: '0'.repeat(64),
  }));
  const resource = makeManifest({}).resources.node;
  assert.equal(isInstalled(root, 'node', resource), true);
  assert.equal(isRuntimeReady(root, 'node', resource, {
    runHealthCheck: () => ({ ok: false, error: 'nope' }),
    checkVersion: () => ({ ok: true }),
  }), false);
});

test('acquireLock times out when another instance holds the lock', () => {
  const root = tmpDir();
  const first = acquireLock(root, 'node', { timeoutMs: 300 });
  try {
    assert.throws(
      () => acquireLock(root, 'node', { timeoutMs: 300 }),
      (err) => err.code === 'LOCK_TIMEOUT',
    );
  } finally {
    releaseLock(first);
  }
});

test('acquireLock steals a lock left by a dead process', () => {
  const root = tmpDir();
  fs.mkdirSync(root, { recursive: true });
  fs.writeFileSync(path.join(root, '.install-node.lock'), JSON.stringify({ pid: 99999999, token: 'old', at: new Date(0).toISOString() }));
  const info = acquireLock(root, 'node', { timeoutMs: 1000 });
  try {
    assert.ok(fs.existsSync(info.path));
    assert.ok(info.token);
  } finally {
    releaseLock(info);
  }
});

test('releaseLock does not remove a lock owned by a different token', () => {
  const root = tmpDir();
  const first = acquireLock(root, 'node', { timeoutMs: 1000 });
  // Simulate a stale releaser with a different token
  releaseLock({ path: first.path, pid: first.pid, token: 'not-the-owner' });
  assert.ok(fs.existsSync(first.path), 'lock should still exist');
  releaseLock(first);
  assert.equal(fs.existsSync(first.path), false);
});

test('flattens a single top-level versioned folder after extraction', async () => {
  const body = Buffer.from('nested-zip');
  const sha = crypto.createHash('sha256').update(body).digest('hex');
  const manifest = makeManifest({ sha256: sha });
  const root = tmpDir();
  const res = await ensureRuntime('node', {
    manifestPath: writeManifest(root, manifest),
    root,
    deps: {
      ...okDeps(),
      extractZip: (_zip, dir) => {
        fs.mkdirSync(path.join(dir, 'node-v14.21.3-win-x64'), { recursive: true });
        fs.writeFileSync(path.join(dir, 'node-v14.21.3-win-x64', 'node.exe'), 'fake');
      },
      downloadFile: (u, dest) => { fs.writeFileSync(dest, body); return { downloaded: body.length }; },
    },
  });
  assert.equal(res.ok, true);
  assert.ok(fs.existsSync(path.join(root, 'node', 'node.exe')));
  assert.ok(isInstalled(root, 'node', manifest.resources.node));
});

test('node health check resolves the relative npm-cli.js arg and version-checks', () => {
  const { runHealthCheck, checkVersion } = require('./runtime-setup');
  const nodeRoot = path.join(__dirname, '..', 'runtime', 'node');
  if (!fs.existsSync(path.join(nodeRoot, 'node.exe'))) {
    return; // dev runtime not provisioned
  }
  const hc = runHealthCheck(nodeRoot, ['node.exe', 'node_modules/npm/bin/npm-cli.js', '--version']);
  assert.equal(hc.ok, true, hc.error);
  assert.match(hc.output, /^6\./);
  const vc = checkVersion(nodeRoot, ['node.exe', '--version'], '14.21.3');
  assert.equal(vc.ok, true, vc.error);
  assert.equal(vc.version, '14.21.3');
});

test('atomicInstall swaps directories and removes the old one', () => {
  const root = tmpDir();
  fs.mkdirSync(path.join(root, 'final'), { recursive: true });
  fs.writeFileSync(path.join(root, 'final', 'old.txt'), 'old');
  fs.mkdirSync(path.join(root, 'staging'), { recursive: true });
  fs.writeFileSync(path.join(root, 'staging', 'new.txt'), 'new');
  atomicInstall(path.join(root, 'staging'), path.join(root, 'final'));
  assert.equal(fs.existsSync(path.join(root, 'final', 'old.txt')), false);
  assert.equal(fs.readFileSync(path.join(root, 'final', 'new.txt'), 'utf8'), 'new');
  assert.ok(!fs.readdirSync(root).some((f) => f.startsWith('final.old-')));
});

test('writeRuntimeConfig is atomic and merges patches', () => {
  const root = tmpDir();
  const env = { LOCALAPPDATA: root, ZBUILD_RUNTIME_ROOT: path.join(root, 'zbuild', 'runtime') };
  writeRuntimeConfig({ mirrorBase: 'https://mirror.example/' }, env);
  writeRuntimeConfig({ overridePython: 'C:\\py.exe' }, env);
  const cfg = loadRuntimeConfig(env);
  assert.equal(cfg.mirrorBase, 'https://mirror.example/');
  assert.equal(cfg.overridePython, 'C:\\py.exe');
  assert.ok(fs.existsSync(runtimeConfigPath(env)));
});

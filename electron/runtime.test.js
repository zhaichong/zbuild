const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('path');
const { resolvePython, findPython, findNode, buildCandidates, isUsableRuntime } = require('./runtime');

function makeEnv(overrides) {
  return {
    LOCALAPPDATA: 'C:\\Users\\test\\AppData\\Local',
    ZBUILD_RUNTIME_ROOT: 'C:\\Users\\test\\AppData\\Local\\zbuild\\runtime',
    ...overrides,
  };
}

function pathJoin(...parts) {
  return path.join(...parts);
}

function healthy() {
  return { ok: true, version: '3.11.9' };
}

test('buildCandidates order: override, dev repo, user root (no legacy resources)', () => {
  const deps = {
    env: makeEnv(),
    readFileSync: () => JSON.stringify({ overridePython: 'C:\\custom\\python.exe' }),
  };
  const c = buildCandidates('C:/app', 'python', deps.env, deps);
  assert.deepEqual(c, [
    'C:\\custom\\python.exe',
    pathJoin('C:/app', 'runtime', 'python', 'python.exe'),
    'C:\\Users\\test\\AppData\\Local\\zbuild\\runtime\\python\\python.exe',
  ]);
  // Explicitly no resourcesPath / legacy candidate
  assert.equal(c.some((p) => String(p).includes('resources')), false);
});

test('prefers the per-user runtime root in production', () => {
  const userPy = 'C:\\Users\\test\\AppData\\Local\\zbuild\\runtime\\python\\python.exe';
  const result = resolvePython('C:/app', {
    env: makeEnv(),
    existsSync: (p) => p === userPy,
  });
  assert.deepEqual(result, { exe: userPy, args: [] });
});

test('dev repository runtime wins over the user root', () => {
  const devPy = pathJoin('C:/app', 'runtime', 'python', 'python.exe');
  const result = resolvePython('C:/app', {
    env: makeEnv(),
    existsSync: (p) => p === devPy,
    validateOverrideExecutable: healthy,
  });
  assert.deepEqual(result, { exe: devPy, args: [] });
});

test('override pointer is the highest priority when healthy', () => {
  const overridePy = 'C:\\custom\\python.exe';
  const result = resolvePython('C:/app', {
    env: makeEnv(),
    readFileSync: () => JSON.stringify({ overridePython: overridePy }),
    existsSync: (p) => p === overridePy,
    validateOverrideExecutable: () => ({ ok: true, version: '3.11.9' }),
  });
  assert.deepEqual(result, { exe: overridePy, args: [] });
});

test('unhealthy override is skipped in favor of user runtime', () => {
  const overridePy = 'C:\\custom\\python.exe';
  const userPy = 'C:\\Users\\test\\AppData\\Local\\zbuild\\runtime\\python\\python.exe';
  const result = resolvePython('C:/app', {
    env: makeEnv(),
    readFileSync: () => JSON.stringify({ overridePython: overridePy }),
    existsSync: (p) => p === overridePy || p === userPy,
    validateOverrideExecutable: (kind, p) => (
      p === overridePy ? { ok: false, error: 'bad deps' } : { ok: true, version: '3.11.9' }
    ),
  });
  assert.deepEqual(result, { exe: userPy, args: [] });
});

test('unhealthy dev runtime is skipped in favor of user runtime', () => {
  const devPy = pathJoin('C:/app', 'runtime', 'python', 'python.exe');
  const userPy = 'C:\\Users\\test\\AppData\\Local\\zbuild\\runtime\\python\\python.exe';
  const result = resolvePython('C:/app', {
    env: makeEnv(),
    existsSync: (p) => p === devPy || p === userPy,
    validateOverrideExecutable: (kind, p) => (
      path.normalize(String(p)) === path.normalize(devPy)
        ? { ok: false, error: 'incomplete dev' }
        : healthy()
    ),
  });
  assert.deepEqual(result, { exe: userPy, args: [] });
});

test('findNode looks up the node executable', () => {
  const node = 'C:\\Users\\test\\AppData\\Local\\zbuild\\runtime\\node\\node.exe';
  const result = findNode('C:/app', {
    env: makeEnv(),
    existsSync: (p) => p === node,
  });
  assert.equal(result, node);
});

test('reports a clear error when no runtime is available', () => {
  assert.throws(
    () => resolvePython('C:/app', { env: makeEnv(), existsSync: () => false }),
    /未找到内置 Python 运行环境/,
  );
});

test('system Python is not used as an automatic fallback', () => {
  const result = findPython('C:/app', {
    env: makeEnv(),
    existsSync: (p) => p === 'C:\\Windows\\py.exe',
  });
  assert.equal(result, null);
});

test('isUsableRuntime accepts healthy dev exe', () => {
  const devPy = pathJoin('C:/app', 'runtime', 'python', 'python.exe');
  assert.equal(
    isUsableRuntime('C:/app', 'python', {
      env: makeEnv(),
      existsSync: (p) => p === devPy,
      deps: {
        validateOverrideExecutable: () => ({ ok: true, version: '3.11.9' }),
      },
    }),
    true,
  );
});

test('isUsableRuntime rejects incomplete dev runtime that fails health', () => {
  const devPy = pathJoin('C:/app', 'runtime', 'python', 'python.exe');
  assert.equal(
    isUsableRuntime('C:/app', 'python', {
      env: makeEnv(),
      existsSync: (p) => p === devPy,
      deps: {
        validateOverrideExecutable: () => ({ ok: false, error: 'missing openpyxl' }),
      },
    }),
    false,
  );
});

test('isUsableRuntime falls through incomplete dev to healthy user runtime', () => {
  const fs = require('fs');
  const os = require('os');
  const { writeReady, isRuntimeReady } = require('./runtime-setup');

  const devPy = pathJoin('C:/app', 'runtime', 'python', 'python.exe');
  // Real on-disk user runtime so isRuntimeReady / isUsableRuntime hit shipped code.
  const userRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'zbuild-usable-'));
  const pyDir = path.join(userRoot, 'python');
  fs.mkdirSync(pyDir, { recursive: true });
  fs.writeFileSync(path.join(pyDir, 'python.exe'), 'fake');
  const resource = {
    version: '3.11.9',
    sha256: 'b'.repeat(64),
    healthCheck: ['python.exe', '--version'],
    healthVersion: ['python.exe', '--version'],
  };
  writeReady(userRoot, 'python', resource);
  const manifestPath = path.join(userRoot, 'runtime-manifest.json');
  fs.writeFileSync(manifestPath, JSON.stringify({
    version: 1,
    resources: { python: resource },
  }));

  try {
    assert.equal(
      isRuntimeReady(userRoot, 'python', resource, {
        runHealthCheck: () => ({ ok: true }),
        checkVersion: () => ({ ok: true }),
      }),
      true,
    );

    // Incomplete dev exe present, but user runtime is ready → usable.
    assert.equal(
      isUsableRuntime('C:/app', 'python', {
        env: {
          LOCALAPPDATA: path.join(userRoot, 'local'),
          ZBUILD_RUNTIME_ROOT: userRoot,
        },
        existsSync: (p) => (p === devPy ? true : fs.existsSync(p)),
        deps: {
          validateOverrideExecutable: () => ({ ok: false, error: 'incomplete dev' }),
          runHealthCheck: () => ({ ok: true }),
          checkVersion: () => ({ ok: true }),
        },
        manifestPath,
      }),
      true,
    );
  } finally {
    try { fs.rmSync(userRoot, { recursive: true, force: true }); } catch (_) {}
  }
});

test('isUsableRuntime rejects override that fails health even if path exists', () => {
  const overridePy = 'C:\\custom\\python.exe';
  assert.equal(
    isUsableRuntime('C:/app', 'python', {
      env: makeEnv(),
      readFileSync: () => JSON.stringify({ overridePython: overridePy }),
      existsSync: (p) => p === overridePy,
      deps: {
        validateOverrideExecutable: () => ({ ok: false, error: 'no deps' }),
      },
    }),
    false,
  );
});

test('isUsableRuntime accepts override when health check passes', () => {
  const overridePy = 'C:\\custom\\python.exe';
  assert.equal(
    isUsableRuntime('C:/app', 'python', {
      env: makeEnv(),
      readFileSync: () => JSON.stringify({ overridePython: overridePy }),
      existsSync: (p) => p === overridePy,
      deps: {
        validateOverrideExecutable: () => ({ ok: true, version: '3.11.9' }),
      },
    }),
    true,
  );
});

test('isUsableRuntime is false when nothing is present', () => {
  assert.equal(
    isUsableRuntime('C:/app', 'python', {
      env: makeEnv(),
      existsSync: () => false,
      manifestPath: null,
    }),
    false,
  );
});

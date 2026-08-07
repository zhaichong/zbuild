const test = require('node:test');
const assert = require('node:assert/strict');
const { resolvePython, findPython, findNode, buildCandidates, isUsableRuntime } = require('./runtime');

function makeEnv(overrides) {
  return {
    LOCALAPPDATA: 'C:\\Users\\test\\AppData\\Local',
    ZBUILD_RUNTIME_ROOT: 'C:\\Users\\test\\AppData\\Local\\zbuild\\runtime',
    ...overrides,
  };
}

function pathJoin(...parts) {
  const path = require('path');
  return path.join(...parts);
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
    validateOverrideExecutable: () => ({ ok: false, error: 'bad deps' }),
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

test('isUsableRuntime prefers override / dev exe without requiring marker', () => {
  const devPy = pathJoin('C:/app', 'runtime', 'python', 'python.exe');
  assert.equal(
    isUsableRuntime('C:/app', 'python', {
      env: makeEnv(),
      existsSync: (p) => p === devPy,
    }),
    true,
  );
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

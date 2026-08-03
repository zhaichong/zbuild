const test = require('node:test');
const assert = require('node:assert/strict');
const { resolvePython } = require('./runtime');

test('prefers bundled Python', () => {
  const result = resolvePython('C:/app', {
    existsSync: path => path.endsWith('tools\\python\\python.exe'),
    probe: () => ({ status: 1 }),
  });
  assert.match(result.exe, /tools\\python\\python\.exe$/);
  assert.deepEqual(result.args, []);
});

test('uses the Windows py launcher when available', () => {
  const result = resolvePython('C:/app', {
    existsSync: () => false,
    probe: command => ({ status: command === 'py' ? 0 : 1 }),
  });
  assert.deepEqual(result, { exe: 'py', args: ['-3'] });
});

test('reports a clear error when Python 3 is unavailable', () => {
  assert.throws(
    () => resolvePython('C:/app', { existsSync: () => false, probe: () => ({ status: 1 }) }),
    /未找到 Python 3/,
  );
});

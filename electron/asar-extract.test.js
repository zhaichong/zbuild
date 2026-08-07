const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('path');
const {
  needsExtractRefresh,
  writeExtractStamp,
  readExtractStamp,
  ensureExtractedResources,
  STAMP_NAME,
} = require('./asar-extract');

function memFs(initial = {}) {
  const files = { ...initial };
  const dirs = new Set();
  return {
    files,
    existsSync: (p) => Object.prototype.hasOwnProperty.call(files, p) || dirs.has(p),
    readFileSync: (p) => {
      if (!Object.prototype.hasOwnProperty.call(files, p)) throw new Error('ENOENT ' + p);
      return files[p];
    },
    writeFileSync: (p, data) => { files[p] = String(data); },
    mkdirSync: (p) => { dirs.add(p); },
    readdirSync: () => [],
    copyFileSync: () => {},
    lstatSync: () => ({ isDirectory: () => false, isSymbolicLink: () => false }),
  };
}

test('needsExtractRefresh is true when stamp is missing', () => {
  const deps = memFs();
  assert.equal(needsExtractRefresh('/x', '2.0.8', ['scripts'], deps), true);
});

test('needsExtractRefresh is false when stamp version and dirs match and dirs exist', () => {
  const root = path.join('C:', 'zbuild-extract');
  const stamp = path.join(root, STAMP_NAME);
  const deps = memFs({
    [stamp]: JSON.stringify({ version: '2.0.8', dirs: ['scripts', 'references'] }),
  });
  deps.existsSync = (p) => {
    if (p === path.join(root, 'scripts')) return true;
    if (p === path.join(root, 'references')) return true;
    if (p === stamp) return true;
    return false;
  };
  deps.readFileSync = (p) => {
    if (p === stamp) return JSON.stringify({ version: '2.0.8', dirs: ['scripts', 'references'] });
    throw new Error('ENOENT');
  };
  assert.equal(needsExtractRefresh(root, '2.0.8', ['scripts', 'references'], deps), false);
});

test('needsExtractRefresh is true when app version changes', () => {
  const root = path.join('C:', 'zbuild-extract');
  const stamp = path.join(root, STAMP_NAME);
  const deps = {
    existsSync: (p) => p === stamp || p === path.join(root, 'scripts') || p === path.join(root, 'references'),
    readFileSync: (p) => {
      if (p === stamp) return JSON.stringify({ version: '2.0.7', dirs: ['scripts', 'references'] });
      throw new Error('ENOENT');
    },
  };
  assert.equal(needsExtractRefresh(root, '2.0.8', ['scripts', 'references'], deps), true);
});

test('ensureExtractedResources skips work when stamp is current', () => {
  const root = path.join('C:', 'zbuild-extract');
  const stamp = path.join(root, STAMP_NAME);
  let copies = 0;
  const deps = {
    existsSync: (p) => true,
    readFileSync: (p) => {
      if (p === stamp) return JSON.stringify({ version: '2.0.8', dirs: ['scripts'] });
      throw new Error('ENOENT');
    },
    writeFileSync: () => { throw new Error('should not write'); },
    mkdirSync: () => {},
    readdirSync: () => { copies++; return []; },
    copyFileSync: () => { copies++; },
    lstatSync: () => ({ isDirectory: () => true, isSymbolicLink: () => false }),
  };
  const res = ensureExtractedResources({
    asarRoot: '/asar',
    extractedRoot: root,
    appVersion: '2.0.8',
    dirs: ['scripts'],
    deps,
  });
  assert.equal(res.refreshed, false);
  assert.equal(res.reason, 'stamp-current');
  assert.equal(copies, 0);
});

test('writeExtractStamp / readExtractStamp round-trip via deps', () => {
  const store = {};
  const root = path.join('C:', 'round');
  const deps = {
    mkdirSync: () => {},
    writeFileSync: (p, data) => { store[p] = data; },
    readFileSync: (p) => {
      if (!store[p]) throw new Error('ENOENT');
      return store[p];
    },
  };
  writeExtractStamp(root, '2.0.8', ['scripts'], deps);
  const stamp = readExtractStamp(root, deps);
  assert.equal(stamp.version, '2.0.8');
  assert.deepEqual(stamp.dirs, ['scripts']);
});

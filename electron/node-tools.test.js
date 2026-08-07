const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('path');
const { resolveManagedNodeNpm } = require('./node-tools');

test('resolveManagedNodeNpm uses findNode result and derives npm from that dir only', () => {
  const root = 'C:\\app';
  const managed = path.join('C:\\Users\\u\\zbuild\\runtime\\node\\node.exe');
  const files = new Set([
    managed,
    path.join(path.dirname(managed), 'npm.cmd'),
  ]);
  // Unhealthy bare managed candidates that must NOT be selected when findNode returns null later.
  const bareDev = path.join(root, 'runtime', 'node', 'node.exe');
  files.add(bareDev);
  files.add(path.join(root, 'runtime', 'node', 'npm.cmd'));

  const res = resolveManagedNodeNpm({
    rootDir: root,
    configured: {},
    findNodeFn: () => managed,
    existsSync: (p) => files.has(p),
  });
  assert.equal(res.node, managed);
  assert.equal(res.npm, path.join(path.dirname(managed), 'npm.cmd'));
});

test('resolveManagedNodeNpm does not fall back to bare managed paths when findNode is null', () => {
  const root = 'C:\\app';
  const bareDev = path.join(root, 'runtime', 'node', 'node.exe');
  const bareUser = path.join('C:\\Users\\u\\zbuild\\runtime\\node\\node.exe');
  const files = new Set([
    bareDev,
    path.join(root, 'runtime', 'node', 'npm.cmd'),
    bareUser,
    path.join(path.dirname(bareUser), 'npm.cmd'),
  ]);

  const res = resolveManagedNodeNpm({
    rootDir: root,
    configured: {},
    // Health-gated finder rejected all managed trees
    findNodeFn: () => null,
    existsSync: (p) => files.has(p),
  });
  assert.equal(res.node, '');
  assert.equal(res.npm, '');
});

test('resolveManagedNodeNpm prefers explicit configured.node when present', () => {
  const cfg = 'C:\\custom\\node.exe';
  const res = resolveManagedNodeNpm({
    rootDir: 'C:\\app',
    configured: { node: cfg, npm: 'C:\\custom\\npm.cmd' },
    findNodeFn: () => { throw new Error('findNode should not run when configured node exists'); },
    existsSync: (p) => p === cfg || p === 'C:\\custom\\npm.cmd',
  });
  assert.equal(res.node, cfg);
  assert.equal(res.npm, 'C:\\custom\\npm.cmd');
});

test('resolveManagedNodeNpm derives npm-cli.js when npm.cmd missing', () => {
  const managed = 'C:\\rt\\node\\node.exe';
  const cli = path.join('C:\\rt\\node', 'node_modules', 'npm', 'bin', 'npm-cli.js');
  const res = resolveManagedNodeNpm({
    rootDir: 'C:\\app',
    configured: {},
    findNodeFn: () => managed,
    existsSync: (p) => p === managed || p === cli,
  });
  assert.equal(res.node, managed);
  assert.equal(res.npm, cli);
});

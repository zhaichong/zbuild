'use strict';
// Pure Node/npm resolution for tool detection (no system Node fallback).
// Managed trees must already pass findNode health; do not re-select bare existsSync paths.

const fs = require('fs');
const path = require('path');

/**
 * Resolve managed Node + npm for the app tool map.
 *
 * @param {object} options
 * @param {string} options.rootDir - app root (dev repo or asar parent)
 * @param {object} [options.env]
 * @param {{ node?: string, npm?: string }} [options.configured] - user tool-config paths
 * @param {function} options.findNodeFn - health-gated finder (shipped findNode)
 * @param {function} [options.existsSync]
 * @returns {{ node: string, npm: string }}
 */
function resolveManagedNodeNpm(options = {}) {
  const {
    rootDir,
    env = process.env,
    configured = {},
    findNodeFn,
    existsSync = fs.existsSync,
  } = options;

  if (typeof findNodeFn !== 'function') {
    throw new Error('resolveManagedNodeNpm requires findNodeFn');
  }

  let nodePath = '';
  const cfgNode = typeof configured.node === 'string' ? configured.node.trim() : '';
  if (cfgNode && existsSync(cfgNode)) {
    // Explicit user tool path from config (recovery / advanced); not the managed tree.
    nodePath = cfgNode;
  } else {
    // Health-gated managed path only — never bare join(rootDir/runtime/node) existsSync.
    nodePath = findNodeFn(rootDir, { env }) || '';
  }

  let npmPath = '';
  const cfgNpm = typeof configured.npm === 'string' ? configured.npm.trim() : '';
  if (cfgNpm && existsSync(cfgNpm)) {
    npmPath = cfgNpm;
  } else if (nodePath) {
    // npm must come from the same install as the accepted node.exe.
    const dir = path.dirname(nodePath);
    const npmCmd = path.join(dir, 'npm.cmd');
    const npmCli = path.join(dir, 'node_modules', 'npm', 'bin', 'npm-cli.js');
    if (existsSync(npmCmd)) npmPath = npmCmd;
    else if (existsSync(npmCli)) npmPath = npmCli;
  }

  return { node: nodePath || '', npm: npmPath || '' };
}

module.exports = { resolveManagedNodeNpm };

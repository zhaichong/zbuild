#!/usr/bin/env node
/**
 * Fill / validate electron/runtime-manifest.json for release.
 *
 * Usage:
 *   node tools/fill-runtime-manifest.cjs --python-zip release/zbuild-python-3.11.9-win-x64.zip
 *   node tools/fill-runtime-manifest.cjs --primary URL [--backup URL] --require-complete
 *   node tools/fill-runtime-manifest.cjs --require-sha
 *   node tools/fill-runtime-manifest.cjs --require-complete
 */
'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const ROOT = path.resolve(__dirname, '..');
const MANIFEST_PATH = path.join(ROOT, 'electron', 'runtime-manifest.json');

function parseArgs(argv) {
  const out = {
    requireComplete: false,
    requireSha: false,
    primary: null,
    backup: null,
    clearBackup: false,
    pythonZip: null,
    manifest: MANIFEST_PATH,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--require-complete') out.requireComplete = true;
    else if (a === '--require-sha') out.requireSha = true;
    else if (a === '--primary') out.primary = argv[++i];
    else if (a === '--backup') out.backup = argv[++i];
    else if (a === '--clear-backup') out.clearBackup = true;
    else if (a === '--python-zip') out.pythonZip = argv[++i];
    else if (a === '--manifest') out.manifest = path.resolve(argv[++i]);
    else if (a === '--help' || a === '-h') {
      console.log(
        'Usage: node tools/fill-runtime-manifest.cjs ' +
        '[--python-zip PATH] [--primary URL] [--backup URL] [--clear-backup] ' +
        '[--require-sha] [--require-complete]',
      );
      process.exit(0);
    } else {
      console.error('Unknown arg:', a);
      process.exit(2);
    }
  }
  return out;
}

function sha256File(filePath) {
  const hash = crypto.createHash('sha256');
  const fd = fs.openSync(filePath, 'r');
  const buf = Buffer.alloc(1024 * 1024);
  let n;
  try {
    while ((n = fs.readSync(fd, buf, 0, buf.length, null)) > 0) hash.update(buf.subarray(0, n));
  } finally {
    fs.closeSync(fd);
  }
  return hash.digest('hex');
}

function isHttps(url) {
  return typeof url === 'string' && /^https:\/\//i.test(url);
}

function validateSha(py, node) {
  const errors = [];
  if (!/^[a-f0-9]{64}$/i.test(py.sha256 || '')) errors.push('python.sha256 is empty or invalid');
  if (!(typeof py.size === 'number' && py.size > 0)) errors.push('python.size must be a positive number');
  if (!Array.isArray(py.healthCheck) || !py.healthCheck.length) errors.push('python.healthCheck missing');
  if (!node || !/^[a-f0-9]{64}$/i.test(node.sha256 || '')) errors.push('node.sha256 is empty or invalid');
  return errors;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!fs.existsSync(args.manifest)) {
    console.error('manifest not found:', args.manifest);
    process.exit(1);
  }
  const m = JSON.parse(fs.readFileSync(args.manifest, 'utf8'));
  if (!m.resources || !m.resources.python) {
    console.error('manifest missing resources.python');
    process.exit(1);
  }
  const py = m.resources.python;

  if (args.pythonZip) {
    const zipPath = path.resolve(args.pythonZip);
    if (!fs.existsSync(zipPath)) {
      console.error('python zip not found:', zipPath);
      process.exit(1);
    }
    const st = fs.statSync(zipPath);
    py.sha256 = sha256File(zipPath);
    py.size = st.size;
    py.file = path.basename(zipPath);
    console.log('Filled python.sha256 =', py.sha256);
    console.log('Filled python.size   =', py.size);
  }

  if (args.primary != null) {
    if (!isHttps(args.primary)) {
      console.error('primary must be HTTPS:', args.primary);
      process.exit(1);
    }
    py.primary = args.primary;
    console.log('Filled python.primary =', py.primary);
  }
  if (args.clearBackup) {
    py.backup = '';
    console.log('Cleared python.backup');
  } else if (args.backup != null) {
    if (!isHttps(args.backup)) {
      console.error('backup must be HTTPS:', args.backup);
      process.exit(1);
    }
    py.backup = args.backup;
    console.log('Filled python.backup  =', py.backup);
  }

  fs.writeFileSync(args.manifest, JSON.stringify(m, null, 2) + '\n', 'utf8');

  if (args.requireSha || args.requireComplete) {
    const node = m.resources.node;
    const errors = validateSha(py, node);
    if (args.requireComplete) {
      if (!isHttps(py.primary)) errors.push('python.primary must be HTTPS');
      // backup is optional; if set must be HTTPS
      if (py.backup && !isHttps(py.backup)) errors.push('python.backup must be HTTPS when set');
      if (!isHttps(node && node.primary) || !isHttps(node && node.backup)) {
        errors.push('node primary/backup must be HTTPS');
      }
      if (py.primary && py.backup && py.primary === py.backup) {
        console.warn('warning: python.primary == python.backup (no real failover source)');
      }
    }
    if (errors.length) {
      console.error('runtime-manifest incomplete:');
      for (const e of errors) console.error(' -', e);
      process.exit(1);
    }
    console.log(args.requireComplete ? 'runtime-manifest validation OK (complete)' : 'runtime-manifest validation OK (sha)');
  }
}

main();

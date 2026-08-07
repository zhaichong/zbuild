'use strict';
// Pure helpers for asar → user-dir extraction (testable without Electron).

const fs = require('fs');
const path = require('path');

const STAMP_NAME = '.extract-stamp.json';

function stampPath(extractedRoot) {
  return path.join(extractedRoot, STAMP_NAME);
}

function readExtractStamp(extractedRoot, deps = {}) {
  const readFileSync = deps.readFileSync || fs.readFileSync;
  try {
    const raw = readFileSync(stampPath(extractedRoot), 'utf8');
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed.version === 'string') return parsed;
  } catch (_) {}
  return null;
}

function writeExtractStamp(extractedRoot, version, dirs, deps = {}) {
  const writeFileSync = deps.writeFileSync || fs.writeFileSync;
  const mkdirSync = deps.mkdirSync || fs.mkdirSync;
  mkdirSync(extractedRoot, { recursive: true });
  const payload = {
    version: String(version || ''),
    dirs: Array.isArray(dirs) ? dirs.slice() : [],
    at: new Date().toISOString(),
  };
  writeFileSync(stampPath(extractedRoot), JSON.stringify(payload, null, 2), 'utf8');
  return payload;
}

/**
 * Whether scripts/references need re-extraction from asar.
 * Refresh when stamp missing, version differs, or required dirs list changes.
 */
function needsExtractRefresh(extractedRoot, appVersion, dirs, deps = {}) {
  const existsSync = deps.existsSync || fs.existsSync;
  const stamp = readExtractStamp(extractedRoot, deps);
  if (!stamp) return true;
  if (String(stamp.version) !== String(appVersion || '')) return true;
  const want = Array.isArray(dirs) ? dirs.slice().sort().join('|') : '';
  const have = Array.isArray(stamp.dirs) ? stamp.dirs.slice().sort().join('|') : '';
  if (want !== have) return true;
  // Require each top-level dir to exist so a partial wipe still refreshes.
  for (const d of (dirs || [])) {
    if (!existsSync(path.join(extractedRoot, d))) return true;
  }
  return false;
}

/**
 * Recursively copy asar (or dir) tree into extractedRoot/dirName.
 * deps allow unit tests to mock filesystem without touching disk.
 */
function extractDirTree(srcRoot, destRoot, dirName, deps = {}) {
  const existsSync = deps.existsSync || fs.existsSync;
  const mkdirSync = deps.mkdirSync || fs.mkdirSync;
  const readdirSync = deps.readdirSync || fs.readdirSync;
  const copyFileSync = deps.copyFileSync || fs.copyFileSync;
  const lstatSync = deps.lstatSync || fs.lstatSync;

  const src = path.join(srcRoot, dirName);
  const dst = path.join(destRoot, dirName);
  if (!existsSync(src)) return { ok: false, error: 'src missing: ' + src };

  function walk(rel) {
    const s = path.join(srcRoot, rel);
    const d = path.join(destRoot, rel);
    let st;
    try { st = lstatSync(s); } catch (err) { return; }
    if (st.isSymbolicLink && st.isSymbolicLink()) return;
    if (st.isDirectory()) {
      mkdirSync(d, { recursive: true });
      let entries = [];
      try { entries = readdirSync(s); } catch (_) { return; }
      for (const name of entries) walk(path.join(rel, name));
      return;
    }
    mkdirSync(path.dirname(d), { recursive: true });
    try { copyFileSync(s, d); } catch (_) {}
  }

  walk(dirName);
  return { ok: true, path: dst };
}

function ensureExtractedResources(options = {}) {
  const {
    asarRoot,
    extractedRoot,
    appVersion,
    dirs = ['scripts', 'references'],
    deps = {},
  } = options;
  if (!asarRoot || !extractedRoot) return { refreshed: false, reason: 'missing roots' };
  if (!needsExtractRefresh(extractedRoot, appVersion, dirs, deps)) {
    return { refreshed: false, reason: 'stamp-current', version: appVersion };
  }
  for (const d of dirs) {
    extractDirTree(asarRoot, extractedRoot, d, deps);
  }
  writeExtractStamp(extractedRoot, appVersion, dirs, deps);
  return { refreshed: true, reason: 'extracted', version: appVersion, dirs };
}

module.exports = {
  STAMP_NAME,
  stampPath,
  readExtractStamp,
  writeExtractStamp,
  needsExtractRefresh,
  extractDirTree,
  ensureExtractedResources,
};

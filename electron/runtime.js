const fs = require('fs');
const path = require('path');
const {
  getRuntimeRoot,
  runtimeConfigPath,
  isRuntimeReady,
  loadManifest,
  validateOverrideExecutable,
} = require('./runtime-setup');

const EXPECTED = { python: '3.11.9', node: '14.21.3' };

function readOverride(kind, env, readFileSync) {
  const file = runtimeConfigPath(env);
  try {
    const cfg = JSON.parse(readFileSync(file, 'utf8'));
    const key = kind === 'python' ? 'overridePython' : 'overrideNode';
    return typeof cfg[key] === 'string' && cfg[key] ? cfg[key] : null;
  } catch (_) {
    return null;
  }
}

/**
 * Resolution order (shared with scripts/tools/bundled.py):
 * 1. explicit user override pointer (system recovery, version verified at write time)
 * 2. dev repository runtime (root/runtime/{kind})
 * 3. per-user runtime root (ZBUILD_RUNTIME_ROOT or %LOCALAPPDATA%\zbuild\runtime)
 *
 * Legacy resources/runtime is intentionally NOT used — old bundled runtimes would
 * bypass manifest version / hash checks after the online-setup migration.
 *
 * Selection is per-executable candidate (not "first root that exists as a directory"),
 * so an incomplete dev tree does not shadow a complete user install.
 */
function buildCandidates(root, kind, env, deps) {
  const readFileSync = (deps && deps.readFileSync) || fs.readFileSync;
  const exe = kind === 'python' ? 'python.exe' : 'node.exe';
  const candidates = [];

  const override = readOverride(kind, env, readFileSync);
  if (override) candidates.push(override);

  candidates.push(path.join(root, 'runtime', kind, exe));

  const userRoot = getRuntimeRoot(env);
  if (userRoot) candidates.push(path.join(userRoot, kind, exe));

  return candidates;
}

function findExe(root, kind, deps) {
  const existsSync = (deps && deps.existsSync) || fs.existsSync;
  const env = (deps && deps.env) || process.env;
  const readFileSync = (deps && deps.readFileSync) || fs.readFileSync;
  const checkOverride = (deps && deps.validateOverrideExecutable) || validateOverrideExecutable;
  const override = readOverride(kind, env, readFileSync);
  const candidates = buildCandidates(root, kind, env, deps);
  return candidates.find((p) => {
    if (!existsSync(p)) return false;
    // Never spawn with a configured override that fails version/deps checks.
    if (override && path.normalize(p) === path.normalize(override)) {
      const r = checkOverride(kind, p, EXPECTED[kind] || '');
      return !!r.ok;
    }
    return true;
  }) || null;
}

// Non-throwing lookups used for path resolution (spawn). Prefer ensureRuntimeReady
// for "is the runtime usable for install skip" decisions.
function findPython(root, deps) {
  return findExe(root, 'python', deps);
}

function findNode(root, deps) {
  return findExe(root, 'node', deps);
}

/**
 * Whether a named runtime is ready for use without reinstall.
 * - override: version + dependency/health (validateOverrideExecutable)
 * - dev runtime: executable exists under root/runtime/{kind}
 * - user runtime: marker + sha256 + health (isRuntimeReady)
 */
function isUsableRuntime(root, kind, options = {}) {
  const {
    env = process.env,
    existsSync = fs.existsSync,
    readFileSync = fs.readFileSync,
    manifestPath = null,
    deps = {},
  } = options;

  const override = readOverride(kind, env, readFileSync);
  if (override && existsSync(override)) {
    const check = deps.validateOverrideExecutable || validateOverrideExecutable;
    const expected = EXPECTED[kind] || '';
    if (check(kind, override, expected).ok) return true;
    // Invalid override does not count as usable (main validateOverride should clear it).
  }

  const devExe = path.join(root, 'runtime', kind, kind === 'python' ? 'python.exe' : 'node.exe');
  if (existsSync(devExe)) return true;

  if (!manifestPath) return false;
  let resource;
  try {
    const m = loadManifest(manifestPath);
    resource = m.resources && m.resources[kind];
  } catch (_) {
    return false;
  }
  if (!resource) return false;
  const userRoot = getRuntimeRoot(env);
  return isRuntimeReady(userRoot, kind, resource, deps);
}

function resolvePython(root, deps) {
  const found = findPython(root, deps);
  if (found) return { exe: found, args: [] };
  throw new Error(
    '未找到内置 Python 运行环境。\n' +
    '请保持联网后重启本工具完成自动安装，\n' +
    '或在失败页通过“恢复指引”手动恢复。'
  );
}

module.exports = {
  resolvePython,
  findPython,
  findNode,
  buildCandidates,
  isUsableRuntime,
};

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

function getPythonCandidates() {
  const candidates = [];

  const addCandidate = (p) => {
    if (p && !candidates.includes(p)) candidates.push(p);
  };

  const localAppData = process.env.LOCALAPPDATA;
  const userProfile = process.env.USERPROFILE;
  const programFiles = process.env.ProgramFiles;
  const programFilesX86 = process.env['ProgramFiles(x86)'];

  const baseDirs = [
    localAppData && path.join(localAppData, 'Programs', 'Python'),
    userProfile && path.join(userProfile, 'AppData', 'Local', 'Programs', 'Python'),
    programFiles,
    programFilesX86,
    'C:\\',
    'D:\\',
    'D:\\application',
    'D:\\application\\python',
  ].filter(Boolean);

  for (const base of baseDirs) {
    try {
      if (!fs.existsSync(base)) continue;
      const directPy = path.join(base, 'python.exe');
      if (fs.existsSync(directPy)) addCandidate(directPy);

      const entries = fs.readdirSync(base, { withFileTypes: true });
      for (const entry of entries) {
        if (entry.isDirectory() && /^python3?\d*/i.test(entry.name)) {
          addCandidate(path.join(base, entry.name, 'python.exe'));
        }
      }
    } catch (_) {}
  }

  addCandidate('C:\\Windows\\py.exe');
  return candidates;
}

function resolvePython(root, dependencies = {}) {
  const existsSync = dependencies.existsSync || fs.existsSync;
  const probe = dependencies.probe || ((command, args) => spawnSync(
    command,
    [...args, '--version'],
    { windowsHide: true, stdio: 'ignore' },
  ));

  // Priority 1: bundled Python shipped via extraResources (process.resourcesPath/runtime/python)
  // This is the self-contained path used in a packaged/distributed Electron app.
  const resourcesPath = (typeof process !== 'undefined' && process.resourcesPath) || '';
  const bundledCandidates = [
    resourcesPath && path.join(resourcesPath, 'runtime', 'python', 'python.exe'),
    path.join(root, 'runtime', 'python', 'python.exe'),   // dev-mode: project root/runtime
    path.join(root, 'tools', 'python', 'python.exe'),
    path.join(root, 'tools-cache', 'python', 'python.exe'),
  ].filter(Boolean);

  const bundled = bundledCandidates.find(existsSync);
  if (bundled) return { exe: bundled, args: [] };

  // Priority 2: system py/python/python3 launchers on PATH
  for (const candidate of [{ exe: 'py', args: ['-3'] }, { exe: 'python', args: [] }, { exe: 'python3', args: [] }]) {
    if (probe(candidate.exe, candidate.args).status === 0) return candidate;
  }

  // Priority 3: probe well-known absolute install paths in case PATH is not set
  const candidates = getPythonCandidates();
  for (const abspath of candidates) {
    if (existsSync(abspath) && probe(abspath, []).status === 0) {
      return { exe: abspath, args: [] };
    }
  }

  throw new Error(
    '未找到 Python 3。\n' +
    '请运行 tools\\setup_runtime.ps1 下载内置 Python，\n' +
    '或在本机安装 Python 3.7+ 后重试。'
  );
}

module.exports = { resolvePython, getPythonCandidates };


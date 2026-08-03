const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

// Well-known absolute paths to probe in case PATH is restricted in the
// spawned Electron environment (e.g. when launched from a CMD without the
// standard Windows paths injected).
const PYTHON_ABS_CANDIDATES = [
  'D:\\application\\python\\python.exe',
  'C:\\Users\\zhaichong\\AppData\\Local\\Programs\\Python\\Python312\\python.exe',
  'C:\\Windows\\py.exe',
];

function resolvePython(root, dependencies = {}) {
  const existsSync = dependencies.existsSync || fs.existsSync;
  const probe = dependencies.probe || ((command, args) => spawnSync(
    command,
    [...args, '--version'],
    { windowsHide: true, stdio: 'ignore' },
  ));
  const bundled = [
    path.join(root, 'tools', 'python', 'python.exe'),
    path.join(root, 'tools-cache', 'python', 'python.exe'),
  ].find(existsSync);
  if (bundled) return { exe: bundled, args: [] };

  for (const candidate of [{ exe: 'py', args: ['-3'] }, { exe: 'python', args: [] }, { exe: 'python3', args: [] }]) {
    if (probe(candidate.exe, candidate.args).status === 0) return candidate;
  }

  // Fallback: probe absolute paths in case py/python are not on PATH
  for (const abspath of PYTHON_ABS_CANDIDATES) {
    if (existsSync(abspath) && probe(abspath, []).status === 0) {
      return { exe: abspath, args: [] };
    }
  }

  throw new Error('未找到 Python 3。请安装 Python 3.10 或更高版本，并确保 py 或 python 命令可用。');
}

module.exports = { resolvePython };

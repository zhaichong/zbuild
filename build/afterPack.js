const fs = require('fs')
const path = require('path')

function rmDir(dirPath, safeRoot) {
  if (!dirPath || safeRoot && !dirPath.startsWith(safeRoot)) return false
  try { fs.rmSync(dirPath, { recursive: true, force: true }); return true }
  catch { return false }
}

function rmGlob(root, pattern) {
  try {
    const entries = fs.readdirSync(root, { withFileTypes: true })
    let count = 0
    for (const entry of entries) {
      if (entry.isDirectory() && entry.name.startsWith(pattern)) {
        if (rmDir(path.join(root, entry.name))) count++
      }
    }
    return count
  } catch { return 0 }
}

function walkDirs(start, name) {
  const result = []
  try {
    const entries = fs.readdirSync(start, { withFileTypes: true })
    for (const entry of entries) {
      if (!entry.isDirectory()) continue
      const full = path.join(start, entry.name)
      if (entry.name === name) { result.push(full); continue }
      if (entry.name !== 'node_modules') {
        result.push(...walkDirs(full, name))
      }
    }
  } catch {}
  return result
}

function pruneNpmDocs(root, track, size) {
  const docDirs = new Set(['benchmark', 'benchmarks', 'doc', 'docs', 'example', 'examples', 'man', 'test', 'tests'])
  const docFiles = /^(authors|changelog|contributing|history|readme|todo)(\..*)?$/i
  let removedBytes = 0
  const walk = (dir) => {
    let entries
    try { entries = fs.readdirSync(dir, { withFileTypes: true }) } catch { return }
    for (const entry of entries) {
      const full = path.join(dir, entry.name)
      if (entry.isDirectory()) {
        if (docDirs.has(entry.name.toLowerCase())) {
          removedBytes += size(full)
          rmDir(full, root)
        } else {
          walk(full)
        }
      } else if (entry.isFile() && docFiles.test(entry.name)) {
        try {
          removedBytes += fs.statSync(full).size
          fs.unlinkSync(full)
        } catch {}
      }
    }
  }
  walk(root)
  track(removedBytes, 'npm nested documentation')
}

module.exports = async function (context) {
  const runtime = path.join(context.appOutDir, 'resources', 'runtime')
  const log = (msg) => console.log(`[prune] ${msg}`)

  if (!fs.existsSync(runtime)) {
    log(`runtime dir not found at ${runtime}, skipping`)
    return
  }

  const pyRoot = path.join(runtime, 'python')
  const nodeRoot = path.join(runtime, 'node')

  let removedMB = 0
  const track = (bytes, label) => {
    if (bytes > 0) {
      removedMB += bytes / (1024 * 1024)
      log(`${label}: ${(bytes / (1024 * 1024)).toFixed(1)} MB`)
    }
  }

  const dirSize = (dir) => {
    if (!fs.existsSync(dir)) return 0
    try {
      let total = 0
      const walk = (d) => {
        for (const entry of fs.readdirSync(d, { withFileTypes: true })) {
          const p = path.join(d, entry.name)
          if (entry.isDirectory()) walk(p)
          else {
            try { total += fs.statSync(p).size } catch {}
          }
        }
      }
      walk(dir)
      return total
    } catch { return 0 }
  }

  // -- Python --
  if (fs.existsSync(pyRoot)) {
    const sp = path.join(pyRoot, 'Lib', 'site-packages')
    if (fs.existsSync(sp)) {
      track(dirSize(path.join(sp, 'pip')), 'pip')
      rmDir(path.join(sp, 'pip'), runtime)
      rmGlob(sp, 'pip-')

      track(dirSize(path.join(sp, 'setuptools')), 'setuptools')
      rmDir(path.join(sp, 'setuptools'), runtime)
      rmGlob(sp, 'setuptools-')

      track(dirSize(path.join(sp, 'wheel')), 'wheel')
      rmDir(path.join(sp, 'wheel'), runtime)
      rmGlob(sp, 'wheel-')
    }

    track(dirSize(path.join(pyRoot, 'Scripts')), 'Scripts')
    rmDir(path.join(pyRoot, 'Scripts'), runtime)

    const pycacheDirs = walkDirs(pyRoot, '__pycache__')
    let pycBytes = 0
    for (const d of pycacheDirs) { pycBytes += dirSize(d); rmDir(d, runtime) }
    track(pycBytes, '__pycache__ (Python)')
  }

  // -- Node --
  if (fs.existsSync(nodeRoot)) {
    const nm = path.join(nodeRoot, 'node_modules')
    if (fs.existsSync(nm)) {
      track(dirSize(path.join(nm, 'corepack')), 'corepack')
      rmDir(path.join(nm, 'corepack'), runtime)

      const npmRoot = path.join(nm, 'npm')
      if (fs.existsSync(npmRoot)) {
        for (const sub of ['changelogs', 'docs', 'man', 'scripts', 'tap-snapshots']) {
          const subPath = path.join(npmRoot, sub)
          track(dirSize(subPath), `npm ${sub}`)
          rmDir(subPath, runtime)
        }
        for (const f of ['AUTHORS', 'CHANGELOG.md', 'CONTRIBUTING.md', 'README.md', 'Makefile', 'make.bat', 'configure', '.travis.yml', '.npmignore', '.npmrc', '.mailmap', '.licensee.json']) {
          const fp = path.join(npmRoot, f)
          if (fs.existsSync(fp)) {
            try { track(fs.statSync(fp).size, `npm ${f}`); fs.unlinkSync(fp) } catch {}
          }
        }
        pruneNpmDocs(npmRoot, track, dirSize)
      }
    }
  }

  log(`done, removed ~${removedMB.toFixed(1)} MB`)
}

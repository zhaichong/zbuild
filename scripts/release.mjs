#!/usr/bin/env node
import { spawnSync } from 'child_process'
import fs from 'fs'
import os from 'os'
import path from 'path'
import { fileURLToPath } from 'url'
import readline from 'readline'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(__dirname, '..')
const npmCmd = process.platform === 'win32' ? 'npm.cmd' : 'npm'

function run(cmd, args, opts = {}) {
  const res = spawnSync(cmd, args, { cwd: root, encoding: 'utf8', stdio: 'pipe', ...opts })
  return { status: res.status, out: `${res.stdout || ''}${res.stderr || ''}`.trim() }
}

function runOk(cmd, args, opts = {}) {
  const r = run(cmd, args, opts)
  if (r.status !== 0) {
    throw new Error(`命令失败: ${cmd} ${args.join(' ')}${r.out ? '\n' + r.out : ''}`)
  }
  return r.out
}

function runNpm(args, opts = {}) {
  return runOk(npmCmd, args, { shell: process.platform === 'win32', ...opts })
}

function bumpVersion(current, type) {
  const [maj, min, pat] = current.split('.').map(Number)
  if (type === 'major') return `${maj + 1}.0.0`
  if (type === 'minor') return `${maj}.${min + 1}.0`
  return `${maj}.${min}.${pat + 1}`
}

function compareVersions(a, b) {
  const pa = a.replace(/^v/, '').split('.').map(Number)
  const pb = b.replace(/^v/, '').split('.').map(Number)
  for (let i = 0; i < 3; i++) {
    const x = (pa[i] || 0) - (pb[i] || 0)
    if (x !== 0) return x
  }
  return 0
}

function getLastTag() {
  const r = runOk('git', ['tag', '--list', 'v*'])
  const tags = r.split(/\r?\n/).filter(Boolean)
  if (!tags.length) return null
  tags.sort(compareVersions)
  return tags[tags.length - 1]
}

function getChangelog() {
  const lastTag = getLastTag()
  const range = lastTag ? `${lastTag}..HEAD` : 'HEAD'
  const r = runOk('git', ['log', range, '--oneline', '--no-merges', '-30'])
  return { lastTag, lines: r.split(/\r?\n/).filter(Boolean) }
}

async function promptVersion(current) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout })
  const ask = (q) => new Promise((resolve) => rl.question(q, resolve))
  const p = bumpVersion(current, 'patch')
  const m = bumpVersion(current, 'minor')
  const j = bumpVersion(current, 'major')
  console.log(`当前版本: ${current}`)
  console.log('请选择升级方式:')
  console.log(`  1) patch  → ${p}`)
  console.log(`  2) minor  → ${m}`)
  console.log(`  3) major  → ${j}`)
  console.log('  4) 自定义版本号')
  const choice = (await ask('请选择 [1-4]: ')).trim()
  let version = null
  if (choice === '1') version = p
  else if (choice === '2') version = m
  else if (choice === '3') version = j
  else if (choice === '4') {
    const v = (await ask('输入版本号 (如 2.1.0): ')).trim()
    if (!/^\d+\.\d+\.\d+$/.test(v)) {
      console.error('[release] 无效版本号，应为 X.Y.Z')
      rl.close()
      process.exit(1)
    }
    version = v
  } else {
    console.error('[release] 无效选择')
    rl.close()
    process.exit(1)
  }
  rl.close()
  return version
}

function prechecks() {
  const steps = [
    ['Git 工作区干净', () => {
      const r = run('git', ['status', '--porcelain'])
      if (r.out) throw new Error('工作区有未提交的更改:\n' + r.out)
    }],
    ['TypeScript 类型检查 (typecheck)', () => runNpm(['run', 'typecheck'])],
    ['Node 主进程测试 (test:node)', () => runNpm(['run', 'test:node'])],
    ['Python 测试 (test:py)', () => runNpm(['run', 'test:py'])],
    ['前端构建 (build)', () => runNpm(['run', 'build'])],
  ]
  for (const [name, fn] of steps) {
    process.stdout.write(`[release] 预检: ${name} ... `)
    try {
      fn()
      console.log('OK')
    } catch (e) {
      console.log('FAILED')
      throw new Error(`预检失败: ${name} — ${e.message}`)
    }
  }
}

async function main() {
  const argv = process.argv.slice(2)
  let dryRun = false
  let versionArg = null
  for (const a of argv) {
    if (a === '--dry-run' || a === '-n') dryRun = true
    else if (a.startsWith('--')) {
      console.error(`[release] 未知参数: ${a}`)
      process.exit(1)
    } else versionArg = a
  }

  const pkg = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'))
  const current = pkg.version
  console.log(`[release] 当前版本: ${current}`)

  let target = null
  if (versionArg) {
    if (['patch', 'minor', 'major'].includes(versionArg)) {
      target = bumpVersion(current, versionArg)
    } else if (/^\d+\.\d+\.\d+$/.test(versionArg)) {
      target = versionArg
    } else {
      console.error(`[release] 无效参数: ${versionArg}，应为 patch / minor / major 或版本号 (如 2.1.0)`)
      process.exit(1)
    }
  } else {
    target = await promptVersion(current)
  }

  if (compareVersions(target, current) <= 0) {
    console.error(`[release] 目标版本 ${target} 未高于当前版本 ${current}`)
    process.exit(1)
  }

  runOk('git', ['fetch', '--tags', '--quiet'])

  const { lastTag, lines } = getChangelog()
  console.log(`[release] 目标版本: ${target}`)
  console.log(`[release] 变更日志 (${lastTag ? `${lastTag}..HEAD` : '最近提交'}):`)
  for (const l of lines) console.log('  ' + l)

  if (dryRun) {
    console.log('[release] --- dry-run 模式，以下为将执行的操作 ---')
    console.log('  预检: git干净 / typecheck / test:node / test:py / build')
    console.log(`  npm version ${target} --no-git-tag-version`)
    console.log('  git add package.json package-lock.json && git commit -m "chore: release v' + target + '"')
    console.log(`  git tag -a v${target} -F <变更日志文件>`)
    console.log('  git push origin <branch> v' + target)
    console.log('[release] dry-run 完成，未执行任何操作')
    return
  }

  try {
    prechecks()
  } catch (e) {
    console.error(`\n[release] ${e.message}`)
    process.exit(1)
  }

  runNpm(['version', target, '--no-git-tag-version'])
  runOk('git', ['add', 'package.json', 'package-lock.json'])
  runOk('git', ['commit', '-m', `chore: release v${target}`])
  const tagMsg = (lines.length ? lines.join('\n') : `Release v${target}`) + '\n'
  const tagMsgFile = path.join(os.tmpdir(), 'zbuild-tag-msg.txt')
  fs.writeFileSync(tagMsgFile, tagMsg, 'utf8')
  try {
    runOk('git', ['tag', '-a', `v${target}`, '-F', tagMsgFile])
  } finally {
    fs.unlinkSync(tagMsgFile)
  }

  const branch = runOk('git', ['rev-parse', '--abbrev-ref', 'HEAD'])
  runOk('git', ['push', 'origin', branch])
  runOk('git', ['push', 'origin', `v${target}`])

  console.log(`[release] 已推送 ${branch} 与 tag v${target}`)
  console.log('[release] CI 检测到 tag v' + target + ' 后将自动构建并发布 GitHub Release')
  console.log('[release] 发布完成')
}

main().catch((e) => {
  console.error(`[release] 出错: ${e.message}`)
  process.exit(1)
})

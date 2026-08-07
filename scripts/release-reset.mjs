#!/usr/bin/env node
import { spawnSync } from 'child_process'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

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

function getRepoInfo() {
  try {
    const pkg = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'))
    const pub = pkg.build && pkg.build.publish
    if (pub && pub.owner && pub.repo) return { owner: pub.owner, repo: pub.repo }
  } catch (_) {}
  const r = run('git', ['remote', 'get-url', 'origin'])
  if (r.status === 0) {
    const m = r.out.match(/github\.com[/:]([^/]+)\/([^/]+?)(?:\.git)?$/)
    if (m) return { owner: m[1], repo: m[2].replace(/\.git$/, '') }
  }
  return null
}

async function listReleases(token, owner, repo) {
  const res = await fetch(`https://api.github.com/repos/${owner}/${repo}/releases`, {
    headers: { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json', 'User-Agent': 'zbuild-ops' },
  })
  if (!res.ok) throw new Error(`查询 Releases 失败: HTTP ${res.status}`)
  return res.json()
}

async function deleteRelease(token, owner, repo, id) {
  const res = await fetch(`https://api.github.com/repos/${owner}/${repo}/releases/${id}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json', 'User-Agent': 'zbuild-ops' },
  })
  if (!res.ok) throw new Error(`删除 Release #${id} 失败: HTTP ${res.status}`)
}

async function main() {
  const argv = process.argv.slice(2)
  const dryRun = argv.includes('--dry-run') || argv.includes('-n')
  const rest = argv.filter((a) => a !== '--dry-run' && a !== '-n')
  if (rest.length) {
    console.error(`[reset] 未知参数: ${rest.join(' ')}`)
    process.exit(1)
  }

  if (run('git', ['rev-parse', '--is-inside-work-tree']).status !== 0) {
    console.error('[reset] 当前目录不是 git 仓库')
    process.exit(1)
  }

  const pkg = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'))
  const token = process.env.GH_TOKEN || process.env.GITHUB_TOKEN || ''
  const repoInfo = getRepoInfo()

  const remoteTags = []
  const ls = run('git', ['ls-remote', '--tags', 'origin'])
  if (ls.status === 0) {
    for (const line of ls.out.split(/\r?\n/)) {
      const m = line.match(/refs\/tags\/(.+?)(\^\{\})?$/)
      if (m && !m[2] && m[1]) remoteTags.push(m[1])
    }
  } else {
    console.warn('[reset] 无法读取远端 tags（可能未配置 origin），将跳过远端 tag 删除')
  }
  const localTags = runOk('git', ['tag', '--list']).split(/\r?\n/).filter(Boolean)

  let releases = []
  if (repoInfo && token) {
    try {
      releases = await listReleases(token, repoInfo.owner, repoInfo.repo)
    } catch (e) {
      console.warn(`[reset] ${e.message}`)
    }
  }

  console.log(`[reset] 当前版本: ${pkg.version}`)
  console.log(`[reset] 远端 tags: ${remoteTags.length} 个 | 本地 tags: ${localTags.length} 个 | GitHub Releases: ${releases.length} 个`)
  if (releases.length && !token) {
    console.warn('[reset] 未检测到 GH_TOKEN / GITHUB_TOKEN，将跳过 GitHub Releases 删除')
  }

  if (dryRun) {
    console.log('[reset] --- dry-run 模式，以下为将执行的操作 ---')
    for (const t of remoteTags) console.log(`  git push origin :refs/tags/${t}`)
    for (const t of localTags) console.log(`  git tag -d ${t}`)
    for (const r of releases) console.log(`  DELETE /releases/${r.id} (${r.tag_name})`)
    if (pkg.version !== '1.0.0') {
      console.log('  npm version 1.0.0 --no-git-tag-version')
      console.log('  git add package.json package-lock.json && git commit && git push origin <branch>')
    } else {
      console.log('  (版本已是 1.0.0，无需恢复)')
    }
    console.log('[reset] dry-run 完成，未执行任何操作')
    return
  }

  for (const t of remoteTags) {
    process.stdout.write(`[reset] 删除远端 tag ${t} ... `)
    try {
      runOk('git', ['push', 'origin', `:refs/tags/${t}`])
      console.log('OK')
    } catch (e) {
      console.log('FAILED: ' + e.message)
    }
  }
  for (const t of localTags) {
    process.stdout.write(`[reset] 删除本地 tag ${t} ... `)
    try {
      runOk('git', ['tag', '-d', t])
      console.log('OK')
    } catch (e) {
      console.log('FAILED: ' + e.message)
    }
  }
  if (token && repoInfo) {
    for (const rel of releases) {
      process.stdout.write(`[reset] 删除 Release ${rel.tag_name} (#${rel.id}) ... `)
      try {
        await deleteRelease(token, repoInfo.owner, repoInfo.repo, rel.id)
        console.log('OK')
      } catch (e) {
        console.log('FAILED: ' + e.message)
      }
    }
  } else if (releases.length) {
    console.warn('[reset] 无 GitHub 凭据，未删除 Releases，请手动在 GitHub 处理')
  }

  if (pkg.version !== '1.0.0') {
    console.log('[reset] 恢复版本 1.0.0 ...')
    runNpm(['version', '1.0.0', '--no-git-tag-version'])
    runOk('git', ['add', 'package.json', 'package-lock.json'])
    runOk('git', ['commit', '-m', 'chore: reset version to 1.0.0'])
    const branch = runOk('git', ['rev-parse', '--abbrev-ref', 'HEAD'])
    runOk('git', ['push', 'origin', branch])
    console.log(`[reset] 已推送 ${branch}（版本 1.0.0）`)
  } else {
    console.log('[reset] 版本已是 1.0.0，无需恢复')
  }
  console.log('[reset] 完成')
}

main().catch((e) => {
  console.error(`[reset] 出错: ${e.message}`)
  process.exit(1)
})

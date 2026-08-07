# Spec：一键发布与清空发布流程

> 目录：`.spec/2026-08-06-release-workflow/`
> 流程档位：Strict
> 确认记录：用户原话「当我执行 npm run release 的时候自动增加版本号发布 或者是清空所有已经发布的内容,包括tag,之前的版本号恢复到v1.0.0」「帮我设计一个发布的一个流程」；方案与决策项经用户确认。

## 目标与价值

为 Electron 应用（Vue3+Vite+Electron，自动更新已就绪）提供两条命令管理发布生命周期：

- `npm run release`：本地质量预检 → 交互选择版本 → 自动生成变更日志 → bump 版本并打 tag → 推送 → CI 检测 `v*` tag 自动构建并发布 GitHub Release → 已装客户端收到更新。
- `npm run release:reset`：删除所有远端/本地 tag 与 GitHub Releases，版本号恢复 1.0.0（不打 tag）。

## 变更面

- 前端：是（仅新增/修改 Node 脚本与 package.json scripts，不触及 UI）
- Java 后端：否
- 数据库：否
- 外部系统：是（GitHub 远端 tag 与 Releases 的删除/推送）

## 场景与规则

- 触发角色：维护者（本地执行命令）
- 触发条件：`npm run release [-- <patch|minor|major|X.Y.Z>]` 或 `npm run release:reset`
- 主路径（release）：
  1. 预检：git 干净、typecheck、test:node、test:py、build；任一失败中止
  2. 版本选择：无参交互式（1 patch / 2 minor / 3 major / 4 自定义），有参直接使用并校验
  3. 变更日志：`git log <上一tag>..HEAD --oneline`，无上一 tag 时取最近提交，预览
  4. bump：`npm version <版本> -m "chore: release v%s"` → commit + annotated tag `vX.Y.Z`（message 含变更日志）
  5. 推送：`git push origin <branch>` + `git push origin <tag>`
  6. 输出 CI 将自动发布 Release 的提示
- 主路径（reset）：
  1. 收集远端/本地 tags 与 GitHub Releases
  2. 删除远端 tag（`git push origin :refs/tags/<t>`）与本地 tag（`git tag -d <t>`）
  3. 有 `GH_TOKEN`/`GITHUB_TOKEN` 时逐个 DELETE Releases；无 token 警告跳过
  4. `npm version 1.0.0 --no-git-tag-version` 恢复版本（不打 tag），有变化才 commit + push 分支
- 异常与边界：
  - 非 git 仓库 / 无 origin / 工作区有未提交更改（release 中止；reset 允许未提交但提示）
  - 非法版本参数 → 报错退出
  - reset 当前远端 0 tag/0 release → 空操作 + 版本恢复
  - 删除 Release 无 token → 仅删 tag 并明确警告

## 数据、接口与外部副作用

| 类型 | 内容 | 权限/敏感性 |
|---|---|---|
| 读取 | git tags/分支/remote、package.json 版本 | 无 |
| 写入 | package.json / package-lock.json 版本号、本地 git tag | 低 |
| 接口/事件 | GitHub REST API `GET/DELETE /repos/{owner}/{repo}/releases[/{id}]` | 需 GH_TOKEN/GITHUB_TOKEN，Bearer 认证 |
| 外部系统 | 推送分支与 tag 到 GitHub；删除远端 tag 与 Releases | 不可逆，影响共享状态 |

## 接口契约

不适用（Node 本地脚本，无前后端契约）。

## 验收标准

- [ ] **AC-01** `npm run release` 无参交互选版本，完成 bump + commit + annotated tag `vX.Y.Z` + push 分支与 tag
- [ ] **AC-02** 预检（git 干净/typecheck/test:node/test:py/build）任一失败 → 中止，无任何 git/远端副作用
- [ ] **AC-03** tag 为 annotated，message 含自上一 tag 起的提交变更列表
- [ ] **AC-04** `npm run release -- --dry-run` 只打印版本计算、变更日志与命令，不执行
- [ ] **AC-05** `npm run release:reset` 删除全部远端与本地 tag
- [ ] **AC-06** reset 有 `GH_TOKEN`/`GITHUB_TOKEN` 时删除全部 GitHub Releases；无 token 时跳过并输出警告
- [ ] **AC-07** reset 后 package.json 版本恢复 1.0.0、不打 tag；版本有变化才 commit + push
- [ ] **AC-08** 非法参数、非 git 仓库等边界路径报错清晰

## 非目标

- 不做 pre-release / draft 发布支持
- 不做自动回滚或多平台产物
- 不做客户端更新弹窗之外的发布通知

## 已知约束与假设

- 已确认事实：项目分支 `master`；当前版本 2.0.0；远端 0 tag / 0 release；CI 的 release job 由 `v*` tag 触发；`master` push 不触发现有 CI；tag 删除事件不触发 GitHub Actions；`package.json build.publish` 指向 zhaichong/zbuild；`win.artifactName` 已修复 latest.yml 文件名一致性
- 待验证假设：Node 22 全局 fetch 可用（Node 22 内置）；`npm version` 在 Windows 下创建 annotated tag 并同步 package-lock
- 项目规范：脚本文件置于 `scripts/`，package.json scripts 使用 `npm run <name>` 调用

## 待决策项

无（已全部确认：交互式选版本；reset 命令名 `release:reset`；凭据读 GH_TOKEN/GITHUB_TOKEN、无则跳过删 Release；恢复 1.0.0 不打 tag；reset 无需二次确认；release 内置预检；变更日志自动从 git 提交生成）

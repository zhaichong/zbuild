# Plan：一键发布与清空发布流程

> 对应：`spec.md`
> 流程档位：Strict

## 方案概述

两个 Node 脚本承担全部逻辑，保持相互独立、无公共依赖（避免新增模块）：

- `scripts/release.mjs`（改造）：在现有 git 干净检查基础上增加质量预检、交互式版本选择、变更日志生成、dry-run。
- `scripts/release-reset.mjs`（新增）：收集 tag/Release → 删除 → 恢复版本 1.0.0。

CI 与自动更新链路不动（此前已就绪），发布动作只依赖 git 与 GitHub API。

## 影响范围

| 动作 | 文件/模块/数据 | 关联 AC | 说明 |
|---|---|---|---|
| 修改 | `scripts/release.mjs` | AC-01~04, AC-08 | 预检、交互、变更日志、dry-run |
| 新增 | `scripts/release-reset.mjs` | AC-05~07 | 清空发布 |
| 修改 | `package.json` scripts | — | 增加 `release:reset` |
| 新增 | `.spec/2026-08-06-release-workflow/` | — | 流程留痕 |

## 风险与缓解

| 风险 | 级别 | 缓解措施 | 回滚/恢复 | 是否需确认 |
|---|---|---|---|---|
| reset 不可逆删除远端 tag/Release | 高 | 内置 `--dry-run`；当前远端 0 tag/0 release；无 token 时不删 Release；输出删除清单 | 无自动恢复，需 GitHub 后台或重建 tag | 否（用户已确认） |
| 预检误阻断发布 | 低 | 预检失败仅中止并输出失败项，可人工处理后重跑 | 无副作用 | 否 |
| push 中途失败留下本地 tag/commit | 低 | 输出清晰错误；本地可 `git tag -d`、`git reset` 手动回滚 | 有 | 否 |
| GH_TOKEN 在本地环境变量残留 | 低 | 脚本只读取，不写入日志 | — | 否 |

## 数据与调用链

```text
release.mjs
  预检(git/typecheck/test:node/test:py/build)
    -> 交互选版本 | 参数版本
    -> git log 生成变更日志
    -> npm version (commit + tag vX.Y.Z)
    -> git push origin <branch> + <tag>
release-reset.mjs
  收集(git ls-remote --tags / git tag / GitHub releases)
    -> 删远端 tag + 本地 tag
    -> 有token: DELETE releases
    -> npm version 1.0.0 --no-git-tag-version
    -> commit + push 分支
```

## 关键选择

- 选择与理由：
  - 变更日志写入 annotated tag 的 message：electron-builder 发布 Release 时以 tag 的说明作为 Release body，客户端 UpdateDialog 可展示。
  - 预检内置于 release 命令：质量门禁前移，且 CI 的 test job 在 tag 事件仍会跑（双保险）。
  - reset 用 `npm version --no-git-tag-version` 恢复版本：同步 package.json 与 package-lock，且不产生 tag。
  - 无 token 跳过删 Release：避免脚本在无凭据时失败卡死，保留核心删 tag 能力。
- 真实存在的替代方案及未采用原因：
  - 用 `gh` CLI 删除 Releases：本机未安装 gh，且增加外部依赖，故用原生 fetch 调 REST API。

## 验证策略

| 验证层级 | 覆盖 AC | 方法 | 回归关注点 |
|---|---|---|---|
| 静态 | AC-08 | `node --check`、非法参数路径 | 退出码与报错文案 |
| dry-run | AC-04, AC-05 | `--dry-run` 打印清单与命令，无副作用 | 清单完整性 |
| 逻辑 | AC-03 | 变更日志生成的 git log 输出 | 无上一 tag 时的 fallback |
| 全量 | — | `npm run typecheck`（保险） | 前端不受影响 |

## 范围外

- CI/自动更新链路（已就绪，不动）
- 真实 push/tag/Release 操作（由用户后续执行 `npm run release` 触发，属于生产副作用）

## Strict 执行门禁

- [x] dry-run / 预览已设计
- [x] 权限、数据范围与外部副作用已确认
- [x] 回滚或恢复方式可执行（git 本地命令可回滚本地 commit/tag）
- [x] 用户已确认关键风险与执行范围

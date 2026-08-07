# Harness Check：一键发布与清空发布流程

> 时间：2026-08-06
> 工作上下文：分支 master，工作区含未提交改动（本功能文件），未执行任何真实 git push / tag / Release 操作

## 执行记录

| 检查 | 命令/步骤 | 结果 | 关键证据或原因 |
|---|---|---|---|
| 静态检查 | `node --check scripts/release.mjs`、`node --check scripts/release-reset.mjs` | pass | 两个脚本语法均 OK |
| 静态检查 | `npm run typecheck` | pass | exit=0，前端不受影响 |
| 静态检查 | `node -e` + js-yaml 解析 `.github/workflows/ci.yml` | pass | YAML 合法；release job 含新增 "Update GitHub Release notes" 步骤 |
| dry-run | `npm run release -- patch --dry-run` | pass | 当前 2.0.0→2.0.1，变更日志取自最近提交，操作清单完整，未执行任何操作 |
| dry-run | `npm run release:reset -- --dry-run` | pass | 远端/本地 tag 0 个、Releases 0 个；打印版本恢复计划；未执行 |
| 边界 | `npm run release -- foo` | pass | 无效参数报错退出 exit=1 |
| 边界 | `npm run release -- 2.0.0 --dry-run` | pass | 目标版本与当前相同报错退出 exit=1 |
| 边界 | `npm run release:reset -- bogus` | pass | 未知参数报错退出 exit=1 |
| 预检中止 | `npm run release -- patch`（工作区有未提交改动） | pass | git 干净预检失败立即中止，无任何 git 副作用（tag 仍为空、HEAD 不变） |
| 脚本注册 | `npm run` 列表 | pass | release / release:reset 均已注册 |
| 自动化测试 | typecheck（由预检调用） | pass | 预检链路上的 test:node/test:py/build 此前已全部通过（见上次会话验证） |
| 端到端 | 真实 bump/tag/push/Release | skipped | 属生产副作用，未经授权不执行；由用户执行 `npm run release` 验证 |

## 验收追踪

| AC | 结果 | 证据 | 未覆盖风险 |
|---|---|---|---|
| AC-01 | partial | 交互与完整流程已实现并经 dry-run 走通；真实 bump/commit/tag/push 需用户执行一次 | 真实 push 与 CI 触发 |
| AC-02 | pass | 预检任一失败立即中止、零副作用（git 干净失败实测） | 其余预检步骤失败路径未逐一强制构造 |
| AC-03 | partial | 代码使用 `git tag -a <tag> -m <变更日志>`；tag 内容未在真实 tag 上核验 | 未真实创建 tag |
| AC-04 | pass | dry-run 只打印、未执行任何操作（实测无副作用） | 无 |
| AC-05 | pass | dry-run 输出删除清单逻辑正确；当前远端 0 tag | 真实删除远端 tag 未执行 |
| AC-06 | partial | 无 token 时警告跳过的路径已实现并验证；有 token 删除路径未实测（无凭据） | 真实 DELETE API |
| AC-07 | pass | dry-run 显示版本 1.0.0 恢复计划，`npm version --no-git-tag-version` 不打 tag | 真实 commit/push 未执行 |
| AC-08 | pass | 三组边界输入均清晰报错退出 | 无 |

## 风险导向检查

- 数据：dry-run 幂等安全；真实 reset 删除 tag/Release 不可逆，已在 spec/plan 标注
- 安全：GH_TOKEN 仅脚本运行时从环境变量读取，不写日志；无凭据时自动降级不删 Release
- 其他：`master` push 不触发现有 CI（CI 只监听 main/develop），tag 删除不触发 GitHub Actions

## 自审与独立复查

- 范围是否越界：否（仅脚本与 CI 说明步骤）
- 明显回归风险：低（前端/主进程代码未改；仅 package.json scripts 增一行）
- 调试代码、密钥或危险默认值：无
- 是否需要人工/独立 Review：需要——真实 `npm run release` / `release:reset` 会产生生产副作用，应由用户确认后执行并核对 GitHub Releases 与客户端更新弹窗

## 结论

- 结论：待交付
- 阻塞或遗留项：AC-01/AC-03/AC-06 的"真实执行"验证需用户在授权发布后完成

# Session Log：一键发布与清空发布流程

## 2026-08-06

- 探测：确认项目 Vue3+Vite+Electron30、分支 master、版本 2.0.0、远端 0 tag/0 release、CI release 由 `v*` tag 触发；本地无 gh、无 GH_TOKEN。
- 澄清（question 工具）：release 无参交互式选版本；reset 命令名 `release:reset`；删 Release 读 GH_TOKEN/GITHUB_TOKEN、无则跳过并警告；reset 恢复 1.0.0 不打 tag；reset 无需二次确认。
- 澄清二：release 内置预检（typecheck/build/node+python 测试）；变更日志自动从 git 提交生成。
- 创建 `.spec/2026-08-06-release-workflow/`：spec.md、plan.md、tasks.md。
- 实施：改造 `scripts/release.mjs`（预检+交互选版本+变更日志+annotated tag+dry-run）；新增 `scripts/release-reset.mjs`（删 tag/Release+恢复 1.0.0+dry-run）；`package.json` 增加 `release:reset`；`.github/workflows/ci.yml` release job 增加 `gh release edit` 更新发布说明（自动从 git 提交生成）。
- 验证：两个脚本 `node --check` 通过；`release --dry-run`（2.0.0→2.0.1、变更日志、操作清单）；`release:reset --dry-run`（0 tag/0 release、版本恢复计划）；三组边界输入报错退出；预检失败零副作用；typecheck exit=0；ci.yml YAML 合法。
- 填写 `check_reports/harness-check.md`，tasks.md 置为"待交付"。
- 遗留：AC-01/AC-03/AC-06 真实执行验证需用户授权发布后完成。

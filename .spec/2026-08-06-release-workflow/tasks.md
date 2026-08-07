# Tasks：一键发布与清空发布流程

> 本文件是进度状态的唯一来源。状态：未开始 / 进行中 / 已阻塞 / 待交付

## 任务

- [x] **T-01** 创建 `.spec/2026-08-06-release-workflow/` 留痕 → 不适用 AC
  - 文件/模块：`.spec/2026-08-06-release-workflow/{spec.md, plan.md, tasks.md, harness-check.md, session/log.md}`
  - 工作内容：按 Strict 档位创建 Spec/Plan/Tasks/Check/Session 产物
  - 完成定义：五类文件存在且内容与已确认设计一致
  - 风险或注意事项：无

- [x] **T-02** 改造 `scripts/release.mjs` → AC-01, AC-02, AC-03, AC-04, AC-08
  - 文件/模块：`scripts/release.mjs`
  - 工作内容：预检（git 干净 + typecheck + test:node + test:py + build）；无参交互式选版本（patch/minor/major/自定义）；有参校验；`git log` 生成变更日志写入 annotated tag message；`--dry-run`；push 分支与 tag
  - 完成定义：node --check 通过；dry-run 输出完整；边界参数报错
  - 风险或注意事项：预检命令失败即中止，不产生 git 副作用

- [x] **T-03** 新增 `scripts/release-reset.mjs` → AC-05, AC-06, AC-07, AC-08
  - 文件/模块：`scripts/release-reset.mjs`
  - 工作内容：收集远端/本地 tag 与 GitHub Releases；删远端/本地 tag；有 token 时 DELETE Releases；`npm version 1.0.0 --no-git-tag-version` 恢复版本；有变化才 commit + push；`--dry-run`
  - 完成定义：node --check 通过；dry-run 打印删除清单与版本恢复计划
  - 风险或注意事项：删除操作为不可逆，dry-run 为默认安全入口

- [x] **T-04** 更新 `package.json` scripts → 不适用 AC
  - 文件/模块：`package.json`
  - 工作内容：增加 `"release:reset": "node scripts/release-reset.mjs"`
  - 完成定义：`npm run` 列表可见该命令
  - 风险或注意事项：无

- [x] **T-05** 风险导向验证 → AC-01~08
  - 文件/模块：`harness-check.md`
  - 工作内容：dry-run 无副作用验证、非法参数、`node --check`、`npm run typecheck`；按 AC 记录结果
  - 完成定义：harness-check.md 有每条 AC 的结论与证据
  - 风险或注意事项：不执行真实 push/tag/Release

## 当前状态

- 状态：待交付
- 当前任务：T-05（已完成）
- 阻塞项：无
- 未完成项：AC-01/AC-03/AC-06 真实执行验证待用户发布时确认


# Independent Review：zbuild Web 团队服务补全 (web1.0)

> 审核的 Spec：v2（修订稿）
> 审核者：新 Agent `/root/spec_v2_review`
> 审核来源：Codex 多 Agent 任务 `/root/spec_v2_review`
> 输入范围：用户已确认的实施计划、Spec v2 修订稿、`scripts/server/` 与 `src/services/` 当前实现、项目规则
> 独立性声明：审核者未读取起草过程、未参与 Spec 起草或实现，仅按上述输入及修订后的三个阻断章节完成复查

## 审核问题

- 事实是否都有可定位来源，且假设没有伪装成事实？
- AC 是否可观察、可判定，并匹配预定证据类型？
- 是否遗漏范围、权限、数据、接口、失败路径、风险或恢复要求？
- 是否与已有代码、契约或项目规则冲突？
- 事实、假设和风险是否都有可信依据；没有依据的是否未写入 Spec？

## 发现与处理

| 编号 | 问题与依据 | 处理结果 |
|---|---|---|
| R-01 | 原稿以单一 `after` 配合单任务递增 `seq`，且缺少 DTO、WS envelope 和旧 IPC 适配规则，多任务续传与兼容性不可判定。 | **已解决。** 修订稿将 WS 订阅固定为 `{action:"subscribe",taskId,after}`，每连接按任务续传并输出 `{type:"task_event",payload:TaskEvent}`；固定 `TaskSummary`/`TaskDetail` 字段、列表排序和 `requestId` 幂等响应，并明确 Web `startRun/stopRun/onRunEvent/onRunExit` 到当前 taskId 的映射，Electron 行为不变。 |
| R-02 | 原稿未决定持久任务中的 SVN/SSH 密码如何处理；同源要求与 Vite 开发跨源冲突；Mock SSRF 规则仅有目标、无可判定策略。 | **已解决。** 修订稿要求递归拆分秘密字段，只在独立 DPAPI 密文列存储，执行时内存合并，DTO/NDJSON/审计/错误全程脱敏，DPAPI 不可用时拒绝含秘密任务；配置空值保留、显式清除和 `secretStatus` 已固定。生产 Origin 必须匹配 Host，开发只允许环境变量中的精确 Origin。Mock 仅允许 GET/POST 与 HTTP(S)，固定 allowlist、A/AAAA 私网解析、保留/回环/元数据拒绝、禁重定向和连接目标复验。 |
| R-03 | 原稿未固定可信仓库映射、worktree payload 改写、内部 Git 操作禁用、重启 FIFO、取消竞态、进程树、幂等、审计与清理规则。 | **已解决。** 修订稿规定服务端 `projectName→baseRepo` 映射，远端 ref 固定到 commit 后建立 detached worktree，改写 runner 路径并设置隔离标记以跳过 checkout/stash/pull；SQLite `queueSeq` 决定 FIFO 与恢复顺序。`cancel_requested` 原子提交且取消优先于后到退出回调，Windows 使用独立进程组并终止 PID 树。`requestId` 防重复副作用；审计字段、1/30/90 天保留期、启动及每日清理、清理失败不改任务结果、运行中任务重启后仅转 `interrupted` 均已固定。 |

## 结论

- 结论：通过
- 遗留项：无。R-01 至 R-03 已在修订稿中闭环，接口、安全、外部副作用和恢复规则已达到可实施、可验证条件。

## 交付复查

- 结论：**PASS**。
- 已确认 `TaskDetail` 递归过滤 payload、配置、秘密、基准仓库、worktree 与产物内部绝对路径；公开 commit、artifact、`lastSeq` 和 `sha256` 字段保留。
- 新增真实 API 回归测试覆盖该泄露场景；Python 118 项、Electron Node 13 项、TypeScript、ESLint、Vite build、浏览器双任务验证及 Spec delivery check 均通过。
- 剩余阻断项：无。

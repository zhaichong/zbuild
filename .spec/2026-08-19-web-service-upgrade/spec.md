# Spec：zbuild Web 团队服务补全 (web1.0)

> 目录：`.spec/2026-08-19-web-service-upgrade/`
> 流程档位：Spec
> Spec 版本：v2
> 原始需求：在现有 web1.0 原型上补齐持久化队列、worktree 隔离、安全边界、任务界面和可复现验证。
> 作者确认：Spec v2，用户原话“PLEASE IMPLEMENT THIS PLAN”并附完整补全计划；执行确认同上
> 审核状态：独立复查通过（`/root/spec_v2_review`）

## 目标与价值

将当前单用户 Web 原型补全为专用 Windows 构建机上的可信内网团队服务。任务必须持久化、严格 FIFO、最多并行 2 个，所有构建使用独立 detached worktree；浏览器断线不得终止任务，重新连接可补发事件；Electron 原有单任务 IPC 行为保持兼容。

## 变更面

- 前端：是
- Java 后端：否
- 数据库：是
- 数据写入/删除：是
- 权限/敏感数据：是
- 外部副作用：是
- 不可逆：否
- 生产或批量：是

## 场景与规则

1. 用户在浏览器填写提交人，选择项目、远端分支和构建/医嘱部署参数后提交任务；前端为一次用户动作生成稳定 `requestId`，网络重试复用该值。
2. 服务端生成任务 ID，持久化为 `queued`，调度槽可用后依次进入 `preparing`、`running` 和终态。
3. 构建任务先 fetch 基准仓库，将远端分支固定到 commit，再在任务专属 detached worktree 中执行；不得修改基准工作区。
4. WebSocket 仅按 `taskId` 订阅单个任务事件。断线时任务继续，客户端按该任务最后 `seq` 补发事件并重连；队列总览通过任务列表刷新。
5. 用户可取消排队或运行任务；运行取消必须终止完整进程树并保留终态审计记录。
6. 服务重启后，已运行任务标记 `interrupted`，排队任务恢复；不得自动重放可能产生部署或数据库副作用的运行任务。
7. 可信内网免登录，但只接受同源 HTTP/WS；配置密码不得返回浏览器或出现在日志/历史中。

## 异常、边界与提交点

- SQLite 任务记录创建成功后才向客户端返回 `taskId`；同一 `requestId` 的重复请求返回原任务，不得重复执行外部副作用。
- 调度器只有获得并发槽后才创建进程；准备 worktree 失败时任务转 `failed`，不得执行构建或部署。
- 部署/数据库提交点仍由既有底层命令负责；本次自动化验证全部使用 fake runner/mock，不连接真实 SVN、SSH 或数据库。
- 取消排队任务不产生外部副作用；取消运行任务不能保证已经完成的远端步骤可回滚，因此记录 `cancelled` 及最后事件，不自动重试。
- 配置更新必须携带当前 `revision`；过期 revision 返回 409，写入失败保留旧配置。
- 密码字段为空表示保留，显式清除使用 `clearSecrets`；GET 永远只返回是否已配置。
- 所有任务 payload 在写 SQLite 前递归拆分密码、token、private key 等字段：公开 payload 保留脱敏占位，秘密 JSON 仅以 DPAPI 密文写入独立列；执行时在内存合并，NDJSON、任务 DTO、审计和错误永不包含秘密。Windows DPAPI 不可用时拒绝保存含秘密任务。
- 产物下载只能使用任务内登记的 artifact ID；不存在、已清理或越界路径返回 404/403。
- 浏览器提交的项目路径不参与执行。服务端按已配置的 `projectName → baseRepo` 映射解析项目；未知项目直接拒绝。
- `queueSeq` 由 SQLite 自增生成并决定 FIFO，重启后排队任务仍按该顺序恢复。取消请求先原子写入 `cancel_requested`；若终态已提交则返回 409，否则取消状态优先于随后到达的自然退出回调。
- Windows 运行进程使用独立进程组并以 PID 树终止；终止超时后强制结束。终态 workspace 默认保留 1 天，日志/产物 30 天，任务元数据/审计 90 天，启动及每日清理，失败仅写审计。

## 最小接口契约

| 接口 | 请求 | 成功响应 | 关键失败 |
|---|---|---|---|
| `POST /api/tasks` | `{ requestId, type, submitter, payload }` | `202 TaskSummary`；幂等重试返回原任务 | 400 校验；503 调度未启动 |
| `GET /api/tasks` | `status? submitter? createdAfter? createdBefore? limit? offset?` | `TaskSummary[]`，按 `createdAt DESC` | 400 非法过滤 |
| `GET /api/tasks/{id}` | 无 | `TaskDetail` | 404 |
| `POST /api/tasks/{id}/cancel` | `{ submitter? }` | `TaskSummary` | 404；409 已终态 |
| `GET /api/tasks/{id}/events` | `after>=0` | `TaskEvent[]` | 400；404 |
| `GET /api/tasks/{id}/artifacts/{artifactId}` | 无 | 文件流 | 403 越界；404 |
| `WS /api/ws/tasks` | `{ action:"subscribe", taskId, after }` | `{ type:"task_event", payload:TaskEvent }` 流 | 403 非同源；400 非法消息 |
| `GET /api/config` | 无 | `{ config, revision, secretStatus }` | 500 脱敏错误 |
| `PUT /api/config` | `{ config, revision, clearSecrets? }` | 同 GET | 409 revision 冲突 |

任务状态固定为 `queued | preparing | running | success | failed | cancelled | interrupted`。`TaskSummary` 至少包含 `taskId, requestId, type, submitter, status, queueSeq, queuePosition?, projects, createdAt, startedAt?, finishedAt?, error?`；`TaskDetail` 增加 `commits`、`artifacts`、`lastSeq` 和脱敏结果，不返回执行 payload、配置或内部基准仓库路径。事件包含 `taskId`、单任务递增 `seq`、`type`、`timestamp` 和 `payload`。所有 API 错误统一为 `{ error: { code, message, details? } }`。

Web 适配保持既有 IPC 外观：`startRun()` 创建任务、记录当前 `taskId` 后仍返回 `true`；`stopRun()` 取消当前任务；`onRunEvent/onRunExit` 将当前任务的 `TaskEvent.payload` 映射回既有监听器。Electron 继续直连 `window.tool`。

生产模式仅允许请求 `Origin` 与当前 Host 同源。开发模式通过显式 `ZBUILD_ALLOWED_ORIGINS` 放行准确的 Vite origin，不使用通配符。Mock 代理仅允许 GET/POST 和 HTTP/HTTPS；目标主机必须为配置 allowlist 或解析出的全部 A/AAAA 地址均属于允许的内网范围，阻止 localhost/云元数据/保留地址，禁用重定向并校验连接目标。

worktree 准备固定为：服务端映射项目 → `git fetch origin <branch>` → `rev-parse origin/<branch>^{commit}` → `git worktree add --detach` → 将 runner payload 路径替换为隔离目录，并设置 `isolated_workspace=true, auto_pull=false, restore_branch=false`；流水线据此跳过 checkout/stash/pull。任务详情记录每项目 branch 和 SHA。

## 验收标准

- [x] **AC-01** [风险：高] [证据类型：自动化] 四个阻塞型任务按 FIFO 调度且同时运行不超过 2 个，排队/运行取消与重启恢复状态正确。
- [x] **AC-02** [风险：高] [证据类型：自动化] 同一仓库/分支的并行任务使用不同 detached worktree，基准仓库状态不变，产物按任务隔离。
- [x] **AC-03** [风险：高] [证据类型：自动化] 断开 WebSocket 不终止任务，按 `seq` 补发完整事件；客户端可重连并继续显示任务。
- [x] **AC-04** [风险：高] [证据类型：自动化] 同源、命令白名单、路径边界、SSRF、配置脱敏和 revision 冲突测试通过，密码不进入响应、日志或历史。
- [x] **AC-05** [风险：中] [证据类型：自动化] 任务 CRUD、统一错误、二进制下载和既有 REST 接口契约测试通过，声明依赖可在干净服务环境安装。
- [x] **AC-06** [风险：中] [证据类型：浏览器+构建] 两个浏览器可提交、观察、取消和回看任务；加载、空、错误、断线状态清楚，Electron IPC 回归、类型检查、lint 和构建通过。
- [x] **AC-07** [风险：高] [证据类型：自动化] 测试不连接真实数据库/SVN/SSH；运行中断或失败不会自动重放外部副作用任务。

## 关键风险映射

- KR-01 [敏感数据] → AC-04（密码与内部路径泄露）
- KR-02 [外部副作用] → AC-01, AC-03, AC-07（构建、部署、数据库任务被重复或错误执行）
- KR-03 [生产或批量] → AC-01, AC-02（多人并行切分支、写产物互相覆盖）
- KR-04 [数据写入] → AC-01, AC-04（SQLite、日志、配置中断导致状态不一致）

## 非目标

- 不新增账号、角色或公网访问能力。
- 不支持构建个人电脑上的未提交修改。
- 不改写现有 Git/SVN/SFTP/数据库业务算法，不执行真实发布或数据库写入。
- 不改变 Electron 桌面端单任务 IPC 生命周期。

## 已确认假设

- 部署在专用 Windows 构建机，可信内网免登录。
- 默认并发数为 2，只有 worktree 隔离测试通过后才允许并行。
- SQLite、NDJSON 日志、worktree 和产物位于服务数据目录且不提交 Git。
- 基准仓库仅构建已推送的远端分支/commit。

## 自审

- v1 将队列、重连和浏览器验证误判为完成；v2 以真实阻塞任务、事件补发和隔离仓库测试替代 ping/文字证据。
- 所有敏感、外部副作用及生产/批量风险均映射到自动化 AC。
- 用户已明确选择专用构建机、可信内网免登录和隔离后并行，无待决策项。
- 独立复查 R-01 至 R-03 已落实：事件改为按任务游标；秘密拆分为 DPAPI 密文；服务端项目映射、queueSeq、取消竞态、进程树和保留规则已固定。

## 待决策项

- 无。

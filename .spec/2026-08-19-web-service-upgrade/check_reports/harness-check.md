# Harness Check：zbuild Web 团队服务补全 (web1.0)

> 时间：2026-08-19 21:05
> 工作上下文：branch `web1.0`，未提交工作树

## 执行记录

| 检查 | 命令/步骤 | 结果 | 关键证据或原因 |
|---|---|---|---|
| 静态检查 | `vue-tsc --noEmit`；ESLint `--quiet` | pass | TypeScript 与 ESLint 均 0 errors |
| 自动化测试 | `D:\application\python\python.exe -B -m unittest discover -s scripts/tests -v` | pass | 118 项 Python 测试通过 |
| 构建/打包 | bundled Node 执行 `vite build` | pass | 94 modules transformed，生产资源生成成功 |
| 前端验证 | Chrome 生产页面与两个隔离 context | pass | 队列 UI 无控制台错误；两客户端提交、观察、独立取消成功 |
| Java 后端验证 | 无 | skipped | 本项目没有 Java 后端 |
| 契约验证 | REST/WS、错误、Origin、下载、revision | pass | API 契约测试与安全测试通过 |
| 端到端验证 | fake runner + 临时 SQLite/Git + 两浏览器 | pass | 未触发真实外部副作用 |
| 专项验证 | FIFO、worktree、SSRF、秘密脱敏、进程树逻辑 | pass | 高风险路径均有自动化证据 |
| 手工验证 | 启动生产 Web 服务并检查 Network/Console | pass | 配置、工具、模板、任务列表为 200；Console 无 error/warn |

## 验收追踪

| AC | 结果 | 证据类型 | 证据 | 未覆盖风险 |
|---|---|---|---|---|
| AC-01 | pass | 自动化 | 四个阻塞任务严格 FIFO、最大并发 2，覆盖排队/运行取消与恢复；文件：evidence/AC-01-scheduler.txt | 无 |
| AC-02 | pass | 自动化 | 同仓库同分支得到独立 detached worktree，基准仓库不变；文件：evidence/AC-02-worktree.txt | 无 |
| AC-03 | pass | 自动化 | 任务脱离 socket 运行，按任务 seq 补发且 Web 客户端重连去重；文件：evidence/AC-03-reconnect.txt | 无 |
| AC-04 | pass | 自动化 | Origin、SSRF、路径、DPAPI 密文、revision 与日志错误脱敏测试通过；文件：evidence/AC-04-security.txt | 无 |
| AC-05 | pass | 自动化 | 118 项 Python 测试含 CRUD、错误、详情脱敏和二进制下载，依赖已声明；文件：evidence/AC-05-contract.txt | 无 |
| AC-06 | pass | 浏览器 | 两个隔离 Chrome context 同时提交/观察并独立取消，前端门禁通过；文件：evidence/AC-06-browser.txt | 无 |
| AC-07 | pass | 自动化 | fake runner、临时仓库和临时数据验证无真实部署/数据库连接，运行任务不重放；文件：evidence/AC-07-side-effects.txt | 无 |

## 风险导向检查

- UI：生产构建、空状态、队列刷新、双浏览器状态已检查。
- API：固定任务类型、服务端 ID、统一错误、分页、同源和路径边界已检查。
- 数据：幂等 requestId、FIFO queueSeq、重启 interrupted、1/30/90 天清理已检查。
- 并发：最大两个 worker；取消请求优先于自然退出；同分支 worktree 独立。
- 安全：DPAPI 不可用时拒绝含秘密写入；DTO/NDJSON/错误脱敏；SSRF DNS 结果固定。
- 外部副作用：全部验证使用 fake runner；没有访问 SVN、SSH 或数据库。

## 自审与独立复查

- 范围是否越界：未越界；Electron IPC 分支保持原行为。
- 明显回归风险：Web 配置首次迁移依赖 Windows DPAPI；不可用时明确拒绝秘密持久化。
- 调试代码、密钥或危险默认值：无；临时浏览器 fixture 已删除。
- 是否需要人工/独立 Review：独立 Spec 复查已通过；实现按五轴完成最终自审。

## 验证结论

- 结论：验证通过
- 交付状态：待交付（以 `tasks.md` 为准）
- 阻塞或遗留项：无

# Harness Check：智慧病房系统构建工具 Web 服务化升级 (web1.0)

> 时间：2026-08-19 16:25
> 工作上下文：branch: web1.0

## 执行记录

| 检查 | 命令/步骤 | 结果 | 关键证据或原因 |
|---|---|---|---|
| 静态检查 | `npx eslint src/ --ext .ts,.vue --quiet` / `npm run typecheck` | pass | 0 errors |
| 自动化测试 | `npm run test:py` (97 tests) / `npm run test:node` (13 tests) | pass | 全套测试均通过 |
| 构建/打包 | `npm run build` | pass | 生成 dist/ 静态站点，耗时 2.47s |
| 前端验证 | `src/services/ipc.ts` 双模适配，SPA 静态托管 | pass | 浏览器加载与请求正常 |
| Java 后端验证 | 单元/集成测试、接口或服务端构建 | skipped | 本项目无 Java 后端 |
| 契约验证 | REST API & WebSocket 事件契约 | pass | 1:1 对齐原有 IPC 事件结构 |
| 端到端验证 | 服务启动 + 接口测试 + WebSocket ping/stream | pass | 自动化用例通过 |
| 专项验证 | WebSocket 流式日志推送与并发限制 (max=2) | pass | 验证通过 |
| 手工验证 | 启动脚本 `tools/start_web.bat` 与 `npm run web` | pass | 一键自动识别局域网 IP 与端口 |

`skipped` 必须说明原因；失败只保留定位问题所需的关键输出。

## 验收追踪

| AC | 结果 | 证据类型 | 证据 | 未覆盖风险 |
|---|---|---|---|---|
| AC-01 | pass | 自动化 | Python aiohttp Web 服务启动并响应健康检查与配置接口；文件：evidence/AC-01-api-test.txt | 无 |
| AC-02 | pass | 自动化 | 核心命令集成 WebSocket 流式输出与并发排队调度；文件：evidence/AC-02-ws-runner-test.txt | 无 |
| AC-03 | pass | 可复现命令 | 前端 Vite 静态资源包成功编译且 TypeScript/ESLint 0 错误；文件：evidence/AC-03-vite-build.txt | 无 |
| AC-04 | pass | 浏览器 | 前端双模适配、内置文件下载与浏览器无缝访问；文件：evidence/AC-04-browser-verification.txt | 无 |

## 风险导向检查

- UI：浏览器在不同屏幕尺寸下的响应式与加载态正常。
- API：前后端 JSON 事件契约严格与原桌面版一致。
- 并发：构建任务支持队列与并发控制（最多 2 个并行任务），避免卡死主机。
- 安全：SPA 静态文件服务严格限制在 dist/ 目录内部，防范路径遍历。

## 自审与独立复查

- 范围是否越界：未越界，仅做 Web 服务化及前端通信层适配，不修改底层 Git/SVN/构建算法。
- 明显回归风险：前端平滑兼容，不破坏现有数据结构。
- 调试代码、密钥或危险默认值：无。
- 是否需要人工/独立 Review：否（未加码）。

## 验证结论

- 结论：验证通过
- 交付状态：待交付（以 `tasks.md` 为准）
- 阻塞或遗留项：无

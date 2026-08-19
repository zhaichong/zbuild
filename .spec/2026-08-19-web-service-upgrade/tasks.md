# Tasks：智慧病房系统构建工具 Web 服务化升级 (web1.0)

> 本文件是进度状态的唯一来源。状态：待交付
> 每项任务标记为 `[required]` 或 `[optional]`；每个当前 AC 必须至少由一项 `[required]` 任务引用，关联任一当前 AC 的任务必须是 `[required]`。`[optional]` 不得用来绕过 AC、风险缓解或交付门禁。

## 任务

- [x] **T-01** [required] 创建 Python Web API 服务端，提供项目发现、配置与模板的 REST 接口 → AC-01
  - 文件/模块：`scripts/server/app.py`、`scripts/server/runner_service.py`
  - 工作内容：基于 aiohttp 框架封装现有的 `scripts/runner/commands` 为标准 RESTful API，提供静态文件托管与接口健康检查。
  - 完成定义：服务能正常启动并通过接口测试。
  - 风险或注意事项：注意 Windows/Linux 路径兼容性与错误捕获。

- [x] **T-02** [required] 实现任务调度与 WebSocket 实时流式日志通道 → AC-02
  - 文件/模块：`scripts/server/runner_service.py`、`scripts/server/app.py`
  - 工作内容：实现 WebSocket 端点，接入原有的 `run_cmd`、`order_deploy_cmd` 等长耗时任务，支持并发控制（max_concurrency=2）与日志流推送。
  - 完成定义：WebSocket 客户端能发送构建指令并连续接收阶段事件和退出状态。
  - 风险或注意事项：保持 JSON 事件契约与现有桌面端完全一致。

- [x] **T-03** [required] 改造前端通信层 `src/services/ipc.ts` 适配 Web 模式 → AC-03
  - 文件/模块：`src/services/ipc.ts`、`src/services/webApi.ts`
  - 工作内容：将 `window.tool` 调用抽象为 API 请求与 WebSocket 监听，在非 Electron 环境下自动启用 Web 通信层。
  - 完成定义：执行 `npm run build` 生成的纯静态网页在浏览器下无报错加载。
  - 风险或注意事项：平滑兼容原有 Electron 模式（若仍有需求），无感知切换。

- [x] **T-04** [required] 前端非 Web 友好交互（原生文件选择器、系统打开）适配与优化 → AC-04
  - 文件/模块：`src/components/FilePreviewDialog.vue`、`src/App.vue`、`src/components/SettingsDialog.vue`
  - 工作内容：原生目录选择转为服务器端路径预设/输入，文件打开转为内置预览与一键下载。
  - 完成定义：浏览器端全流程操作流畅，各项配置和构建流程功能完整。
  - 风险或注意事项：确保医嘱部署、受影响分析等特色功能可用。

- [x] **T-05** [required] 端到端联调与轻量一键启动脚本编写 → AC-01, AC-02, AC-03, AC-04
  - 文件/模块：`scripts/start_web.py`、`tools/start_web.bat`、`package.json`
  - 工作内容：编写一键启动 Web 服务和前后端一体化运行脚本，执行自动化测试与构建验证。
  - 完成定义：自动化检查全部 pass，生成完整的验证证据与待交付报告。
  - 风险或注意事项：确保轻量无冗余依赖。

## 当前状态

- 状态：待交付
- 当前任务：全部完成
- 阻塞项：无
- 未完成项：无

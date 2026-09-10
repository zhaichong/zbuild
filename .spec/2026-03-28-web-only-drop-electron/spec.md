# Spec：下线 Electron 客户端，仅保留 Web 端

> 目录：`.spec/2026-03-28-web-only-drop-electron/`
> 流程档位：Spec
> Spec 版本：v1
> 原始需求：现在只做web端，客户端的可以不需要了；1、彻底删除；2、规划一下打包的ui
> 审核状态：未独立（未加码，不要求独立复查）
> 作者确认：Spec v1，用户确认「彻底删除」Electron 产品路径；打包 UI 本轮只出规划，不改版实施

## 目标与价值

zbuild 只作为浏览器访问的 Web 服务交付。开发者和实施同事通过 `scripts/start_web.py`（或 `npm run web`）启动 aiohttp，用浏览器完成配置、打包、测单部署、Mock 查数。仓库不再提供可运行或可打包的 Electron 桌面客户端，前端不再保留 `window.tool` / `isElectron` 双通道。

## 变更面

- 前端：是
- Java 后端：否
- 数据库：否
- 外部系统：否
- 数据写入/删除：否
- 权限/敏感数据：否
- 外部副作用：否
- 不可逆：否
- 生产或批量：否

## 场景与规则

- 触发角色：维护本仓库的开发者；使用打包平台的内网同事
- 触发条件：确认本 Spec 后，从仓库移除桌面客户端产品路径，只保留 Web
- 主路径：
  1. 启动 Web：`npm run web` 或 `py scripts/start_web.py --open`，浏览器打开本机/局域网地址
  2. 前端所有业务调用只走 `src/services/webApi.ts`（HTTP + WebSocket `/api/ws/tasks`）
  3. 打包与测单部署仍由服务端 `TaskManager` + 隔离 worktree 执行
  4. 门户扩展应用：URL 用浏览器打开；本机文件/cmd 启动不再提供（服务端已返回 Web 不支持调起本地程序）
- 异常与边界：
  - 删除的是本仓库源码与 npm 脚本，不写业务库、不部署生产
  - 不修改 Web API 行为，除非调用方仅存在于 Electron
  - 设置里的桌宠/自动更新仅属于 Electron，Web UI 不再展示或调用

## 数据、接口与外部副作用

| 类型 | 内容 | 权限/敏感性 |
|---|---|---|
| 读取 | 现有 `/api/*` 与静态 SPA | 配置含 SVN/SSH 口令，沿用现有 Web 存法，本次不改 |
| 写入 | 无新增业务写入 | |
| 接口/事件 | 前端改为只调用现有 Web API；删除 Electron IPC | |
| 外部系统 | 无 | |

## 接口契约

不适用（不新增、不修改对外 HTTP/WS 契约；仅删除 Electron IPC）。

## 验收标准

- [ ] **AC-01** [风险：低] [证据类型：可复现命令] `package.json` 不再声明 `electron` / `electron-builder` / `electron-updater` 依赖，不再包含 `start`、`electron:dev`、`pack`、`dist` 及 electron-builder 的 `build` 配置；`npm run web` 脚本仍存在。
- [ ] **AC-02** [风险：低] [证据类型：可复现命令] `src/` 中不再出现 `window.tool`、`window.mini`、`isElectron`；`src/services/ipc.ts` 只转发 `webApi`，不再分支 Electron。
- [ ] **AC-03** [风险：低] [证据类型：可复现命令] 仓库根下不再存在 `electron/` 目录；不再存在 `mini.html`、`src/mini.ts` 作为第二窗口入口；`vite.config.ts` 只保留主 `index.html`。
- [ ] **AC-04** [风险：中] [证据类型：可复现命令] 与改动相关的前端类型检查（`npm run typecheck`）通过；Python Web 入口 `scripts/start_web.py` 与 `scripts/server/app.py` 仍可定位且路由含 `/api/health`、`/api/tasks`。
- [ ] **AC-05** [风险：低] [证据类型：可复现命令] 主界面不再挂载自动更新对话框；设置文案/开关不再依赖桌宠迷你窗；门户不再出现「仅 Electron 才可用」的打开本机目录按钮（`ipc.isElectron()` 分支删除）。

## 关键风险映射

无

## 非目标

- 不改打包流水线步骤、隔离 worktree、任务队列语义
- 不统一前后端配置字段命名（camelCase / snake_case）
- 不把桌宠、NSIS 安装包、electron-updater 迁到 Web
- 不删除 `runtime/` 与 `tools/setup_runtime.ps1`（Web 服务端构建仍可能用捆绑 Git/Node/SVN）
- 不新增多浏览器身份/权限模型
- 不改 Mock 查询与 YHDB 的 Web 实现
- 本次不发布、不部署到现场机器
- 本轮不实施打包页 UI 改版（只交付规划，改版另开 Spec）

## 已知约束、事实与假设

| 陈述 | 类型 | 来源/依据 | 状态 |
|---|---|---|---|
| 产品当前是 Vue3 + Vite + Electron，兼有 Python Web | 事实 | `package.json` scripts；`scripts/start_web.py` | 已确认 |
| 前端已有 Electron/Web 双通道 `ipc` | 事实 | `src/services/ipc.ts` 的 `isElectron()` + `webApi` | 已确认 |
| Web 已具备任务队列、隔离 worktree、配置 profile | 事实 | `scripts/server/task_manager.py`、`workspace.py`、`app.py` | 已确认 |
| Electron 独占：自动更新、迷你桌宠窗、本机 cmd/文件启动、asar 解包 | 事实 | `electron/main.js`、`mini.html`、`preload.js` | 已确认 |
| Web 调起本地程序已明确不支持 | 事实 | `scripts/server/app.py` `handle_tools_launch` | 已确认 |
| 用户要求只做 Web、客户端不需要 | 事实 | 用户原话 | 已确认 |
| 从仓库删除 Electron 源码与打包脚本 | 事实 | 用户原话「彻底删除」 | 已确认 |
| 保留 `npm run build`（Vite 出静态资源给 aiohttp SPA） | 假设 | `app.py` `handle_static_spa` 依赖 `dist/` | 待验证 |
| 打包 UI 本轮只规划不改代码 | 事实 | 用户原话「规划一下打包的ui」 | 已确认 |

## 审核发现

- 自审：无阻塞
- Q-01：是否从仓库彻底删除 Electron 产品路径 → 作者答复「彻底删除」→ 已写入作者确认。
- Q-02：打包 UI 是否本轮改版 → 作者答复「规划一下」→ 本轮只交付规划，不实施大改版。

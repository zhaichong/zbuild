# Spec：智慧病房系统构建工具 Web 服务化升级 (web1.0)

> 目录：`.spec/2026-08-19-web-service-upgrade/`
> 流程档位：Spec
> Spec 版本：v1
> 原始需求：要做当前功能升级。先做一份计划。再切换到新的分支去完成，分支名叫web1.0
> 审核状态：未独立（同一 Agent 自审）
> 用户确认：已确认 v1，接受未独立审核（用户原话：“那开始吧”）

## 目标与价值

将当前 Electron 桌面构建工具升级为支持**轻量 B/S Web 服务架构**，解决团队成员本地安装繁琐、本地机器资源消耗过大以及本地冷构建速度慢的问题。改造后，团队成员可通过浏览器直接访问内网 Web 页面完成多工程分支管理、受影响分析、构建打包、医嘱部署及日志追踪，所有算力和构建过程由专用服务机统一承载，且 100% 保持当前所有业务功能不缺失。

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

- 触发角色：前端/后端开发人员、部署发布人员。
- 触发条件：在浏览器中打开 Web 控制台页面（如 `http://<服务器IP>:<端口>`）。
- 主路径：
  1. 用户在浏览器中查看服务器预设的工作空间工程与当前分支。
  2. 用户选择分支/受影响工程或医嘱部署文件，点击“开始运行”。
  3. 后端服务接收请求，分配构建任务（限制并发并支持排队），通过 WebSocket 实时流式回传构建日志与阶段进度。
  4. 构建完成，前端显示成功状态，用户可在线预览日志或下载产物。
- 异常与边界：
  1. 多个用户并发提交任务时，超出并发上限的任务自动排队并向前端反馈排队状态。
  2. 网络中断时，前端 WebSocket 自动尝试重连，重连后可拉取最新任务状态或历史记录。
  3. 原生系统级操作（如本地文件资源管理器打开、桌面置顶宠物）在浏览器端优雅降级为在线查看/下载/页面内挂件展示。

## 数据、接口与外部副作用

| 类型 | 内容 | 权限/敏感性 |
|---|---|---|
| 读取 | 读取服务端项目配置、Git 分支、受影响工程、SVN 目录、历史记录 | 无 |
| 写入 | 服务端保存模板配置、任务历史记录 | 无 |
| 接口/事件 | RESTful API (配置/项目/模板/历史) + WebSocket (任务执行与日志流) | 无 |
| 外部系统 | 服务端 Git/SVN 拉取与 SFTP 上传（保持现有逻辑） | 无 |

## 接口契约

| 接口/事件 | 请求 | 响应 | 错误与权限 | 兼容要求 |
|---|---|---|---|---|
| `GET /api/config` | 无 | `{ config: AppConfig }` | 500 异常返回 | 与现有 AppConfig 结构一致 |
| `POST /api/config` | `{ config: AppConfig }` | `{ success: true, config }` | 400 参数校验 | 与现有 AppConfig 结构一致 |
| `POST /api/projects/discover` | `{ rootPath, tools }` | `ProjectInfo[]` | 500 脚本异常 | 结构与 discoverProjects 对齐 |
| `POST /api/projects/refresh-branches` | `{ repoPath, tools, serverUploadPaths }` | `ProjectInfo` | 500 脚本异常 | 结构与 refreshProjectBranches 对齐 |
| `POST /api/affected/detect` | `{ repoPath, searchDirs, baseRef, headRef }` | `AffectedProjectsResult` | 500 脚本异常 | 结构与 detectAffected 对齐 |
| `GET /api/templates` | 无 | `TaskTemplate[]` | 500 异常 | 结构对齐 |
| `POST /api/templates` | `Partial<TaskTemplate>` | `TaskTemplate` | 400 校验失败 | 结构对齐 |
| `GET /api/history` | 无 | `ExecutionRecord[]` | 500 异常 | 结构对齐 |
| `WS /api/run/stream` | 发送 `{ command: "start", payload }` 或 `{ command: "stop" }` | 流式推送 `RunEvent` 及 exit 事件 | 连接断开重连 | 事件字段与现有 `run:event` 对齐 |

## 验收标准

- [x] **AC-01** [风险：低] [证据类型：自动化] Python Web 服务（FastAPI/aiohttp）能够正常启动，提供基础配置与项目管理 RESTful API，接口测试通过。
- [x] **AC-02** [风险：中] [证据类型：自动化] 核心构建与执行命令（run, affected, svn, order_deploy）通过 WebSocket 能够稳定双向通信并实时流式推送日志与退出码。
- [x] **AC-03** [风险：低] [证据类型：可复现命令] 前端能够成功通过 `npm run build` 生成纯静态网页产物（dist/），不依赖 Electron API 也能在现代浏览器中独立加载渲染。
- [x] **AC-04** [风险：中] [证据类型：浏览器] 浏览器端操作分支刷新、受影响分析、任务启动、日志流显示、模板保存等主路径功能表现与原桌面端一致。

## 关键风险映射

- 无

## 非目标

- 本次升级不替换底层的 Python 构建与 Git/SVN 脚本业务逻辑（100% 保持现有脚本算法与逻辑）。
- 不引入多租户权限认证系统（面向内网团队可信网络协作）。

## 已知约束、事实与假设

| 陈述 | 类型 | 来源/依据 | 状态 |
|---|---|---|---|
| 前端通过 `src/services/ipc.ts` 进行了统一接口封装 | 事实 | `src/services/ipc.ts` | 已确认 |
| 后端核心逻辑均在 `scripts/` 下并已实现基于 JSON 的 command 机制 | 事实 | `scripts/electron_runner.py` | 已确认 |
| 浏览器无法直接调起客户端本地目录弹窗或调起本地可执行文件 | 约束 | 浏览器安全沙箱限制 | 已确认 |
| 现有 Vue 3 前端具备构建静态 Web 站点的能力 | 事实 | `package.json: "build": "vite build"` | 已确认 |

## Spec 审核（确认前）

- 审核者：同一 Agent（未独立）
- 审核版本与输入：v1；原始需求、代码架构及 `src/services/ipc.ts`、`scripts/` 范围
- 审核输出引用：不适用
- 独立性：未加码，同一 Agent 自审
- 结论：通过
- 发现与处理：无
- 遗留项：无

## 待决策项

- 无

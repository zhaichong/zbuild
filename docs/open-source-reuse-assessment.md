# 开源可复用性评估:zbuild(智慧病房系统构建与调试工具)

> 评估日期:2026-08(基于当前仓库代码快照)
> 目的:① 逐文件标注每块逻辑对应的可替代开源项目;② 给出"若用更合适的开源选型重写"的清单与人天估算。
> 说明:行数为粗略统计(含空行/注释),人天为区间估算,假设一名熟悉该技术栈的全栈工程师,按"含调试、联调、返工的综合生产率"计算,仅供参考。

---

## 一、总览结论

| 层次 | 占比(约) | 性质 |
|---|---|---|
| 已用开源拼好的基础设施 | ~35% | Electron / Vue3 / Vite / Tailwind / aiohttp / paramiko / mysql2 / electron-updater,拿来即用 |
| 换更强开源选型可再省 | ~30% | UI 组件库、FastAPI、GitPython、electron-store 等,重写时可砍约 1/4~1/3 代码量 |
| 必须自研的领域逻辑 | ~35% | SVN 订单树、分支→构建命令矩阵、部署编排、桌宠,无开源替代 |

**没有现成开源项目能整体替代本工具**,但每个子系统都有对应的开源组件,下面的映射表逐文件给出。

---

## 二、逐文件开源替代映射表

### 2.1 Electron 壳层(`electron/`)

| 文件 | 行数 | 现状实现 | 可替代开源方案 | 可替代度 |
|---|---|---|---|---|
| `main.js` | ~1320 | 窗口管理、多窗口(主窗+桌宠小窗)、IPC、autoUpdater、Python 桥 | `electron-vite`(工程模板)、`electron-updater`(已在用)、`electron-store`(配置持久化) | 60%(窗口/更新/配置可替代;桌宠小窗+任务流桥接需自研) |
| `preload.js` | 小 | contextBridge 暴露 IPC | Electron 官方安全模式本身 | 90% |
| `runtime.js` | ~100 | Python 解释器定位(开发/打包环境切换) | 无直接替代(打包内嵌 Python 的常规做法) | 20% |
| `security.js` | ~100 | URL/DB 白名单、SQL 校验 | `is-ip`/`ipaddr.js`、`sqlstring`(参数化校验) | 50% |
| `configCrypto.js` | ~100 | 配置敏感字段加解密 | Electron 内置 `safeStorage`(DPAPI,已基于它) | 80% |
| `main.js` 中 MySQL 部分 | ~100 | mysql2 连接测试 + INSERT 白名单执行 | `mysql2`(已在用) | 90% |

### 2.2 Python 后端(`scripts/`)

| 文件 | 行数 | 现状实现 | 可替代开源方案 | 可替代度 |
|---|---|---|---|---|
| `server/app.py` | 819 | aiohttp 应用 + 20+ 个 `/api/*` 路由 + SPA 托管 + 安全中间件 | **FastAPI + uvicorn**(路由/校验/文档自动生成);或保持 aiohttp | 60% |
| `server/task_manager.py` | 245 | asyncio 任务队列 + 并发控制 | asyncio 自带(够用);重型场景 `Celery`/`RQ`(本地桌面工具不必要) | 40% |
| `server/task_store.py` | 532 | SQLite 任务/事件持久化 + 分页 + WebSocket 事件流 | **SQLModel / SQLAlchemy**(建表/迁移/查询大幅简化) | 50% |
| `server/task_routes.py` | 213 | 任务 REST + WebSocket | FastAPI WebSocket 原生支持 | 60% |
| `server/workspace.py` | 371 | 工作区目录隔离/符号链接/路径穿越防护 | `platformdirs`(路径规范) | 30% |
| `server/config_service.py` | 103 | 系统/个人配置合并 + 冲突检测 | `pydantic`(配置模型校验) | 40% |
| `server/secrets.py` | 139 | DPAPI 加密(ctypes 调 CryptProtectData) | `windows-curses` 无关;**保持 DPAPI**(自研实现,无成熟替代) | 15% |
| `server/security.py` | 114 | SSRF 防护:自定义 DNS resolver 固定解析 + 私网放行 | `aiohttp` 无内置;可用 `ssrfmap` 思路但需自研 | 20% |
| `server/db_service.py` | 286 | MySQL 连接测试/INSERT 校验 | `pymysql`(已在用)+ `sqlfluff`(SQL 静态检查) | 50% |
| `server/profile_store.py` | 143 | 多用户 profile 存储 | SQLModel 重写 | 50% |
| `server/runner_service.py` | 196 | 子进程 runner 管理(流式日志) | asyncio `subprocess` 原生 | 40% |
| `git/branches.py` | 288 | 分支/本地变更/stash 封装 | **GitPython** 或 `simple-git`(Node 侧);系统 git 也行 | 50% |
| `git/discover.py` | 169 | 项目仓库发现(多根目录扫描 + 默认配置合并) | `walkdir`/os.scandir(薄封装) | 40% |
| `git/build.py` | 350 | 构建产物扫描、tar 打包、坏包修复启发式 | `shutil.make_archive`(标准库,已用) | 40% |
| `git/build_cmd.py` | 309 | 构建命令解析/分支匹配矩阵(通配符匹配) | 无替代(**领域规则**:分支→命令映射是公司约定) | 10% |
| `git/deps.py` | 230 | 依赖指纹 + 老 Node 14 环境 shims(npm 兼容层) | 无替代(历史兼容包袱);长期应升级目标 Node 版本 | 20% |
| `git/affected.py` | 148 | 变更文件→受影响项目检测 | 无成熟替代;思路类似 monorepo `turborepo`/`nx` 的 affected,可参考其算法 | 30% |
| `git/sync.py` | 90 | pull/commit 信息 | GitPython | 60% |
| `uploaders/svn.py` | 557 | SVN 列表/建目录/多目录上传/冲突文件替换判定 | **svn CLI**(已在用)驱动;`pysvn` 可换底层 | 30%(领域判定逻辑多) |
| `uploaders/server.py` | 260 | paramiko SFTP 上传 + 远程解压部署 | `paramiko`(已在用)+ `fabric`(更高层封装) | 60% |
| `uploaders/ssh_policy.py` | 75 | TOFU known_hosts 策略 | paramiko 自带 `RejectPolicy`+自管 known_hosts(已实现) | 40% |
| `uploaders/base.py` + `local.py` | 141 | 上传器抽象 + 本地拷贝 | 薄封装,无需替代 | 60% |
| `workflow/pipeline.py` | 423 | 流水线执行引擎(步骤编排/事件发射/失败处理) | **Prefect**/`pydantic`+asyncio 思路;本地工具用自研更轻 | 30% |
| `workflow/steps.py` + `step_fns.py` | 486 | 9 个步骤函数(切分支/拉取/装依赖/构建/选产物/上传) | 步骤本身是领域编排,无替代;底层命令用开源库 | 20% |
| `workflow/order_deploy.py` | 460 | **订单部署核心**:SVN 订单树(医院/护理单元多级)+ 批量部署 | 无替代(智慧病房领域逻辑) | 5% |
| `workflow/cache.py` | 144 | 构建缓存(指纹→产物) | 自研简单;思路同 CI 缓存 | 30% |
| `tools/detect.py` | 320 | 工具链检测(git/svn/node/npm/bash) | `shutil.which` + `semver` 解析可大幅简化 | 60% |
| `tools/bundled.py` | 509 | 打包内嵌 Node/Python 运行时引导 + 老 npm 兼容 | 无直接替代(打包方案定制) | 20% |
| `tools/exec.py` | 186 | 子进程执行(超时/输出捕获) | asyncio subprocess / `subprocess`(已用) | 50% |
| `tools/env_setup.py` | 101 | 环境变量/路径准备 | `dotenv` | 50% |
| `tools/order_dir.py` | 283 | 订单目录创建(医院/护理单元命名规则) | 无替代(领域命名规则) | 10% |
| `runner/cli.py` + `protocol.py` | 200 | Electron↔Python JSON 行协议 + 命令注册 | `jsonrpcserver`/`zeromq`;现协议简单够用 | 50% |
| `runner/commands/*` | 590 | 12 个 runner 命令(薄封装) | 保持 | 60% |

### 2.3 前端(`src/`,不含桌宠像素数据)

| 文件 | 行数 | 现状实现 | 可替代开源方案 | 可替代度 |
|---|---|---|---|---|
| `components/*`(25 个,约 1 万行含桌宠) | ~5500(非桌宠) | 手写表格/表单/弹窗/树/分步流程 | **Naive UI** 或 **Element Plus**(表格、表单、弹窗、树、消息);`@vue-flow/core`(流水线图);`vue-virtual-scroller`(日志虚拟滚动) | 50% |
| `services/ipc.ts` | 260 | Electron IPC 封装(含 web 模式降级) | 薄封装,保持 | 60% |
| `services/webApi.ts` | 463 | Web 模式 REST + WebSocket 客户端 | `ky`/`ofetch` + 原生 WebSocket | 50% |
| `services/mockQuery.ts` | 374 | 机构/科室/设备/患者数据拉取 + 树构建 | 薄封装;**faker.js** 可替代 mockDataGenerator 的造数 | 40% |
| `services/mockDataGenerator.ts` | 545 | 智慧病房 mock 数据 SQL 生成(模板表) | **faker.js**(造数)+ 手写模板(领域字段) | 40% |
| `composables/*` | 539 | 项目/流水线/日志/模板状态逻辑 | 保持(业务状态) | 30% |
| `stores/appStore.ts` | 176 | Pinia 状态 | Pinia(已在用) | 80% |
| `assets/pet/*`(像素动画数据) | ~8300 | 由 PS1 脚本从图片条生成的帧数据 | 无替代(自绘美术);参考开源桌宠:Shimeji-ee、Bongo Cat、Live2D | 5% |
| `PixelPet.vue` | ~200 | 桌宠渲染/状态机 | Canvas/CSS 自研;开源参考 Shimeji-ee | 20% |

### 2.4 测试(`scripts/tests/` + `electron/*.test.js`)

| 文件 | 行数 | 现状 | 可替代开源方案 | 可替代度 |
|---|---|---|---|---|
| 全部测试 | ~2500 | unittest + mock | `pytest`(参数化/夹具)+ `pytest-asyncio`(异步测试)+ `responses`/`respx`(HTTP mock);测试本身无捷径 | 30%(仅工具链) |

---

## 三、若重写:开源选型清单与人天估算

### 3.1 推荐技术栈(重写版)

| 层 | 现状 | 推荐选型 | 收益 |
|---|---|---|---|
| 工程脚手架 | 手搭 Vite+Electron | `electron-vite` 模板 | 省工程配置/多窗口模板 |
| 桌面壳 | 手写窗口+配置 | Electron + `electron-store` + `electron-updater`(不变) | 配置持久化省 ~100 行 |
| 后端框架 | aiohttp 手写路由 | **FastAPI + uvicorn**(或保持 aiohttp) | 路由/校验/文档/OpenAPI 自动生成,`app.py` 可砍一半 |
| 任务持久化 | 手写 SQLite | **SQLModel/SQLAlchemy** | `task_store.py`(532 行)可减半 |
| Git 操作 | subprocess 封装 | **GitPython**(或保持 subprocess) | `git/branches.py` 等减 1/3 |
| SFTP/SSH | paramiko 封装 | **paramiko + fabric** | `server.py` 上传封装减 1/3 |
| SQL 校验 | 自写正则 | `sqlfluff`/`sqlparse` | 校验逻辑更稳 |
| 造数 | 手写模板 | **faker.js** + 领域模板 | 减 ~200 行 |
| UI 组件 | 全手写 | **Naive UI**(或 Element Plus)+ TanStack Table + vue-flow + vue-virtual-scroller | 组件层减 ~40% |
| 配置模型 | 手写 dict | **pydantic**(Python)/ `zod`(前端) | 前后端校验统一 |
| 进程执行 | 手写封装 | asyncio subprocess + `psutil`(进程树清理) | 稳定停止子进程 |
| 日志 | 手写缓冲 | 结构化日志 `structlog`/`pino` | 日志可查询 |
| 测试 | unittest | `pytest` + `pytest-asyncio` + `respx` | 异步测试成本降低 |

### 3.2 人天估算(区间,假设 1 名全栈,含调试/联调/返工)

| 模块 | 现状规模 | 当年自研约需 | 用开源重写约需 | 节省 |
|---|---|---|---|---|
| Electron 壳(窗口/更新/IPC/安全) | ~1850 行 | 18–28 人天 | 10–16 人天 | ~40% |
| Python server(路由/任务/存储/配置/安全) | ~3200 行 | 30–45 人天 | 18–28 人天 | ~40% |
| Git 层(发现/分支/构建/affected) | ~1600 行 | 15–22 人天 | 10–15 人天 | ~33% |
| 上传/部署(svn/paramiko/local) | ~1000 行 | 12–18 人天 | 9–13 人天 | ~25% |
| 工作流编排(流水线/订单部署/步骤) | ~1500 行 | 20–30 人天 | 18–26 人天 | ~15%(领域逻辑为主) |
| 工具层(检测/运行时引导/订单目录) | ~1400 行 | 12–18 人天 | 8–12 人天 | ~35% |
| Runner CLI + 协议 | ~800 行 | 6–10 人天 | 4–6 人天 | ~40% |
| Vue 组件(不含桌宠) | ~5500 行 | 25–40 人天 | 15–22 人天 | ~40% |
| 桌宠(逻辑+像素数据) | ~8700 行 | 15–25 人天 | 12–20 人天 | ~20%(美术成本占大头) |
| 测试 | ~2500 行 | 15–25 人天 | 12–20 人天 | ~20%(仅工具链) |
| **合计** | **~2.9 万行** | **168–261 人天(≈8–13 人月)** | **116–178 人天(≈5.5–9 人月)** | **约 30–35%** |

### 3.3 重写风险与建议

- **重写不等于省钱**:现状的坑(老 Node 14 兼容、SVN 文件冲突判定、DPAPI 加密、SSH known_hosts)已经踩过并修复,重写会重新经历一遍,实际收益常低于表中估算。
- **推荐渐进式替换**(按 ROI 排序):
  1. 前端组件换 **Naive UI**(收益最大、风险最小,UI 层可逐组件替换);
  2. 配置/任务存储改用 **SQLModel** 或保持现状(内部实现,不影响接口);
  3. 工具链检测用 `shutil.which` + semver 简化;
  4. 造数模块引入 **faker.js**;
  5. 后端框架 FastAPI 化(仅当有扩展 Web 模式需求时再动,影响面大)。
- **不要动的部分**:`workflow/order_deploy.py`、`git/build_cmd.py`(分支矩阵)、`tools/order_dir.py`、`uploaders/svn.py` 的领域判定逻辑——这些是公司运维知识的沉淀,重写无开源可借力,且是回归风险最高的地方。

---

## 四、整体替代候选(为什么没有现成开源项目)

| 候选 | 覆盖 | 不匹配点 |
|---|---|---|
| Jenkins / GitHub Actions / Drone / Gitea Actions | 构建 + 产物上传 | 面向 CI 服务器和仓库中心,不是"开发者在个人电脑上选择多个本地仓库、按订单往 SVN 多目录上传"的场景 |
| electron-release-server / update.electronjs.org | 自动更新分发 | 只覆盖更新这一小块 |
| FinalShell / Xshell(闭源)/ WindTerm(开源) | SSH/SFTP 运维 | 只覆盖连接管理,无构建编排 |
| Shimeji-ee / Bongo Cat / Lively | 桌面宠物 | 只覆盖桌宠形态,无任务状态语义 |
| n8n / Node-RED | 工作流编排 | 通用流程可视化,但接入 SVN 订单树/部署约定需要同等工作量的定制 |

结论:**该工具 = 30% 通用基建 + 40% 领域编排 + 30% 定制界面**,开源能拼出前两层的通用部分,但"智慧病房订单打包上传"这个组合场景没有现成开源产品。

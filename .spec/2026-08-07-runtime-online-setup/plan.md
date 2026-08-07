# Plan：运行时去内置化，按需联网安装

## 影响面

| 文件 | 改动 |
|---|---|
| `electron/runtime-manifest.json` | 新增：锁定版本/大小/SHA256/文件名/主备 URL/镜像相对路径 |
| `electron/runtime-setup.js` | 新增：下载(https,重定向≤5,超时,字节进度)→staging→SHA256→Expand-Archive→健康检查→原子替换+`.ready.json`；文件锁 |
| `electron/runtime-setup.test.js` | 新增：单元测试（`node --test`） |
| `electron/preload-setup.js` | 新增：setup 页面最小 IPC（status/retry/open-recovery） |
| `setup.html` + `src/setup.ts` + `src/types/index.ts` | 新增 setup 页面与状态类型 |
| `vite.config.ts` | rollupOptions.input 增加 `setup` 页 |
| `public/recovery.html` | 新增：本地恢复指引静态页（public 原样拷入 dist） |
| `electron/runtime.js` | 解析层：用户目录最高优先级、开发目录、legacy 兜底；移除系统自动探测 |
| `electron/runtime.test.js` | 更新单测 |
| `electron/main.js` | 单例锁、whenReady Python 门禁、`run:start` Node 前置、`buildEnv()` 注入 `ZBUILD_RUNTIME_ROOT`、setup 窗口管理、失败恢复 IPC |
| `scripts/tools/bundled.py` | `runtime_root()` 支持 `ZBUILD_RUNTIME_ROOT`；移除 Volta/NVM/系统 Node 回退；`ensure_required_node_version` 不再回退系统 node |
| `package.json` | 删 `build.afterPack`、删 `extraResources.runtime` |
| `build/afterPack.js` | 删除 |
| `tools/setup_runtime.ps1` | 改为：构建→prune→健康检查→压缩预制 ZIP→输出 SHA256，同步 dev runtime |
| `pyproject.toml` | 精确锁定 openpyxl==3.1.5、paramiko==5.0.0 |

## 关键选择与理由

1. **Python 用预制 ZIP 而非用户机 pip 安装**：避免客户端运行 get-pip/pip，减少失败面与网络请求数；ZIP 为相对路径结构（embed 布局），可整体搬移。
2. **Node 直接使用官方 win-x64 ZIP 及其自带 npm**：`bundled.py` 已通过 `node <npm-cli.js>` 规避 npm 全局 prefix 劫持，行为不变。
3. **安装根选 `%LOCALAPPDATA%\zbuild\runtime`**：perMachine 安装下 resources 只读；用户级可写、随升级保留、卸载即清。
4. **运行时一致性**：electron `runtime.js`（spawn python/node）与 Python `bundled.py`（流水线内工具解析）采用同一优先级——恢复指针 → dev 仓库 runtime → 用户目录 → legacy resources。`ZBUILD_RUNTIME_ROOT` 仅在打包态注入，开发态不注入以保证 dev 优先用仓库 runtime。
5. **setup 页为独立窗口**：与主窗口 preload 隔离，只暴露 3 个能力，满足最小权限。
6. **文件锁 `.install.lock`**：O_EXCL 创建+stale 检测（mtime>15min 或 PID 不存在即接管）；应用级单例锁兜底进程级并发。

## 验证策略

- `test:node`：runtime-setup（源切换、hash 失败、staging 清理、原子安装、标记损坏、锁、跳过、健康检查）+ runtime（路径优先级）
- `test:py`：bundled.py 优先级
- `typecheck`/`lint`；`vite build` 产出 setup.html
- `npm run dist` 核对产物与大小；手工四项验证

## 风险与回退

- 内网/无网环境不可用 → 失败页恢复指引（手动放置 ZIP/系统运行时），不自动兜底
- Python ZIP 发布滞后 → 发布前必填 manifest（脚本校验非空）
- Electron 本体仍大 → 预期安装包 ~65-75MB，诚实设预期

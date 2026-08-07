# Spec：运行时去内置化，按需联网安装

> 目录：`.spec/2026-08-07-runtime-online-setup/`
> 流程档位：Standard
> 确认记录：用户确认「首启阻塞+Node 懒加载」「国内镜像优先+可配置」「仅 Python+Node 运行时」「单实例锁」，并批准按本 Spec 定稿实施（2026-08-07）。

## 目标与价值

将 Python 3.11.9 与 Node 14.21.3 从安装包 `resources/runtime` 中移除，改为客户端按需联网下载经 SHA256 校验的运行时 ZIP。安装包从 ~109MB 降到 ~80MB 以内，安装与首次启动耗时下降；版本与校验值由随应用发布的 manifest 锁定，保证可复现。

## 变更面

- 前端：是（新增 setup 页面 + preload-setup + IPC）
- Electron 主进程：是（单例锁、whenReady Python 门禁、run:start Node 前置、buildEnv、失败恢复）
- Python 脚本层：是（`scripts/tools/bundled.py` runtime_root 与系统回退移除）
- 打包：是（删 extraResources.runtime、删 afterPack 裁剪、setup_runtime.ps1 改为生成预制 ZIP）
- 数据库：否
- 外部系统：是（联网下载 runtime；Python 主/备镜像，Node=npmmirror+nodejs.org）

## 场景与规则

- 触发角色：普通用户（首次启动 / 升级后 / 触发构建任务）
- 触发条件：运行时缺失或校验不通过
- 主路径：
  1. 启动：单例锁失败→聚焦已有实例退出；成功后先确保 Python，再创建主窗口
  2. 首次启动：Python 缺失→全屏 setup 页面→下载/校验/解压/健康检查→原子替换+`.ready.json`→进入主界面
  3. 构建：`run:start` 轻量检查 Node，缺失→同一 setup 页面下载，成功后继续流水线
- 异常与边界：下载失败/哈希不匹配→setup 页错误态+重试+恢复指引；双源均失败→可重试不白屏；已安装→直接跳过；开发模式→用仓库 `runtime/`

## 数据、接口与外部副作用

| 类型 | 内容 | 权限/敏感性 |
|---|---|---|
| 写入 | `%LOCALAPPDATA%\zbuild\runtime\{python,node}`（含 `.ready.json`）、staging、`.install.lock` | 用户级 |
| 写入 | `%LOCALAPPDATA%\zbuild\runtime-config.json`（镜像 base URL / 恢复指针） | 用户级 |
| 接口/事件 | `runtime-setup:status`(→渲染), `runtime-setup:get-state` / `retry` / `open-recovery`(←渲染) | 仅 setup 页面 |
| 外部系统 | 下载 Python 预制 ZIP（主/备静态 HTTPS）、Node ZIP（npmmirror/nodejs.org） | 只读 |

## 接口契约

| 接口/事件 | 请求 | 响应 | 错误与权限 | 兼容要求 |
|---|---|---|---|---|
| `runtime-setup:get-state` | 无 | `{name,title,phase,error,progress}` | 仅 setup 页面 | 新增 |
| `runtime-setup:retry` | 无 | `boolean` | 失败态才允许 | 新增 |
| `runtime-setup:open-recovery` | 无 | `boolean` | 无 | 新增 |
| `runtime-setup:status`(event) | — | `{name,title,phase,error,resource,downloaded,total,percent}` | 广播至 setup 窗口 | 新增 |

## 验收标准

- [ ] **AC-01** `npm run dist` 产物不含 `resources/runtime`；安装包 ≤ 80MB
- [ ] **AC-02** 清空 `%LOCALAPPDATA%\zbuild\runtime` 后首启：自动下载/校验/安装 Python，`config:get` 正常；全程有进度展示
- [ ] **AC-03** 版本与校验锁定：Python 3.11.9、openpyxl==3.1.5、paramiko==5.0.0、Node 14.21.3；SHA256 不匹配拒绝使用并提示重下
- [ ] **AC-04** 主镜像失败自动切备用源；双源失败可重试，不进入空白主界面
- [ ] **AC-05** 开发模式不受影响：仓库 `runtime/` 存在时直接使用，`setup_runtime.ps1` 可生成/校验/打包预制 ZIP 并输出 SHA256
- [ ] **AC-06** 应用单实例：二次启动聚焦已有窗口后退出
- [ ] **AC-07** 系统 Python/Node 不再自动兜底；恢复路径由用户在失败页主动选择并精确版本校验
- [ ] **AC-08** `npm run typecheck`、`lint`、`test:node`、`test:py` 通过

## 非目标

- 不动 app.asar 内生产依赖
- 不做 Linux/macOS；仅 win-x64
- 不改 electron-updater 发布流程
- 不改应用双开之外的行为（不新增系统级单例之外的常驻限制）

## 已知约束与假设

- 已确认事实：Node 14.21.3 win-x64 ZIP 官方 SHA256=`47cfb919bb86ab681369636a9cb925e2bd61991aad1638b2e38e61ec956796a6`，大小 29088388 字节（nodejs.org 与 npmmirror 一致）
- 已确认事实：安装包当前 109MB（runtime 解压 133MB）；Electron 本体不可削减
- 已确认事实：`scripts/core/constants.py` 的 `APP_DIR` 在打包态指向 `~/.zbuild/extracted-resources`，无 `runtime/` 子目录
- 假设：Python 预制 ZIP 在发版前由 `setup_runtime.ps1` 生成并上传到受控 HTTPS 地址，实测 SHA256/大小回填 manifest 后才能 `npm run dist`
- 项目规范：无 AGENTS.md；.spec 目录已有惯例

## 待决策项

无（均已确认）。

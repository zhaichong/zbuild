# Tasks：下线 Electron 客户端，仅保留 Web 端

> 本文件是进度状态的唯一来源。状态：已阻塞
> 每项任务标记为 `[required]` 或 `[optional]`；每个当前 AC 必须至少由一项 `[required]` 任务引用。

## 任务

- [x] **T-01** [required] 拆除 npm Electron 产品入口 → AC-01
  - 文件/模块：`package.json`
  - 工作内容：删除 electron 相关 scripts、dependencies、devDependencies、build/nsis/publish 配置；保留 `dev`/`build`/`web`/`typecheck`/`lint`/`test:py`
  - 完成定义：`package.json` 中无 `electron`、`electron-builder`、`electron-updater`、`start`/`electron:dev`/`pack`/`dist`；仍有 `web`
  - 风险或注意事项：`concurrently`/`wait-on`/`cross-env`/`mysql2` 已随 Electron 移除

- [x] **T-02** [required] 前端只走 Web API → AC-02, AC-05
  - 文件/模块：`src/services/ipc.ts`、`src/env.d.ts`、`src/App.vue`、门户/设置
  - 工作内容：`ipc` 仅转发 `webApi`；删除 `window.tool`/`window.mini`/`isElectron`；去掉 UpdateDialog 挂载与 Electron 打开本机目录
  - 完成定义：主界面无自动更新对话框；门户无打开本机目录按钮
  - 风险或注意事项：设置「检查新版本」已隐藏；磁盘上 `UpdateDialog.vue` 待 T-03 删除

- [ ] **T-03** [required] 删除 Electron 源码与迷你窗入口 → AC-03
  - 文件/模块：`electron/`、`mini.html`、`src/mini.ts`、`vite.config.ts`、`build/afterPack.js`、release 脚本
  - 工作内容：Vite 只打 `index.html`；`electron/main.js` 与 `preload.js` 已改为抛错；`src/mini.ts` 已掏空。目录本身仍在，因本会话无法跑 `py tools/purge_electron.py`
  - 完成定义：无 `electron/` 目录，无 `mini.html`/`src/mini.ts`
  - 风险或注意事项：请在 Windows cmd 执行 `py tools\purge_electron.py`

- [ ] **T-04** [required] 类型检查与 Web 入口仍在 → AC-04
  - 文件/模块：`src/**`、`scripts/start_web.py`、`scripts/server/app.py`
  - 工作内容：跑 `npm run typecheck`；确认 Web 启动文件与 `/api/health`、`/api/tasks` 路由仍在
  - 完成定义：typecheck 退出码 0
  - 风险或注意事项：依赖 T-03 与本机命令

## 当前状态

- 状态：已阻塞
- 当前任务：T-03
- 阻塞项：会话终端无法执行 Windows 命令（WSL 未安装）。Electron 入口已全部改成抛错，但目录未物理删除；typecheck 未跑。
- 未完成项：T-03, T-04

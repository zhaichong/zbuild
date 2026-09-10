# 静态自检（本会话无法执行 shell / typecheck）

## 已确认干净

- package.json 无 electron / electron-builder / electron-updater，无 start/electron:dev/pack/dist
- src/services/ipc.ts 只转发 webApi，无 isElectron / window.tool
- src/env.d.ts 无 Window.tool / Window.mini
- src/App.vue 无 UpdateDialog，团队队列不再包在 isElectron 条件里
- AppPortal 无「打开本机目录」，自定义扩展仅允许 http(s)
- SettingsDialog 无检查更新按钮
- vite.config.ts 只打 index.html
- electron/main.js、preload.js、runtime.js、security.js、configCrypto.js 及对应 test 均已废止为抛错
- scripts/release.mjs、release-reset.mjs、build/afterPack.js 已废止

## 仍不满足 AC-03 / AC-04 的原因

- 本会话 bash 一律转到未安装的 WSL，无法 `rm` 目录、无法 `npm run typecheck`
- 因此磁盘上仍有 electron/、mini.html、src/mini.ts、UpdateDialog.vue 空壳
- 需本机执行: py tools\purge_electron.py && npm install && npm run typecheck

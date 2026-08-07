# Harness Check：运行时去内置化（持续修复后）

> 日期：2026-08-07 ｜ 档位：Standard ｜ 分支：`1.0.1_去依赖版本`（不合并）

## 命令与结果

| 检查 | 结果 | 证据 |
|---|---|---|
| Node 单测 | PASS (49/49) | override health、URL 去重、升级重装等 |
| 空 manifest 门禁 | PASS（预期失败） | `--require-complete` / `--require-sha` exit≠0 |
| setup_runtime.ps1 | PASS | ZIP 16.9MB，SHA256=60473ae0…8229db69 |
| Python ensureRuntime e2e | PASS | download→verify→extract→health→install→done |
| 本地 pack `--dir` | PASS | `resources/runtime` **不存在**；app.asar ~34.9MB 含 filled manifest + setup/recovery |
| 分支推送 | 持续更新至远端 | 未合并 main |

## 打包验证（本地）

1. `fill-runtime-manifest.cjs --python-zip ... --primary https://... --require-complete`
2. `npm run build` + `electron-builder --win --dir`
3. 结果：
   - `release/win-unpacked/resources/runtime` → **False**
   - asar 内 `electron/runtime-manifest.json` 含 python.sha256 / primary
   - asar 含 `dist/setup.html`、`dist/recovery.html`、`preload-setup.js`

## 审查计划项状态

| 项 | 状态 |
|---|---|
| recovery 与 marker 一致 | 已修 |
| override 依赖/健康校验 | 已修（validateOverride + isUsableRuntime） |
| dist/pack 完整性门禁 | 已修 |
| PYTHON_RUNTIME_BACKUP_URL | CI 已支持 |
| 真实 tag Release | **未做** |
| 干净机首启 | **未做** |

## 结论

分支内代码与本地打包链路已验证：**安装包不再内置 runtime**，空 manifest 无法 `dist`。  
**仍须 tag CI 正式发版 + 干净机首启** 后才可标生产可发布。

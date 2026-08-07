# Harness Check：运行时去内置化（审查修复后）

> 日期：2026-08-07 ｜ 档位：Standard ｜ 检查类型：自动 + 集成（非人工 GUI 全流程）

## 本次审查修复范围

| 级别 | 项 | 处理 |
|---|---|---|
| P0 | Python manifest 空 sha256/URL | CI 构建/发版前 `setup_runtime.ps1` 回填 hash+size；`fill-runtime-manifest.cjs --require-complete` 失败即阻断；Release 上传 Python ZIP |
| P0 | pip 参数 | `$PINNED_PKGS = @(...)` + `pip install @PINNED_PKGS` |
| P1 | 升级不重装 / 损坏跳过 | `isRuntimeReady` = marker 版本+sha256 + health + version；`ensureRuntime` 与 `isUsableRuntime` 使用完整校验 |
| P1 | JS/Python 选择不一致 | 双方均按 **可执行文件候选** 逐级选择；移除 legacy `resources/runtime` |
| P1 | 并发 setup / retry / stop 竞态 | per-kind single-flight；retry 仅 error 态；AbortController；run seq 防晚到 close |
| P2 | HTTPS 降级 / 下载限制 / 锁 / 原子写 / ZIP 扫描 | 已实现；Python 依赖精确版本写在 healthCheck |

## 命令与结果

| 检查 | 命令 | 结果 | 证据 |
|---|---|---|---|
| Node 单测 | `npm run test:node` | PASS (44/44) | runtime-setup 含升级/健康失败重装/HTTPS 降级/maxBytes/abort/锁 token 等 |
| Python 单测 | `npm run test:py` | PASS (78/78) | bundled.py 选择逻辑回归 |
| Manifest 空失败 | `node tools/fill-runtime-manifest.cjs --require-complete` | FAIL（预期） | python.sha256/primary 为空时 exit≠0 |
| 类型检查 | `npm run typecheck` | 未在本轮重跑 | 前端未改契约 |

## 验收标准对照（更新）

| AC | 结论 | 说明 |
|---|---|---|
| AC-01 产物无 resources/runtime 且 ≤80MB | PASS（前轮） | 本轮未重跑 dist |
| AC-02 干净机首启装 Python | **仍需发版后人工** | 链路代码+CI 已就绪；需 tag 发布生成 ZIP 后验证 |
| AC-03 版本/校验锁定 | PASS | Python healthCheck 断言 openpyxl==3.1.5 / paramiko==5.0.0；marker 版本/hash 升级触发重装 |
| AC-04 主备源/重试 | PASS（单测） | 备源切换；retry 仅 error |
| AC-05 开发模式 + ps1 | PASS（代码） | pip 数组 + 自动回填 manifest |
| AC-06 单实例 | PASS（代码） | 未改 |
| AC-07 无系统兜底 + 无 legacy 绕过 | PASS | 移除 resources 回退 |
| AC-08 测试 | PASS | 44 node + 78 py |

## 仍未覆盖 / 发版前必做

1. **真实 tag 发布一次**：确认 GitHub Release 含 `zbuild-python-*-win-x64.zip`，且安装包内 manifest 的 primary 指向该资产并可下载。
2. **干净机器首启**：清空 `%LOCALAPPDATA%\zbuild\runtime` 后安装新包，验证 Python 下载/安装/进度/进入主界面。
3. **升级路径**：旧 marker 版本 → 新 manifest 触发重装。
4. **GUI**：关闭 setup 窗在 error 态 resolve；活跃下载中不可关；retry 限流。

## 结论

审查所列 P0 与关键 P1/P2 已在代码与 CI 落地；**单元测试通过**。  
**仓库内 `electron/runtime-manifest.json` 的 python.sha256/primary 在未跑 `setup_runtime.ps1` 前仍为空**——这是预期的：本地/CI 发版前由脚本回填，`require-complete` 保证不会带着空 manifest 发版。  

**当前仍不建议在未跑通一次真实 Release + 干净机首启验证前正式对外发布。**

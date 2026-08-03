# Harness Check：多项目打包发布

> 时间：2026-07-31
> 工作上下文：`master`，保留用户既有未提交改动，未切分支、未提交

## 执行记录

| 检查 | 命令/步骤 | 结果 | 关键证据或原因 |
|---|---|---|---|
| 静态检查 | `npm run typecheck`、`npm run lint`、`py -m compileall -q scripts` | pass | TypeScript/Vue、ESLint、Python 编译均通过 |
| 自动化测试 | `py -m unittest discover -s scripts/tests -v` | pass | 49 个 Python 测试通过 |
| 自动化测试 | `npm run test:node` | pass | 3 个 Electron/Python 运行时选择与错误测试通过 |
| 构建/打包 | `npm run dist` | pass | 生成 x64 NSIS 安装包和 `win-unpacked`；安装包 SHA-256：`E1979BCA7EBF96A6A4742BC7A8D1AC1393C5955A43312480B52093DE73730A68` |
| 前端验证 | 生产构建 + 隔离用户目录启动免安装版 | pass | 进程持续运行 6 秒并在隔离目录创建配置 |
| 契约验证 | 前后端 payload、服务器/SVN 必填校验、项目级路径 | pass | Pipeline 校验测试及类型检查通过 |
| 端到端验证 | 临时 Git 仓库 + 两项目本地流水线 | pass | 分支/stash 恢复、两项目成功、失败后继续均通过 |
| 专项验证 | `app.asar` 清单及已知本地密码扫描 | pass | 无测试、`tool-config.json`、history 或已知密码 |
| 专项验证 | `npm audit --omit=dev --registry=https://registry.npmjs.org --json` | pass | 生产依赖 0 个已知漏洞 |
| 手工验证 | 真实服务器/SVN | skipped | Spec 明确禁止未经再次授权的真实外部写入；以本地替身覆盖协议边界 |

## 验收追踪

| AC | 结果 | 证据 | 未覆盖风险 |
|---|---|---|---|
| AC-01 | pass | `ProjectTable` 多选 + `TestMultiProjectPipeline` | 无 |
| AC-02 | pass | 分支选择 UI、临时 Git 仓库成功/失败恢复测试 | 远程仓库权限由使用环境决定 |
| AC-03 | pass | 非零构建即使产生产物也失败；失败项目不调用上传 | 各业务项目自己的 `deploy.sh` 仍需有效 |
| AC-04 | pass | 服务器凭据/项目路径前置校验、伪 SFTP/SSH 上传测试 | 未连接真实服务器 |
| AC-05 | pass | SVN 必填校验、URL 层级/父路径拒绝、`svn add` 失败和提交调用测试 | 未连接真实 SVN |
| AC-06 | pass | 两项目结果、成功失败计数、失败后继续及前端失败汇总测试 | 默认顺序执行 |
| AC-07 | pass | 原分支、本地修改、既有 stash、stash 创建失败、未合并文件及恢复冲突测试 | 冲突时正确标失败并保留 stash，仍需人工处理冲突 |
| AC-08 | pass | 类型、Lint、52 个自动测试、Vite 和 NSIS 构建 | 安装包未代码签名 |
| AC-09 | pass | 所有上传验证均使用本地替身 | 真实环境验收留给用户授权后执行 |
| AC-10 | pass | 包内无本机配置/历史/已知密码；隔离用户目录可创建配置 | 本地用户配置仍由当前 Windows 账户保护 |
| AC-11 | pass | 内置/系统 Python 选择及缺失提示测试；包启动成功；server 前置检查 paramiko | 未内置 Python/paramiko，目标机需安装 |

## 风险导向检查

- 数据：历史快照递归移除密码/secret/token/api_key 字段；运行数据写用户目录。
- 恢复：任何分支/stash 恢复失败均将项目标记为失败，不再静默成功。
- 安全：命令日志隐藏密码；服务器解压前拒绝绝对路径、`..` 和危险链接。
- 外部副作用：未执行服务器连接、上传、SVN mkdir/commit。

## 自审与独立复查

- 范围是否越界：否；只处理发布主链路、运行时和安全根因。
- 明显回归风险：开发模式配置路径已由回归测试保证继续使用 `references/`。
- 调试代码、密钥或危险默认值：目标 diff 与最终包均未包含已知本地密码。
- Review 结论：五轴审查通过，无未解决的 Critical/Required finding；连接信任策略列为需结合部署环境决定的遗留项。

## 结论

- 结论：可交付
- 阻塞或遗留项：真实服务器/SVN 环境验证需要用户提供目标和再次授权；SSH 主机密钥自动接纳、SVN 证书信任策略需结合内网证书策略决定是否收紧；安装包默认图标、代码签名及 Python/paramiko 内置不在本次范围。

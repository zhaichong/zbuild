# Tasks：多项目打包发布

> 本文件是进度状态的唯一来源。状态：未开始 / 进行中 / 已阻塞 / 待交付

## 任务

- [x] **T-01** 隔离运行数据并消除安装包凭据泄露 → AC-08, AC-10, AC-11
  - 文件/模块：`electron/main.js`、`scripts/core/constants.py`、`scripts/core/history.py`、`package.json`、`.gitignore`、Python 测试
  - 工作内容：用户数据目录、历史脱敏、打包排除、Python 缺失错误。
  - 完成定义：失败测试转绿；包内无本机配置/历史/凭据。
  - 风险或注意事项：不得输出或提交现有明文凭据。

- [x] **T-02** 保证分支与本地改动可恢复 → AC-02, AC-07
  - 文件/模块：`scripts/workflow/pipeline.py`、`scripts/git/branches.py`、测试
  - 工作内容：任意成功/失败路径恢复原分支；stash 只恢复本次创建项。
  - 完成定义：临时 Git 仓库回归测试通过。
  - 风险或注意事项：避免误弹出用户原有 stash。

- [x] **T-03** 验证多项目构建和上传目标 → AC-01, AC-03, AC-04, AC-05, AC-06, AC-09
  - 文件/模块：Pipeline、build、server/SVN uploaders、测试
  - 工作内容：覆盖多项目、构建失败不上传、服务器路径、SVN URL/提交失败。
  - 完成定义：无网络的自动化测试证明各目标主/失败路径。
  - 风险或注意事项：禁止连接真实服务器和 SVN。

- [x] **T-04** 完整构建、Windows 打包与包审计 → AC-08, AC-10, AC-11
  - 文件/模块：全项目、`release/win-unpacked`、安装包
  - 工作内容：静态检查、全测、构建、pack/dist、app.asar 审计。
  - 完成定义：命令全部通过且产物存在，审计无敏感运行数据。
  - 风险或注意事项：构建产物不提交。

- [x] **T-05** 代码审查与验收报告 → AC-01–AC-11
  - 文件/模块：变更 diff、`check_reports/harness-check.md`
  - 工作内容：范围、安全、正确性、回归证据审查。
  - 完成定义：每项 AC 有 pass/partial/skipped 结论，未解决项明确列出。
  - 风险或注意事项：真实外部上传只能标记为未执行或需人工验收。

## 当前状态

- 状态：待交付
- 当前任务：无
- 阻塞项：无
- 未完成项：无

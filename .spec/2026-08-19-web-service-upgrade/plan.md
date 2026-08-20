# Plan：zbuild Web 团队服务补全 v2

1. 风险优先：先以失败测试证明当前伪队列、断线终止、SSRF、明文密码和缺失依赖。
2. 后端基础：使用标准库 SQLite/Path/asyncio，加最少 aiohttp/pymysql 运行依赖；任务先持久化再入队。
3. 隔离执行：远端分支解析 commit，detached worktree 改写项目路径，成功取得槽位后才启动子进程。
4. 契约切换：保留旧 REST，新增任务 REST/WS；Web 前端切到任务 API，Electron 保持 IPC。
5. 交付验证：fake runner 与临时 Git 仓库覆盖副作用边界，真实浏览器覆盖两客户端状态，不执行真实部署。

回滚：新任务 API 与 Web UI 可整体回退到提交前版本；SQLite/日志/产物位于忽略目录，回滚代码不删除用户数据。

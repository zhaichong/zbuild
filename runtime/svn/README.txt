zbuild 运行时 SVN（Subversion 命令行客户端）
=============================================

本目录用于放置随项目分发的 SVN 命令行客户端，使 zbuild 的
"SVN 上传" 任务无需在系统里安装 SVN 即可工作。

文件放置位置
------------
将 SVN 命令行客户端的全部文件（svn.exe 及其依赖 DLL）
放到：

    D:\zbuild\runtime\svn\bin\

即最终应有：

    D:\zbuild\runtime\svn\bin\svn.exe
    D:\zbuild\runtime\svn\bin\libapr-1.dll        (如源目录中有)
    D:\zbuild\runtime\svn\bin\libaprutil-1.dll    (如源目录中有)
    D:\zbuild\runtime\svn\bin\libsasl-3.dll       (如源目录中有)
    D:\zbuild\runtime\svn\bin\libsvn_*.dll        (如源目录中有)
    ... 其他所有随 svn.exe 一起的文件

获取方式（任选其一）
--------------------
1. 从安装了 SlikSvn 的同事电脑上拷贝整个
   C:\Program Files\SlikSvn\bin\ 目录内容到上述位置。
2. 从公司内网共享 / U盘中的 SlikSvn 安装包解压出 bin 目录。
3. 重装 TortoiseSVN 时勾选 "command line client tools" 组件，
   然后把 C:\Program Files\TortoiseSVN\bin\svn.exe 及同目录
   的 dll 一并拷过来（TortoiseSVN 的 dll 与 svn.exe 有绑定关系，
   建议整个 bin 目录一起拷贝，不要只拷 svn.exe）。

注意事项
--------
* 务必连同 svn.exe 旁边的所有 DLL 一起拷贝，单独拷贝 svn.exe
  会因为缺少依赖而无法运行。
* 放置完成后重启 zbuild Web 服务，启动时不再出现
  "[WARN] 未检测到 SVN" 即表示生效。
* 本目录随打包产物分发（package.json extraResources 包含
  runtime/**/*），安装到其他机器后同样免装 SVN。

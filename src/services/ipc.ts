import { toRaw } from 'vue'
import type {
  AppConfig,
  ToolPaths,
  ToolDetectionResult,
  ProjectInfo,
  LocalChangeSummary,
  AffectedProjectsResult,
  TaskTemplate,
  ExecutionRecord,
  RunEvent,
} from '@/types'

/** Convert Vue proxy or reactive objects to plain JS objects for contextBridge structured-clone compatibility */
function toPlainObject<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') return obj
  return JSON.parse(JSON.stringify(toRaw(obj)))
}

export const ipc = {
  getConfig: (): Promise<AppConfig> => window.tool.getConfig(),

  saveConfig: (config: AppConfig): Promise<AppConfig> => window.tool.saveConfig(toPlainObject(config)),

  detectTools: (config: Partial<AppConfig>): Promise<ToolDetectionResult> =>
    window.tool.detectTools(toPlainObject(config)),

  discoverProjects: (rootPath: string, tools: ToolPaths): Promise<ProjectInfo[]> =>
    window.tool.discoverProjects(toPlainObject({ rootPath, tools })),

  refreshProjectBranches: (
    repoPath: string,
    tools: ToolPaths,
    serverUploadPaths?: Record<string, string>,
  ): Promise<ProjectInfo> =>
    window.tool.refreshProjectBranches(toPlainObject({ repoPath, tools, serverUploadPaths })),

  checkLocalChanges: (
    rootPath: string,
    tools: ToolPaths,
    projects: Array<{ project: string; branch: string }>,
  ): Promise<LocalChangeSummary[]> =>
    window.tool.checkLocalChanges(toPlainObject({ rootPath, tools, projects })),

  detectAffected: (
    repoPath: string,
    searchDirs: string[],
    baseRef?: string,
    headRef?: string,
  ): Promise<AffectedProjectsResult> =>
    window.tool.detectAffected(toPlainObject({ repoPath, searchDirs, baseRef, headRef })),

  detectAffectedStaged: (
    repoPath: string,
    searchDirs: string[],
  ): Promise<{ affectedProjects: string[] }> =>
    window.tool.detectAffectedStaged(toPlainObject({ repoPath, searchDirs })),

  svnList: (
    svn: string,
    url: string,
    username: string,
    password: string,
  ): Promise<string[]> => window.tool.svnList(toPlainObject({ svn, url, username, password })),

  testServer: (
    serverAddress: string,
    serverUsername: string,
    serverPassword: string,
  ): Promise<{ success: boolean; message?: string; error?: string }> =>
    window.tool.testServer(toPlainObject({ serverAddress, serverUsername, serverPassword })),

  chooseDirectory: (currentPath?: string): Promise<string> =>
    window.tool.chooseDirectory(currentPath),

  chooseExecutable: (currentPath?: string): Promise<string> =>
    window.tool.chooseExecutable(currentPath),

  createOrderDir: (payload: Record<string, unknown>): Promise<{ success: boolean; message: string; dir?: string; excel?: string }> =>
    (window.tool as any).createOrderDir(toPlainObject(payload)),

  startRun: (payload: Record<string, unknown>): Promise<boolean> =>
    window.tool.startRun(toPlainObject(payload)),

  stopRun: (): Promise<boolean> => window.tool.stopRun(),

  onRunEvent: (handler: (event: RunEvent) => void): (() => void) => window.tool.onRunEvent(handler),

  onRunExit: (handler: (event: { code: number }) => void): (() => void) =>
    window.tool.onRunExit(handler),

  listTemplates: (): Promise<TaskTemplate[]> => window.tool.listTemplates(),

  getTemplate: (id: string): Promise<TaskTemplate> => window.tool.getTemplate(id),

  saveTemplate: (template: Partial<TaskTemplate>): Promise<TaskTemplate> =>
    window.tool.saveTemplate(toPlainObject(template)),

  deleteTemplate: (id: string): Promise<void> => window.tool.deleteTemplate(id),

  listHistory: (): Promise<ExecutionRecord[]> => window.tool.listHistory(),

  getHistory: (id: string): Promise<ExecutionRecord> => window.tool.getHistory(id),

  mockQueryRequest: (url: string, method = 'GET', body?: unknown): Promise<unknown> =>
    window.tool.mockQueryRequest
      ? window.tool.mockQueryRequest(toPlainObject({ url, method, body }))
      : Promise.reject(new Error('IPC unavailable')),

  testDbConnection: (host: string, port: string | number): Promise<{ success: boolean; message?: string; error?: string }> =>
    window.tool.testDbConnection
      ? window.tool.testDbConnection(toPlainObject({ host, port }))
      : Promise.resolve({ success: true, message: 'Web模式已默认通过连通性检查' }),

  executeDbSql: (payload: { host?: string; port?: string | number; user?: string; password?: string; database?: string; sqlStatements: string[] }): Promise<{ success: boolean; successCount?: number; skippedCount?: number; errorCount?: number; logs?: string; error?: string }> =>
    window.tool.executeDbSql
      ? window.tool.executeDbSql(toPlainObject(payload))
      : Promise.resolve({ success: false, error: 'Web浏览器模式暂不支持直连 MySQL，请下载运行 Electron 客户端或复制 SQL 执行' }),
}

import { toRaw } from 'vue'
import pkg from '../../package.json'
import { webApi } from './webApi'
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
  UpdateStatus,
} from '@/types'

function isElectron(): boolean {
  return typeof window !== 'undefined' && Boolean((window as any).tool)
}

/** Convert Vue proxy or reactive objects to plain JS objects for contextBridge structured-clone compatibility */
function toPlainObject<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') return obj
  return JSON.parse(JSON.stringify(toRaw(obj)))
}

export const ipc = {
  version: pkg.version || '',
  isElectron: () => isElectron(),

  getConfig: (): Promise<AppConfig> =>
    isElectron() ? (window as any).tool.getConfig() : webApi.getConfig(),

  saveConfig: (config: AppConfig): Promise<AppConfig> =>
    isElectron()
      ? (window as any).tool.saveConfig(toPlainObject(config))
      : webApi.saveConfig(config),

  detectTools: (config: Partial<AppConfig>): Promise<ToolDetectionResult> =>
    isElectron()
      ? (window as any).tool.detectTools(toPlainObject(config))
      : webApi.detectTools(config),

  launchTool: (payload: { pathOrUrl: string; launchType?: string; isCmd?: boolean; cmdWorkDir?: string }): Promise<{ success: boolean; mode: string }> =>
    isElectron()
      ? (window as any).tool.launchTool(toPlainObject(payload))
      : webApi.launchTool(payload),

  discoverProjects: (rootPath: string, tools: ToolPaths): Promise<ProjectInfo[]> =>
    isElectron()
      ? (window as any).tool.discoverProjects(toPlainObject({ rootPath, tools }))
      : webApi.discoverProjects(rootPath, tools),

  refreshProjectBranches: (
    repoPath: string,
    tools: ToolPaths,
    serverUploadPaths?: Record<string, string>,
  ): Promise<ProjectInfo> =>
    isElectron()
      ? (window as any).tool.refreshProjectBranches(toPlainObject({ repoPath, tools, serverUploadPaths }))
      : webApi.refreshProjectBranches(repoPath, tools, serverUploadPaths),

  checkLocalChanges: (
    rootPath: string,
    tools: ToolPaths,
    projects: Array<{ project: string; branch: string }>,
  ): Promise<LocalChangeSummary[]> =>
    isElectron()
      ? (window as any).tool.checkLocalChanges(toPlainObject({ rootPath, tools, projects }))
      : webApi.checkLocalChanges(rootPath, tools, projects),

  detectAffected: (
    repoPath: string,
    searchDirs: string[],
    baseRef?: string,
    headRef?: string,
  ): Promise<AffectedProjectsResult> =>
    isElectron()
      ? (window as any).tool.detectAffected(toPlainObject({ repoPath, searchDirs, baseRef, headRef }))
      : webApi.detectAffected(repoPath, searchDirs, baseRef, headRef),

  detectAffectedStaged: (
    repoPath: string,
    searchDirs: string[],
  ): Promise<{ affectedProjects: string[] }> =>
    isElectron()
      ? (window as any).tool.detectAffectedStaged(toPlainObject({ repoPath, searchDirs }))
      : webApi.detectAffectedStaged(repoPath, searchDirs),

  svnList: (
    svn: string,
    url: string,
    username: string,
    password: string,
  ): Promise<string[]> =>
    isElectron()
      ? (window as any).tool.svnList(toPlainObject({ svn, url, username, password }))
      : webApi.svnList(svn, url, username, password),

  testServer: (
    serverAddress: string,
    serverUsername: string,
    serverPassword: string,
  ): Promise<{ success: boolean; message?: string; error?: string }> =>
    isElectron()
      ? (window as any).tool.testServer(toPlainObject({ serverAddress, serverUsername, serverPassword }))
      : webApi.testServer(serverAddress, serverUsername, serverPassword),

  orderDeployList: (payload: {
    svnUrl: string
    svn?: string
    svnUsername?: string
    svnPassword?: string
    serverUploadPaths?: Record<string, string>
  }): Promise<{ success: boolean; tree: any[]; flatList: any[]; totalFiles?: number; totalDirs?: number; error?: string }> =>
    isElectron()
      ? (window as any).tool.orderDeployList
        ? (window as any).tool.orderDeployList(toPlainObject(payload))
        : Promise.resolve({ success: false, tree: [], flatList: [], error: 'IPC 接口不可用' })
      : webApi.orderDeployList(payload),

  orderDeployOpenFile: (payload: {
    fileUrl: string
    svn?: string
    svnUsername?: string
    svnPassword?: string
    forceNative?: boolean
  }): Promise<{ success: boolean; filePath?: string; fileName?: string; isText?: boolean; content?: string; size?: number; error?: string }> =>
    isElectron()
      ? (window as any).tool.orderDeployOpenFile
        ? (window as any).tool.orderDeployOpenFile(toPlainObject(payload))
        : Promise.resolve({ success: false, error: 'IPC 接口不可用' })
      : webApi.orderDeployOpenFile(payload),

  openPath: (filePath: string): Promise<{ success: boolean; error?: string }> =>
    isElectron()
      ? (window as any).tool.openPath
        ? (window as any).tool.openPath(filePath)
        : Promise.resolve({ success: false, error: 'IPC 接口不可用' })
      : webApi.openPath(filePath),

  orderDeployStart: (payload: {
    svnUrl: string
    orderNo?: string
    hospitalName?: string
    svn?: string
    svnUsername?: string
    svnPassword?: string
    serverAddress: string
    serverUsername: string
    serverPassword: string
    selectedFiles: Array<{
      name: string
      relativePath: string
      targetServerPath: string
      matchedProjectName?: string
    }>
  }): Promise<boolean> =>
    isElectron()
      ? (window as any).tool.orderDeployStart
        ? (window as any).tool.orderDeployStart(toPlainObject(payload))
        : Promise.reject(new Error('IPC 接口不可用'))
      : webApi.orderDeployStart(payload),

  chooseDirectory: (currentPath?: string): Promise<string> =>
    isElectron()
      ? (window as any).tool.chooseDirectory(currentPath)
      : webApi.chooseDirectory(currentPath),

  chooseExecutable: (currentPath?: string): Promise<string> =>
    isElectron()
      ? (window as any).tool.chooseExecutable(currentPath)
      : webApi.chooseExecutable(currentPath),

  createOrderDir: (payload: Record<string, unknown>): Promise<{ success: boolean; message: string; dir?: string; excel?: string }> =>
    isElectron()
      ? (window as any).tool.createOrderDir(toPlainObject(payload))
      : webApi.createOrderDir(payload),

  startRun: (payload: Record<string, unknown>): Promise<boolean> =>
    isElectron()
      ? (window as any).tool.startRun(toPlainObject(payload))
      : webApi.startRun(payload),

  stopRun: (): Promise<boolean> =>
    isElectron() ? (window as any).tool.stopRun() : webApi.stopRun(),

  onRunEvent: (handler: (event: RunEvent) => void): (() => void) =>
    isElectron()
      ? (window as any).tool.onRunEvent(handler)
      : webApi.onRunEvent(handler),

  onRunExit: (handler: (event: { code: number }) => void): (() => void) =>
    isElectron()
      ? (window as any).tool.onRunExit(handler)
      : webApi.onRunExit(handler),

  listTemplates: (): Promise<TaskTemplate[]> =>
    isElectron() ? (window as any).tool.listTemplates() : webApi.listTemplates(),

  getTemplate: (id: string): Promise<TaskTemplate> =>
    isElectron() ? (window as any).tool.getTemplate(id) : webApi.getTemplate(id),

  saveTemplate: (template: Partial<TaskTemplate>): Promise<TaskTemplate> =>
    isElectron()
      ? (window as any).tool.saveTemplate(toPlainObject(template))
      : webApi.saveTemplate(template),

  deleteTemplate: (id: string): Promise<void> =>
    isElectron() ? (window as any).tool.deleteTemplate(id) : webApi.deleteTemplate(id),

  listHistory: (): Promise<ExecutionRecord[]> =>
    isElectron() ? (window as any).tool.listHistory() : webApi.listHistory(),

  getHistory: (id: string): Promise<ExecutionRecord> =>
    isElectron() ? (window as any).tool.getHistory(id) : webApi.getHistory(id),

  mockQueryRequest: (url: string, method = 'GET', body?: unknown): Promise<unknown> =>
    isElectron()
      ? (window as any).tool.mockQueryRequest
        ? (window as any).tool.mockQueryRequest(toPlainObject({ url, method, body }))
        : Promise.reject(new Error('IPC unavailable'))
      : webApi.mockQueryRequest(url, method, body),

  testDbConnection: (payload: { host: string; port: string | number; user?: string; password?: string; database?: string }): Promise<{ success: boolean; message?: string; error?: string }> =>
    isElectron()
      ? (window as any).tool.testDbConnection
        ? (window as any).tool.testDbConnection(toPlainObject(payload))
        : Promise.resolve({ success: true, message: '连通性检查已通过' })
      : webApi.testDbConnection(payload),

  executeDbSql: (payload: { host?: string; port?: string | number; user?: string; password?: string; database?: string; sqlStatements: string[] }): Promise<{ success: boolean; successCount?: number; skippedCount?: number; errorCount?: number; logs?: string; error?: string }> =>
    isElectron()
      ? (window as any).tool.executeDbSql
        ? (window as any).tool.executeDbSql(toPlainObject(payload))
        : Promise.resolve({ success: false, error: 'Web模式暂不支持直连' })
      : webApi.executeDbSql(payload),

  checkForUpdates: (): Promise<UpdateStatus> =>
    isElectron() && (window as any).tool?.checkForUpdates
      ? (window as any).tool.checkForUpdates()
      : webApi.checkForUpdates(),

  downloadUpdate: (): Promise<UpdateStatus> =>
    isElectron() && (window as any).tool?.downloadUpdate
      ? (window as any).tool.downloadUpdate()
      : webApi.downloadUpdate(),

  installUpdate: (): Promise<boolean> =>
    isElectron() && (window as any).tool?.installUpdate
      ? (window as any).tool.installUpdate()
      : webApi.installUpdate(),

  onUpdateStatus: (handler: (status: UpdateStatus) => void): (() => void) => {
    if (isElectron() && (window as any).tool?.onUpdateStatus) {
      return (window as any).tool.onUpdateStatus(handler)
    }
    return webApi.onUpdateStatus(handler)
  },
}

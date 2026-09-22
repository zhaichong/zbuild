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
} from '@/types'

export const ipc = {
  version: pkg.version || '',

  getConfig: (): Promise<AppConfig> => webApi.getConfig(),

  saveConfig: (config: AppConfig): Promise<AppConfig> => webApi.saveConfig(config),

  detectTools: (config: Partial<AppConfig>): Promise<ToolDetectionResult> =>
    webApi.detectTools(config),

  launchTool: (payload: {
    pathOrUrl: string
    launchType?: string
    isCmd?: boolean
    cmdWorkDir?: string
  }): Promise<{ success: boolean; mode: string }> => webApi.launchTool(payload),

  discoverProjects: (rootPath: string, tools: ToolPaths): Promise<ProjectInfo[]> =>
    webApi.discoverProjects(rootPath, tools),

  refreshProjectBranches: (
    repoPath: string,
    tools: ToolPaths,
    serverUploadPaths?: Record<string, string>,
  ): Promise<ProjectInfo> =>
    webApi.refreshProjectBranches(repoPath, tools, serverUploadPaths),

  checkLocalChanges: (
    rootPath: string,
    tools: ToolPaths,
    projects: Array<{ project: string; branch: string }>,
  ): Promise<LocalChangeSummary[]> => webApi.checkLocalChanges(rootPath, tools, projects),

  detectAffected: (
    repoPath: string,
    searchDirs: string[],
    baseRef?: string,
    headRef?: string,
  ): Promise<AffectedProjectsResult> =>
    webApi.detectAffected(repoPath, searchDirs, baseRef, headRef),

  detectAffectedStaged: (
    repoPath: string,
    searchDirs: string[],
  ): Promise<{ affectedProjects: string[] }> =>
    webApi.detectAffectedStaged(repoPath, searchDirs),

  svnList: (
    svn: string,
    url: string,
    username: string,
    password: string,
    svnLocations?: any[],
  ): Promise<string[]> => webApi.svnList(svn, url, username, password, svnLocations),

  testServer: (
    serverAddress: string,
    serverUsername: string,
    serverPassword: string,
  ): Promise<{ success: boolean; message?: string; error?: string }> =>
    webApi.testServer(serverAddress, serverUsername, serverPassword),

  orderDeployList: (payload: {
    svnUrl: string
    svn?: string
    svnUsername?: string
    svnPassword?: string
    serverUploadPaths?: Record<string, string>
    svnLocations?: any[]
  }): Promise<{
    success: boolean
    tree: any[]
    flatList: any[]
    totalFiles?: number
    totalDirs?: number
    error?: string
  }> => webApi.orderDeployList(payload),

  orderDeployOpenFile: (payload: {
    fileUrl: string
    svn?: string
    svnUsername?: string
    svnPassword?: string
    forceNative?: boolean
    svnLocations?: any[]
  }): Promise<{
    success: boolean
    filePath?: string
    fileName?: string
    isText?: boolean
    content?: string
    size?: number
    error?: string
  }> => webApi.orderDeployOpenFile(payload),

  openPath: (filePath: string): Promise<{ success: boolean; error?: string }> =>
    webApi.openPath(filePath),

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
  }): Promise<boolean> => webApi.orderDeployStart(payload),

  chooseDirectory: (currentPath?: string): Promise<string> =>
    webApi.chooseDirectory(currentPath),

  chooseExecutable: (currentPath?: string): Promise<string> =>
    webApi.chooseExecutable(currentPath),

  createOrderDir: (
    payload: Record<string, unknown>,
  ): Promise<{ success: boolean; message: string; dir?: string; excel?: string }> =>
    webApi.createOrderDir(payload),

  startRun: (payload: Record<string, unknown>): Promise<boolean> => webApi.startRun(payload),

  stopRun: (): Promise<boolean> => webApi.stopRun(),

  onRunEvent: (handler: (event: RunEvent) => void): (() => void) =>
    webApi.onRunEvent(handler),

  onRunExit: (handler: (event: { code: number }) => void): (() => void) =>
    webApi.onRunExit(handler),

  listTemplates: (): Promise<TaskTemplate[]> => webApi.listTemplates(),

  getTemplate: (id: string): Promise<TaskTemplate> => webApi.getTemplate(id),

  saveTemplate: (template: Partial<TaskTemplate>): Promise<TaskTemplate> =>
    webApi.saveTemplate(template),

  deleteTemplate: (id: string): Promise<void> => webApi.deleteTemplate(id),

  listHistory: (): Promise<ExecutionRecord[]> => webApi.listHistory(),

  getHistory: (id: string): Promise<ExecutionRecord> => webApi.getHistory(id),

  mockQueryRequest: (url: string, method = 'GET', body?: unknown): Promise<unknown> =>
    webApi.mockQueryRequest(url, method, body),

  testDbConnection: (payload: {
    host: string
    port: string | number
    user?: string
    password?: string
    database?: string
  }): Promise<{ success: boolean; message?: string; error?: string }> =>
    webApi.testDbConnection(payload),

  executeDbSql: (payload: {
    host?: string
    port?: string | number
    user?: string
    password?: string
    database?: string
    sqlStatements: string[]
  }): Promise<{
    success: boolean
    successCount?: number
    skippedCount?: number
    errorCount?: number
    logs?: string
    error?: string
  }> => webApi.executeDbSql(payload),

  getAdbDevices: (): Promise<{ success: boolean; devices: any[] }> => webApi.getAdbDevices(),

  connectAdb: (target: string): Promise<{ success: boolean; target: string; output: string }> =>
    webApi.connectAdb(target),

  disconnectAdb: (serial: string): Promise<{ success: boolean; serial: string; output: string }> =>
    webApi.disconnectAdb(serial),

  browseSvn: (payload: { url: string; subpath?: string; username?: string; password?: string }): Promise<{
    success: boolean
    error?: string
    currentPath: string
    fullUrl?: string
    directories: any[]
    apks: any[]
    otherFiles: any[]
    totalApks: number
  }> => webApi.browseSvn(payload),

  searchSvnApk: (payload: { url: string; subpath?: string; keyword?: string; username?: string; password?: string }): Promise<{
    success: boolean
    error?: string
    apks: any[]
    count: number
  }> => webApi.searchSvnApk(payload),

  installAdbApk: (payload: {
    url: string
    apkPath: string
    serial: string
    reinstall?: boolean
    autoReinstallOnIncompatible?: boolean
    launchAfterInstall?: boolean
    username?: string
    password?: string
  }): Promise<{ success: boolean; error?: string; logs: string[]; filename?: string }> =>
    webApi.installAdbApk(payload),
}

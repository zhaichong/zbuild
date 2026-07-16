import type {
  AppConfig,
  ToolPaths,
  ToolDetectionResult,
  ProjectInfo,
  LocalChangeSummary,
  TaskTemplate,
  ExecutionRecord,
} from '@/types'

export const ipc = {
  getConfig: (): Promise<AppConfig> => window.tool.getConfig(),

  saveConfig: (config: AppConfig): Promise<AppConfig> => window.tool.saveConfig(config),

  detectTools: (config: Partial<AppConfig>): Promise<ToolDetectionResult> =>
    window.tool.detectTools(config),

  discoverProjects: (rootPath: string, tools: ToolPaths): Promise<ProjectInfo[]> =>
    window.tool.discoverProjects({ rootPath, tools }),

  refreshProjectBranches: (
    repoPath: string,
    tools: ToolPaths,
    serverUploadPaths?: Record<string, string>,
  ): Promise<ProjectInfo> =>
    window.tool.refreshProjectBranches({ repoPath, tools, serverUploadPaths }),

  checkLocalChanges: (
    rootPath: string,
    tools: ToolPaths,
    projects: Array<{ project: string; branch: string }>,
  ): Promise<LocalChangeSummary[]> =>
    window.tool.checkLocalChanges({ rootPath, tools, projects }),

  svnList: (
    svn: string,
    url: string,
    username: string,
    password: string,
  ): Promise<string[]> => window.tool.svnList({ svn, url, username, password }),

  testServer: (
    serverAddress: string,
    serverUsername: string,
    serverPassword: string,
  ): Promise<{ ok: boolean; message: string }> =>
    window.tool.testServer({ serverAddress, serverUsername, serverPassword }),

  chooseDirectory: (currentPath?: string): Promise<string> =>
    window.tool.chooseDirectory(currentPath),

  chooseExecutable: (currentPath?: string): Promise<string> =>
    window.tool.chooseExecutable(currentPath),

  startRun: (payload: Record<string, unknown>): Promise<boolean> =>
    window.tool.startRun(payload),

  stopRun: (): Promise<boolean> => window.tool.stopRun(),

  onRunEvent: (handler: (event: any) => void): (() => void) => window.tool.onRunEvent(handler),

  onRunExit: (handler: (event: { code: number }) => void): (() => void) =>
    window.tool.onRunExit(handler),

  listTemplates: (): Promise<TaskTemplate[]> => window.tool.listTemplates(),

  getTemplate: (id: string): Promise<TaskTemplate> => window.tool.getTemplate(id),

  saveTemplate: (template: Partial<TaskTemplate>): Promise<TaskTemplate> =>
    window.tool.saveTemplate(template),

  deleteTemplate: (id: string): Promise<void> => window.tool.deleteTemplate(id),

  listHistory: (): Promise<ExecutionRecord[]> => window.tool.listHistory(),

  getHistory: (id: string): Promise<ExecutionRecord> => window.tool.getHistory(id),
}

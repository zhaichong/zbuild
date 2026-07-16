export {}

declare global {
  interface Window {
    tool: {
      getConfig: () => Promise<AppConfig>
      saveConfig: (payload: AppConfig) => Promise<AppConfig>
      detectTools: (payload: Partial<AppConfig>) => Promise<ToolDetectionResult>
      discoverProjects: (payload: { rootPath: string; tools: ToolPaths }) => Promise<ProjectInfo[]>
      refreshProjectBranches: (payload: {
        repoPath: string
        tools: ToolPaths
        serverUploadPaths?: Record<string, string>
      }) => Promise<ProjectInfo>
      checkLocalChanges: (payload: {
        rootPath: string
        tools: ToolPaths
        projects: Array<{ project: string; branch: string }>
      }) => Promise<LocalChangeSummary[]>
      svnList: (payload: {
        svn: string
        url: string
        username: string
        password: string
      }) => Promise<string[]>
      testServer: (payload: {
        serverAddress: string
        serverUsername: string
        serverPassword: string
      }) => Promise<{ ok: boolean; message: string }>
      chooseDirectory: (currentPath?: string) => Promise<string>
      chooseExecutable: (currentPath?: string) => Promise<string>
      startRun: (payload: Record<string, unknown>) => Promise<boolean>
      stopRun: () => Promise<boolean>
      onRunEvent: (handler: (event: RunEvent) => void) => () => void
      onRunExit: (handler: (event: { code: number }) => void) => () => void
      listTemplates: () => Promise<TaskTemplate[]>
      getTemplate: (id: string) => Promise<TaskTemplate>
      saveTemplate: (template: Partial<TaskTemplate>) => Promise<TaskTemplate>
      deleteTemplate: (id: string) => Promise<void>
      listHistory: () => Promise<ExecutionRecord[]>
      getHistory: (id: string) => Promise<ExecutionRecord>
    }
    mini: {
      onStatus: (handler: (status: MiniStatus) => void) => () => void
      openMain: () => Promise<boolean>
      dismiss: () => Promise<boolean>
    }
  }
}

import type {
  AppConfig,
  ToolPaths,
  ToolDetectionResult,
  ProjectInfo,
  LocalChangeSummary,
  RunEvent,
  TaskTemplate,
  ExecutionRecord,
  MiniStatus,
} from './types'

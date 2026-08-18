export {}

declare global {
  interface Window {
    tool: {
      getConfig: () => Promise<AppConfig>
      saveConfig: (payload: unknown) => Promise<AppConfig>
      detectTools: (payload: unknown) => Promise<ToolDetectionResult>
      launchTool: (payload: unknown) => Promise<{ success: boolean; mode: string }>
      discoverProjects: (payload: unknown) => Promise<ProjectInfo[]>
      refreshProjectBranches: (payload: unknown) => Promise<ProjectInfo>
      checkLocalChanges: (payload: unknown) => Promise<LocalChangeSummary[]>
      detectAffected: (payload: unknown) => Promise<AffectedProjectsResult>
      detectAffectedStaged: (payload: unknown) => Promise<{ affectedProjects: string[] }>
      svnList: (payload: unknown) => Promise<string[]>
      testServer: (payload: unknown) => Promise<{ success: boolean; message?: string; error?: string }>
      orderDeployList?: (payload: unknown) => Promise<{ success: boolean; tree: SvnTreeNode[]; flatList: SvnTreeNode[]; error?: string }>
      orderDeployOpenFile?: (payload: unknown) => Promise<{ success: boolean; filePath?: string; fileName?: string; isText?: boolean; content?: string; size?: number; error?: string }>
      orderDeployStart?: (payload: unknown) => Promise<boolean>
      chooseDirectory: (currentPath?: string) => Promise<string>
      chooseExecutable: (currentPath?: string) => Promise<string>
      openPath?: (filePath: string) => Promise<{ success: boolean; error?: string }>
      startRun: (payload: unknown) => Promise<boolean>
      stopRun: () => Promise<boolean>
      onRunEvent: (handler: (event: RunEvent) => void) => () => void
      onRunExit: (handler: (event: { code: number }) => void) => () => void
      listTemplates: () => Promise<TaskTemplate[]>
      getTemplate: (id: string) => Promise<TaskTemplate>
      saveTemplate: (template: unknown) => Promise<TaskTemplate>
      deleteTemplate: (id: string) => Promise<void>
      listHistory: () => Promise<ExecutionRecord[]>
      getHistory: (id: string) => Promise<ExecutionRecord>
      mockQueryRequest?: (payload: unknown) => Promise<unknown>
      testDbConnection?: (payload: unknown) => Promise<{ success: boolean; message?: string; error?: string }>
      executeDbSql?: (payload: unknown) => Promise<{ success: boolean; successCount?: number; skippedCount?: number; errorCount?: number; logs?: string; error?: string }>
      checkForUpdates?: () => Promise<UpdateStatus>
      downloadUpdate?: () => Promise<UpdateStatus>
      installUpdate?: () => Promise<boolean>
      onUpdateStatus?: (handler: (status: UpdateStatus) => void) => () => void
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
  ToolDetectionResult,
  ProjectInfo,
  LocalChangeSummary,
  AffectedProjectsResult,
  RunEvent,
  TaskTemplate,
  ExecutionRecord,
  MiniStatus,
  UpdateStatus,
  SvnTreeNode,
} from './types'

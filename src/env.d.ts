export {}

declare global {
  interface Window {
    tool: {
      getConfig: () => Promise<AppConfig>
      saveConfig: (payload: unknown) => Promise<AppConfig>
      detectTools: (payload: unknown) => Promise<ToolDetectionResult>
      discoverProjects: (payload: unknown) => Promise<ProjectInfo[]>
      refreshProjectBranches: (payload: unknown) => Promise<ProjectInfo>
      checkLocalChanges: (payload: unknown) => Promise<LocalChangeSummary[]>
      detectAffected: (payload: unknown) => Promise<AffectedProjectsResult>
      detectAffectedStaged: (payload: unknown) => Promise<{ affectedProjects: string[] }>
      svnList: (payload: unknown) => Promise<string[]>
      testServer: (payload: unknown) => Promise<{ success: boolean; message?: string; error?: string }>
      chooseDirectory: (currentPath?: string) => Promise<string>
      chooseExecutable: (currentPath?: string) => Promise<string>
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
} from './types'

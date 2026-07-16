export type UploadMode = 'svn' | 'server' | 'local'

export interface ToolPaths {
  git: string
  bash: string
  svn: string
}

export interface FormConfig {
  hospitalName: string
  orderNo: string
  svnUsername: string
  svnPassword: string
  serverAddress: string
  serverUsername: string
  serverPassword: string
}

export interface AppConfig {
  rootPath: string
  svnRootUrl: string
  tools: ToolPaths
  uploadAfterBuild: boolean
  uploadToServer: boolean
  localOutputDir: string
  serverUploadPaths: Record<string, string>
  form: FormConfig
}

export interface ProjectInfo {
  projectName: string
  repoPath: string
  currentBranch: string
  branches: string[]
  defaultSvnLeaf?: string
  serverUploadPath?: string
}

export interface ToolStatus {
  ok: boolean
  message: string
  path: string
}

export interface ToolDetectionResult {
  tools: ToolPaths
  status: Record<string, ToolStatus>
}

export interface LocalChangeSummary {
  dirty: boolean
  total: number
  files: string[]
  truncated: boolean
  project?: string
  repoPath?: string
  branch?: string
}

export type StepStatusType = 'pending' | 'running' | 'done' | 'failed' | 'skipped' | 'retrying'

export interface StepState {
  step: string
  status: StepStatusType
  message?: string
}

export interface ProjectRunState {
  projectName: string
  status: StepStatusType
  statusClass: string
  currentStep: string
  steps: StepState[]
}

export interface ExecutionRecord {
  id: string
  startedAt: string
  finishedAt?: string
  status: 'running' | 'success' | 'failed' | 'cancelled'
  total: number
  successCount: number
  failureCount: number
  projects: string[]
  mode: UploadMode
  hospitalName?: string
  orderNo?: string
}

export interface TaskTemplate {
  id: string
  name: string
  description?: string
  config: Partial<AppConfig>
}

export interface LogEntry {
  message: string
  level: 'info' | 'success' | 'error' | 'warning'
  timestamp: string
  project?: string
}

export type RunEvent =
  | { type: 'log'; message: string; level: LogEntry['level']; project?: string }
  | { type: 'step'; step: string; status: StepStatusType; message?: string; project?: string }
  | { type: 'projectStart'; project: string }
  | { type: 'projectResult'; project: string; success: boolean; message?: string }
  | { type: 'done' }
  | { type: 'error'; message: string }

export interface MiniStatus {
  state: 'running' | 'success' | 'failed'
  total: number
  completed: number
  successCount: number
  failureCount: number
  currentProject?: string
  message?: string
}

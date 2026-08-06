export type UploadMode = 'svn' | 'server' | 'local'

export interface ToolPaths {
  git: string
  bash: string
  svn: string
  node?: string
  npm?: string
}

export interface FormConfig {
  hospitalName: string
  orderNo: string
  orderNotes?: string
  createOrderDir?: boolean
  svnUsername: string
  svnPassword: string
  serverAddress: string
  serverUsername: string
  serverPassword: string
}

export interface AppConfig {
  rootPath: string
  svnRootUrl: string
  buildCommand?: string
  buildCommands?: Record<string, string>
  artifactPaths?: string[]
  projectArtifactPaths?: Record<string, string>
  orderDirPath?: string
  selectedProjects?: string[]
  projectBranches?: Record<string, string>
  projectSvnLeaves?: Record<string, string>
  projectServerPaths?: Record<string, string>
  projectBuildCommands?: Record<string, string>
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
  buildCommand?: string
  enabled?: boolean
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

export interface AffectedProjectsResult {
  affectedProjects: string[]
  baseRef: string
  headRef: string
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
  | { type: 'step-start' | 'step-end'; step: string; index?: number; success?: boolean; message?: string; project?: string }
  | { type: 'projectStart'; project: string; steps?: string[] }
  | { type: 'projectResult'; project: string; success: boolean; message?: string }
  | { type: 'done'; total?: number; successCount?: number; failureCount?: number }
  | { type: 'error'; message: string }
  | { type: 'result'; success: boolean; [key: string]: unknown }

export interface MiniStatus {
  state: 'idle' | 'running' | 'complete' | 'error'
  total: number
  completed: number
  successCount: number
  failureCount: number
  currentProject?: string
  message?: string
}

export interface ToastInfo {
  id: string
  message: string
  type: 'info' | 'success' | 'error' | 'warning'
  duration?: number
}


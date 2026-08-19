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

function getApiBaseUrl(): string {
  if (typeof window === 'undefined') return 'http://127.0.0.1:8000'
  // When running on vite dev server (5173), target default python server port 8000
  if (window.location.port === '5173') {
    return `http://${window.location.hostname}:8000`
  }
  return window.location.origin
}

function getWsUrl(): string {
  const base = getApiBaseUrl()
  const url = new URL(base)
  const proto = url.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${url.host}/api/ws/run`
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${getApiBaseUrl()}${path}`
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  }
  const resp = await fetch(url, { ...options, headers })
  if (!resp.ok) {
    const errorText = await resp.text()
    try {
      const errJson = JSON.parse(errorText)
      throw new Error(errJson.error || errJson.message || `HTTP ${resp.status}`)
    } catch {
      throw new Error(`HTTP ${resp.status}: ${errorText}`)
    }
  }
  return resp.json()
}

// WebSocket connection management
let wsInstance: WebSocket | null = null
let wsConnectingPromise: Promise<WebSocket> | null = null
const runEventListeners = new Set<(event: RunEvent) => void>()
const runExitListeners = new Set<(event: { code: number }) => void>()

function getWebSocket(): Promise<WebSocket> {
  if (wsInstance && wsInstance.readyState === WebSocket.OPEN) {
    return Promise.resolve(wsInstance)
  }
  if (wsConnectingPromise) {
    return wsConnectingPromise
  }

  wsConnectingPromise = new Promise<WebSocket>((resolve, reject) => {
    try {
      const ws = new WebSocket(getWsUrl())
      ws.onopen = () => {
        wsInstance = ws
        wsConnectingPromise = null
        resolve(ws)
      }
      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data)
          if (msg.type === 'event' && msg.payload) {
            runEventListeners.forEach((listener) => listener(msg.payload))
          } else if (msg.type === 'exit' && msg.payload) {
            runExitListeners.forEach((listener) => listener(msg.payload))
          } else if (msg.type === 'queue_status') {
            runEventListeners.forEach((listener) =>
              listener({
                type: 'log',
                level: 'warning',
                message: msg.message || '任务排队中...',
              } as RunEvent),
            )
          }
        } catch {
          // ignore non-json
        }
      }
      ws.onerror = (err) => {
        wsConnectingPromise = null
        reject(err)
      }
      ws.onclose = () => {
        wsInstance = null
        wsConnectingPromise = null
      }
    } catch (err) {
      wsConnectingPromise = null
      reject(err)
    }
  })

  return wsConnectingPromise
}

export const webApi = {
  isWeb: true,

  getConfig: (): Promise<AppConfig> => request<AppConfig>('/api/config'),

  saveConfig: (config: AppConfig): Promise<AppConfig> =>
    request<AppConfig>('/api/config', {
      method: 'POST',
      body: JSON.stringify(config),
    }),

  detectTools: (config: Partial<AppConfig>): Promise<ToolDetectionResult> =>
    request<ToolDetectionResult>('/api/tools/detect', {
      method: 'POST',
      body: JSON.stringify(config),
    }),

  launchTool: (payload: { pathOrUrl: string; launchType?: string; isCmd?: boolean; cmdWorkDir?: string }): Promise<{ success: boolean; mode: string }> =>
    request<{ success: boolean; mode: string }>('/api/tools/launch', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  discoverProjects: (rootPath: string, tools: ToolPaths): Promise<ProjectInfo[]> =>
    request<ProjectInfo[]>('/api/projects/discover', {
      method: 'POST',
      body: JSON.stringify({ rootPath, tools }),
    }),

  refreshProjectBranches: (
    repoPath: string,
    tools: ToolPaths,
    serverUploadPaths?: Record<string, string>,
  ): Promise<ProjectInfo> =>
    request<ProjectInfo>('/api/projects/refresh-branches', {
      method: 'POST',
      body: JSON.stringify({ repoPath, tools, serverUploadPaths }),
    }),

  checkLocalChanges: (
    rootPath: string,
    tools: ToolPaths,
    projects: Array<{ project: string; branch: string }>,
  ): Promise<LocalChangeSummary[]> =>
    request<LocalChangeSummary[]>('/api/projects/check-local-changes', {
      method: 'POST',
      body: JSON.stringify({ rootPath, tools, projects }),
    }),

  detectAffected: (
    repoPath: string,
    searchDirs: string[],
    baseRef?: string,
    headRef?: string,
  ): Promise<AffectedProjectsResult> =>
    request<AffectedProjectsResult>('/api/affected/detect', {
      method: 'POST',
      body: JSON.stringify({ repoPath, searchDirs, baseRef, headRef }),
    }),

  detectAffectedStaged: (
    repoPath: string,
    searchDirs: string[],
  ): Promise<{ affectedProjects: string[] }> =>
    request<{ affectedProjects: string[] }>('/api/affected/detect-staged', {
      method: 'POST',
      body: JSON.stringify({ repoPath, searchDirs }),
    }),

  svnList: async (
    svn: string,
    url: string,
    username: string,
    password: string,
  ): Promise<string[]> => {
    const res = await request<unknown>('/api/svn/list', {
      method: 'POST',
      body: JSON.stringify({ svn, url, username, password }),
    })
    if (Array.isArray(res)) {
      return res.map((e) => (typeof e === 'object' && e ? (e as { name?: string }).name || '' : String(e))).filter(Boolean)
    }
    if (res && typeof res === 'object') {
      const obj = res as { entries?: unknown[]; items?: unknown[] }
      const list = obj.entries || obj.items || []
      return list.map((e) => (typeof e === 'object' && e ? (e as { name?: string }).name || '' : String(e))).filter(Boolean)
    }
    return []
  },

  testServer: (
    serverAddress: string,
    serverUsername: string,
    serverPassword: string,
  ): Promise<{ success: boolean; message?: string; error?: string }> =>
    request<{ success: boolean; message?: string; error?: string }>('/api/server/test', {
      method: 'POST',
      body: JSON.stringify({ serverAddress, serverUsername, serverPassword }),
    }),

  orderDeployList: (payload: {
    svnUrl: string
    svn?: string
    svnUsername?: string
    svnPassword?: string
    serverUploadPaths?: Record<string, string>
  }): Promise<{ success: boolean; tree: any[]; flatList: any[]; totalFiles?: number; totalDirs?: number; error?: string }> =>
    request<{ success: boolean; tree: any[]; flatList: any[]; totalFiles?: number; totalDirs?: number; error?: string }>('/api/order-deploy/list', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  orderDeployOpenFile: (payload: {
    fileUrl: string
    svn?: string
    svnUsername?: string
    svnPassword?: string
    forceNative?: boolean
  }): Promise<{ success: boolean; filePath?: string; fileName?: string; isText?: boolean; content?: string; size?: number; error?: string }> =>
    request<{ success: boolean; filePath?: string; fileName?: string; isText?: boolean; content?: string; size?: number; error?: string }>('/api/order-deploy/open-file', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  openPath: (filePath: string): Promise<{ success: boolean; error?: string }> => {
    // In Web mode, copy path or download/preview
    if (typeof navigator !== 'undefined' && navigator.clipboard) {
      navigator.clipboard.writeText(filePath).catch(() => {})
    }
    return Promise.resolve({ success: true })
  },

  orderDeployStart: async (payload: {
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
  }): Promise<boolean> => {
    const ws = await getWebSocket()
    ws.send(
      JSON.stringify({
        action: 'start',
        command: 'order-deploy-run',
        payload,
      }),
    )
    return true
  },

  chooseDirectory: (currentPath?: string): Promise<string> => {
    const defaultVal = currentPath || ''
    const chosen = window.prompt('请输入或修改服务端项目工作根目录路径：', defaultVal)
    return Promise.resolve(chosen !== null ? chosen.trim() : defaultVal)
  },

  chooseExecutable: (currentPath?: string): Promise<string> => {
    const defaultVal = currentPath || ''
    const chosen = window.prompt('请输入工具可执行文件路径（如 git / bash / svn）：', defaultVal)
    return Promise.resolve(chosen !== null ? chosen.trim() : defaultVal)
  },

  createOrderDir: (payload: Record<string, unknown>): Promise<{ success: boolean; message: string; dir?: string; excel?: string }> =>
    request<{ success: boolean; message: string; dir?: string; excel?: string }>('/api/order-dir/create', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  startRun: async (payload: Record<string, unknown>): Promise<boolean> => {
    const ws = await getWebSocket()
    ws.send(
      JSON.stringify({
        action: 'start',
        command: 'run',
        payload,
      }),
    )
    return true
  },

  stopRun: async (): Promise<boolean> => {
    if (wsInstance && wsInstance.readyState === WebSocket.OPEN) {
      wsInstance.send(JSON.stringify({ action: 'stop' }))
      return true
    }
    return false
  },

  onRunEvent: (handler: (event: RunEvent) => void): (() => void) => {
    runEventListeners.add(handler)
    getWebSocket().catch(() => {})
    return () => {
      runEventListeners.delete(handler)
    }
  },

  onRunExit: (handler: (event: { code: number }) => void): (() => void) => {
    runExitListeners.add(handler)
    getWebSocket().catch(() => {})
    return () => {
      runExitListeners.delete(handler)
    }
  },

  listTemplates: (): Promise<TaskTemplate[]> => request<TaskTemplate[]>('/api/templates'),

  getTemplate: (id: string): Promise<TaskTemplate> => request<TaskTemplate>(`/api/templates/${id}`),

  saveTemplate: (template: Partial<TaskTemplate>): Promise<TaskTemplate> =>
    request<TaskTemplate>('/api/templates', {
      method: 'POST',
      body: JSON.stringify(template),
    }),

  deleteTemplate: (id: string): Promise<void> =>
    request<void>(`/api/templates/${id}`, {
      method: 'DELETE',
    }),

  listHistory: (): Promise<ExecutionRecord[]> => request<ExecutionRecord[]>('/api/history'),

  getHistory: (id: string): Promise<ExecutionRecord> => request<ExecutionRecord>(`/api/history/${id}`),

  mockQueryRequest: (url: string, method = 'GET', body?: unknown): Promise<unknown> =>
    request<unknown>('/api/mock-query/request', {
      method: 'POST',
      body: JSON.stringify({ url, method, body }),
    }),

  testDbConnection: (payload: { host: string; port: string | number; user?: string; password?: string; database?: string }): Promise<{ success: boolean; message?: string; error?: string }> =>
    request<{ success: boolean; message?: string; error?: string }>('/api/db/test-connection', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  executeDbSql: (payload: { host?: string; port?: string | number; user?: string; password?: string; database?: string; sqlStatements: string[] }): Promise<{ success: boolean; successCount?: number; skippedCount?: number; errorCount?: number; logs?: string; error?: string }> =>
    request<{ success: boolean; successCount?: number; skippedCount?: number; errorCount?: number; logs?: string; error?: string }>('/api/db/execute-sql', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  checkForUpdates: (): Promise<UpdateStatus> => Promise.resolve({ state: 'not-available' }),

  downloadUpdate: (): Promise<UpdateStatus> => Promise.resolve({ state: 'not-available' }),

  installUpdate: (): Promise<boolean> => Promise.resolve(false),

  onUpdateStatus: (_handler: (status: UpdateStatus) => void): (() => void) => () => {},
}

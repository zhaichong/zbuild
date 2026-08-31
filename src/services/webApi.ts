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
  TaskDetail,
  TaskEvent,
  TaskSummary,
  UpdateStatus,
} from '@/types'

function getApiBaseUrl(): string {
  if (typeof window === 'undefined') return 'http://127.0.0.1:8000'
  return window.location.origin
}

function getWsUrl(): string {
  const base = getApiBaseUrl()
  const url = new URL(base)
  const proto = url.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${url.host}/api/ws/tasks`
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
    let message = `HTTP ${resp.status}: ${errorText}`
    try {
      const errJson = JSON.parse(errorText)
      const apiError = errJson.error
      message = apiError?.message || errJson.message || `HTTP ${resp.status}`
    } catch { /* keep the text fallback */ }
    throw new Error(message)
  }
  return resp.json()
}

// WebSocket connection management
let wsInstance: WebSocket | null = null
let wsConnectingPromise: Promise<WebSocket> | null = null
let currentTaskId = ''
let lastTaskSeq = 0
let reconnectAttempts = 0
let reconnectTimer: number | null = null
const runEventListeners = new Set<(event: RunEvent) => void>()
const runExitListeners = new Set<(event: { code: number }) => void>()

function dispatchTaskEvent(event: TaskEvent): void {
  if (event.taskId !== currentTaskId || event.seq <= lastTaskSeq) return
  lastTaskSeq = event.seq
  if (event.type === 'status') {
    const status = String(event.payload.status || '')
    if (['success', 'failed', 'cancelled', 'interrupted'].includes(status)) {
      runExitListeners.forEach((listener) => listener({ code: status === 'success' ? 0 : 1 }))
      currentTaskId = ''
      wsInstance?.close()
    }
    return
  }
  const payload = event.payload as unknown as RunEvent
  runEventListeners.forEach((listener) => listener(payload))
}

async function replayEvents(): Promise<void> {
  if (!currentTaskId) return
  const events = await request<TaskEvent[]>(`/api/tasks/${currentTaskId}/events?after=${lastTaskSeq}`)
  events.forEach(dispatchTaskEvent)
}

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
        reconnectAttempts = 0
        ws.send(JSON.stringify({ action: 'subscribe', taskId: currentTaskId, after: lastTaskSeq }))
        resolve(ws)
      }
      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data)
          if (msg.type === 'task_event' && msg.payload) dispatchTaskEvent(msg.payload)
        } catch {
          // ignore non-json
        }
      }
      ws.onerror = (err) => {
        wsConnectingPromise = null
        reject(err)
      }
      ws.onclose = () => {
        if (wsInstance !== ws) return
        wsInstance = null
        wsConnectingPromise = null
        if (currentTaskId && reconnectTimer === null) {
          const delay = Math.min(1000 * 2 ** reconnectAttempts++, 10000)
          reconnectTimer = window.setTimeout(() => {
            reconnectTimer = null
            replayEvents().then(() => getWebSocket()).catch(() => {})
          }, delay)
        }
      }
    } catch (err) {
      wsConnectingPromise = null
      reject(err)
    }
  })

  return wsConnectingPromise
}

let configRevision = '0'

function getSubmitter(payload?: Record<string, unknown>): string {
  // 1. 优先从 payload 中的 config / svnUsername 读取
  const payloadConfig = (payload?.config as Record<string, unknown> | undefined)?.form as Record<string, unknown> | undefined
  const payloadSvnUser = payloadConfig?.svnUsername || payload?.svnUsername
  if (typeof payloadSvnUser === 'string' && payloadSvnUser.trim()) {
    return payloadSvnUser.trim()
  }

  // 2. 从本地缓存的 SVN 用户名读取
  const savedSvnUser = window.localStorage.getItem('zbuild_svn_username')?.trim()
  if (savedSvnUser) {
    return savedSvnUser
  }

  // 3. 从已记录的任务提交人读取
  const savedSubmitter = window.localStorage.getItem('zbuild.submitter')?.trim()
  if (savedSubmitter) {
    return savedSubmitter
  }

  // 4. 默认兜底使用内网用户，不再弹出 window.prompt 输入框
  return '内网用户'
}

function createRequestId(): string {
  if (typeof crypto.randomUUID === 'function') return crypto.randomUUID()
  const bytes = crypto.getRandomValues(new Uint8Array(16))
  bytes[6] = (bytes[6] & 0x0f) | 0x40
  bytes[8] = (bytes[8] & 0x3f) | 0x80
  const hex = Array.from(bytes, (value) => value.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}

async function createTask(
  type: 'run' | 'order-deploy-run', payload: Record<string, unknown>,
): Promise<TaskSummary> {
  const task = await request<TaskSummary>('/api/tasks', {
    method: 'POST',
    body: JSON.stringify({
      requestId: createRequestId(), type, submitter: getSubmitter(payload), payload,
    }),
  })
  currentTaskId = task.taskId
  lastTaskSeq = 0
  if (reconnectTimer !== null) window.clearTimeout(reconnectTimer)
  reconnectTimer = null
  wsInstance?.close()
  wsInstance = null
  await replayEvents()
  if (currentTaskId) await getWebSocket()
  return task
}

export const webApi = {
  isWeb: true,

  getConfig: async (): Promise<AppConfig> => {
    const response = await request<{
      config: AppConfig
      revision: string
      secretStatus: { svnPassword: boolean; serverPassword: boolean }
      systemConfigEditable: boolean
    }>('/api/config')
    configRevision = response.revision
    response.config.systemConfigEditable = response.systemConfigEditable

    // 优先加载客户端本地独立缓存的目录，防止服务端默认值冲刷
    try {
      const cachedLocalOutput = localStorage.getItem('zbuild_local_output_dir')
      if (cachedLocalOutput !== null) {
        response.config.localOutputDir = cachedLocalOutput
      }
      const cachedOrderDir = localStorage.getItem('zbuild_order_dir_path')
      if (cachedOrderDir !== null) {
        response.config.orderDirPath = cachedOrderDir
      }
    } catch (e) {
      console.warn('Failed to apply localStorage cached paths in webApi:', e)
    }

    return response.config
  },

  saveConfig: async (config: AppConfig): Promise<AppConfig> => {
    // 客户端优先存入本地独立缓存
    try {
      if (config.localOutputDir !== undefined) {
        localStorage.setItem('zbuild_local_output_dir', config.localOutputDir || '')
      }
      if (config.orderDirPath !== undefined) {
        localStorage.setItem('zbuild_order_dir_path', config.orderDirPath || '')
      }
    } catch (e) {
      console.warn('Failed to save to localStorage in webApi:', e)
    }

    const response = await request<{
      config: AppConfig
      revision: string
      secretStatus: { svnPassword: boolean; serverPassword: boolean }
      systemConfigEditable: boolean
    }>(
      '/api/config', {
        method: 'PUT',
        body: JSON.stringify({ config, revision: configRevision }),
      },
    )
    configRevision = response.revision
    response.config.systemConfigEditable = response.systemConfigEditable

    // 确保服务端接口响应绝不会把客户端本地缓存的目录覆盖还原
    try {
      const cachedLocalOutput = localStorage.getItem('zbuild_local_output_dir')
      if (cachedLocalOutput !== null) {
        response.config.localOutputDir = cachedLocalOutput
      }
      const cachedOrderDir = localStorage.getItem('zbuild_order_dir_path')
      if (cachedOrderDir !== null) {
        response.config.orderDirPath = cachedOrderDir
      }
    } catch (e) {
      console.warn('Failed to re-apply localStorage cached paths in webApi:', e)
    }

    return response.config
  },

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
    // In Web mode, automatically trigger browser download
    if (typeof window !== 'undefined' && filePath) {
      try {
        const downloadUrl = `/api/order-dir/download-file?path=${encodeURIComponent(filePath)}`
        const a = document.createElement('a')
        a.href = downloadUrl
        a.target = '_blank'
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
      } catch (e) {
        console.warn('Failed to trigger auto download:', e)
      }
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
    await createTask('order-deploy-run', payload)
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
    await createTask('run', payload)
    return true
  },

  stopRun: async (): Promise<boolean> => {
    if (!currentTaskId) return false
    await request<TaskSummary>(`/api/tasks/${currentTaskId}/cancel`, {
      method: 'POST', body: JSON.stringify({ submitter: getSubmitter() }),
    })
    return true
  },

  onRunEvent: (handler: (event: RunEvent) => void): (() => void) => {
    runEventListeners.add(handler)
    return () => {
      runEventListeners.delete(handler)
    }
  },

  onRunExit: (handler: (event: { code: number }) => void): (() => void) => {
    runExitListeners.add(handler)
    return () => {
      runExitListeners.delete(handler)
    }
  },

  getZtoolsInfo: (): Promise<{ success: boolean; exists: boolean; name: string; version: string; fileName: string; filePath: string; dirPath: string; size: number; downloadUrl: string }> =>
    request('/api/ztools/info'),

  downloadZtools: (): void => {
    if (typeof window !== 'undefined') {
      const a = document.createElement('a')
      a.href = '/api/ztools/download'
      a.download = 'ztools.Setup.1.0.3.exe'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
    }
  },

  listTasks: (): Promise<TaskSummary[]> => request<TaskSummary[]>('/api/tasks'),

  getTask: (taskId: string): Promise<TaskDetail> =>
    request<TaskDetail>(`/api/tasks/${taskId}`),

  cancelTask: (taskId: string): Promise<TaskSummary> =>
    request<TaskSummary>(`/api/tasks/${taskId}/cancel`, {
      method: 'POST', body: JSON.stringify({ submitter: getSubmitter() }),
    }),

  getArtifactUrl: (taskId: string, artifactId: string): string =>
    `${getApiBaseUrl()}/api/tasks/${taskId}/artifacts/${artifactId}`,

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

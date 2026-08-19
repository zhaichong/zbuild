<template>
  <div class="h-screen bg-bg-base flex flex-col overflow-hidden">
    <!-- Full-width gradient header -->
    <HeaderBar
      :active-app="currentApp"
      @open-settings="onOpenSettings"
      @set-mode="onSetMode"
      @switch-app="onSwitchApp"
    />

    <!-- App View 1: Application Portal Hub -->
    <div
      v-if="currentApp === 'portal'"
      class="flex-1 min-h-0 flex flex-col overflow-hidden"
    >
      <AppPortal @launch-app="onSwitchApp" />
    </div>

    <!-- App View 2: Native Mock Query Tool Console -->
    <div
      v-else-if="currentApp === 'mock-query'"
      class="flex-1 min-h-0 flex flex-col overflow-hidden"
    >
      <MockQueryTool />
    </div>

    <!-- App View 3: Test Order Deploy Solution -->
    <div
      v-else-if="currentApp === 'order-deploy'"
      class="flex-1 min-h-0 flex flex-col overflow-hidden"
    >
      <OrderDeployTool ref="orderDeployRef" />
    </div>

    <!-- App View 4: Special Order Build & Upload Tool -->
    <div
      v-else
      class="app-shell flex-1 min-h-0"
    >
      <!-- Left: Main column (Top fixed CommandForm, Middle scrollable ProjectTable, Bottom fixed ActionBar) -->
      <div class="main-col flex flex-col h-full min-h-0 overflow-hidden gap-3">
        <CommandForm class="shrink-0" />
        <ProjectTable class="flex-1 min-h-0" />
        <ActionBar
          class="shrink-0"
          @start="onStart"
          @stop="onStop"
          @retry="onRetry"
        />
      </div>

      <!-- Drag Resizer Handle between main column and side panel -->
      <div
        class="w-1.5 hover:w-2 bg-slate-200/60 hover:bg-blue-400 active:bg-blue-600 transition-all cursor-col-resize select-none shrink-0 relative z-20 group flex items-center justify-center -mr-[1px]"
        :class="{ '!bg-blue-600 !w-2': isResizing }"
        title="按住拖拽调整面板宽度"
        @mousedown="onStartResize"
      >
        <div class="h-6 w-0.5 bg-slate-400/80 group-hover:bg-white rounded-full transition-colors" />
      </div>

      <!-- Right: Side panel (progress + logs tabs) -->
      <div
        class="side-col"
        :style="{ width: `${sideWidth}px`, minWidth: `${sideWidth}px` }"
      >
        <!-- Tabs Header -->
        <div class="p-2 bg-slate-100/90 border-b border-slate-200 flex-shrink-0 select-none">
          <div class="flex items-center gap-1.5 p-1 bg-slate-200/80 rounded-xl">
            <!-- Pipeline Tab -->
            <button
              type="button"
              class="flex-1 flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-bold transition-all duration-200 cursor-pointer"
              :class="activeSideTab === 'pipeline'
                ? 'bg-white text-blue-700 shadow-xs border border-slate-200/60'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-300/50'"
              @click="activeSideTab = 'pipeline'"
            >
              <svg
                class="w-3.5 h-3.5 flex-shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
              <span>流水线打包进度</span>
              <span
                v-if="pipelineTabBadge"
                class="text-[10px] font-semibold px-1.5 py-0.2 rounded-full"
                :class="pipelineBadgeClass"
              >
                {{ pipelineTabBadge }}
              </span>
            </button>

            <!-- Logs Tab -->
            <button
              type="button"
              class="flex-1 flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-bold transition-all duration-200 cursor-pointer"
              :class="activeSideTab === 'logs'
                ? 'bg-white text-blue-700 shadow-xs border border-slate-200/60'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-300/50'"
              @click="activeSideTab = 'logs'"
            >
              <svg
                class="w-3.5 h-3.5 flex-shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
              <span>日志部分</span>
              <span
                v-if="store.logs.length > 0"
                class="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded-full"
                :class="hasErrorLogs ? 'bg-red-500 text-white' : 'bg-slate-400 text-white'"
              >
                {{ store.logs.length }}
              </span>
            </button>

            <!-- Width Toggle Button -->
            <button
              type="button"
              class="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-300/50 transition-colors cursor-pointer shrink-0"
              :title="sideWidth > 520 ? '还原标准宽度 (460px)' : '展开宽屏视图 (680px)'"
              @click="toggleSideWidth"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path v-if="sideWidth > 520" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
                <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Tab Content 1: Pipeline Progress -->
        <div
          v-show="activeSideTab === 'pipeline'"
          class="flex-1 min-h-0 flex flex-col overflow-hidden"
        >
          <PipelineView />
        </div>

        <!-- Tab Content 2: Log Viewer -->
        <div
          v-show="activeSideTab === 'logs'"
          class="flex-1 min-h-0 flex flex-col overflow-hidden"
        >
          <LogViewer />
        </div>
      </div>
    </div>

    <SettingsDialog ref="settingsRef" />
    <StashDialog
      ref="stashRef"
      @cancel="onStashCancel"
      @skip="onStashSkip"
      @stash="onStashContinue"
    />
    <ConfirmDialog
      ref="confirmRef"
      @confirm="onConfirmExecute"
    />
    <UpdateDialog ref="updateRef" />

    <!-- Toast notifications container -->
    <div class="fixed top-4 right-4 z-[9999] space-y-2 pointer-events-none w-80">
      <transition-group name="toast-fade">
        <div
          v-for="toast in store.toasts"
          :key="toast.id"
          class="toast pointer-events-auto flex items-center justify-between p-3.5 rounded-xl shadow-xl text-sm font-semibold text-white transition-all duration-300 transform"
          :class="{
            'bg-blue-600': toast.type === 'info',
            'bg-green-600': toast.type === 'success',
            'bg-red-600': toast.type === 'error',
            'bg-yellow-600': toast.type === 'warning',
          }"
        >
          <div class="flex items-center gap-2">
            <svg
              v-if="toast.type === 'success'"
              class="w-4 h-4 text-green-100 flex-shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <svg
              v-else-if="toast.type === 'error'"
              class="w-4 h-4 text-red-100 flex-shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <svg
              v-else
              class="w-4 h-4 text-blue-100 flex-shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span>{{ toast.message }}</span>
          </div>
        </div>
      </transition-group>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, toRaw, watch } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { ipc } from '@/services/ipc'
import HeaderBar from '@/components/HeaderBar.vue'
import AppPortal from '@/components/AppPortal.vue'
import MockQueryTool from '@/components/MockQueryTool.vue'
import OrderDeployTool from '@/components/OrderDeployTool.vue'
import CommandForm from '@/components/CommandForm.vue'
import ProjectTable from '@/components/ProjectTable.vue'
import PipelineView from '@/components/PipelineView.vue'
import LogViewer from '@/components/LogViewer.vue'
import ActionBar from '@/components/ActionBar.vue'
import SettingsDialog from '@/components/SettingsDialog.vue'
import StashDialog from '@/components/StashDialog.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import UpdateDialog from '@/components/UpdateDialog.vue'
import { refreshProjects } from '@/composables/useProjects'
import { setupRunListeners, startRun, stopRun } from '@/composables/usePipeline'
import { checkLocalChanges } from '@/composables/useProjects'
import { saveConfig } from '@/composables/useConfig'
import type { UploadMode, LocalChangeSummary, AppConfig } from '@/types'

const currentApp = ref<'zbuild' | 'portal' | 'mock-query' | 'order-deploy'>('portal')

function onSwitchApp(appId: string) {
  if (appId === 'portal') {
    currentApp.value = 'portal'
  } else if (appId === 'mock-query') {
    currentApp.value = 'mock-query'
  } else if (appId === 'order-deploy') {
    currentApp.value = 'order-deploy'
  } else {
    currentApp.value = 'zbuild'
  }
}

interface RunPayloadProject {
  name: string
  path?: string
  branch: string
  svn_leaf?: string
  server_upload_path?: string
  build_command?: string
  enabled: boolean
}

interface RunPayload {
  config: Record<string, unknown>
  projects: RunPayloadProject[]
  mode: UploadMode
  stash?: boolean
}

const store = useAppStore()
const activeSideTab = ref<'pipeline' | 'logs'>('pipeline')
const settingsRef = ref<InstanceType<typeof SettingsDialog> | null>(null)
const confirmRef = ref<InstanceType<typeof ConfirmDialog> | null>(null)
const stashRef = ref<InstanceType<typeof StashDialog> | null>(null)
const updateRef = ref<InstanceType<typeof UpdateDialog> | null>(null)
const pendingPayload = ref<RunPayload | null>(null)
const pendingDirtyNames = ref<Set<string>>(new Set())

// Resizable Side Panel
const sideWidth = ref(460)
const isResizing = ref(false)

function onStartResize(e: MouseEvent) {
  isResizing.value = true
  const startX = e.clientX
  const startWidth = sideWidth.value

  const onMouseMove = (moveEvent: MouseEvent) => {
    const delta = startX - moveEvent.clientX
    const newWidth = Math.min(Math.max(startWidth + delta, 360), 850)
    sideWidth.value = newWidth
  }

  const onMouseUp = () => {
    isResizing.value = false
    window.removeEventListener('mousemove', onMouseMove)
    window.removeEventListener('mouseup', onMouseUp)
  }

  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
}

function toggleSideWidth() {
  if (sideWidth.value > 520) {
    sideWidth.value = 460
  } else {
    sideWidth.value = 680
  }
}

// Switch to pipeline tab when running starts
watch(
  () => store.running,
  (isRunning) => {
    if (isRunning) {
      activeSideTab.value = 'pipeline'
    }
  }
)

const pipelineTabBadge = computed(() => {
  if (store.running) {
    return '执行中'
  }
  const total = Object.keys(store.projectStates).length
  if (total > 0) {
    if (store.failureCount > 0) {
      return `失败 ${store.failureCount}`
    }
    return `${store.successCount}/${total}`
  }
  return ''
})

const pipelineBadgeClass = computed(() => {
  if (store.running) {
    return 'bg-blue-100 text-blue-700'
  }
  if (store.failureCount > 0) {
    return 'bg-red-100 text-red-700'
  }
  if (store.successCount > 0) {
    return 'bg-emerald-100 text-emerald-700'
  }
  return 'bg-slate-200 text-slate-600'
})

const hasErrorLogs = computed(() => {
  return store.logs.some((l) => l.level === 'error')
})

const orderDeployRef = ref<InstanceType<typeof OrderDeployTool> | null>(null)

function onOpenSettings() {
  if (currentApp.value === 'order-deploy') {
    if (orderDeployRef.value) {
      orderDeployRef.value.openSettings()
    }
  } else {
    if (settingsRef.value) {
      settingsRef.value.visible = true
    }
  }
}

function onSetMode(mode: UploadMode) {
  if (!store.config) return
  store.config.uploadAfterBuild = mode === 'svn'
  store.config.uploadToServer = mode === 'server'
}

function buildPayload(onlyFailed = false): RunPayload {
  const projectMap = new Map(store.projects.map((p) => [p.projectName, p]))

  let names: string[]
  if (onlyFailed) {
    // Only include projects that failed in the last run
    names = Object.entries(store.projectStates)
      .filter(([, state]) => state.status === 'failed')
      .map(([name]) => name)
  } else {
    names = Array.from(store.selectedProjects)
  }

  const selectedList: RunPayloadProject[] = []
  for (const name of names) {
    const proj = projectMap.get(name)
    if (proj) {
      const branch = store.projectBranches[name] || proj.currentBranch || ''
      selectedList.push({
        name: proj.projectName,
        path: proj.repoPath,
        branch,
        svn_leaf: store.projectSvnLeaves[name] || proj.defaultSvnLeaf || '',
        server_upload_path: store.projectServerPaths[name] || proj.serverUploadPath || '',
        build_command: store.getEffectiveBuildCommand(name, branch),
        enabled: true,
      })
    }
  }

  // Build config with per-project server path and build command overrides merged in
  const rawConfig = JSON.parse(JSON.stringify(toRaw(store.config)))
  if (!rawConfig.buildCommand) {
    rawConfig.buildCommand = 'deploy.sh'
  }
  if (rawConfig.serverUploadPaths) {
    Object.assign(rawConfig.serverUploadPaths, store.projectServerPaths)
  } else {
    rawConfig.serverUploadPaths = { ...store.projectServerPaths }
  }
  if (rawConfig.buildCommands) {
    Object.assign(rawConfig.buildCommands, store.projectBuildCommands)
  } else {
    rawConfig.buildCommands = { ...store.projectBuildCommands }
  }

  return {
    config: rawConfig,
    projects: selectedList,
    mode: store.mode,
  }
}

function validatePayload(payload: RunPayload): string | null {
  const mode = payload.mode || store.mode
  const projects = payload.projects || []

  // 1. At least one project
  if (projects.length === 0) {
    return '请至少选择一个项目。'
  }

  // 2. SVN mode: hospital name and order number required
  if (mode === 'svn') {
    const form = store.config?.form
    if (!form?.hospitalName || !form?.orderNo) {
      return 'SVN 上传模式下，医院名称和订单号不能为空。'
    }
    if (!form?.svnUsername || !form?.svnPassword) {
      return 'SVN 上传模式下，必须填写 SVN 账号和密码。'
    }
  }

  // 3. Server mode: server credentials required
  if (mode === 'server') {
    const form = store.config?.form
    if (!form?.serverAddress || !form?.serverUsername || !form?.serverPassword) {
      return '服务器上传模式下，必须填写服务器地址、用户名和密码。'
    }
    // Every selected project must have a server upload path
    const missing = projects
      .filter((p) => !p.server_upload_path && !store.config?.serverUploadPaths?.[p.name])
      .map((p) => p.name)
    if (missing.length > 0) {
      return '以下项目未配置服务器上传路径：' + missing.join('、')
    }
  }

  return null
}

async function onStart() {
  const payload = buildPayload()

  // Validate before proceeding
  const error = validatePayload(payload)
  if (error) {
    store.showToast(error, 'error')
    return
  }

  // Check for local changes before starting
  try {
    const config = store.config
    if (config) {
      const projectsForCheck = payload.projects
        .map((p) => ({ project: p.name, branch: p.branch }))
      const changes = await checkLocalChanges(projectsForCheck)
      const dirtyChanges = changes.filter((c: LocalChangeSummary) => c.dirty)
      if (dirtyChanges.length > 0) {
        // Store payload and dirty project names for the stash dialog
        pendingPayload.value = payload
        pendingDirtyNames.value = new Set(dirtyChanges.map((c: LocalChangeSummary) => c.project).filter((p): p is string => Boolean(p)))
        if (stashRef.value) {
          stashRef.value.show(dirtyChanges)
        }
        return
      }
    }
  } catch (e) {
    console.warn('Local change check failed, proceeding:', e)
  }

  if (confirmRef.value) {
    confirmRef.value.show(payload)
  }
}

function onRetry() {
  const payload = buildPayload(true)
  const error = validatePayload(payload)
  if (error) {
    store.showToast(error, 'error')
    return
  }
  if (confirmRef.value) {
    confirmRef.value.show(payload)
  }
}

async function onConfirmExecute(confirmedPayload: RunPayload | null) {
  if (confirmedPayload) {
    // Save config before running to ensure latest settings are persisted
    try {
      if (store.config) {
        await saveConfig(store.config)
      }
    } catch (e) {
      console.warn('Failed to save config before run:', e)
    }
    await startRun(confirmedPayload as unknown as Record<string, unknown>)
  }
}

async function onStop() {
  await stopRun()
}

// -- Stash dialog handlers --
function onStashCancel() {
  // User chose to cancel -- do nothing, just close
  pendingPayload.value = null
  pendingDirtyNames.value = new Set()
}

function onStashSkip() {
  // Skip dirty projects: filter them out from pending payload and proceed
  if (!pendingPayload.value) return
  const dirtyNames = pendingDirtyNames.value
  // Filter out dirty projects from payload (keep only clean ones)
  const filteredPayload: RunPayload = {
    ...pendingPayload.value,
    projects: (pendingPayload.value.projects || [])
      .filter((p) => !dirtyNames.has(p.name)),
  }
  pendingPayload.value = null
  pendingDirtyNames.value = new Set()
  if (filteredPayload.projects.length === 0) {
    store.showToast('所有选中的项目都有本地变更，无法跳过。请选择"继续并 stash"或取消。', 'warning')
    return
  }
  if (confirmRef.value) {
    confirmRef.value.show(filteredPayload)
  }
}

function onStashContinue() {
  // Continue with stash: proceed with the pipeline, backend will stash changes
  if (!pendingPayload.value) return
  const payload: RunPayload = { ...pendingPayload.value, stash: true }
  pendingPayload.value = null
  pendingDirtyNames.value = new Set()
  if (confirmRef.value) {
    confirmRef.value.show(payload)
  }
}

const defaultConfig: AppConfig = {
  rootPath: '',
  svnRootUrl: 'https://10.1.1.120/svn/智慧病房特殊订单',
  svnLocations: [
    {
      id: 'loc-default',
      name: '默认特殊订单库',
      url: 'https://10.1.1.120/svn/智慧病房特殊订单',
      isDefault: true,
    },
  ],
  buildCommand: 'deploy.sh',
  buildCommands: {},
  artifactPaths: ['dist', 'release', 'build', 'output', 'target'],
  projectArtifactPaths: {},
  orderDirPath: '',
  selectedProjects: [],
  projectBranches: {},
  projectSvnLeaves: {},
  projectServerPaths: {},
  projectBuildCommands: {},
  tools: {
    git: '',
    bash: '',
    svn: '',
    node: '',
    npm: '',
  },
  uploadAfterBuild: true,
  uploadToServer: false,
  localOutputDir: '',
  serverUploadPaths: {},
  form: {
    hospitalName: '',
    orderNo: '',
    orderNotes: '',
    createOrderDir: false,
    svnUsername: '',
    svnPassword: '',
    serverAddress: '',
    serverUsername: '',
    serverPassword: '',
  },
}

onMounted(async () => {
  if (!window.tool) {
    store.config = JSON.parse(JSON.stringify(defaultConfig))
    return
  }

  try {
    try {
      store.config = await ipc.getConfig()
    } catch (e) {
      console.error('Failed to get config from backend:', e)
      store.config = JSON.parse(JSON.stringify(defaultConfig))
      store.showToast('配置读取失败，已启用默认配置。请检查环境', 'warning')
    }

    if (!store.config) {
      store.config = JSON.parse(JSON.stringify(defaultConfig))
    }
    const cfg = store.config!
    if (!cfg.svnLocations || cfg.svnLocations.length === 0) {
      cfg.svnLocations = [
        {
          id: 'loc-default',
          name: '默认特殊订单库',
          url: cfg.svnRootUrl || 'https://10.1.1.120/svn/智慧病房特殊订单',
          isDefault: true,
        },
      ]
    }
    if (!cfg.tools) {
      cfg.tools = { git: '', bash: '', svn: '', node: '', npm: '' }
    }

    // Auto-detect tools - always run detection to ensure paths are set
    try {
      const detection = await ipc.detectTools(JSON.parse(JSON.stringify(toRaw(cfg))))
      if (detection && detection.tools) {
        const d = detection.tools as unknown as Record<string, { path?: string; version?: string } | string>
        const getPath = (key: string) => {
          const v = d[key]
          return typeof v === 'string' ? v : (v && typeof v === 'object' && 'path' in v ? v.path || '' : '')
        }
        const git = getPath('git')
        const bash = getPath('bash')
        const svn = getPath('svn')
        const node = getPath('node')
        const npm = getPath('npm')
        if (git) cfg.tools.git = git
        if (bash) cfg.tools.bash = bash
        if (svn) cfg.tools.svn = svn
        if (node && !cfg.tools.node) cfg.tools.node = node
        if (npm && !cfg.tools.npm) cfg.tools.npm = npm
      }
    } catch (e) {
      console.warn('Auto-detect tools failed:', e)
    }

    try {
      await refreshProjects()
    } catch (e) {
      console.warn('Failed to refresh projects on startup:', e)
    }
    setupRunListeners()
    try {
      if (updateRef.value) {
        await updateRef.value.check()
      }
    } catch (e) {
      console.warn('Update check failed on startup:', e)
    }
  } catch (error) {
    console.error('Failed to initialize:', error)
  }
})
</script>

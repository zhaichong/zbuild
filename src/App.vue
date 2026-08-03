<template>
  <div class="min-h-screen bg-bg-base">
    <!-- Full-width gradient header -->
    <HeaderBar
      @open-settings="onOpenSettings"
      @set-mode="onSetMode"
    />

    <!-- Two-column shell -->
    <div class="app-shell">
      <!-- Left: Main scrollable column -->
      <div class="main-col">
        <div class="space-y-4">
          <TemplateSelector />
          <CommandForm />
          <ProjectTable />
          <ActionBar
            @start="onStart"
            @stop="onStop"
            @retry="onRetry"
          />
        </div>
      </div>

      <!-- Right: Side panel (progress + logs tabs) -->
      <div class="side-col">
        <!-- Tabs Header -->
        <div class="p-2 bg-slate-50 border-b border-slate-200 flex-shrink-0 select-none">
          <div class="flex items-center gap-1 p-1 bg-slate-200/70 rounded-xl">
            <!-- Pipeline Tab -->
            <button
              type="button"
              class="flex-1 flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-bold transition-all duration-200 cursor-pointer"
              :class="activeSideTab === 'pipeline'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'"
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
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'"
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
                class="text-[10px] font-mono font-semibold px-1.5 py-0.2 rounded-full"
                :class="hasErrorLogs ? 'bg-red-100 text-red-700' : 'bg-slate-300/80 text-slate-700'"
              >
                {{ store.logs.length }}
              </span>
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
import TemplateSelector from '@/components/TemplateSelector.vue'
import CommandForm from '@/components/CommandForm.vue'
import ProjectTable from '@/components/ProjectTable.vue'
import PipelineView from '@/components/PipelineView.vue'
import LogViewer from '@/components/LogViewer.vue'
import ActionBar from '@/components/ActionBar.vue'
import SettingsDialog from '@/components/SettingsDialog.vue'
import StashDialog from '@/components/StashDialog.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { refreshProjects } from '@/composables/useProjects'
import { setupRunListeners, startRun, stopRun } from '@/composables/usePipeline'
import { checkLocalChanges } from '@/composables/useProjects'
import { saveConfig } from '@/composables/useConfig'
import type { UploadMode, LocalChangeSummary } from '@/types'

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
const pendingPayload = ref<RunPayload | null>(null)
const pendingDirtyNames = ref<Set<string>>(new Set())

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

function onOpenSettings() {
  if (settingsRef.value) {
    settingsRef.value.visible = true
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
      selectedList.push({
        name: proj.projectName,
        path: proj.repoPath,
        branch: store.projectBranches[name] || proj.currentBranch || '',
        svn_leaf: store.projectSvnLeaves[name] || proj.defaultSvnLeaf || '',
        server_upload_path: store.projectServerPaths[name] || proj.serverUploadPath || '',
        build_command:
          store.projectBuildCommands[name] ||
          store.config?.buildCommands?.[name] ||
          proj.buildCommand ||
          store.config?.buildCommand ||
          'deploy.sh',
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

onMounted(async () => {
  try {
    store.config = await ipc.getConfig()
    // Auto-detect tools - always run detection to ensure paths are set
    if (store.config) {
      try {
        const detection = await ipc.detectTools(JSON.parse(JSON.stringify(toRaw(store.config))))
        if (detection.tools) {
          const d = detection.tools as unknown as Record<string, { path?: string; version?: string } | string>
          const getPath = (key: string) => {
            const v = d[key]
            return typeof v === 'string' ? v : (v && typeof v === 'object' && 'path' in v ? v.path || '' : '')
          }
          // Prefer detected paths so discover/refresh always receive a real git.exe
          // (Electron desktop launches often lack Git on PATH).
          const git = getPath('git')
          const bash = getPath('bash')
          const svn = getPath('svn')
          if (git) store.config.tools.git = git
          if (bash) store.config.tools.bash = bash
          if (svn && !store.config.tools.svn) store.config.tools.svn = svn
        }
      } catch (e) {
        console.warn('Auto-detect tools failed:', e)
      }
    }
    try {
      await refreshProjects()
    } catch (e) {
      console.warn('Failed to refresh projects on startup:', e)
    }
    setupRunListeners()
  } catch (error) {
    console.error('Failed to initialize:', error)
  }
})
</script>

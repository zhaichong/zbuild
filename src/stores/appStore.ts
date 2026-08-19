import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  AppConfig,
  ProjectInfo,
  ProjectRunState,
  LogEntry,
  TaskTemplate,
  StepState,
  StepStatusType,
  UploadMode,
  ToastInfo,
} from '@/types'

export const useAppStore = defineStore('app', () => {
  const config = ref<AppConfig | null>(null)
  const projects = ref<ProjectInfo[]>([])
  const selectedProjects = ref<Set<string>>(new Set())
  const projectBranches = ref<Record<string, string>>({})
  const projectSvnLeaves = ref<Record<string, string>>({})
  const projectSvnRoots = ref<Record<string, string>>({})
  const projectServerPaths = ref<Record<string, string>>({})
  const projectBuildCommands = ref<Record<string, string>>({})
  const running = ref(false)
  const projectStates = ref<Record<string, ProjectRunState>>({})
  const logs = ref<LogEntry[]>([])
  const templates = ref<TaskTemplate[]>([])
  const activeTemplateId = ref<string>('')
  const toasts = ref<ToastInfo[]>([])

  const mode = computed<UploadMode>(() => {
    if (!config.value) return 'svn'
    if (config.value.uploadToServer) return 'server'
    if (config.value.uploadAfterBuild) return 'svn'
    return 'local'
  })

  const selectedCount = computed(() => selectedProjects.value.size)

  const successCount = computed(() => {
    return Object.values(projectStates.value).filter((p) => p.status === 'done').length
  })

  const failureCount = computed(() => {
    return Object.values(projectStates.value).filter((p) => p.status === 'failed').length
  })

  function showToast(message: string, type: 'info' | 'success' | 'error' | 'warning' = 'info', duration = 3000) {
    const id = Math.random().toString(36).substring(2, 9)
    toasts.value.push({ id, message, type, duration })
    setTimeout(() => {
      toasts.value = toasts.value.filter((t) => t.id !== id)
    }, duration)
  }

  function addLog(entry: LogEntry) {
    logs.value.push(entry)
  }

  function clearLogs() {
    logs.value = []
  }

  function resetRunState() {
    running.value = false
    projectStates.value = {}
    clearLogs()
  }

  function toggleProject(projectName: string) {
    const newSet = new Set(selectedProjects.value)
    if (newSet.has(projectName)) {
      newSet.delete(projectName)
    } else {
      newSet.add(projectName)
    }
    selectedProjects.value = newSet
  }

  function selectAll() {
    selectedProjects.value = new Set(projects.value.map((p) => p.projectName))
  }

  function deselectAll() {
    selectedProjects.value = new Set()
  }

  function setProjectState(projectName: string, state: Partial<ProjectRunState>) {
    const current = projectStates.value[projectName] || {
      projectName,
      status: 'pending' as StepStatusType,
      statusClass: 'text-gray-500',
      currentStep: '',
      steps: [],
    }
    projectStates.value[projectName] = { ...current, ...state }
  }

  function setStepState(projectName: string, step: string, status: StepStatusType, message?: string) {
    const state = projectStates.value[projectName]
    if (!state) return

    const stepIndex = state.steps.findIndex((s) => s.step === step)
    const stepState: StepState = { step, status, message }

    if (stepIndex >= 0) {
      state.steps[stepIndex] = stepState
    } else {
      state.steps.push(stepState)
    }

    state.currentStep = step
    if (status === 'failed') {
      state.status = 'failed'
      state.statusClass = 'text-red-600'
    } else if (status === 'running') {
      state.status = 'running'
      state.statusClass = 'text-blue-600'
    }
  }

  function getEffectiveBuildCommand(projectName: string, branch?: string): string {
    const targetBranch = branch || projectBranches.value[projectName] || ''
    const branchCmds = config.value?.branchBuildCommands?.[projectName]
    if (branchCmds && targetBranch) {
      if (branchCmds[targetBranch]) {
        return branchCmds[targetBranch]
      }
      for (const [pattern, cmd] of Object.entries(branchCmds)) {
        if (pattern.endsWith('*')) {
          const prefix = pattern.slice(0, -1)
          if (targetBranch.startsWith(prefix)) {
            return cmd
          }
        }
      }
    }
    return (
      config.value?.buildCommands?.[projectName] ||
      projectBuildCommands.value[projectName] ||
      config.value?.buildCommand ||
      'deploy.sh'
    )
  }

  return {
    config,
    projects,
    selectedProjects,
    projectBranches,
    projectSvnLeaves,
    projectSvnRoots,
    projectServerPaths,
    projectBuildCommands,
    running,
    projectStates,
    logs,
    templates,
    activeTemplateId,
    mode,
    selectedCount,
    successCount,
    failureCount,
    toasts,
    showToast,
    addLog,
    clearLogs,
    resetRunState,
    toggleProject,
    selectAll,
    deselectAll,
    setProjectState,
    setStepState,
    getEffectiveBuildCommand,
  }
})

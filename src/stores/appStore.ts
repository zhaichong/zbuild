import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  AppConfig,
  ProjectInfo,
  ProjectRunState,
  LogEntry,
  TaskTemplate,
  ExecutionRecord,
  StepState,
  StepStatusType,
  UploadMode,
} from '@/types'

export const useAppStore = defineStore('app', () => {
  const config = ref<AppConfig | null>(null)
  const projects = ref<ProjectInfo[]>([])
  const selectedProjects = ref<Set<string>>(new Set())
  const projectBranches = ref<Record<string, string>>({})
  const projectSvnLeaves = ref<Record<string, string>>({})
  const projectServerPaths = ref<Record<string, string>>({})
  const running = ref(false)
  const failedProjects = ref<Set<string>>(new Set())
  const projectStates = ref<Record<string, ProjectRunState>>({})
  const logs = ref<LogEntry[]>([])
  const templates = ref<TaskTemplate[]>([])
  const historyRecords = ref<ExecutionRecord[]>([])

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

  function addLog(entry: LogEntry) {
    logs.value.push(entry)
  }

  function clearLogs() {
    logs.value = []
  }

  function resetRunState() {
    running.value = false
    failedProjects.value.clear()
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
      failedProjects.value.add(projectName)
    } else if (status === 'done') {
      state.status = 'done'
      state.statusClass = 'text-green-600'
    } else if (status === 'running') {
      state.status = 'running'
      state.statusClass = 'text-blue-600'
    }
  }

  return {
    config,
    projects,
    selectedProjects,
    projectBranches,
    projectSvnLeaves,
    projectServerPaths,
    running,
    failedProjects,
    projectStates,
    logs,
    templates,
    historyRecords,
    mode,
    selectedCount,
    successCount,
    failureCount,
    addLog,
    clearLogs,
    resetRunState,
    toggleProject,
    selectAll,
    deselectAll,
    setProjectState,
    setStepState,
  }
})

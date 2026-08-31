import { toRaw } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { ipc } from '@/services/ipc'
import type { ProjectInfo, LocalChangeSummary } from '@/types'

const STORAGE_KEY_SELECTED_BRANCHES = 'zbuild_selected_branches'
const STORAGE_KEY_CACHED_BRANCHES = 'zbuild_cached_branches'

function loadStoredSelectedBranches(): Record<string, string> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_SELECTED_BRANCHES)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

function saveStoredSelectedBranches(branches: Record<string, string>) {
  try {
    localStorage.setItem(STORAGE_KEY_SELECTED_BRANCHES, JSON.stringify(branches))
  } catch {
    // ignore
  }
}

function loadStoredCachedBranches(): Record<string, string[]> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_CACHED_BRANCHES)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

function saveStoredCachedBranches(projectName: string, branches: string[]) {
  try {
    const cached = loadStoredCachedBranches()
    cached[projectName] = branches
    localStorage.setItem(STORAGE_KEY_CACHED_BRANCHES, JSON.stringify(cached))
  } catch {
    // ignore
  }
}

export async function refreshProjects(): Promise<ProjectInfo[]> {
  const store = useAppStore()
  if (!store.config || !store.config.rootPath) return []

  const projects = await ipc.discoverProjects(store.config.rootPath, JSON.parse(JSON.stringify(toRaw(store.config.tools))))
  
  // Restore cached branch lists from localStorage for instant display
  const cachedBranchesMap = loadStoredCachedBranches()
  const storedSelectedBranches = loadStoredSelectedBranches()

  for (const project of projects) {
    if (cachedBranchesMap[project.projectName] && cachedBranchesMap[project.projectName].length > 0) {
      project.branches = cachedBranchesMap[project.projectName]
    }
  }

  store.projects = projects

  for (const project of projects) {
    // Preserve previously selected target branch if available, fallback to currentBranch
    const savedBranch = storedSelectedBranches[project.projectName]
    store.projectBranches[project.projectName] = savedBranch || project.currentBranch

    if (project.defaultSvnLeaf) {
      store.projectSvnLeaves[project.projectName] = project.defaultSvnLeaf
    }
    const serverPath =
      store.config.serverUploadPaths?.[project.projectName] ||
      project.serverUploadPath ||
      ''
    if (serverPath) {
      store.projectServerPaths[project.projectName] = serverPath
    }
    const buildCmd =
      store.config.buildCommands?.[project.projectName] ||
      project.buildCommand ||
      store.config.buildCommand ||
      'deploy.sh'
    store.projectBuildCommands[project.projectName] = buildCmd
  }

  // Automatically pre-fetch and refresh remote branches for all projects in background
  Promise.allSettled(
    projects.map((p) => refreshBranches(p.projectName, true))
  ).catch(() => {})

  return projects
}

export async function refreshBranches(projectName: string, _silent = false): Promise<ProjectInfo> {
  const store = useAppStore()
  if (!store.config) throw new Error('Config not loaded')

  const project = store.projects.find((p) => p.projectName === projectName)
  if (!project) throw new Error(`Project ${projectName} not found`)

  const updated = await ipc.refreshProjectBranches(
    project.repoPath,
    JSON.parse(JSON.stringify(toRaw(store.config.tools))),
    JSON.parse(JSON.stringify(toRaw(store.config.serverUploadPaths || {}))),
  )

  const index = store.projects.findIndex((p) => p.projectName === projectName)
  if (index >= 0) {
    const existing = store.projects[index]
    const newBranches = updated.branches.length > 0 ? updated.branches : existing.branches
    store.projects[index] = {
      ...existing,
      branches: newBranches,
      currentBranch: updated.currentBranch || existing.currentBranch,
    }

    if (newBranches && newBranches.length > 0) {
      saveStoredCachedBranches(projectName, newBranches)
    }

    // If no target branch is selected or user hasn't explicitly picked one, keep existing or fallback
    const currentTarget = store.projectBranches[projectName]
    if (!currentTarget) {
      store.projectBranches[projectName] = store.projects[index].currentBranch
    }
    saveStoredSelectedBranches(store.projectBranches)
  }

  return updated
}

export async function checkLocalChanges(
  projects: Array<{ project: string; branch: string }>,
): Promise<LocalChangeSummary[]> {
  const store = useAppStore()
  if (!store.config) return []

  return await ipc.checkLocalChanges(store.config.rootPath, JSON.parse(JSON.stringify(toRaw(store.config.tools))), projects)
}

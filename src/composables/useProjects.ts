import { toRaw } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { ipc } from '@/services/ipc'
import type { ProjectInfo, LocalChangeSummary } from '@/types'

export async function refreshProjects(): Promise<ProjectInfo[]> {
  const store = useAppStore()
  if (!store.config || !store.config.rootPath) return []

  const projects = await ipc.discoverProjects(store.config.rootPath, JSON.parse(JSON.stringify(toRaw(store.config.tools))))
  store.projects = projects

  for (const project of projects) {
    store.projectBranches[project.projectName] = project.currentBranch
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

  return projects
}

export async function refreshBranches(projectName: string): Promise<ProjectInfo> {
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
    store.projects[index] = {
      ...existing,
      branches: updated.branches.length > 0 ? updated.branches : existing.branches,
      currentBranch: updated.currentBranch || existing.currentBranch,
    }
    store.projectBranches[projectName] = store.projects[index].currentBranch
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

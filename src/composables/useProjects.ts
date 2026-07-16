import { useAppStore } from '@/stores/appStore'
import { ipc } from '@/services/ipc'
import type { ProjectInfo, LocalChangeSummary } from '@/types'

export async function refreshProjects(): Promise<ProjectInfo[]> {
  const store = useAppStore()
  if (!store.config) return []

  const projects = await ipc.discoverProjects(store.config.rootPath, store.config.tools)
  store.projects = projects

  for (const project of projects) {
    store.projectBranches[project.projectName] = project.currentBranch
    if (project.defaultSvnLeaf) {
      store.projectSvnLeaves[project.projectName] = project.defaultSvnLeaf
    }
    if (project.serverUploadPath) {
      store.projectServerPaths[project.projectName] = project.serverUploadPath
    }
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
    store.config.tools,
    store.config.serverUploadPaths,
  )

  const index = store.projects.findIndex((p) => p.projectName === projectName)
  if (index >= 0) {
    store.projects[index] = updated
    store.projectBranches[projectName] = updated.currentBranch
  }

  return updated
}

export async function checkLocalChanges(
  projects: Array<{ project: string; branch: string }>,
): Promise<LocalChangeSummary[]> {
  const store = useAppStore()
  if (!store.config) return []

  return await ipc.checkLocalChanges(store.config.rootPath, store.config.tools, projects)
}

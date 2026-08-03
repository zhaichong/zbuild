import { ref } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { ipc } from '@/services/ipc'

export function useAffected() {
  const store = useAppStore()
  const loading = ref(false)
  const affectedProjects = ref<string[]>([])

  async function detectAffected(
    baseRef: string = 'main',
    headRef: string = 'HEAD'
  ): Promise<string[]> {
    loading.value = true
    try {
      const config = store.config
      if (!config?.rootPath) {
        return []
      }

      // Get the repo path from the first project or use rootPath
      const repoPath = store.projects[0]?.repoPath || config.rootPath
      const searchDirs = [config.rootPath]

      const result = await ipc.detectAffected(repoPath, searchDirs, baseRef, headRef)
      affectedProjects.value = result.affectedProjects

      return result.affectedProjects
    } catch (err) {
      console.error('Failed to detect affected projects:', err)
      return []
    } finally {
      loading.value = false
    }
  }

  async function detectAffectedStaged(): Promise<string[]> {
    loading.value = true
    try {
      const config = store.config
      if (!config?.rootPath) {
        return []
      }

      const repoPath = store.projects[0]?.repoPath || config.rootPath
      const searchDirs = [config.rootPath]

      const result = await ipc.detectAffectedStaged(repoPath, searchDirs)
      affectedProjects.value = result.affectedProjects

      return result.affectedProjects
    } catch (err) {
      console.error('Failed to detect staged affected projects:', err)
      return []
    } finally {
      loading.value = false
    }
  }

  function selectAffected() {
    // Deselect all first
    store.deselectAll()
    // Select only affected projects
    for (const projectName of affectedProjects.value) {
      if (!store.selectedProjects.has(projectName)) {
        store.toggleProject(projectName)
      }
    }
  }

  return {
    loading,
    affectedProjects,
    detectAffected,
    detectAffectedStaged,
    selectAffected,
  }
}

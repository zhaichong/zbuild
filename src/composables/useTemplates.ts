import { useAppStore } from '@/stores/appStore'
import { ipc } from '@/services/ipc'
import type { TaskTemplate } from '@/types'

export async function loadTemplates(): Promise<TaskTemplate[]> {
  const store = useAppStore()
  const templates = await ipc.listTemplates()
  store.templates = templates
  return templates
}

export async function applyTemplate(templateId: string): Promise<void> {
  const store = useAppStore()
  if (!templateId) return
  const template = await ipc.getTemplate(templateId)

  if (template && template.config) {
    const cfg = template.config as any
    if (store.config) {
      store.config = {
        ...store.config,
        ...cfg,
        form: {
          ...store.config.form,
          ...(cfg.form || {}),
        },
      }
    }
    if (Array.isArray(cfg.selectedProjects)) {
      store.selectedProjects = new Set(cfg.selectedProjects)
    }
    if (cfg.projectBranches && typeof cfg.projectBranches === 'object') {
      store.projectBranches = { ...store.projectBranches, ...cfg.projectBranches }
    }
    if (cfg.projectSvnLeaves && typeof cfg.projectSvnLeaves === 'object') {
      store.projectSvnLeaves = { ...store.projectSvnLeaves, ...cfg.projectSvnLeaves }
    }
    if (cfg.projectServerPaths && typeof cfg.projectServerPaths === 'object') {
      store.projectServerPaths = { ...store.projectServerPaths, ...cfg.projectServerPaths }
    }
    if (cfg.projectBuildCommands && typeof cfg.projectBuildCommands === 'object') {
      store.projectBuildCommands = { ...store.projectBuildCommands, ...cfg.projectBuildCommands }
    }
    store.showToast(`已应用模板「${template.name}」`, 'info')
  }
}

export async function saveCurrentAsTemplate(
  name: string,
  description?: string,
): Promise<TaskTemplate> {
  const store = useAppStore()
  if (!store.config) throw new Error('未加载配置')

  const fullConfig = {
    ...store.config,
    selectedProjects: Array.from(store.selectedProjects),
    projectBranches: { ...store.projectBranches },
    projectSvnLeaves: { ...store.projectSvnLeaves },
    projectServerPaths: { ...store.projectServerPaths },
    projectBuildCommands: { ...store.projectBuildCommands },
  }

  const template = await ipc.saveTemplate({
    name,
    description: description || '',
    config: fullConfig as any,
  })

  await loadTemplates()
  store.showToast(`模板「${name}」保存成功`, 'success')
  return template
}

export async function deleteTemplate(templateId: string): Promise<void> {
  const store = useAppStore()
  await ipc.deleteTemplate(templateId)
  store.templates = store.templates.filter((t) => t.id !== templateId)
  store.showToast('模板删除成功', 'info')
}

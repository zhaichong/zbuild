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
  const template = await ipc.getTemplate(templateId)

  if (store.config && template.config) {
    store.config = {
      ...store.config,
      ...template.config,
    }
  }
}

export async function saveCurrentAsTemplate(
  name: string,
  description?: string,
): Promise<TaskTemplate> {
  const store = useAppStore()
  if (!store.config) throw new Error('Config not loaded')

  const template = await ipc.saveTemplate({
    name,
    description,
    config: store.config,
  })

  store.templates.push(template)
  return template
}

export async function deleteTemplate(templateId: string): Promise<void> {
  const store = useAppStore()
  await ipc.deleteTemplate(templateId)
  store.templates = store.templates.filter((t) => t.id !== templateId)
}

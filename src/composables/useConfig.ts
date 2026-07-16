import { useAppStore } from '@/stores/appStore'
import { ipc } from '@/services/ipc'
import type { AppConfig, ToolDetectionResult } from '@/types'

export async function saveConfig(config: AppConfig): Promise<AppConfig> {
  const store = useAppStore()
  const saved = await ipc.saveConfig(config)
  store.config = saved
  return saved
}

export async function detectTools(config: Partial<AppConfig>): Promise<ToolDetectionResult> {
  const result = await ipc.detectTools(config)
  return result
}

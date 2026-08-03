import { useAppStore } from '@/stores/appStore'
import { ipc } from '@/services/ipc'
import type { AppConfig } from '@/types'

export async function saveConfig(config: AppConfig): Promise<AppConfig> {
  const store = useAppStore()
  const saved = await ipc.saveConfig(config)
  store.config = saved
  return saved
}


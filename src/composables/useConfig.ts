import { useAppStore } from '@/stores/appStore'
import { ipc } from '@/services/ipc'
import type { AppConfig } from '@/types'

export async function saveConfig(config: AppConfig): Promise<AppConfig> {
  const store = useAppStore()
  const saved = await ipc.saveConfig(config)
  store.config = saved

  const svnUser = saved.form?.svnUsername?.trim()
  if (svnUser) {
    localStorage.setItem('zbuild_svn_username', svnUser)
  } else {
    localStorage.removeItem('zbuild_svn_username')
    localStorage.removeItem('zbuild.submitter')
  }

  return saved
}


import { onMounted } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { detectTools } from './useConfig'

export function useEnvDetect() {
  const store = useAppStore()

  async function detect() {
    if (!store.config) return

    const result = await detectTools(store.config)

    if (store.config) {
      store.config.tools = result.tools
    }

    return result
  }

  onMounted(async () => {
    await detect()
  })

  return {
    detect,
  }
}

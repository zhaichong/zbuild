import { computed, ref } from 'vue'
import { useAppStore } from '@/stores/appStore'
import type { LogEntry } from '@/types'

export function useLog() {
  const store = useAppStore()
  const stepFilter = ref<string>('')
  const projectFilter = ref<string>('')
  const levelFilter = ref<string>('')

  const filteredLogs = computed(() => {
    return store.logs.filter((log: LogEntry) => {
      if (stepFilter.value && !log.message.includes(stepFilter.value)) {
        return false
      }
      if (projectFilter.value && log.project !== projectFilter.value) {
        return false
      }
      if (levelFilter.value && log.level !== levelFilter.value) {
        return false
      }
      return true
    })
  })

  return {
    filteredLogs,
    stepFilter,
    projectFilter,
    levelFilter,
  }
}

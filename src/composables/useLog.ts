import { computed, ref } from 'vue'
import { useAppStore } from '@/stores/appStore'
import type { LogEntry } from '@/types'

export function useLog() {
  const store = useAppStore()
  const projectFilter = ref<string>('')
  const levelFilter = ref<string>('')
  const searchKeyword = ref<string>('')

  const counts = computed(() => {
    let info = 0
    let success = 0
    let warning = 0
    let error = 0
    for (const log of store.logs) {
      if (projectFilter.value && log.project !== projectFilter.value) continue
      if (log.level === 'error') error++
      else if (log.level === 'warning') warning++
      else if (log.level === 'success') success++
      else info++
    }
    return { all: store.logs.length, info, success, warning, error }
  })

  const filteredLogs = computed(() => {
    const q = searchKeyword.value.trim().toLowerCase()
    return store.logs.filter((log: LogEntry) => {
      if (projectFilter.value && log.project !== projectFilter.value) {
        return false
      }
      if (levelFilter.value && log.level !== levelFilter.value) {
        return false
      }
      if (q) {
        const msg = log.message.toLowerCase()
        const prj = (log.project || '').toLowerCase()
        if (!msg.includes(q) && !prj.includes(q)) {
          return false
        }
      }
      return true
    })
  })

  return {
    filteredLogs,
    projectFilter,
    levelFilter,
    searchKeyword,
    counts,
  }
}


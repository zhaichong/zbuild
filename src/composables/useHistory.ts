import { useAppStore } from '@/stores/appStore'
import { ipc } from '@/services/ipc'
import type { ExecutionRecord } from '@/types'

export async function loadHistory(): Promise<ExecutionRecord[]> {
  const store = useAppStore()
  const records = await ipc.listHistory()
  store.historyRecords = records
  return records
}

export async function getHistoryRecord(id: string): Promise<ExecutionRecord> {
  return await ipc.getHistory(id)
}
